# FeelUOwn 说明文档

## screenshot
- [查看最新进展截图](https://github.com/cosven/FeelUOwn/issues/140)
- [查看最新开发进度](https://github.com/cosven/FeelUOwn/issues/156)

![](http://7xnn7w.com1.z0.glb.clouddn.com/new_2.png)

## 安装

```
sudo apt-get install python3-pip
pip3 install feeluown
feeluown-install-dev   # 安装依赖
feeluown-genicon   # 生成图标

### 运行
feeluown

### 开发者运行
feeluown -d

### 更新，建议没事可以更新它，会有一些小的bug修复
### 有大的更新的时候，运行软件的时候会提示
pip3 install feeluown --upgrade
```
如果要体验最新开发进展：直接 git clone 项目，`make run` 即可


## 插件编写与安装
[插件编写与安装说明](https://github.com/cosven/FeelUOwn/issues/148)


## 常见问题
##### 搜索应用时有多个 feeluown, 桌面 feeluown 没有图标

手动删除桌面 feeluown 图标，因为它已经没用了，然后运行下面命令。
```
cd ~/.local/share/applications
rm FeelUOwn.desktop
```

##### 桌面歌词
- 首先下载安装 [feeluown-mpris2-plugin](https://github.com/cosven/feeluown-mpris2-plugin.git)
- 然后安装著名的 [osdlyrics](https://github.com/osdlyrics/osdlyrics)。安装这个东西有两种方法：一种自己编译安装，第二种在google上搜索 osdlyrics_0.4.3-1-precise1_amd64
  这个包，安装即可。（我自己只在Ubuntu 15.10上测试过）

##### Ubuntu 16.04 不能正常播放
```
sudo apt-get install gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly -y
```

##### 所有的依赖

```
# feeluown 包的系统依赖
gstreamer0.10-plugins-good  # 有的系统依赖 gstreamer1.0 版本
gstreamer0.10-plugins-bad
gstreamer0.10-plugins-ugly

python3-pyqt5
python3-pyqt5.qtmultimedia
libqt5multimedia5-plugins
fcitx-frontend-qt5  # 为了支持搜狗等 fcitx类的 中文输入法

# python3 的依赖
requests
quamash>=0.55

# 网易云音乐插件　需要的依赖
pycrypto    # python 库
```

> 安装一些其他的插件时，可能也需要其他的依赖包，请参照插件的　README

##### 获取更多主题
<https://github.com/mbadolato/iTerm2-Color-Schemes/tree/master/konsole>
下载喜欢的主题文件 `example.colorscheme`，把它放入 `~/.FeelUOwn/themes` 文件夹中
