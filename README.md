## FeelUOwn - feel your own

[![Documentation Status](https://readthedocs.org/projects/feeluown/badge/?version=latest)](http://feeluown.readthedocs.org)
[![Build Status](https://travis-ci.org/cosven/FeelUOwn.svg?branch=master)](https://travis-ci.org/cosven/FeelUOwn)
[![Coverage Status](https://coveralls.io/repos/github/cosven/FeelUOwn/badge.svg?branch=master&service=github)](https://coveralls.io/github/cosven/FeelUOwn?branch=master)
[![PyPI](https://img.shields.io/pypi/v/fuocore.svg)](https://pypi.python.org/pypi/feeluown)
[![python](https://img.shields.io/pypi/pyversions/fuocore.svg)](https://pypi.python.org/pypi/feeluown)

FeelUOwn 是一个符合 Unix 哲学的跨平台的音乐播放器～

[![macOS 效果预览](https://user-images.githubusercontent.com/4962134/52162110-ea439f80-2709-11e9-9558-47f015de839b.png)](https://www.bilibili.com/video/av46787694/)

### 特性

- 安装简单，新手友好，默认提供国内各音乐平台插件（网易云、虾米、QQ）
- 较强的可扩展性可以满足大家折腾的欲望 | [Slack 插件示例](https://gist.github.com/cosven/7a746fa61f94a4c83cb6bf654cea6bf8) | [MPRIS2 插件](https://github.com/cosven/feeluown-mpris2-plugin)
  - 和 Emacs 集成、纯命令行使用 | [DEMO](https://www.youtube.com/watch?v=-JFXo0J5D9E)
- 核心模块有较好文档和测试覆盖，欢迎大家参与开发 | [详细文档](http://feeluown.readthedocs.org) | [开发者/用户交流群](https://t.me/joinchat/H7k12hG5HYtsnOWpUDNMVw)

### 文档

详细用户及开发者文档请看：https://feeluown.readthedocs.io/

### 安装与使用

**安装**

```shell
# Arch Linux 用户可以从 aur 中安装，包名为 feeluown

# Ubuntu 用户可以依次执行以下命令进行安装
sudo apt-get install python3-pyqt5  # 安装 Python PyQt5 依赖包
sudo apt-get install python3-pyqt5.qtopengl
sudo apt-get install libmpv1        # 安装 libmpv1 系统依赖
pip3 install 'feeluown[battery]>=3.0' --user -i https://pypi.org/simple/
## 为 feeluown 生成图标（Linux 用户）
feeluown-genicon   # 生成图标

## 一些非必须依赖
sudo apt-get install fcitx-frontend-qt5  # 使用 fcitx 输入法的用户可能需要安装

# macOS 用户安装方法
brew install pyqt
brew install mpv
pip3 install 'feeluown[battery,macos]>=3.0' --user -i https://pypi.org/simple/
```

**使用**

```shell
# 第一种方法：Linux 用户直接点击图标运行程序
# 第二种方法：在命令行中启动，这时候会弹出 GUI 界面
fuo
# 第三种方法：适用于不需要 GUI 界面的用户（比如使用命令行或者使用 Emacs 插件等）
fuo -nw     # -nw 表示 no window
fuo -nw -d  # -d 表示打开 debug 模式，会输出更多日志
```

### 已知的一些插件

大家如果发现或者自己编写了一些插件，可以在下面进行补充～

| 插件名 | 开发者们  | 状态 |
| ------- | ------ | -------- |
| [MPRIS2](https://github.com/cosven/feeluown-mpris2-plugin) | [@cosven](https://github.com/cosven) | 可用 |
| [Discord RPC Rich Precense 服务](https://github.com/BruceZhang1993/feeluown-discordrpc-plugin) | [@BruceZhang1993](https://github.com/BruceZhang1993) | 可用 |
