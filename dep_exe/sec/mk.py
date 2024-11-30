import re

rr =r"C:\Users\Administrator\Desktop\bb\soeasypack\dep_exe\sec\窗体.bac"
# with open(rr, encoding='gbk')as fp:
#     content = fp.read()
#     nn = re.sub("运行",  '运行()', content)
#     # print(nn)
# # content = content.replace('运行命令', r'运行("C:\Users\Administrator\Desktop\bb\my_dist2\runtime0\python.exe", 1)', )
# # content = content.replace('运行("runtime\python.exe script\main.py", 1)', '运行命令', )
# with open(rr, mode='w', encoding='gbk')as fp:
#     fp.write(nn)

with open(rr, encoding='gbk')as fp:
    content = fp.read()
    print(content)