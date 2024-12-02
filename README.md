# SoEasyPack
- 此项目受[PyStand](https://github.com/skywind3000/PyStand "PyStand")和[PythonSizeCruncher](https://github.com/mengdeer589/PythonSizeCruncher "PythonSizeCruncher")启发。
- 不需要复制嵌入式包，也不必再二次瘦身,一次打包理论上就是最小依赖
- 用简易的方式复制你的python项目并自动精准匹配环境依赖，几乎没有什么多余文件，
并且可以生成一个exe外壳（用[极语言](http://sec.z5x.cn/ "极语言")制作）作为程序入口启动项目。
因为只有windows电脑,所以此项目仅支持windows
- 原理：使用微软[procmon](https://learn.microsoft.com/en-us/sysinternals/downloads/procmon "procmon")进程监控工具，监控项目运行时访问的文件记录
- 仅在windows10上测试过

## 一项目测试对比
 
- 使用PyStand仅删除pip文件夹，项目大小为56.9M,
- 使用Pyinstaller打包后报模块缺失，补上后项目大小为49.3M
- 使用soeasypack的快速模式打包，项目大小为39.3M
- 使用soeasypack的普通模式打包，项目大小为38.3M
- 使用PythonSizeCruncher的安全模式对PyStand打包的项目瘦身后，项目大小为51.4M
- 使用soeasypack的to_slim_file对PyStand打包的项目瘦身后，项目大小为36.5M
- 使用soeasypack的to_slim_file对Pyinstaller打包的项目瘦身后,项目大小为36.6M

## 安装

To install soeasypack, follow these steps:


```shell
    pip install soeasypack
```
## 操作演示
   [操作演示](https://www.bilibili.com/video/BV1Pfz4YdEAZ/ "操作演示")
## 介绍

- **1**: 模式介绍
- 项目有两种打包模式：普通打包和快速打包（默认使用快速打包）
  
- 普通打包会先复制当前python主环境的必要官方文件，然后复制当前py环境的整个site-packages
  文件夹到你指定的保存目录，然后启动分析工具分析依赖文件，然后根据依赖文件去删除site-packages
  中无用的文件，会保留被删除的文件到removed_file中，然后自动生成exe, 还可选将你的脚本文件转为pyd,
  最后项目就打包完成了。因为会复制整个site-packages文件夹，所以普通模式只建议在虚拟环境中使用。
       
- 快速打包是先启动分析工具分析依赖文件。然后把依赖文件复制到保存目录，再自动生成exe, 没有项目瘦身这一步骤，
  所以没有虚拟环境的话，建议使用快速打包模式，它不会复制整个site-packages文件夹
- **2**: 注意事项
- 因360安全卫士会拦截打包相关工具, 所以，打包前请先关闭360安全卫士。
- 建议在虚拟环境中使用，非虚拟环境可能会打包无用的依赖
- 为了能完整记录依赖文件，监控工具启动后，会自动运行你的脚本，请对你的项目进行必要的操作：如点击运行按钮等，
  如：我使用openpyxl往表格中插入图片，项目自动启动后，我要让脚本执行这一操作，
  这样，监控工具才能监控到依赖文件，否则，最后的依赖文件记录不到，
  所以，请一定要注意，你的项目启动后，一定要默认监控时间18秒内执行必要的操作。
  18秒大概会产生几百兆的日志，所以，监控时间可以根据实际情况调整。
       
- **3**: 函数介绍

    - 1.打包项目
      ```python
      from soeasypack import to_pack
    
      def test():
          save_dir = r'C:\Users\Administrator\Desktop\aa\save_dir'
          main_py_path = r'C:\Users\Administrator\Desktop\bb\my_project\main.py'
          exe_name = '大都督'
          to_pack(main_py_path, save_dir, exe_name=exe_name, fast_mode=True,
              file_version='2.0', company='大都督', auto_py_pyd=True) 
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
- 如果你觉得对你有帮助的话，可以打赏1元让作者买个馍哦
![](https://github.com/XMQSVIP/MyImage/blob/main/zhi_wei.png?raw=true)

