"""
ast分析依赖
@author: xmqsvip
Created on 2025-01-05
"""
import os
import sys
from soeasypack.lib.modulegraph.modulegraph import ModuleGraph


def add_depends(depends: set, pkg_paths: set, special_pkgs: set):
    add_depend_paths = []
    depend_paths_append = add_depend_paths.append
    checked_dir = set()
    for depend_path in depends:
        if 'site-packages' not in depend_path:
            continue
        depend_path_split = depend_path.split('site-packages')
        package_path = depend_path_split[0] + 'site-packages\\' + depend_path_split[1].split('\\', 2)[1]
        if depend_path in checked_dir:
            continue
        checked_dir.add(depend_path)

        py_files_path = []
        other_files = {}

        py_files_append = py_files_path.append
        for root, dirs, files in os.walk(package_path, topdown=True):
            if '__pycache__' in root:
                continue
            for f in files:
                if f.endswith('.py'):
                    py_files_append(os.path.join(root, f))
                else:
                    file_path = os.path.join(root, f)
                    file_name = os.path.basename(file_path)
                    if f.endswith(('.json', '.pem')):
                        add_depend_paths.append(file_path)
                        continue
                    elif f.endswith('.dll'):
                        other_files[file_name] = file_path
                    elif f.endswith('.pyd'):
                        file_name = file_name.split('.', 1)[0]
                        other_files[file_name] = file_path

        if not other_files:
            continue
        py_files_path.extend(other_files.values())
        for file in py_files_path:
            if not other_files:
                break
            fined_dll_files = []
            mode = 'rb'
            encodings = None
            if file.endswith('.py'):
                mode = 'r'
                encodings = 'utf-8'

            with open(file, mode=mode, encoding=encodings) as fp:
                content = fp.read()

            for dll_file_name in other_files:
                if mode == 'rb':
                    dll_file_name = dll_file_name.encode('utf-8')
                if dll_file_name in content:
                    if mode == 'rb':
                        dll_file_name = dll_file_name.decode('utf-8')
                    depend_paths_append(other_files[dll_file_name])
                    fined_dll_files.append(dll_file_name)
            for f in fined_dll_files:
                del other_files[f]
            del content

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
    pyd_names = pyd_name_path.keys()
    for site_pkg_name in site_pkg_names:
        for pyd_name in pyd_names:
            if site_pkg_name in pyd_name:
                file_path = os.path.join(site_pkg_dir, pyd_name_path[pyd_name])
                depends.add(file_path)

    # #补充python目录下的dll
    base_env_dir = sys.base_prefix
    for f in os.listdir(base_env_dir):
        if os.path.isfile(os.path.join(base_env_dir, f)) and f.endswith('.dll'):
            dll_file = os.path.join(base_env_dir, f)
            depends.add(dll_file)

    encodings_dir_files = ('gbk.py', 'latin_1.py', 'utf_8.py', 'utf_16_be.py')
    for encodings_file in encodings_dir_files:
        depends.add(os.path.join(base_env_dir, 'Lib', 'encodings', encodings_file))

    dlls_dir_files = ['libcrypto-1_1.dll', 'libffi-7.dll']
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
            if 'demos' in root:
                continue
            for f in files:
                depends.add(os.path.join(root, f))

    for dlls_file in dlls_dir_files:
        depends.add(os.path.join(base_env_dir, 'DLLs', dlls_file))

    if 'curl_cffi' in special_pkgs:
        curl_cffi_dirs = [i for i in pkg_paths if 'curl_cffi' in i]
        for package_path in curl_cffi_dirs:
            if package_path.endswith('curl_cffi'):
                continue
            for root, dirs, files in os.walk(package_path, topdown=True):
                if '__pycache__' in root:
                    continue
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
                'pycparser', 'packaging', 'setuptools', 'unittest']
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
                elif 'curl_cffi':
                    special_pkgs.add('curl_cffi')

                depends.add(abs_path)
                if node.packagepath:
                    pkg_paths.add(node.packagepath[0])

    os.chdir(current_dir)
    add_depends(depends, pkg_paths, special_pkgs)
    return depends
