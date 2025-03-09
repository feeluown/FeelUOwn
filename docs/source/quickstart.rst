快速上手
========

FeelUOwn 使用 Python 3 进行开发，目前默认使用 mpv 作为其播放引擎，
基于 PyQt5 构建 GUI。

安装
----

如果你有一定折腾经验，你可以参考“通用安装办法”，它可控性强、行为可预期。
你也可以参考各个平台的安装教程来安装 FeelUOwn。你可以在两种方法中灵活选择。

通用安装办法
~~~~~~~~~~~~~~~~

安装 FeelUOwn 分两步。一步是安装 libmpv；一步是安装 FeelUOwn 及其依赖的 Python 包。

1. libmpv 通常可以使用系统包管理器安装
2. FeelUOwn 及其依赖的 Python 包可以使用 Python 包管理工具来安装（如 pipx 或者 uv）。

libmpv, pipx 通常可以通过系统包管理器来安装，如 Debian Linux 可以使用 apt-get 命令，
macOS 可以 brew 命令等。

.. sourcecode:: sh

    # macOS
    brew install mpv pipx

    # Ubuntu
    sudo apt-get install libmpv1 pipx

在安装好 libmpv 和 Python 包管理工具后。你可以运行如下命令来安装 FeelUOwn 及其依赖的 Python 包：

.. sourcecode:: sh

    # Linux 用户可以使用如下命令
    pipx install feeluown[battery,ai,cookies,webengine,qt] -v

    # macOS 和 Windows 用户可以分别使用如下命令
    # 建议优先使用 Python 3.10/3.11 版本（部分依赖包没有适配 3.12 和 3.13 版本）
    pipx install feeluown[battery,ai,cookies,webengine,qt,macos] --python `which python3.11` -v
    pipx install feeluown[battery,ai,cookies,webengine,qt,win32] --python `which python3.11` -v

Ubuntu
~~~~~~

下面命令在 Ubuntu 18.04 中测试通过，理论上其它 Linux 发行版
安装流程类似，只是一些包的名字可能有些许差别。

.. sourcecode:: sh

    # 安装 Python 3 和 pipx （大部分系统已经安装好了）
    sudo apt-get install python3 python3-pip pipx

    # 配置 pipx
    # pipx 的安装配置教程可以参考：https://github.com/pypa/pipx?tab=readme-ov-file#on-linux
    pipx ensurepath
    sudo pipx ensurepath --global

    # 安装 libmpv1
    sudo apt-get install libmpv1

    # 安装 PyQt5
    sudo apt-get install python3-pyqt5 python3-pyqt5.qtopengl python3-pyqt5.qtsvg

    # 安装 dbus-python
    sudo apt-get install python3-dbus python3-dbus.mainloop.pyqt5

    # 安装 feeluown （是一个 Python 包）
    # --upgrade 代表安装最新版，--user 代表不安装到系统目录
    pipx install 'feeluown[battery,cookies,webengine,ai]'
    pipx inject feeluown pyopengl

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

    # macOS Monterey（版本12）实测可以安装，版本 11 可能不能正常安装
    # (https://github.com/feeluown/FeelUOwn/issues/421)
    brew tap feeluown/feeluown
    brew install feeluown --with-battery # 更多选项见 `brew info feeluown`
    feeluown genicon  # 在桌面会生成一个 FeelUOwn 图标

Windows
~~~~~~~

你可以从 `发布页 <https://github.com/feeluown/distribution/releases>`_ 直接下载打包好的压缩包。
也可以按照如下步骤手动进行安装：

1. 安装 Python 3，参考 `链接 <https://www.python.org/downloads/windows/>` （请勿从应用商店安装）
2. 下载 `mpv-1.dll <https://github.com/feeluown/FeelUOwn/releases/latest>`_ ，
   将 mpv-1.dll 放入 ``C:\Windows\System32`` 目录。
3. 安装 PyQt5，在 cmd 中运行 ``pip3 install PyQt5 -i https://pypi.douban.com/simple``
4. 安装 feeluown，在 cmd 中运行 ``pip3 install feeluown[battery,win32]``
5. 在 cmd 中运行 ``python -m feeluown genicon`` 命令，可以生成桌面图标

Arch Linux
~~~~~~~~~~

https://archlinux.org/packages/extra/any/feeluown/

Gentoo
~~~~~~

https://github.com/microcai/gentoo-zh/tree/master/media-sound/feeluown

Debian
~~~~~~

https://github.com/coslyk/debianopt-repo

NixOS
~~~~~

https://github.com/berberman/flakes

openSUSE
~~~~~~~~

对于 openSUSE Tumbleweed，请以根用户 root 运行下面命令：

.. sourcecode:: sh

    zypper addrepo https://download.opensuse.org/repositories/home:weearcm/openSUSE_Tumbleweed/home:weearcm.repo
    zypper refresh
    zypper install --recommends feeluown

对于 openSUSE Slowroll，请以根用户 root 运行下面命令：

.. sourcecode:: sh

    zypper addrepo https://download.opensuse.org/repositories/home:weearcm/openSUSE_Slowroll/home:weearcm.repo
    zypper refresh
    zypper install --recommends  feeluown

详情可以参考： `#833 <https://github.com/feeluown/FeelUOwn/issues/833>`_

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
