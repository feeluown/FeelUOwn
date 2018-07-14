# feel your own

> trying to be a hackable music player for \*nix

**feeluown 的几个终极目标：**

1. 提供一个安装简单、使用方便的音乐播放器
2. 容易和外部 *nix 程序集成
3. 可以帮助 Python 爱好者成长的项目

- [项目开发计划](https://github.com/cosven/FeelUOwn/projects/1)
- [用户/开发者交流群](https://t.me/joinchat/H7k12hG5HYsGeBErs1tUQQ)
- [详细文档](http://feeluown.readthedocs.io)

## Features

- [x] 容易安装，不折腾
- [ ] [60%] 网络操作异步化
- [ ] 基于 TCP 的远程控制
- [x] 支持本地音乐、网易云音乐部分功能（登录等）
- [ ] [05%] 文档健全
- [ ] [30%] 简单的插件机制
- [x] 多平台支持

## screenshot
![截图](https://user-images.githubusercontent.com/4962134/41827460-2a38b370-7862-11e8-9195-24dd3987c4b3.png)

## 安装方法

```
pip3 install feeluown>=2.0a0 --user

# 安装系统依赖
## Ubuntu/Debian
sudo apt-get install python3-pyqt5
sudo apt-get install fcitx-frontend-qt5  # 使用 fcitx 输入法的用户需要安装
sudo apt-get install libmpv1  # 安装 mpv 播放器
feeluown-genicon   # 生成图标

## MacOS
brew install pyqt
brew install mpv
```

## 开发

在本地新建一个虚拟环境，clone feeluown 和 feeluown-core 两个项目。
将两个项目安装到虚拟环境当中，然后进行开发。项目正处于积极开发阶段，
代码每天都可能有较多修改，建议大家开发前先 rebase；另外，feeluown
最新代码很可能会依赖 master 分支的 feeluown-core 代码。

```
# install feeluown
git clone https://github.com/cosven/FeelUOwn.git
cd feeluown
pip install -e . # Ensure you have activated your venv
cd ..

# install feeluown-core
git clone https://github.com/cosven/feeluown-core
cd feeluown-core
pip install -e .
```
