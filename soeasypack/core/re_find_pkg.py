"""
查找项目使用的包
@author: xmqsvip
Created on 2025-01-05
"""
import re
import os
import sys

CHECK_PKGS = ('PySide2', 'PySide6', 'PyQt5', 'PyQt6', 'PySimpleGUI', 'nicegui', 'flet', 'kivy',
              'matplotlib')
EXCLUDE_DIRS = ['pip', 'IPython', 'PyInstaller', 'nuitka', 'cx_Freeze', 'py2exe', 'soeasypack']


def find_imports(file_dir, search_compile, add_pkg_names):
    imports = set()

    for root, dirs, files in os.walk(file_dir, topdown=True):
        for dir_ in EXCLUDE_DIRS:
            if dir_ in root:
                continue
        remove_dirs = [dir_ for dir_ in dirs if dir_.startswith('.')]
        dirs[:] = [d for d in dirs if d not in remove_dirs]

        for file in files:
            if file.endswith('.py'):
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as fp:
                        for line in fp:
                            # 匹配 import 包名 或 from 包名 import ...
                            match = search_compile.match(line)
                            if match:
                                package = next(filter(None, match.groups()), None)
                                if package and package not in add_pkg_names:
                                    imports.add(package)
                except Exception:
                    pass

    return imports


def get_import_pkgs(pkg_names, site_pkg_dir, search_compile, add_pkg_names, remove_pkg_names, project_pkg_names):
    for pkg_name in pkg_names:
        if pkg_name in add_pkg_names:
            continue

        pkg_path = os.path.join(site_pkg_dir, pkg_name)
        if os.path.exists(pkg_path):
            add_pkg_names.add(pkg_name)
            imports = find_imports(pkg_path, search_compile, add_pkg_names)
            imports = imports - remove_pkg_names
            if imports:
                for check_pkg in CHECK_PKGS:
                    if check_pkg in imports and check_pkg not in project_pkg_names:
                        imports.remove(check_pkg)

                get_import_pkgs(imports, site_pkg_dir, search_compile, add_pkg_names, remove_pkg_names,
                                project_pkg_names)
                pkg_names.union(imports)
        else:
            remove_pkg_names.add(pkg_name)


def find_pkgs(file_path):
    pkg_names = set()
    current_env_dir = sys.prefix
    search_compile = re.compile(r'^(?:\s*from\s+(\w+)|\s*import\s+(\w+))')
    file_dir = os.path.dirname(file_path)
    site_pkg_dir = os.path.join(current_env_dir, 'Lib\\site-packages')
    project_pkg_names = find_imports(file_dir, search_compile, pkg_names)

    for pkg_name in project_pkg_names:
        pkg_path = os.path.join(site_pkg_dir, pkg_name)
        if os.path.exists(pkg_path):
            pkg_names.add(pkg_name)

    add_pkg_names = set()
    remove_pkg_names = set()
    get_import_pkgs(pkg_names, site_pkg_dir, search_compile, add_pkg_names, remove_pkg_names, project_pkg_names)
    pkg_names = pkg_names | add_pkg_names - remove_pkg_names
    for i in EXCLUDE_DIRS:
        if i in pkg_names:
            pkg_names.remove(i)

    return pkg_names