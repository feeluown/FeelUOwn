# FeelUOwn

从之前的 “网易云音乐 For Linux(第三方版)” 项目发展过来
之前的项目托管地址：<https://git.oschina.net/zjuysw/NetEaseMusic>

技术框架大致的说明： <http://www.cosven.com/2015/07/07/FeelUOwn-%E6%8A%80%E6%9C%AF%E9%98%B6%E6%AE%B5%E6%80%BB%E7%BB%93/>

> 欢迎有兴趣的小伙伴进行合作开发，搭建基础的框架。也可以开发一些插件，比如说 添加一些数据可视化，增加一些炫酷的动画特效。等等

** 2015-8-2 **

1. 使用 `asyncio` 对项目进行重构
2. 提高程序的性能和稳定性

> 最新程序使用了`asyncio`库的原因，所以要求python版本最低是3.3, 最好是3.4.
> ( Ubuntu 14.04 和 deepin 2014.3 上面的python3版本默认已经是3.4了， 或者upgrade一下就行)， 其他版本的我还没有试过


** 接下来打算 **

- 添加设置功能
- 添加数据缓存功能

## 目前依賴
Python 3, PyQt5

```
sudo apt-get install python3-pyqt5.qtmultimedia
sudo apt-get install python3-pyqt5.qtwebkit
```

有的系统，比如说Ubuntu 还需要安装:（尤其那些播放不出声音来的，请把下面的依赖全部安装，以免出现未知的问题）

```
sudo apt-get install libqt5multimedia5-plugins
sudo apt-get install gstreamer0.10-plugins-good gstreamer0.10-plugins-bad gstreamer0.10-plugins-ugly
sudo apt-get install gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav
```

ArchLinux下的包名可能有些不一样, 比如上面提到的gstreamer1.0-*这些包


```
sudo pacman -S gst-plugins-good gst-plugins-bad gst-plugins-ugly
```

如果在安装完这些包之后，还是没有声音，可以提交相关issue

### 安装使用

```
git clone https://github.com/cosven/FeelUOwn.git
cd FeelUOwn
./install.sh
```

### 更新
```
cd FeelUOwn
# 运行update脚本
./update.sh
```

然后就可以搜索 FeelUOwn, 就可以从系统程序中找到


## 程序架构

**想实现的一些特性**

1. 可以支持大部分音乐平台的资源。
2. 支持歌曲缓存

### 界面显示模块
1. 界面交互控制模块。前端的交互控制，给用户良好的交互体验。
2. 主题切换模块。主要依靠切换qss文件来切换主题

### 控制模块
1. 播放器模块
2. 网络访问模块（主要负责和第三方的音乐网站链接）（可能将来会合并到qt的网络模块中去）
3. 插件模块。提供一些接口用来编写插件，比如说连接第三方音乐网站的api。还有一些歌词显示功能，或者相似歌曲推荐这样的高级功能，都可以作为plugin合并入项目。
4. Qt网络访问模块，提供一些具体的图片及其音乐下载。（异步，将为用户提供更好的体验）

### 数据模型
1. 数据标准模型。从第三方来的数据都需要转换为一个标准的数据模型。
2. 数据提取模型。第三方的数据格式或者数据内容各不一样，所以需要对它们进行转换。
3. 数据缓存模型

## 其他模块
1. 调试输出模块
2. 基本路径等配置

## 开发注意事项
1. 配置PYTHONPATH为`src`目录
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
