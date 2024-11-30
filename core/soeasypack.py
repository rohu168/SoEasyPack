"""
简易打包
xmqsvip
2024-11-29
"""

import os
import re
import subprocess
import sys
import shutil
import logging
import time
from pathlib import Path

from .py_to_pyd import to_pyd
from .slimfile import to_slim_file, check_dependency_files, process_exists_by_pid

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


def copy_py_env(save_dir, main_run_path=None, fast_mode=False):
    """
    复制 Python环境依赖
    :param save_dir:
    :param main_run_path:
    :param fast_mode:
    :return:
    """

    base_env_dir = str(sys.base_prefix)
    current_env_dir = str(sys.prefix)
    if fast_mode:
        logging.info("使用快速模式复制python环境...")
        dependency_files = check_dependency_files(main_run_path, save_dir, fast_mode=fast_mode)
        runtime_dir = str(Path.joinpath(Path(save_dir), 'runtime'))
        for dependency_file in dependency_files:
            dependency_file_ = dependency_file.replace(base_env_dir, runtime_dir).replace(current_env_dir, runtime_dir)
            if os.path.isdir(dependency_file):
                continue
            if os.path.exists(dependency_file):
                to_save_dir = os.path.dirname(dependency_file_)
                os.makedirs(to_save_dir, exist_ok=True)
                try:
                    shutil.copy(dependency_file, to_save_dir)
                except OSError:
                    pass
                    # logging.error(f'文件 {dependency_file} 复制失败')

    else:
        logging.info("使用普通模式复制python环境...")
        # # 排除复制官方python无用的文件和文件夹
        py_exclusions = ['Scripts', 'Doc', 'LICENSE', 'LICENSE.txt',
                         'NEWS.txt', 'share', 'Tools', 'include', 'venv', 'site-packages', 'test'
                         ]

        dest = Path.joinpath(Path(save_dir), 'runtime')

        def ignore_files(directory, files):
            return [f for f in files if f in py_exclusions]

        shutil.copytree(base_env_dir, dest, ignore=ignore_files, dirs_exist_ok=True)

        # # 复制 site-packages 中的所有文件
        lib_path = Path.joinpath(Path(current_env_dir), 'Lib/site-packages')
        to_lib_path = Path.joinpath(Path(dest), 'Lib/site-packages')
        shutil.copytree(lib_path, to_lib_path, dirs_exist_ok=True)

    pyenv_file = Path.joinpath(Path(save_dir), 'runtime/pyvenv.cfg')
    if pyenv_file.exists():
        os.remove(pyenv_file)

    logging.info('python环境复制完毕')


def copy_py_script(main_py_path, save_dir):
    """
    复制用户脚本
    :param script_dir:
    :return:
    """
    logging.info('复制你的脚本...')
    script_dir = os.path.dirname(main_py_path)
    save_dir = Path.joinpath(Path(save_dir), 'script')
    shutil.copytree(script_dir, save_dir, dirs_exist_ok=True)


def create_bat(main_py_path, save_dir):
    # 生成bat脚本
    main_py_relative_path = 'script/' + os.path.basename(main_py_path)
    py_interpreter = 'runtime/python.exe'
    bat_file_content = f'''
    @echo off
    set "currentDir=%~dp0"
    "%currentDir%{py_interpreter}" "%currentDir%{main_py_relative_path}"
    exit
    '''
    bat_path = Path.joinpath(Path(save_dir), 'run.bat')
    with open(bat_path, 'w', encoding='utf-8') as bat_file:
        bat_file.write(bat_file_content)
    return bat_path


def bat_to_exe(bat_path, save_dir, hide_cmd: bool = False, exe_name: str = 'main.exe', icon_path: str = '',
               x64: bool = True, uac_admin: bool = False, uac_user: bool = False,
               file_version: str = '1.0.0.0', product_version: str = '1.0.0',
               product_name: str = '', originalfilename: str = '',
               internalname: str = '', description: str = '', company: str = '', trademarks: str = '',
               copyright: str = '', privatebuild: str = '',
               specialbuild: str = '', comments: str = ''):
    #  bat转exe
    current_dir = Path(__file__).parent.parent
    converter_path = Path.joinpath(current_dir, 'dep_exe/Bat_To_Exe_Converter.exe')

    exe_path = f"/exe {Path.joinpath(Path(save_dir), exe_name)}"
    bat_path = f"/bat {bat_path}"
    command = f"{converter_path} {bat_path} {exe_path} /overwrite"
    if hide_cmd:
        command += " /invisible"
    if x64:
        command += " /x64"
    if uac_admin:
        command += " /uac_admin"
    if uac_user:
        command += " /uac_user"

    params = {
        'icon': icon_path,
        'fileversion': file_version,
        'productversion': product_version,
        'productname': product_name,
        'originalfilename': originalfilename,
        'internalname': internalname,
        'description': description,
        'company': company,
        'trademarks': trademarks,
        'copyright': copyright,
        'privatebuild': privatebuild,
        'specialbuild': specialbuild,
        'comments': comments
    }

    for key, value in params.items():
        if value:  # 仅在参数值存在时才添加
            command += f" /{key} {value}"

    # print(command)
    logging.info('生成exe...')
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
    output, error = process.communicate()
    if output:
        print(output)
    if error:
        print(error)
    logging.info('结束')


