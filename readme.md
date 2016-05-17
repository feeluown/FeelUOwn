# FeelUOwn 说明文档

## screenshot
- [查看最新进展截图](https://github.com/cosven/FeelUOwn/issues/140)
- [查看最新开发进度](https://github.com/cosven/FeelUOwn/issues/156)

![](http://7xnn7w.com1.z0.glb.clouddn.com/new_2.png)

## 手动安装（适合于有一定技术基础）

```
git clone https://github.com/cosven/FeelUOwn.git
git checkout dev    # 使用开发版
cd FeelUOwn

sudo apt-get install python3-pyqt5.qtmultimedia libqt5multimedia5-plugins -y    # 播放音乐需要
sudo apt-get install fcitx-frontend-qt5 -y  # 输入中文需要
sudo apt-get install gstreamer0.10-plugins-good gstreamer0.10-plugins-bad gstreamer0.10-plugins-ugly -y   # 系统依赖

# 这些东西很多系统已经有了，以防万一，也安装一次
sudo apt-get install python3-setuptools
sudo apt-get install python3-pip
pip3 install -r requirements.txt  # 可能需要 加 sudo

```

#### 生成桌面图标
`sudo ./install.py`

## 插件编写与安装
[插件编写与安装说明](https://github.com/cosven/FeelUOwn/issues/148)


## 运行

普通用户搜索feeluown，点击图标运行即可

```
# 开发者调试程序
make run
```

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
