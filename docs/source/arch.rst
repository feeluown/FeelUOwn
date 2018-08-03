程序架构（WIP）
===============

在整体设计上，FeelUOwn 由两大部分组成：界面逻辑部分和核心逻辑部分。
它们对应着两个项目 `feeluown <https://github.com/cosven/feeluown>`_ 和
`feeluown-core <https://github.com/cosven/feeluown-core>`_

- feeluown 项目主要实现 FeelUOwn 的 GUI 逻辑
- feeluown-core 中实现一些核心逻辑，它以 fuocore 包的形式存在，`详细文档 <http://feeluown-core.readthedocs.io/zh_CN/latest/>`_：

  - 音乐播放引擎
  - fuo 协议
  - 音乐资源抽象（音乐库模块）
  - 插件模块（暂时在 feeluown 项目中，之后会迁移）

程序主界面
----------
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

音乐播放引擎模块(TODO)
----------------------

音乐库模块
----------
程序界面上「我的音乐」部分展示了程序已经支持的音乐提供方，我们称之为 ``provider``，
多个 provider 组成一个媒体库，称之为 ``library`` 。library 负责管理各 provider，将
相应的请求分发到个 provider 上。

当用户搜索音乐时，程序会调用 library 的 ``search`` 方法进行搜索，library 会把搜索
请求分发给各 provider，然后对各 provider 返回结果进行整合，展现给用户。

下面我们介绍下「音乐库」部分的整体架构：

App 实例有一个 library 属性，它负责管理各个 provider，我们可以使用
library 的 ``register`` 方法来注册 provider。

.. graphviz::

    digraph G {
        node[
            fontname = "Monospace"
            shape=record
            fontsize=8
        ]

        AbstractProvider [
            label="{
                \N
                |+ identifier: \<string\>\l
                |+ name: \<string\>\l
                |...
                |+ search(keyword, **kwargs): \<SearchModel\> \l
                |...
                |+ user: \<UserModel\> or None\l
                |...
                |+ Song: \<SongModel\>\l
                |+ Playlist: \<PlaylistModel\>\l
                |+ Artist: \<ArtistModel\>\l
                |+ Album: \<AlbumModel\>\l
                |...
            }"
        ]

        Library [
            label="{
                \N
                |+ register(provider): \l
                |+ search(keyword, **kwargs): \l
            }"
        ]

        NeteaseProvider -> AbstractProvider[arrowhead=empty]
        LocalProvider -> AbstractProvider[arrowhead=empty]
        XxxProvider -> AbstractProvider[arrowhead=empty]

        Library -> NeteaseProvider
        Library -> LocalProvider
        Library -> XxxProvider

        app[label="app.library"]
        app -> Library

        subgraph cluster0 {
            label="fuocore"
            style="dashed"
            color="grey"
            AbstractProvider
            NeteaseProvider
            LocalProvider
            XxxProvider
        }
    }

目前我们有网易云音乐、本地音乐、QQ 音乐三个资源提供放，
也有许多音乐爱好者也会使用 last.fm 等一些其它音乐平台，
但目前我们还没有足够精力支持这些平台 =。=，欢迎大家贡献插件。

编写一个音乐库的成本其实挺低的。目前，每个音乐库都是一个
小插件，我们只需要抓包获取其 API，然后就能轻松的写一个插件，编写方法可以参考
``feeluown/plugins/neteasemusic`` ，之后我们也会补充一些简单的例子和详细的教程。

插件模块(TODO)
--------------

fuo 协议模块(TODO)
------------------
