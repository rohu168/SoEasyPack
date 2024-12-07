"""
简易打包
@author: xmqsvip
Created on 2024-11-29
"""

import json
import os
import py_compile
import subprocess
import sys
import shutil
import logging
from pathlib import Path

from .py_to_pyd import to_pyd
from .slimfile import to_slim_file, check_dependency_files

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


def copy_py_env(save_dir, main_run_path=None, fast_mode=False, monitoring_time=18, except_packages=None):
    """
    复制 Python环境依赖
    :param save_dir:
    :param main_run_path:
    :param fast_mode:
    :return:
    """

    base_env_dir = str(sys.base_prefix)
    current_env_dir = str(sys.prefix)
    if current_env_dir == base_env_dir:
        is_go = input(f"当前你的环境：非虚拟环境，{current_env_dir}, 若继续操作，请输入Y或y：")
        if is_go.lower() != 'y':
            sys.exit()
        logging.warning("非虚拟环境可能会打包无用的依赖文件！")
    if fast_mode:
        logging.info("当前模式：快速模式")
        dependency_files = check_dependency_files(main_run_path, save_dir, fast_mode=fast_mode,
                                                  monitoring_time=monitoring_time, except_packages=except_packages)
        rundep_dir = str(Path.joinpath(Path(save_dir), 'rundep'))
        logging.info("复制python环境...")
        for dependency_file in dependency_files:
            dependency_file_ = dependency_file.replace(base_env_dir, rundep_dir).replace(current_env_dir, rundep_dir)
            if os.path.exists(dependency_file):
                to_save_dir = os.path.dirname(dependency_file_)
                os.makedirs(to_save_dir, exist_ok=True)
                try:
                    shutil.copy(dependency_file, to_save_dir)
                except OSError:
                    pass
                    # logging.error(f'文件 {dependency_file} 复制失败')

    else:
        logging.info("当前模式：普通模式")

        dest = Path.joinpath(Path(save_dir), 'rundep')

        def ignore_files(directory, files):
            # # 排除复制官方python无用的文件和文件夹
            py_exclusions = ['Scripts', 'Doc', 'LICENSE', 'LICENSE.txt',
                             'NEWS.txt', 'share', 'Tools', 'include', 'venv',
                             'site-packages', 'test'
                             ]
            return [f for f in files if f in py_exclusions]

        shutil.copytree(base_env_dir, dest, ignore=ignore_files, dirs_exist_ok=True)

        # # 复制 site-packages 中的所有文件
        lib_path = Path.joinpath(Path(current_env_dir), 'Lib/site-packages')
        to_lib_path = Path.joinpath(Path(dest), 'Lib/site-packages')
        shutil.copytree(lib_path, to_lib_path, dirs_exist_ok=True)

    pyenv_file = Path.joinpath(Path(save_dir), 'rundep/pyvenv.cfg')
    if pyenv_file.exists():
        os.remove(pyenv_file)


def copy_py_script(main_py_path, save_dir):
    """
    复制用户脚本
    """
    logging.info('复制你的脚本...')
    script_dir = os.path.dirname(main_py_path)
    save_dir = Path.joinpath(Path(save_dir), 'rundep\\AppData')
    shutil.copytree(script_dir, save_dir, dirs_exist_ok=True)
    new_main_py_path = os.path.join(save_dir, os.path.basename(main_py_path))
    return new_main_py_path


def create_bat(save_dir):
    # 生成bat脚本
    main_py_relative_path = 'rundep/AppData/main.pyc'
    py_interpreter = 'rundep/python.exe'
    bat_file_content = f'''start {py_interpreter} {main_py_relative_path}"
    exit
    '''
    bat_path = Path.joinpath(Path(save_dir), 'run.bat')
    with open(bat_path, 'w', encoding='utf-8') as bat_file:
        bat_file.write(bat_file_content)
    return bat_path


