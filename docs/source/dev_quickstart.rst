本地开发快速上手
================
首先，非常感谢您愿意贡献自己的力量让 FeelUOwn 播放器变得更好～

推荐的开发流程
--------------

这里假设读者已经对 Git 和 Python 相关工具比较熟悉

1. 在 GitHub 上 fork 一份代码到自己名下
2. clone 自己 fork 的代码： ``git clone git@github.com:username/FeelUOwn.git``
3. 在 Home 目录或者项目目录下创建一个虚拟环境（假设你已经安装 Python 3） ::

     # 以在 Home 目录下创建虚拟环境为例

     # 创建 ~/.venvs 目录，如果之前没有创建的话
     mkdir -p ~/.venvs

     # 创建虚拟环境（大家也可以选择用 virtualenv）
     python3 -m venv ~/.venvs/fuo

     # 激活虚拟环境
     source ~/.venvs/fuo/bin/activate

     # 安装项目依赖
     pip3 install -e .


.. note::

   在 Linux 或者 macOS 下，大家一般都是用 apt-get 或者 brew 将 ``PyQt5`` 安装到 Python 系统包目录，
   也就是说，在虚拟环境里面， **不能 import 到 PyQt5 这个包** 。建议的解决方法是：

   1. 创建一个干净的虚拟环境（不包含系统包）
   2. ``pip3 install -e .`` 安装项目以及依赖
   3. 将虚拟环境配置改成包含系统包，将 ``~/.venvs/fuo/pyvenv.cfg``
      配置文件中的 ``include-system-site-packages`` 字段的值改为 ``true``

   这样可以尽量避免包版本冲突、以及依赖版本过低的情况

4. 以 debug 模式启动 feeluown ::

     # 运行 feeluown -h 查看更多选项
     feeluown --debug

5. 修改代码
6. push 到自己的 master 或其它分支
7. 给 FeelUOwn 项目提交 PR
8. （可选）在开发者群中通知大家进行 review


程序启动流程
----------------------

``feeluown(fuo)`` 命令入口文件为 ``feeluown/entry_points/run.py`` ，主函数为 run 函数。


.. _feeluown: http://github.com/feeluown/feeluown
.. _廖雪峰的Git教程: https://www.liaoxuefeng.com/wiki/0013739516305929606dd18361248578c67b8067c8c017b000
