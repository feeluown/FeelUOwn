程序架构图
==========


Provider 管理部分
-----------------

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
                |+ user: \<UserModel\> or None\l
                |...
                |+ Song: \<SongModel\>\l
                |+ Playlist: \<PlaylistModel\>\l
                |+ ArtistModel: \<ArtistModel\>\l
                |+ AlbumModel: \<AlbumModel\>\l
                |...
            }"
        ]

        ProviderManager [
            label="{
                \N
                |+ list(): list\<AbstractProvider\>\l
                |+ get(identifier): \<AbstractProvider\>\l
                |+ register(provider): \l
                |...
            }"
        ]

        NeteaseProvider -> AbstractProvider[dir=back, arrowtail=odiamond]
        LocalProvider -> AbstractProvider[dir=back, arrowtail=odiamond]
        XxxProvider -> AbstractProvider[dir=back, arrowtail=odiamond]

        ProviderManager -> NeteaseProvider
        ProviderManager -> LocalProvider
        ProviderManager -> XxxProvider
    }