def build_exe(save_dir, hide_cmd: bool = True, exe_name: str = 'main', png_path: str = '',
              file_version: str = '', product_name: str = '', company: str = '',
              ):
    """
    使用go语言编译
    :param main_py_path:
    :param project_dir:
    :param hide_cmd:
    :param exe_name:
    :param icon_path:
    :param file_version:
    :param product_version:
    :param product_name:
    :param company:
    :return:
    """
    logging.info('生成exe...')
    current_dir = Path(__file__).parent.parent
    go_exe_path = Path.joinpath(current_dir, 'dep_exe/go_env/bin/go.exe')
    go_py_path = Path.joinpath(current_dir, 'dep_exe/go_env/go_py.go')
    winres_path = Path.joinpath(current_dir, 'dep_exe/go_env/go-winres.exe')
    winres_json_path = Path.joinpath(current_dir, 'dep_exe/go_env/winres.json')
    temp_build_dir = Path.joinpath(Path(save_dir), 'temp_build')
    os.makedirs(temp_build_dir, exist_ok=True)
    save_winres_json = Path.joinpath(temp_build_dir, "winres.json")
    shutil.copyfile(go_py_path, Path.joinpath(temp_build_dir, 'go_py.go'))
    if png_path and os.path.exists(png_path):
        copy_icon_path = Path.joinpath(temp_build_dir, f'{os.path.basename(png_path)}')
        shutil.copyfile(png_path, copy_icon_path)
        icon_name = os.path.basename(png_path)
    else:
        icon_name = ''

    if not os.path.exists(save_winres_json):
        shutil.copy(winres_json_path, save_winres_json)
        winres_json = json.load(open(winres_json_path, encoding='utf-8'))
        if icon_name:
            winres_json["RT_GROUP_ICON"]["APP"]["0000"].append(icon_name)
        if file_version:
            winres_json["RT_VERSION"]["#1"]["0000"]["fixed"]["file_version"] = file_version
        if product_name:
            winres_json["RT_VERSION"]["#1"]["0000"]["info"]["0409"]["ProductName"] = product_name
        if company:
            winres_json["RT_VERSION"]["#1"]["0000"]["info"]["0409"]["CompanyName"] = company
        json.dump(winres_json, open(save_winres_json, 'w', encoding='utf-8'), indent=4)

    os.chdir(temp_build_dir)
    with open('go.mod', mode='w', encoding='utf-8') as fp:
        fp.write("module go_py\n\ngo 1.23")

    pro = subprocess.Popen(f'{winres_path} make --in {save_winres_json}')
    pro.wait()
    save_exe_path = Path.joinpath(Path(save_dir), exe_name + '.exe')
    is_show_cmd = '-ldflags "-s -w -H windowsgui"' if hide_cmd else '-ldflags "-s -w"'

    command = f'{go_exe_path} build {is_show_cmd} -o {save_exe_path}'
    build_process = subprocess.Popen(command)
    build_process.wait()
    os.chdir(save_dir)
    shutil.rmtree(temp_build_dir)


def py_to_pyc(dst_dir):
    logging.info('开始将py文件转成pyc文件...')
    ready_remove_dirs = []
    for root, dirs, files in os.walk(dst_dir):
        if '__pycache__' in root:
            ready_remove_dirs.append(root)
            continue
        for file in files:
            if file.endswith('.py'):
                py_file = os.path.join(root, file)
                try:
                    py_compile.compile(py_file, cfile=py_file + 'c', quiet=1, optimize=2)
                    os.remove(py_file)
                except Exception as e:
                    logging.error(f"{py_file} 转pyc时发生错误: {e}")

    for i in ready_remove_dirs:
        shutil.rmtree(i)


def to_pack(main_py_path: str = 'main.py', save_dir: str = None,
            exe_name: str = 'main', png_path: str = '', hide_cmd: bool = False,
            fast_mode: bool = True, force_copy_env: bool = False, auto_py_pyd: bool = False,
            monitoring_time: int = 18, except_packages: list = None,
            **kwargs):
    """

    :param main_py_path:主入口py文件路径
    :param save_dir:打包保存目录(默认为桌面目录)
    :param exe_name:生成的exe文件名字
    :param png_path: exe图标路径
    :param hide_cmd:是否显示控制台窗口
    :param fast_mode:快速打包模式：监控分析依赖文件，然后复制依赖，不用再瘦身，适合非虚拟环境（虚拟环境也可）。
    普通模式：先复制python环境依赖包，然后监控分析依赖文件，再进行项目瘦身,会保存被移除的文件，
    因为会复制整个site-packages文件夹，所以不建议在非虚拟环境使用，
    快速打包模式会比普通模式大几兆
    :param force_copy_env: 强行每次复制python环境依赖包
    :param auto_py_pyd：知否把你的脚本转为pyd
    :param create_exe: 是否生成exe
    :param monitoring_time: 监控工具运行时长（秒）
    :param monitoring_time: 排除的第三方包名称
    :param kwargs:
    :return:
    """

    if not os.path.exists(main_py_path):
        logging.error(f'未找到{main_py_path}，请检查路径')
        return

    if not save_dir:
        # 获取桌面目录
        save_dir = Path.joinpath(Path.home(), 'Desktop\\SoEasyPack')
    os.makedirs(save_dir, exist_ok=True)

    rundep_dir = str(save_dir) + '\\rundep'
    if force_copy_env:
        logging.info('强制复制环境')
        if os.path.exists(rundep_dir):
            shutil.rmtree(rundep_dir)
        copy_py_env(save_dir, main_py_path, fast_mode, monitoring_time, except_packages)
    else:
        if os.path.exists(rundep_dir):
            logging.info('rundep文件夹已存在，跳过环境复制')
        else:
            copy_py_env(save_dir, main_py_path, fast_mode, monitoring_time, except_packages)

    new_main_py_path = copy_py_script(main_py_path, save_dir)

    if not fast_mode:
        to_slim_file(new_main_py_path, check_dir=rundep_dir, project_dir=save_dir, monitoring_time=monitoring_time)

    if auto_py_pyd:
        script_dir = save_dir + '\\rundep\\AppData'
        script_dir_main_py = os.path.join(script_dir, os.path.basename(main_py_path))
        to_pyd(script_dir, script_dir_main_py=script_dir_main_py)

    py_to_pyc(rundep_dir)
    create_bat(save_dir)
    build_exe(save_dir, hide_cmd, exe_name, png_path, **kwargs)

    logging.info('完成')
