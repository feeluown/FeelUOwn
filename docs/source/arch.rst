程序架构
========

在整体设计上，FeelUOwn 由两大部分组成：界面逻辑部分和核心逻辑部分，
它们对应着两个项目 `feeluown <https://github.com/cosven/feeluown>`_ 和
`feeluown-core <https://github.com/cosven/feeluown-core>`_ 。

GUI 模块
--------
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

核心模块
--------
请看 feeluown-core 的 `设计文档 <https://feeluown-core.readthedocs.io/zh_CN/latest/design.html>`_
