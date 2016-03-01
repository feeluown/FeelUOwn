# FeelUOwn

![](http://7xnn7w.com1.z0.glb.clouddn.com/feeluown.png)


## Ubuntu 15.10 安装

> 运行下面3条命令，小白也可以正常使用。

```
git clone https://github.com/cosven/FeelUOwn.git
cd FeelUOwn
./install.sh
```

## Fedora 安装

可以从 FZUG 源安装。感谢 @1dot75cm, issue #97

```sh
sudo dnf install feeluown
```

### archlinux安装
感谢 @wenLiangcan
<https://aur.archlinux.org/packages/feeluown-git/>

```sh
yaourt -S feeluown-git 
```

## 目前依賴 (以ubuntu的包名为准)
Python 3, PyQt5

```
sudo apt-get install python3-pyqt5.qtmultimedia
sudo apt-get install python3-pyqt5.qtwebkit
sudo apt-get install libqt5multimedia5-plugins
sudo apt-get install fcitx-frontend-qt5
sudo apt-get install python3-xlib
sudo apt-get install python3-dbus
sudo apt-get install python3-dbus.mainloop.pyqt5

pip3 install -r requirements.txt
```

有的系统，比如说Ubuntu 还需要安装:（尤其那些播放不出声音来的，请把下面的依赖全部安装，以免出现未知的问题）

```
sudo apt-get install gstreamer0.10-plugins-good gstreamer0.10-plugins-bad gstreamer0.10-plugins-ugly
sudo apt-get install gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav
```

ArchLinux下的包名可能有些不一样, 比如上面提到的gstreamer1.0-*这些包


```
sudo pacman -S gst-plugins-good gst-plugins-bad gst-plugins-ugly
yaourt -S python-quamash-qt5
```

如果在安装完这些包之后，还是没有声音，可以提交相关issue

### 更新
```
cd FeelUOwn
# 运行update脚本
./update.sh
```

然后就可以搜索 FeelUOwn, 就可以从系统程序中找到

## Changelog

**2016年２月１日**
增加 _Linux MPRIS2 dbus interface_ 支持

**2015年11月10日**

1. 增加歌单操作功能
2. 增加相似歌曲功能

**2015年09月20日**

1. 加入私人FM
2. 完善桌面mini窗口
3. 自定义通知控件
4. 重构『播放器』的后台代码

**2015年08月27日**

1. 加入mac和linux平台的快捷键支持
2. 增加mini模式（按esc返回正常模式）
3. 改进代码结构
4. 去除任务栏图标.

**2015年08月10日**

1. 在并发这块，采用 asyncio 模块进行重构（所以，现在python3版本必须是3.3以上，最好3.4）
2. 网络库采用 requests 进行重构, 较好的提高了程序的性能和稳定性。
3. 自动登录
4. 修复部分已知bug
5. 改进UI，交互基本没变

**2015年07月07日**

1. 加入mv播放的功能（Ubuntu等一些系统需要下载VLC播放器，deepin需要有自带的deepin-movie）
2. 歌手和专辑链接可点击
3. 桌面歌词（有一定的bug，一些设置操作还没完成）

**2015-06-18**

1. 切换到Python3 + Pyqt5 + qtmultimedia开发
2. 去除了私人FM功能，帮助功能

**2015-6-3**

1. 用户登录（手机，网易通行证），保存密码
2. 读取用户自己创建和收藏列表，并进行播放
3. 歌曲搜索并播放
4. 添加歌曲到 个人喜欢的列表
5. 完善私人电台的功能

**2015-4-20**

1. 支持保存密码
2. 添加私人电台功能
3. 实现添加到喜欢列表的功能
4. 改善既有代码结构
5. 支持脚本更新

**2015-4-4**

1. 双击播放用户歌曲列表
2. 添加帮助功能
3. 修复：未登录情况下，专辑图片加载bug

**2015-4-3**

1. 改善既有代码结构
2. 添加手机登陆接口，支持手机号登陆
3. 当前播放列表中的当前播放歌曲高亮


**2015-4-2**

1. 增强用户可交互性：左下角的statusbar的信息提示更加科学

## 开发注意事项
1. 配置PYTHONPATH为`feeluown`目录
2. 确认安装了python3，pyqt5，pyqt5的multimedia库
3. 尽量遵守google的python代码风格指南
4. `TRY TO BE MORE PYTHONIC`


```
The Zen of Python, by Tim Peters

Beautiful is better than ugly.
Explicit is better than implicit.
Simple is better than complex.
Complex is better than complicated.
Flat is better than nested.
Sparse is better than dense.
Readability counts.
Special cases aren't special enough to break the rules.
Although practicality beats purity.
Errors should never pass silently.
Unless explicitly silenced.
In the face of ambiguity, refuse the temptation to guess.
There should be one-- and preferably only one --obvious way to do it.
Although that way may not be obvious at first unless you're Dutch.
Now is better than never.
Although never is often better than *right* now.
If the implementation is hard to explain, it's a bad idea.
If the implementation is easy to explain, it may be a good idea.
Namespaces are one honking great idea -- let's do more of those!
```


-----------------------------------------
> 此作品仅供学习参考，如有任何侵权，请通知作者。
> email: yinshaowen241\[at\]gmail\[dot\]com
