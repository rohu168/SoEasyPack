"""
查找项目使用的包
"""
import re
import os
import sys


def find_imports(file_dir, search_compile, add_pkg_names):
    imports = set()

    for root, dirs, files in os.walk(file_dir, topdown=True):
        exclude_dirs =('IPython', 'PyInstaller', 'py2exe', 'nuitka', 'soeasypack')
        for dir_ in exclude_dirs:
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

def get_import_pkgs(pkg_names, site_pkg_dir, search_compile, add_pkg_names, remove_pkg_names):
    for pkg_name in pkg_names:
        if pkg_name in add_pkg_names:
            continue

        pkg_path = os.path.join(site_pkg_dir, pkg_name)
        if os.path.exists(pkg_path):
            add_pkg_names.add(pkg_name)
            imports = find_imports(pkg_path, search_compile, add_pkg_names)
            imports = imports - remove_pkg_names
            if imports:
                get_import_pkgs(imports, site_pkg_dir, search_compile, add_pkg_names, remove_pkg_names)
                pkg_names.union(imports)
        else:
            remove_pkg_names.add(pkg_name)

def find_pkgs(file_path):
    pkg_names = set()
    current_env_dir = sys.prefix
    search_compile = re.compile(r'^(?:\s*from\s+(\w+)|\s*import\s+(\w+))')
    file_dir = os.path.dirname(file_path)
    site_pkg_dir = os.path.join(current_env_dir, 'Lib\\site-packages')
    pkg_names_ = find_imports(file_dir, search_compile, pkg_names)
    for pkg_name in pkg_names_:
        pkg_path = os.path.join(site_pkg_dir, pkg_name)
        if os.path.exists(pkg_path):
            pkg_names.add(pkg_name)

    add_pkg_names = set()
    remove_pkg_names = set()
    get_import_pkgs(pkg_names, site_pkg_dir, search_compile, add_pkg_names, remove_pkg_names)
    pkg_names = pkg_names | add_pkg_names - remove_pkg_names
    for i in ('IPython', 'PyInstaller', 'nuitka', 'cx_Freeze', 'py2exe', 'soeasypack'):
        if i in pkg_names:
            pkg_names.remove(i)
    return pkg_names

