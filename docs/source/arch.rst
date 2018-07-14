程序架构图
==========

音乐库模块
----------
程序界面上「我的音乐」部分展示了程序支持的音乐库，目前有网易云音乐、
本地音乐、QQ 音乐，这进行搜索的时候，程序会在这几个音乐库中进行搜索。
也有许多音乐爱好者也会使用 last.fm 等一些其它音乐平台，
但目前我们还没有足够精力支持这些平台 =。=，欢迎大家贡献插件。

编写一个音乐库的成本其实挺低的。目前，每个音乐库都是一个
小插件，我们只需要抓包获取其 API，然后就能轻松的写一个插件，编写方法可以参考
``feeluown/plugins/neteasemusic`` ，之后我们也会补充一些简单的例子和详细的教程。

下面我们介绍下「音乐库」部分的整体架构：


App 实例有一个 LibrariesModel 属性，它负责管理各个 Library，我们可以使用
Librariesmodel 的 register 方法来注册 Library。

一个 Library 对应 fuocore 中的一个 provider，feeluown 中只依赖 Library
这个概念，不会大量使用 provider 概念。

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

        LibrariesModel [
            label="{
                \N
                |+ register(library): \l
                |+ search(keyword, **kwargs): \l
            }"
        ]

        LibraryModel [
            label="{
                \N
                |+ identifier: \<string\> \l
                |+ name: \<string\> \l
                |+ icon: \<string\> \l
                |+ desc: \<string\> \l
                |...
                |+ _on_click: \l
                |...
                |+ search(keyword, **kwargs): \l
                |...
            }"
        ]

        NeteaseProvider -> AbstractProvider[arrowhead=empty]
        LocalProvider -> AbstractProvider[arrowhead=empty]
        XxxProvider -> AbstractProvider[arrowhead=empty]

        LibrariesModel -> NeteaseLibrary
        LibrariesModel -> LocalLibrary
        LibrariesModel -> XxxLibrary
        XxxLibrary -> LibraryModel[arrowhead=empty]

        XxxLibrary -> XxxProvider[style=dashed, dir=none]

        app[label="App(instance)"]
        app -> LibrariesModel

        subgraph cluster0 {
            label="fuocore"
            style="dashed"
            color="grey"
            AbstractProvider
            NeteaseProvider
            LocalProvider
            XxxProvider
        }

        subgraph cluster1 {
            label="feeluown"
            style="dashed"
            color="grey"
            LibrariesModel
            NeteaseLibrary
            LocalLibrary
            XxxLibrary
            LibraryModel
        }
    }


插件模块
--------