def ji_to_exe(main_py_path, project_dir, hide_cmd: bool = True, exe_name: str = 'main.exe', icon_path: str = '',
              file_version: str = '1.0.0', product_name: str = '', company: str = '',
              description: str = '', trademarks: str = '', copyright: str = '', comments: str = ''):
    """
    使用国产 极语言 编译
    http://sec.z5x.cn/
    :param main_py_path:
    :param project_dir:
    :param hide_cmd:
    :param exe_name:
    :param icon_path:
    :param file_version:
    :param product_version:
    :param product_name:
    :param company:
    :param description:
    :param trademarks:
    :param copyright:
    :param comments:
    :return:
    """
    logging.info('使用极语言生成exe...')
    current_dir = Path(__file__).parent.parent
    user_exe_path = Path.joinpath(current_dir, 'dep_exe/sec/sep.exe')
    compiler_file = Path.joinpath(current_dir, 'dep_exe/sec/Sc.exe')
    bac_path = Path.joinpath(current_dir, 'dep_exe/sec/窗体.bac')
    sec_path = Path.joinpath(current_dir, 'dep_exe/sec/sep.SEC')
    if icon_path and os.path.exists(icon_path):
        copy_icon_path = Path.joinpath(current_dir, f'dep_exe/sec/{os.path.basename(icon_path)}')
        shutil.copy(icon_path, copy_icon_path)
        icon_name = os.path.basename(icon_path)
    else:
        icon_name = 'main.ico'
        copy_icon_path = ''
    params = {
        'sep.exe': exe_name,
        'main.ico': icon_name,
        '1.00': file_version,
        '简易打包': product_name,
        '文件描述': description,
        '公司名': company,
        '合法商标': trademarks,
        '合法版权': copyright,
        '注释': comments
    }

    # 修改版本信息
    with open(sec_path, 'r', encoding='gbk') as fp:
        sec_content = fp.read()
        new_sec_content = None
    for key, value in params.items():
        if value:
            if new_sec_content:
                new_sec_content = new_sec_content.replace(key, value)
            else:
                new_sec_content = sec_content.replace(key, value)
    if new_sec_content:
        with open(sec_path, 'w', encoding='gbk') as fp:
            fp.write(new_sec_content)

    # 修改极语言源程序
    with open(bac_path, 'r', encoding='gbk') as fp:
        build_file_content = fp.read()

    is_show_cmd = 1 if hide_cmd else 0
    user_command = f'运行("runtime/python.exe script/{os.path.basename(main_py_path)}", {is_show_cmd})'

    build_file_content = re.sub("运行.*?\)", user_command, build_file_content)

    with open(bac_path, 'w', encoding='gbk') as fp:
        fp.write(build_file_content)

    # 编译
    command = f"{compiler_file} {sec_path}"
    process = subprocess.Popen(command)
    time.sleep(1.5)
    process.kill()
    if os.path.exists(user_exe_path):
        os.rename(str(user_exe_path), str(user_exe_path).replace("sep", exe_name))
        user_exe_path = os.path.dirname(user_exe_path) + '\\' + exe_name + '.exe'
        old_exe_path = f"{project_dir}\\{exe_name}.exe"
        if os.path.exists(old_exe_path):
            os.remove(old_exe_path)
        shutil.move(user_exe_path, project_dir)
    else:
        logging.error('XXX   编译失败   XXX')
    if os.path.exists(copy_icon_path):
        os.remove(copy_icon_path)
    # 恢复源文件
    with open(sec_path, 'w', encoding='gbk') as fp:
        fp.write(sec_content)
    logging.info('完成')


def to_pack(main_py_path: str = 'main.py', save_dir: str = '',
            exe_name: str = 'main', icon_path: str = '', hide_cmd: bool = False,
            fast_mode: bool = True, force_copy_env: bool = False, auto_py_pyd: bool = False,
            **kwargs):
    """

    :param main_py_path:主入口py文件路径
    :param save_dir:打包保存目录
    :param exe_name:生成的exe文件名字
    :param icon_path: exe图标路径
    :param hide_cmd:是否显示控制台窗口
    :param fast_mode:快速打包模式：监控分析依赖文件，然后复制依赖，不用再瘦身，适合非虚拟环境（虚拟环境也可）。
    普通模式：先复制python环境依赖包，然后监控分析依赖文件，再进行项目瘦身,会保存被移除的文件，
    因为会复制整个site-packages文件夹，所以不建议在非虚拟环境使用，
    快速打包模式会比普通模式大几兆
    :param force_copy_env: 强行每次复制python环境依赖包
    :param kwargs:
    :return:
    """

    if not save_dir:
        # 获取桌面目录
        save_dir = Path.joinpath(Path.home(), 'Desktop')

    runtime_dir = str(save_dir) + '\\runtime'
    if force_copy_env:
        if os.path.exists(runtime_dir):
            shutil.rmtree(runtime_dir)
        copy_py_env(save_dir, main_py_path, fast_mode)
    else:
        if os.path.exists(runtime_dir):
            logging.info('runtime文件夹已存在，跳过环境复制')
        else:
            copy_py_env(save_dir, main_py_path, fast_mode)

    if not os.path.exists(main_py_path):
        logging.error('未找到你的脚本，请检查路径')
        return

    copy_py_script(main_py_path, save_dir)

    bat_path = create_bat(main_py_path, save_dir)
    if not fast_mode:
        to_slim_file(main_py_path, check_dir=runtime_dir, project_dir=save_dir)

    # bat_to_exe(bat_path, save_dir, hide_cmd, exe_name, icon_path, **kwargs)
    ji_to_exe(main_py_path, save_dir, hide_cmd, exe_name, icon_path, **kwargs)

    if auto_py_pyd:
        script_dir = save_dir + '\\script'
        script_dir_main_py = os.path.join(script_dir, os.path.basename(main_py_path))
        to_pyd(script_dir, script_dir_main_py=script_dir_main_py)
