"""
项目瘦身
xmqsvip
2024-11-29
"""

import os
import csv
import sys
import time
import shutil
import psutil
import logging
import subprocess
from pathlib import Path

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


def process_exists_by_pid(pid):
    try:
        process = psutil.Process(pid)
        return process.is_running()
    except psutil.NoSuchProcess:
        return False


def check_dependency_files(main_run_path, project_dir, check_dir=None, fast_mode=False, monitoring_time=20):
    """
    检查依赖文件
    """

    current_dir = Path(__file__).parent.parent
    procmon_path = current_dir.joinpath('dep_exe/Procmon64.exe')
    pmc_base_path = current_dir.joinpath('dep_exe/ProcmonConfiguration.pmc')
    procmon_log_path = Path(project_dir).joinpath('procmon_log.pml')
    csv_log_path = Path(project_dir).joinpath('procmon_log.csv')
    dependency_file_csv = Path(project_dir).joinpath("dependency.csv")

    if fast_mode:
        dependency_file_csv = Path(project_dir).joinpath("dependency_fast.csv")
    if dependency_file_csv.exists():
        logging.info('已存在依赖文件清单表，跳过依赖文件检查')
        dependency_files = get_dependency_list(dependency_file_csv)
        dependency_files.add(str(dependency_file_csv))
        return dependency_files

    logging.info('当你的项目稍后自动运行后，请进行一些必要的功能操作：如点击运行按钮等,否则可能会造成依赖缺失')
    time.sleep(5)
    if os.path.exists(procmon_log_path):
        os.remove(procmon_log_path)
    logging.info(f'开始监控依赖文件，{monitoring_time}秒后自动结束监控')
    cmd = [
        procmon_path,
        "/Minimized",
        "/AcceptEula",
        "/Runtime", str(monitoring_time),
        "/Quiet",
        "/Backingfile", procmon_log_path,
        # "/LoadConfig", pmc_base_path,
    ]

    procmon_process = subprocess.Popen(cmd)
    procmon_pid = procmon_process.pid
    time.sleep(1)
    # 启动你的脚本
    if 'py' in str(Path(main_run_path).suffix):
        if fast_mode:
            current_env_py = str(sys.prefix) + '/Scripts/python.exe'
            main_run_cmd = [current_env_py, main_run_path]
        else:
            python_exe_path = Path(project_dir).joinpath('runtime/python.exe')
            pythonw_exe_path = Path(project_dir).joinpath('runtime/pythonw.exe')
            if python_exe_path.exists():
                main_run_cmd = [str(python_exe_path), main_run_path]
            elif python_exe_path.exists():
                main_run_cmd = [str(pythonw_exe_path), main_run_path]
            else:
                logging.warning(f'未找到{project_dir}/runtime文件夹中的python，使用当前环境的python运行脚本')
                current_env_py = str(sys.prefix) + '/Scripts/python.exe'
                main_run_cmd = [current_env_py, main_run_path]

    else:
        main_run_cmd = main_run_path

    main_run_process = subprocess.Popen(main_run_cmd)
    time.sleep(monitoring_time)
    main_run_process.kill()

    while True:
        if process_exists_by_pid(procmon_pid):
            time.sleep(2)
        else:
            break

    cmd = [
        procmon_path,
        "/Minimized",
        "/AcceptEula",
        "/Quiet",
        "/NoConnect",
        "/OpenLog", procmon_log_path,
        "/SaveAs", csv_log_path,
        "/LoadConfig", pmc_base_path,
    ]
    procmon_process = subprocess.Popen(cmd)
    procmon_pid = procmon_process.pid
    while True:
        if process_exists_by_pid(procmon_pid):
            time.sleep(2)
        else:
            break

    while True:
        if Path.exists(csv_log_path):
            break
        time.sleep(1)

    dependency_files = get_dependency_list(csv_log_path, check_dir, fast_mode)

    with open(dependency_file_csv, mode='w', newline='', encoding='utf-8') as fp:
        csv_writer = csv.writer(fp)
        for i in dependency_files:
            csv_writer.writerow([i])
    try:
        os.remove(procmon_log_path)
        os.remove(csv_log_path)
    except Exception as e:
        logging.error(f"删除日志文件失败:{e}")

    return dependency_files


def get_dependency_list(dependency_file_csv, check_dir=None, fast_mode=False):
    if fast_mode:
        base_env_dir = sys.base_prefix
        current_env_dir = sys.prefix
        if base_env_dir == current_env_dir:
            check_dir = base_env_dir
        else:
            check_dir = [base_env_dir, current_env_dir]

    dependency_files = set()
    with open(dependency_file_csv, encoding='utf-8') as fp:
        csvreader = csv.reader(fp)
        if check_dir:
            if isinstance(check_dir, list):
                for row in csvreader:
                    cell_value = row[0]
                    if cell_value and ((check_dir[0] in cell_value) or (check_dir[1] in cell_value)):
                        dependency_files.add(cell_value)
            else:
                for row in csvreader:
                    cell_value = row[0]
                    if cell_value and (check_dir in cell_value):
                        dependency_files.add(cell_value)
        else:
            # 已经判断过了，无需再次判断路径
            for row in csvreader:
                dependency_files.add(row[0])
    dependency_files.add(str(dependency_file_csv))
    return dependency_files


def move_files(check_dir, project_dir, dependency_files):
    """从源目录（包括子文件夹）移动未被占用的文件到目标目录"""
    logging.info('开始瘦身...')
    project_dir = os.path.join(project_dir, "removed_file")

    moved_file_num = 0
    removed_size = 0

    for root, dirs, files in os.walk(check_dir):
        for filename in files:
            src_file = str(os.path.join(root, filename))
            if src_file in dependency_files:
                continue
            else:
                try:
                    # 保持目录结构
                    relative_path = str(os.path.relpath(root, check_dir))
                    dest_folder = os.path.join(project_dir, relative_path)
                    os.makedirs(dest_folder, exist_ok=True)
                    removed_size += os.path.getsize(src_file)
                    # 移动文件
                    shutil.move(src_file, os.path.join(dest_folder, filename))
                    moved_file_num += 1
                except Exception as e:
                    logging.error(f"无法移动文件: {src_file}: {e}")

    # 移除空文件夹
    for dir_path in Path(project_dir).rglob('*'):
        if dir_path.is_dir() and not list(dir_path.iterdir()):
            dir_path.rmdir()
    removed_size = f"{removed_size / (1024 * 1024):.2f}"
    logging.info(f"瘦身完成，移除了{moved_file_num}个文件, 减小了{removed_size}M")
    if moved_file_num > 0:
        logging.info(f"移除的文件保存到了:{project_dir}")


def to_slim_file(main_run_path: str, check_dir: str, project_dir: str = None, monitoring_time=20):
    """
    项目瘦身
    :param main_run_path: 项目主运行文件路径,py或其它
    :param check_dir: 需要瘦身的目录
    :param project_dir:  项目目录
    :return:
    """
    if project_dir is None:
        project_dir = check_dir

    main_run_path = main_run_path.replace("/", "\\")
    check_dir = check_dir.replace("/", "\\")
    project_dir = project_dir.replace("/", "\\")
    dependency_files = check_dependency_files(main_run_path, project_dir, check_dir, monitoring_time=monitoring_time)
    move_files(check_dir, project_dir, dependency_files)


