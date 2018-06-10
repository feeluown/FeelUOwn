# FeelUOwn 说明文档

> trying to be a hackable music player for \*nix

## Features

- [x] 容易安装，不折腾
- [ ] 网络操作异步化
- [ ] 基于 TCP 的远程控制
- [x] 支持网易云音乐部分功能（登录等）
- [ ] 文档健全
- [ ] 简单的插件机制
- [x] 多平台支持

## screenshot
![截图](https://cloud.githubusercontent.com/assets/4962134/17672685/235ae556-6350-11e6-98c6-1f18051e5da1.png)

## 安装方法

### ubuntu 安装方法

```shell
sudo apt-get install libmpv1
sudo apt-get install python3-pip
sudo -H pip3 install feeluown
feeluown-install-dev   # 安装依赖
mkdir ~/.FeelUOwn
feeluown-genicon   # 生成图标

### 开发者运行
feeluown -d

### 更新，建议没事可以更新它，会有一些小的bug修复
pip3 install feeluown --upgrade
```

建议安装[feeluown-mpris2-plugin](https://github.com/cosven/feeluown-mpris2-plugin.git) 这个插件支持快捷键等高级特性。

### osx 安装方法

```shell
brew install mpv  # 安装 mpv 播放器
brew install pyqt --with-python3  # 安装 pyqt5， python3 支持
pip3 install feeluown

# 运行
feeluown
```

## 插件编写与安装
[插件编写与安装说明](https://github.com/cosven/FeelUOwn/issues/148)

一个非常[简单的插件例子](https://gist.github.com/cosven/7a746fa61f94a4c83cb6bf654cea6bf8)