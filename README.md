# FeelUOwn 说明文档

> trying to be a hackable music player for \*nix

## Features

- [x] 容易安装，不折腾
- [ ] [60%] 网络操作异步化
- [ ] 基于 TCP 的远程控制
- [x] 支持本地音乐、网易云音乐部分功能（登录等）
- [ ] 文档健全
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
