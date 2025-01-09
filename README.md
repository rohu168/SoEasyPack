[![PyPI Version](https://img.shields.io/pypi/v/soeasypack)](https://pypi.org/project/soeasypack)
[![PyPI Downloads](https://static.pepy.tech/badge/soeasypack)](https://pepy.tech/projects/soeasypack)
# SoEasyPack
- 此项目受[PyStand](https://github.com/skywind3000/PyStand "PyStand")和[PythonSizeCruncher](https://github.com/mengdeer589/PythonSizeCruncher "PythonSizeCruncher")启发。
- 不需要复制嵌入式包，也不必再二次瘦身,一次打包理论上就是最小依赖文件数
- 用简易的方式复制你的python项目并自动精准匹配环境依赖，几乎没有什么多余文件，
  并且可以生成一个exe启动器启动项目。（用go语言编译,已内置简化过的go环境）
- 快速/普通模式原理：使用微软[procmon](https://learn.microsoft.com/en-us/sysinternals/downloads/procmon "procmon")进程监控工具（已内置），监控项目运行时访问的文件记录
- 仅支持windows，且仅在windows10和11上测试过
## 虚拟环境打包大小对比
| 打包工具                        | 打包后大小 |
|-----------------------------|-------|
| nuitka 2.5.9打包              | 67.9M |
| PyStand仅删除pip文件夹            | 56.9M |
| Pyinstaller 6.11.1打包缺依赖 补上后 | 49.3M |
| soeasypack的ast模式打包          | 43.7M |
| soeasypack的快速模式打包           | 33.5M |
| soeasypack的普通模式打包           | 33.5M |
| soeasypack的单exe模式打包         | 16.3M |

| 使用soeasypack的to_slim_file瘦身  | 原体积大小 | 瘦身后大小    | 瘦身比例   |
|---------------------------------|-------|------------|--------|
| 对PyStand打包的项目瘦身            | 56.9M | 36.5M      | 35.79% |
| 对nuitka打包的项目瘦身             | 67.9M | 54.8M      | 19.37% |
| 对Pyinstaller打包的项目瘦身        | 49.3M | 36.6M      | 25.52% |

## 安装

soeasypack is available on PyPI. You can install it through pip:


```shell
    pip install soeasypack
```
## 操作演示
   [点击查看操作演示](https://b23.tv/2UH6YO3 "操作演示") 
## 介绍

- **1**: 模式介绍
- 项目有四种打包模式：【普通打包】【快速打包】【伪轻量打包】【ast模式打包】（默认使用快速打包）.
- pack_mode：0/快速打包模式 ，1/普通打包模式， 2/伪轻量打包模式， 3/ast模式打包

- 普通打包会先复制当前python主环境的必要官方文件，然后复制当前py环境的整个site-packages
文件夹到你指定的保存目录，然后启动分析工具分析依赖文件，然后根据依赖文件去删除rundep文件夹
中无用的文件，会保留被删除的文件到removed_file中，然后自动生成exe, 还可选将你的脚本文件转为pyd,
最后项目就打包完成了。因为会复制整个site-packages文件夹，所以普通模式只建议在虚拟环境中使用。
       
- 快速打包是先启动分析工具分析依赖文件。然后把依赖文件复制到保存目录，再自动生成exe, 没有项目瘦身这一步骤，
所以没有虚拟环境的话，建议使用快速打包模式，它不会复制整个site-packages文件夹

- 伪轻量打包是复制当前python主环境除了site-packages文件夹之外的必要官方文件，然后复制用户脚本目录，复制requirements.txt,
用户启动程序后检查依赖是否缺失，缺失自动pip下载,下载完成后rundep目录生成compiled_pip.txt，用以下次启动判断是否需要下载依赖项，
建议requirements.txt使用pipreqs包生成

- **2**: 嵌入exe介绍
- 普通嵌入exe：设置embed_exe=True,会把rundep/AppData文件夹下用户的所有.py文件转换为.pyc，然后嵌入exe中，其它类型和其它文件夹不会嵌入。
- 单exe文件：设置onefile=True,会把rundep/AppData文件夹下用户的所有.py文件转换为.pyc，然后嵌入exe中，
然后把rundep文件下所有文件压缩成一个zip压缩包嵌入exe中，exe运行时会解压缩到临时目录，退出程序则删除临时目录.
其它制作单exe文件方法：使用[Enigma Virtual Box](https://www.enigmaprotector.com/cn/downloads.html)工具打包成只有一个exe  
- **3**: 函数介绍
    - 1.打包项目
    ```python
    from soeasypack import to_pack
    
    save_dir = r'C:\save_dir'
    main_py_path = r'C:\my_project\main.py' 
    exe_name = '大都督'
    to_pack(main_py_path, save_dir, pack_mode=0, embed_exe=False,exe_name=exe_name, 
            pyc_optimize=1, except_packages=['numpy']) 
    ```
    - 2.项目瘦身
    ```python
    from soeasypack import to_slim_file
    to_slim_file(main_run_path: str, check_dir: str, project_dir: str = None, monitoring_time=20)
    ```
    - 3.生成pyd
    ```python
    from soeasypack import to_pyd
    to_pyd(script_dir: str, script_dir_main_py: str, is_del_py: bool = False)
    ```
## 注意事项
- 因360安全卫士会拦截procmon相关工具, 所以，打包前请先关闭360安全卫士或放行。
- 以管理员身份运行打包代码，或在以管理员身份打开的编辑器中运行程序可避免每次启动procmon时弹出用户账户控制确认窗口，
以管理员身份运行用户程序，拖放文件到窗口功能会失效
- 默认会将大全部.py文件转为.pyc.不保留原.py文件，优化级别默认使用为1。
- 会自动将主py文件重命名为main, exe启动时会将工作目录切换至rundep/Appdata,会依次寻找文件夹下mian.pyc,.py,.pyd启动文件
- 建议在虚拟环境中使用，非虚拟环境可能会打包无用的依赖(非虚拟环境测试项目：未使用numpy,但项目运行时不知为何访问了numpy,导致复制了这个无用的包)
- 为了能完整记录依赖文件，监控工具启动后，会自动运行你的脚本，请对你的项目进行必要的操作：如点击运行按钮等，
  如：我使用openpyxl往表格中插入图片，项目自动启动后，我要让脚本执行这一操作，
  这样，监控工具才能监控到依赖文件，否则最后虽然能启动项目但是插入图片时会报错，
  所以，请一定要注意，你的项目启动后，一定要默认监控时间18秒内执行必要的操作。
  18秒大概会产生几百兆的日志，所以，监控时间可以根据实际情况调整。
- 因.pyc可能会被反编译，建议使用soeasypack的py文件转pyd函数（好像需要先安装Visual Studio, 我自己之前安装的有，其它情况也没试）或使用嵌入exe功能
- 伪轻量打包会自动将AppData文件夹下全部.py文件转为.pyc，然后嵌入exe
- 程序图标需要使用png格式
- 若启动出错无法查看报错信息可设置hide_cmd=False,编译成带控制台的exe，然后在cmd中去启动程序查看报错信息
- 多进程需要添加冻结指令
```python
import sys
from multiprocessing import freeze_support
if __name__ == '__main__':
    # 冻结支持，确保在打包后的环境中正确启动新的Python解释器进程
    sys.frozen = True
    freeze_support()
```


- 如果你觉得对你有帮助的话，可以打赏1元让作者买个馍呀
![](https://github.com/XMQSVIP/MyImage/blob/main/wx_zsm.jpg?raw=true)

