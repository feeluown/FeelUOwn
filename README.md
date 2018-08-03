## FeelUOwn - feel your own

FeelUOwn 是一个符合 Unix 哲学的跨平台的音乐播放器，主要面向 Linux/macOS 用户。

[![macOS 效果预览](https://user-images.githubusercontent.com/4962134/43506587-1c56c960-959d-11e8-964f-016159cbeeb9.png)](https://github.com/cosven/FeelUOwn/wiki/Gallery)

### 特性

- 安装简单，新手友好
- 默认提供国内各音乐平台插件（网易云、虾米、QQ）
- 较强的可扩展性可以满足大家折腾的欲望 | [Slack 插件示例](https://gist.github.com/cosven/7a746fa61f94a4c83cb6bf654cea6bf8) | [MPRIS2 插件](https://github.com/cosven/feeluown-mpris2-plugin)
  - 和 Emacs 集成、纯命令行使用 | [DEMO](https://www.youtube.com/watch?v=-JFXo0J5D9E)
- 核心模块有较好文档和测试覆盖，欢迎大家参与开发 | [详细文档](http://feeluown.readthedocs.org) | [开发者/用户交流群](https://t.me/joinchat/H7k12hG5HYsGeBErs1tUQQ)

### 使用方法

**安装**

```shell
# Ubuntu 用户可以依次执行以下命令进行安装
sudo apt-get install python3-pyqt5  # 安装 Python PyQt5 依赖包
sudo apt-get install libmpv1        # 安装 libmpv1 系统依赖
pip3 install 'feeluown>=2.0.1' --user -i https://pypi.org/simple/
## 为 feeluown 生成图标（Linux 用户）
feeluown-genicon   # 生成图标

## 一些非必须依赖
sudo apt-get install fcitx-frontend-qt5  # 使用 fcitx 输入法的用户可能需要安装

# macOS 用户安装方法
brew install pyqt
brew install mpv
pip3 install 'feeluown>=2.0.1' --upgrade --user
```

**使用**

```shell
# 第一种方法：Linux 用户直接点击图标运行程序
# 第二种方法：在命令行中启动，这时候会弹出 GUI 界面
feeluown
# 第三种方法：适用于不需要 GUI 界面的用户（比如使用命令行或者使用 Emacs 插件等）
feeluown -nw     # -nw 表示 no window
feeluonw -nw -d  # -d 表示打开 debug 模式，会输出更多日志
```

### 常见问题
其它常见问题请阅读文档：http://feeluown.readthedocs.io/en/latest/faq.html

##### 怎样参与设计开发、如果编写插件？

目前，一方面可以通过阅读开发者文档来了解项目整体架构；另一方面，可以加入开发者/用户交流群，与大家一起讨论，大部分我自己也会在线，如果有相关疑问，我会尽量和大家沟通。

##### 程序遇到错误怎么办？

一般来说，feeluown 运行时，会将日志输出到 `~/.FeelUOwn/stdout.log` ，如果大家在使用时遇到程序异常，可以新建一个 Issue，将日志或者截图放在 Issue 中，让大家帮忙解答。另外，大家也可以加入交流群，在群中提出建议或者反馈。

##### 有项目开发计划或者 bug 修复排期吗？

大家可以参考[这个项目开发计划](https://github.com/cosven/FeelUOwn/projects)
