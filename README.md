# FeelUOwn - feel your own

## 目标

1. 首先得是一个安装简单、使用方便的音乐播放器！
2. 还要是一个[符合 Unix 哲学](http://feeluown.readthedocs.io/en/latest/philosophy.html#unix-philosophy)的程序
3. 也希望成为一个 Python 新手可以快速上手的项目

- [项目开发计划](https://github.com/cosven/FeelUOwn/projects/1)
- [用户/开发者交流群](https://t.me/joinchat/H7k12hG5HYsGeBErs1tUQQ)
- [项目详细文档](http://feeluown.readthedocs.io)

## 特性
[Gallery](https://github.com/cosven/FeelUOwn/wiki/Gallery)

- [x] 容易安装，不折腾
- [x] 可以与 tmux/Emacs/vim 轻松集成
- [x] 支持本地音乐、网易云音乐主要功能（登录等）
- [ ] [10%] 文档健全
- [ ] [30%] 简单的插件机制
- [x] 多音乐平台支持
- [ ] [10%] 资源占用率低

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
