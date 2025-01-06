"""
@author:xmqsvip
Created on 2024-11-29
"""
from soeasypack import __version__
from setuptools import setup, find_namespace_packages

with open('README.md', encoding='utf-8') as fp:
    long_description = fp.read()

setup(name='soeasypack',
      description='简易精准打包python项目和依赖环境 Easy and precise packaging of python projects and dependencies',
      author='xmqsvip',
      author_email='xmqsvip@qq.com',
      long_description=long_description,
      long_description_content_type='text/markdown',
      packages=find_namespace_packages(),
      package_data={
          'soeasypack': ['dep_exe/**/*']},
      include_package_data=True,
      license='MIT',
      version=__version__,
      zip_safe=False,
      url="https://github.com/XMQSVIP/SoEasyPack",
      classifiers=[
          'Programming Language :: Python :: 3',
      ],
      keywords="soeasypack,SoEasyPack,packaging,pyinstaller,py2exe,cxfreeze",
      install_requires=["altgraph", "Cython"]
      )
# python setup.py sdist
# twine upload dist/*
