"""
py编译为pyd
xmqsvip
2024-11-30
"""

import logging
import os
import glob
import shutil
from setuptools import setup
from Cython.Build import cythonize

from .my_logger import my_logger


def find_msvc_version(vs_edition_path):
    """查找 MSVC 版本"""
    msvc_path = os.path.join(vs_edition_path, "VC", "Tools", "MSVC")
    if os.path.exists(msvc_path):
        # 获取所有版本目录并排序
        versions = [
            d
            for d in os.listdir(msvc_path)
            if os.path.isdir(os.path.join(msvc_path, d))
        ]
        versions.sort(reverse=True)  # 最新版本在前
        if versions:
            return versions[0]  # 返回最新版本,
    return None


def find_windows_sdk():
    """查找 Windows SDK 路径"""
    sdk_root = r"C:\Program Files (x86)\Windows Kits\10"
    if os.path.exists(sdk_root):
        # 获取最新的 SDK 版本
        include_path = os.path.join(sdk_root, "Include")
        if os.path.exists(include_path):
            versions = [
                d
                for d in os.listdir(include_path)
                if os.path.isdir(os.path.join(include_path, d))
            ]
            versions.sort(reverse=True)
            if versions:
                return sdk_root, versions[0]
    return None, None


def to_pyd(script_dir: str, script_dir_main_py: str, is_del_py: bool = False):
    my_logger.info("开始py转为pyd")
    os.chdir(script_dir)
    temp_build_dir = os.path.join(script_dir, "temp_build")  # 临时构建目录

    # 尝试 VS2022 和 VS2019
    vs_configs = [
        {
            "path": r"C:\Program Files\Microsoft Visual Studio\2022",
            "env_var": "VS170COMNTOOLS",
        },
        {
            "path": r"C:\Program Files (x86)\Microsoft Visual Studio\2019",
            "env_var": "VS160COMNTOOLS",
        },
    ]

    vs_found = False
    for vs_config in vs_configs:
        vs_path = vs_config["path"]
        if os.path.exists(vs_path):
            # 设置 DISTUTILS_USE_SDK 和 MSSdk
            os.environ["DISTUTILS_USE_SDK"] = "1"
            os.environ["MSSdk"] = "1"

            # 查找 Windows SDK
            sdk_root, sdk_version = find_windows_sdk()
            if not sdk_root or not sdk_version:
                my_logger.warning("未找到 Windows SDK，跳过 pyd 转换")
                continue

            # 设置 VS 路径
            for edition in ["Community", "Professional", "Enterprise"]:
                vs_edition_path = os.path.join(vs_path, edition)
                if os.path.exists(vs_edition_path):
                    # 设置 VS 工具路径
                    os.environ[vs_config["env_var"]] = os.path.join(
                        vs_edition_path, "Common7", "Tools"
                    )

                    # 查找 MSVC 版本
                    msvc_version = find_msvc_version(vs_edition_path)
                    if msvc_version:
                        # 设置 cl.exe 路径
                        cl_path = os.path.join(
                            vs_edition_path,
                            "VC",
                            "Tools",
                            "MSVC",
                            msvc_version,
                            "bin",
                            "Hostx64",
                            "x64",
                        )
                        if os.path.exists(cl_path):
                            # 设置 PATH
                            paths = [
                                cl_path,
                                # 添加 rc.exe 路径
                                os.path.join(sdk_root, "bin", sdk_version, "x64"),
                                os.environ["PATH"],
                            ]
                            os.environ["PATH"] = os.pathsep.join(paths)

                            # 设置 INCLUDE 路径
                            include_paths = [
                                os.path.join(
                                    vs_edition_path,
                                    "VC",
                                    "Tools",
                                    "MSVC",
                                    msvc_version,
                                    "include",
                                ),
                                os.path.join(sdk_root, "Include", sdk_version, "ucrt"),
                                os.path.join(sdk_root, "Include", sdk_version, "um"),
                                os.path.join(
                                    sdk_root, "Include", sdk_version, "shared"
                                ),
                            ]
                            os.environ["INCLUDE"] = os.pathsep.join(include_paths)

                            # 设置 LIB 路径
                            lib_paths = [
                                os.path.join(
                                    vs_edition_path,
                                    "VC",
                                    "Tools",
                                    "MSVC",
                                    msvc_version,
                                    "lib",
                                    "x64",
                                ),
                                os.path.join(
                                    sdk_root, "Lib", sdk_version, "ucrt", "x64"
                                ),
                                os.path.join(sdk_root, "Lib", sdk_version, "um", "x64"),
                            ]
                            os.environ["LIB"] = os.pathsep.join(lib_paths)

                            my_logger.info(
                                f"找到 Visual Studio: {os.path.basename(vs_path)}"
                            )
                            my_logger.info(f"找到 MSVC 版本: {msvc_version}")
                            my_logger.info(f"找到 SDK 版本: {sdk_version}")
                            vs_found = True
                            break
                if vs_found:
                    break
            if vs_found:
                break

    if not vs_found:
        my_logger.warning("未找到 Visual Studio 安装，跳过 pyd 转换")
        return

    py_files = glob.glob(os.path.join(script_dir, "**", "*.py"), recursive=True)
    white_list = []
    for py_file in py_files:
        if ("__init__.py" in py_file) or (script_dir_main_py in py_file):
            white_list.append(py_file)
    for py_file in white_list:
        py_files.remove(py_file)
    if not py_files:
        logging.warning(f"只有一个主py文件，不可转为pyd")
        return

    os.makedirs(temp_build_dir, exist_ok=True)

    # 编译 .py 文件
    ext_modules = cythonize(
        py_files, quiet=True, compiler_directives={"language_level": "3"}
    )

    # 使用 setup 函数进行构建
    setup(
        ext_modules=ext_modules,
        script_args=[
            "build_ext",
            "--inplace",
            "--build-lib",
            temp_build_dir,
        ],  # 指定临时库目录
    )
    pyd_files = glob.glob(os.path.join(temp_build_dir, "**", "*.pyd"), recursive=True)

    # 将构建的 .pyd 文件移动到原始路径
    for py_file in py_files:
        original_py_dir = os.path.dirname(py_file)
        original_py_name = os.path.basename(py_file).replace(".py", "")

        for pyd_file in pyd_files:
            pyd_base_name = os.path.basename(pyd_file).split(".", 1)[0]
            if original_py_name == pyd_base_name:
                pyd_save_path = temp_build_dir + "\\" + os.path.basename(pyd_file)
                if pyd_save_path:
                    old_pyd_save_path = (
                        original_py_dir + "\\" + os.path.basename(pyd_file)
                    )
                    if os.path.exists(old_pyd_save_path):
                        # 删除旧的pyd
                        os.remove(old_pyd_save_path)
                    pyd_file_dir = os.path.dirname(pyd_file)
                    os.rename(pyd_file, f"{pyd_file_dir}/{pyd_base_name}.pyd")
                    shutil.move(f"{pyd_file_dir}/{pyd_base_name}.pyd", original_py_dir)

                    if is_del_py:
                        os.remove(py_file)
                    break
    # # 删除c文件
    c_files = glob.glob(os.path.join(script_dir, "**", "*.c"), recursive=True)
    for c_file in c_files:
        os.remove(c_file)

    shutil.rmtree(temp_build_dir, ignore_errors=True)
    py_cache = os.path.join(script_dir, "__pycache__")
    shutil.rmtree(py_cache, ignore_errors=True)
    shutil.rmtree(script_dir + "\\build", ignore_errors=True)
