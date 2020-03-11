快速上手
========

FeelUOwn 使用 Python 3 进行开发，目前默认使用 mpv 作为其播放引擎，
基于 PyQt5 构建 GUI。

安装
----

Ubuntu
~~~~~~

下面命令在 Ubuntu 18.04 中测试通过，理论上其它 Linux 发行版
安装流程类似，只是一些包的名字可能有些许差别。

.. sourcecode:: sh

    # 安装 Python 3 和 pip3（大部分系统已经安装好了）
    sudo apt-get install python3 python3-pip

    # 安装 libmpv1
    sudo apt-get install libmpv1

    # 安装 PyQt5
    sudo apt-get install python3-pyqt5
    sudo apt-get install python3-pyqt5.qtopengl

    # 安装 dbus-python
    sudo apt-get install python3-dbus
    sudo apt-get install python3-dbus.mainloop.pyqt5

    # 安装 feeluown （是一个 Python 包）
    # --upgrade 代表安装最新版，--user 代表不安装到系统目录
    pip3 install 'feeluown>=3.0[battery]' --upgrade --user

    # 运行 feeluown -h 来测试安装是否成功
    # 如果提示 Commmand Not Found，请查看文档「常见问题」部分
    feeluown -h

    # 生成桌面图标
    feeluown-genicon

    # （可能还需要安装）使用 fcitx 输入法的用户可能需要安装
    # 否则有可能不能在 GUI 中切换输入法
    sudo apt-get install fcitx-frontend-qt5

macOS
~~~~~

.. sourcecode:: sh

    brew install python3
    brew install pyqt
    brew install mpv
    pip3 install 'feeluown[battery,macos]>=3.0' --upgrade
    feeluown-genicon  # 在桌面会生成一个 FeelUOwn 图标

Windows
~~~~~~~

1. 安装 Python 3，参考 `链接 <https://www.python.org/downloads/windows/>` （请勿从应用商店安装）
2. 下载 `mpv-1.dll <https://github.com/cosven/FeelUOwn/releases/download/v3.0.1/mpv-1.dll>`_ ，
   将 mpv-1.dll 放入 ``C:\Windows\System32`` 目录。
3. 安装 PyQt5，在 cmd 中运行 ``pip3 install PyQt5 -i https://pypi.douban.com/simple``
4. 安装 feeluown，在 cmd 中运行 ``pip3 install feeluown[battery,win32]``
5. 在 cmd 中运行 ``python -m feeluown genicon`` 命令，可以生成桌面图标

Arch Linux
~~~~~~~~~~

https://aur.archlinux.org/packages/feeluown/

Gentoo
~~~~~~

https://github.com/microcai/gentoo-zh/tree/master/media-sound/feeluown

Debian
~~~~~~

https://github.com/coslyk/debianopt-repo


基本使用
--------

大家有几种方式启动 FeelUOwn：

1. 直接双击桌面 FeelUOwn 图标，这时启动 GUI/Daemon 混合模式
2. 在命令行中运行 ``feeluown`` 命令，这时也是混合模式
3. 在命令行中运行 ``feeluown -nw`` 命令，这时是 Daemon 模式

Daemon 模式的使用方法，这里简单说明：
（提示：如果不熟悉命令行，DAEMON 模式可能会有一定的折腾）

.. code:: sh

    feeluown -nw  # 使用 Daemon 模式启动 feeluown
    fuo status  # 查看播放器状态
    fuo search 周杰伦  # 搜索歌曲
    fuo play fuo://netease/songs/470302665  # 播放：（世界が终るまでは…）《灌篮高手》


如果大家对 `NetCat <https://en.wikipedia.org/wiki/Netcat>`_ 工具熟悉

.. code:: sh

    nc localhost 23333
    # 输入 `status` 命令，可以查看播放器状态
    # 输入 `fuo play fuo://netease/songs/470302665` 可以播放音乐

关于 Daemon 更多使用细节，大家可以参考运行 ``fuo -h`` 来查看帮助文档
