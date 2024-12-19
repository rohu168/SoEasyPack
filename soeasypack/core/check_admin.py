"""
检查当前程序是否以管理员身份运行
"""
import ctypes


def is_admin():
    try:
        # 检查是否有管理员权限
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False
