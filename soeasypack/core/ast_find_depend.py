"""
ast分析依赖
@author: xmqsvip
Created on 2025-01-05
"""
import copy
import os
import re
import sys
from soeasypack.core.re_find_pkg import find_pkgs
from soeasypack.lib.modulegraph.modulegraph import ModuleGraph


def add_depends(depends: set, pkg_paths: set, special_pkgs: set, project_pkg_names: set):
    """

    """
    add_depend_paths = []
    depend_paths_append = add_depend_paths.append
    checked_dir = set()
    remove_paths = []
    has_web_engine = False
    sub_compile = re.compile(r'(?<!\\)#.*?$|(?:\'\'\'[\s\S]*?\'\'\'|\"\"\"[\s\S]*?\"\"\")', flags=re.MULTILINE)
    for depend_path in depends:
        if 'site-packages' not in depend_path:
            continue
        depend_path_split = depend_path.split('site-packages')
        package_name = depend_path_split[1].split('\\', 2)[1]
        package_path = depend_path_split[0] + f'site-packages\\{package_name}'
        if depend_path in checked_dir or os.path.isfile(package_path):
            continue
        checked_dir.add(package_path)
        is_remove = False
        for pkg_name in project_pkg_names:
            if pkg_name.lower() not in package_name.lower():
                is_remove = True
            else:
                is_remove = False
                break
        if is_remove:
            remove_paths.append(package_path)
            if package_path in pkg_paths:
                pkg_paths.remove(package_path)
            continue

        py_files_path = []
        other_files = {}
        py_files_append = py_files_path.append
        for root, dirs, files in os.walk(package_path, topdown=True):
            if '__pycache__' in root:
                continue
            for f in files:
                file_path = os.path.join(root, f)
                if f.endswith('.pyx'):
                    py_files_append(file_path)
                elif f.endswith('.py'):
                    if os.path.join(root, f) in depends:
                        py_files_append(file_path)
                else:
                    file_name = os.path.basename(file_path)
                    if f.endswith(('.json', '.pem')):
                        add_depend_paths.append(file_path)
                        continue
                    elif f.endswith('.dll'):
                        other_files[file_name] = file_path
                    elif f.endswith('.pyd'):
                        file_name = file_name.split('.', 1)[0]
                        other_files[file_name] = file_path

        # # 判断似乎否有 QtWebEngine
        if 'PySide' in package_path:
            for root, dirs, files in os.walk(package_path + '\\plugins'):
                for f in files:
                    depend_paths_append(os.path.join(root, f))
            if 'QtWebEngineWidgets' in depends:
                has_web_engine = True

        if not other_files:
            continue
        py_files_path.extend(other_files.values())
        for file in py_files_path:
            if not other_files:
                break
            file_name = os.path.basename(file)
            fined_dll_files = []
            mode = 'rb'
            encodings = None
            if file.endswith(('.py', 'pyx')):
                mode = 'r'
                encodings = 'utf-8'

            with open(file, mode=mode, encoding=encodings) as fp:
                content = fp.read()

            for dll_file_name in other_files:
                base_dll_name = dll_file_name.split('.', 1)[0]
                if base_dll_name.replace('Qt6', '') not in file_name:
                    is_in = False
                    if mode == 'rb':
                        dll_file_name = dll_file_name.encode('utf-8')
                        if dll_file_name.endswith(b'.dll'):
                            if dll_file_name in content:
                                is_in = True
                        else:
                            # # pyd
                            if b'.' + dll_file_name in content:
                                is_in = True
                    else:
                        # # py
                        # # 去除注释和文档字符串
                        content = sub_compile.sub('', content)
                        if dll_file_name in content or base_dll_name in content:
                            is_in = True

                    if is_in:

                        if mode == 'rb':
                            dll_file_name = dll_file_name.decode('utf-8')
                        depend_paths_append(other_files[dll_file_name])
                        fined_dll_files.append(dll_file_name)

            for f in fined_dll_files:
                del other_files[f]
            del content
            # # 去除WebEngine
            if not has_web_engine:
                depends_ = copy.deepcopy(add_depend_paths)
                for depend in depends_:
                    if 'Web' in depend:
                        add_depend_paths.remove(depend)
                del depends_
    depends_ = copy.deepcopy(depends)
    for depend_path in depends_:
        if 'site-packages' not in depend_path:
            continue
        for i in remove_paths:
            if i in depend_path and depend_path in depends:
                depends.remove(depend_path)
    del depends_
    for file_path in add_depend_paths:
        depends.add(file_path)

    # # 补充site-packages目录下的pyd
    current_env_dir = sys.prefix
    site_pkg_dir = os.path.join(current_env_dir, 'Lib\\site-packages')
    pyd_name_path = {}
    site_pkg_names = []
    for f in os.listdir(site_pkg_dir):
        ff = os.path.join(site_pkg_dir, f)
        if os.path.isfile(ff) and f.endswith('.pyd'):
            pyd_name_path[f.split('.', 1)[0]] = ff
        else:
            if ff in pkg_paths:
                site_pkg_names.append(f)

    for site_pkg_name in site_pkg_names:
        for pyd_name in pyd_name_path:
            if site_pkg_name in pyd_name:
                file_path = pyd_name_path[pyd_name]
                depends.add(file_path)

    # #补充python目录下的dll
    base_env_dir = sys.base_prefix
    for f in os.listdir(base_env_dir):
        if os.path.isfile(os.path.join(base_env_dir, f)) and f.endswith('.dll'):
            dll_file = os.path.join(base_env_dir, f)
            depends.add(dll_file)
    # # 补充encodings
    encodings_dir_files = ('gbk.py', 'latin_1.py', 'utf_8.py', 'utf_16_be.py', 'cp437.py')
    for encodings_file in encodings_dir_files:
        depends.add(os.path.join(base_env_dir, 'Lib', 'encodings', encodings_file))
    # # 补充libxxx.dll
    dlls_dir = os.path.join(base_env_dir, 'DLLs')
    for f in os.listdir(dlls_dir):
        file_path = os.path.join(dlls_dir, f)
        if 'lib' in f and os.path.isfile(file_path):
            dll_file_path = file_path
            depends.add(dll_file_path)
    # #补充tkinter包数据
    dlls_dir_files = []
    if 'tkinter' in special_pkgs:
        import tkinter
        import _tkinter
        tcl_version, tk_version = _tkinter.TCL_VERSION, _tkinter.TK_VERSION
        tcl_v = tcl_version.replace('.', '')
        tk_v = tk_version.replace('.', '')
        tcl = tkinter.Tcl()
        tcl_dir = tcl.eval("info library")
        tk_dir = f"{os.path.dirname(tcl_dir)}\\tk{tk_version}"
        dlls_dir_files.extend([f'tcl{tcl_v}t.dll', f'tk{tk_v}t.dll'])
        for root, _, files in os.walk(tcl_dir, topdown=True):
            for f in files:
                depends.add(os.path.join(root, f))
        for root, _, files in os.walk(tk_dir, topdown=True):
            if 'demos' in root or '__pycache__' in root:
                continue
            for f in files:
                depends.add(os.path.join(root, f))

    for dlls_file in dlls_dir_files:
        depends.add(os.path.join(dlls_dir, dlls_file))
    # #补充curl_cffi包数据
    if 'curl_cffi' in special_pkgs:
        for dir_ in os.listdir(site_pkg_dir):
            if 'curl_cffi' in dir_ and (not dir_.endswith('curl_cffi')):
                full_dir = os.path.join(site_pkg_dir, dir_)
                for root, dirs, files in os.walk(full_dir):
                    for f in files:
                        depends.add(os.path.join(root, f))


