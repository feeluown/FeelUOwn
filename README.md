# FeelUOwn 说明文档

> trying to be a hackable music player for \*nix

**NOTICE**: 当前正在基于 [feeluown-core](https://github.com/cosven/FeelUOwn-core) 对 feeluown 进行重构，请看 refactor 分支。

## Features

1. 支持网易云音乐大部分功能
2. 简单的插件机制
3. 多平台支持
4. TODO 远程控制（更方便的编写插件）

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

安装[这个插件](https://github.com/cosven/feeluown-mac-hotkey-plugin)可以在 osx 使用多媒体快捷键。


## 插件编写与安装
[插件编写与安装说明](https://github.com/cosven/FeelUOwn/issues/148)

一个非常[简单的插件例子](https://gist.github.com/cosven/7a746fa61f94a4c83cb6bf654cea6bf8)


#### linux 桌面歌词
- 首先下载安装 [feeluown-mpris2-plugin](https://github.com/cosven/feeluown-mpris2-plugin.git)
- 然后安装著名的 [osdlyrics](https://github.com/osdlyrics/osdlyrics)。安装这个东西有两种方法：一种自己编译安装，第二种在google上搜索 osdlyrics_0.4.3-1-precise1_amd64
  这个包，安装即可。（我自己只在Ubuntu 15.10上测试过）

**下面是我自己编译安装 osdlyrics 的过程**

```
git clone https://github.com/osdlyrics/osdlyrics
git checkout develop    # 我试过其他分支，反正就这个分支靠谱一些

./autogen.sh  # 安装好相关依赖，它会提醒你应该安装哪些依赖
make
sudo make install
```

##### 获取更多主题
<https://github.com/mbadolato/iTerm2-Color-Schemes/tree/master/konsole>
下载喜欢的主题文件 `example.colorscheme`，把它放入 `~/.FeelUOwn/themes` 文件夹中


##### 怎样收藏歌曲到某个歌单
把歌曲拖动到某个歌单即可。
