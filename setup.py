from setuptools import setup, find_packages

with open('README.md', encoding='utf-8')as fp:
      long_description = fp.read()

setup(name='soeasypack',
      description='简易精准打包python项目和依赖环境 \nEasy and precise packaging of python projects and dependencies',
      author='xmqsvip',
      author_email='xmqsvip@qq.com',
      long_description=long_description,
      long_description_content_type='text/markdown',
      packages=find_packages(),
      package_data={
      'soeasypack': ['dep_exe/**/*']},
      include_package_data=True,
      license='MIT',
      version='0.6.3',
      zip_safe=False,
      url = "https://github.com/XMQSVIP/SoEasyPack",
      classifiers=[
            'Programming Language :: Python :: 3',
      ],
      #搜索词
      keywords="soeasypack,SoEasyPack",
      install_requires=["Cython"]
      )