def analyze_depends(main_script_path, except_pkgs=None):
    """
    分析给定Python项目主文件的所有依赖关系。

    """

    base_env_dir = sys.base_prefix
    current_env_dir = sys.prefix
    sys_path = sys.path
    script_dir = os.path.dirname(os.path.abspath(main_script_path))
    search_paths = [script_dir]
    for path in sys_path:
        if base_env_dir in path or current_env_dir in path:
            search_paths.append(path)

    sys.path = search_paths

    excludes = ['IPython', 'test', 'lib2to3', 'pydoc_data', 'tests', 'pkg_resources',
                'pycparser', 'packaging', 'setuptools', 'unittest', 'IPython',
                'PyInstaller', 'nuitka', 'cx_Freeze', 'py2exe', 'soeasypack']
    project_pkg_names = find_pkgs(main_script_path)
    check_pkgs = ('PySide2', 'PySide6', 'PyQt5', 'PyQt6')
    for check_pkg in check_pkgs:
        if check_pkg not in project_pkg_names:
            excludes.append(check_pkg)

    if except_pkgs:
        excludes.extend(except_pkgs)
    mg = ModuleGraph(excludes=excludes)

    current_dir = os.getcwd()
    os.chdir(script_dir)

    depends = set()
    pkg_paths = set()
    special_pkgs = set()
    mg.run_script(main_script_path)

    for node in mg.nodes():
        if hasattr(node, 'filename') and node.filename:
            abs_path = os.path.abspath(node.filename)
            if os.path.isfile(abs_path):
                if script_dir in abs_path or '__pycache' in abs_path or (
                        'site-packages' in abs_path and abs_path.endswith('.pyd')):
                    continue

                if 'tkinter' in abs_path:
                    special_pkgs.add('tkinter')
                elif 'curl_cffi' in abs_path:
                    special_pkgs.add('curl_cffi')

                depends.add(abs_path)
                if node.packagepath:
                    pkg_paths.add(node.packagepath[0])

    add_depends(depends, pkg_paths, special_pkgs, project_pkg_names)
    os.chdir(current_dir)
    return depends
