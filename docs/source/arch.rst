程序架构
========

FeelUOwn 中有一个核心对象 ``app``, 它是我们进行几乎一切操作的入口。
在初始化 app 时，我们会实例化一些类，比如 Library/LiveLyric, 这些实例工作不依赖
app 对象，我们把它们放在 feeluown 包中。另外，我们也会创建很多 Manager 实例，
比如 PluginManager/HotkeyManager 等，它们往往都是依赖 app 的，
我们目前将它们各自作为一个模块放在 feeluown 包中。

主要模块
--------

======   =================   =======================
稳定         名字                模块
======   =================   =======================
🔴       音乐资源模型          :py:mod:`feeluown.models`
🔴       音乐库               :py:class:`feeluown.library.Library`
🔴       播放器               :py:mod:`feeluown.player`
🔴       fuo 协议             :py:class:`feeluown.protocol.FuoProcotol`
🔴       版本                 :py:class:`feeluown.version.VersionManager`
🔴       小提示管理            :py:class:`feeluown.tips.TipsManager`
🔴       本地收藏管理           :py:class:`feeluown.collection.CollectionManager`
🔴       浏览历史记录           :py:mod:`feeluown.browser`
🔴       快捷键管理            :py:class:`feeluown.hotkey.HotkeyManager`
🔴       图片管理              :py:mod:`feeluown.image`
🔴       资源提供方 UI        :py:class:`feeluown.gui.uimodels.ProviderUiManager`
🔴       我的音乐 UI          :py:class:`feeluown.gui.uimodels.MyMusicUiManager`
🔴       歌单列表 UI          :py:mod:`feeluown.gui.uimodels.playlist`
======   =================   =======================


界面
--------

FeelUOwn 启动时有两种模式可以选择，CLI 模式和 GUI 模式，大部分 Manager
可以在两种模式下工作，也有一部分 Manager只在 GUI 模式下工作，这些 Manager
往往和 UI 操作相关。

FeelUOwn UI 部分的核心对象是 ``app.ui``, 我们下面就从界面开始，
来详细了解 FeelUOwn 程序的整体架构。

整个 GUI 区域划分比较简单和规整，下图大致的描述了 GUI 的几个主要组成部分。

图中文字部分对应的都是代码中的变量，它们也比较好的反映了对应区域的功能。
一开始对项目可能不是特别熟悉，大家可以对照这个图来看代码。

.. image:: https://user-images.githubusercontent.com/4962134/43657563-cf19c1aa-9788-11e8-9114-e83b9c9e41cf.png

从区域划分来看，程序主界面主要分为四大块（蓝色部分）：

1. ``magicbox`` : 用户搜索、显示用户操作通知、执行 fuo 命令、
   执行 Python 代码相关操作都在此组件中完成
2. ``left_panel`` : 显示音乐库、用户操作历史记录、用户歌单列表
3. ``right_panel`` : 目前显示歌单列表详情、歌手详情等。
   之后可能会支持更多其实形式的展示：比如批量展示专辑。
4. ``pc_panel`` : 与播放器相关的控制部分，主要是播放/暂停、进度条、
   音量调节、显示当前播放列表、修改播放模式等操作按钮。

各大块可以拆分成小块（红色部分）：

- **left_panel 区域**

  - ``provider_view`` 组件展示应用支持的音乐提供方
  - ``histories_view`` 组件展示用户浏览记录
  - ``playlists_view`` 组件展示用户歌单列表


- **right_panel 区域**

  - ``songs_table`` 批量展示歌曲，比如：歌单中的歌曲、搜索结果的歌曲部分等，
  - ``table_overview`` 是对 songs_table 的概览，由封面图和描述组成。
