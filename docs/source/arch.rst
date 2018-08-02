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

插件模块
--------

fuo 协议模块
------------
