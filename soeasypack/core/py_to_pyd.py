"""
py编译为pyd
xmqsvip
2024-11-29
"""

import os
import glob
import shutil
from setuptools import setup
from Cython.Build import cythonize


def to_pyd(script_dir: str, script_dir_main_py: str, is_del_py: bool = False):
    print("开始py转为pyd")
    os.chdir(script_dir)
    temp_build_dir = os.path.join(script_dir, 'temp_build')  # 临时构建目录
    py_files = glob.glob(os.path.join(script_dir, '**', '*.py'), recursive=True)
    white_list = []
    for py_file in py_files:
        if ('__init__.py' in py_file) or (script_dir_main_py in py_file):
            white_list.append(py_file)
    for py_file in white_list:
        py_files.remove(py_file)
    os.makedirs(temp_build_dir, exist_ok=True)

    # 编译 .py 文件
    ext_modules = cythonize(py_files, quiet=True, compiler_directives={'language_level': '3'})

    # 使用 setup 函数进行构建
    setup(
        ext_modules=ext_modules,
        script_args=["build_ext", "--inplace", "--build-lib", temp_build_dir]  # 指定临时库目录
    )
    pyd_files = glob.glob(os.path.join(temp_build_dir, '**', '*.pyd'), recursive=True)

    # 将构建的 .pyd 文件移动到原始路径
    for py_file in py_files:
        original_py_dir = os.path.dirname(py_file)
        original_py_name = os.path.basename(py_file).replace('.py', '')

        for pyd_file in pyd_files:
            if original_py_name == os.path.basename(pyd_file).split('.', 1)[0]:
                pyd_save_path = temp_build_dir + '\\' + os.path.basename(pyd_file)
                if pyd_save_path:
                    old_pyd_save_path = original_py_dir + '\\' + os.path.basename(pyd_file)
                    if os.path.exists(old_pyd_save_path):
                        # 删除旧的pyd
                        os.remove(old_pyd_save_path)

                    shutil.move(pyd_file, original_py_dir)
                    if is_del_py:
                        os.remove(py_file)
                    break
    # # 删除c文件
    c_files = glob.glob(os.path.join(script_dir, '**', '*.c'), recursive=True)
    for c_file in c_files:
        os.remove(c_file)

    shutil.rmtree(temp_build_dir, ignore_errors=True)
    py_cache = os.path.join(script_dir, '__pycache__')
    shutil.rmtree(py_cache, ignore_errors=True)
    shutil.rmtree(script_dir + "\\build", ignore_errors=True)