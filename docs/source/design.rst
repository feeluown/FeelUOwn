核心模块设计
============

fuocore 是 feeluown core 的缩写，它是 feeluown 的核心模块。
而 fuocore 又由几个小模块组成，它们分别是：

1. ``音乐库模块`` ：对各平台音乐资源进行抽象及统一
2. ``播放器模块`` ：音乐播放器
3. ``歌词模块`` ：歌词解析

另外，fuocore 也包含了几个工具类

1. asyncio/threading tcp server
2. signal/slot
3. pubsub server

.. note::

   Q: 部分基础组件已经有更好的开源实现，为什么我们这里要重新造了一个轮子？
   比如 tcp server，Python 标准库 Lib/socketserver.py 中提供了更加完善的
   TcpServer 实现。

   A: 我也不知道为啥，大概是为了学习和玩耍，嘿嘿～ 欢迎大家对它们进行优化，
   希望大家享受造轮子和改进轮子的过程。


音乐库模块
---------
音乐库模块由几个部分组成：音乐对象模型(Model)、音乐提供方(Provider)、提供方管理(Library)。

音乐对象模型
''''''''''
**音乐库模块最重要的部分就是定义了音乐相关的一些领域模型** 。
比如歌曲模型、歌手模型、专辑模型等。其它各模块都会依赖这些模型。
这些模型在代码中的体现就是一个个 Model，这些 Model 都定义在 models.py 中，
举个例子，我们对歌曲模型的定义为::

    class SongModel(BaseModel):
        class Meta:
            model_type = ModelType.song.value
            # TODO: 支持低/中/高不同质量的音乐文件
            fields = ['album', 'artists', 'lyric', 'comments', 'title', 'url',
                      'duration', ]

        @property
        def artists_name(self):
            return ','.join((artist.name for artist in self.artists))

        @property
        def album_name(self):
            return self.album.name if self.album is not None else ''

        @property
        def filename(self):
            return '{} - {}.mp3'.format(self.title, self.artists_name)

        def __str__(self):
            return 'fuo://{}/songs/{}'.format(self.source, self.identifier)  # noqa

        def __eq__(self, other):
            return all([other.source == self.source,
                        other.identifier == self.identifier])

这个模型的核心意义在于：它定义了一首歌曲 **有且只有** 某些属性， **其它模块可以依赖这些属性** 。
举个例子，在程序的其它模块中，当我们遇到 song 对象时，我们可以确定，
这个对象一定 **会有 title 属性** 。如上所示，还有 ``album`` , ``artists`` , ``lyric`` ,
``comments`` , ``artists_name`` 等属性。

虽然这些模型一定会有这些属性，但我们访问时仍然要注意两点。

1. **属性的值不一定是可用的** 。比如一首歌可能没有歌词，
也没有评论，这时，我们访问这首歌 ``song.lyric`` 时，得到的就是一个空字符串，
访问 ``song.comments`` 属性时，得到的是一个空列表，但不会是 None 。

2. **第一次获取属性的值的时候可能会产生网络请求** 。以歌曲为例，
第一次获取歌曲 ``url`` , ``lyric`` , ``comments`` 等属性时，往往会产生网络请求；
以专辑为例，第一次获取专辑的 songs 属性时，往往也会产生网络请求，而第二次获取
就会非常快。

.. todo::

   第二点也隐含一个问题： *获取一个 Model 某个字段的值的行为变得不可预期* 。

   这个设计对开发者来说有利有弊，这样设计的缘由 :ref:`research-model`
   欢迎大家对此进行讨论，提出更好的方案。

provider
''''''''
每个音乐提供方都对应一个 provider，provider 是我们访问具体一个音乐平台资源音乐的入口。

举个栗子，如果我们要从网易云音乐中搜索音乐：

.. code:: python

   from fuocore.netease import provider
   result = provider.search('keyword')

再举另外一个栗子，如果我们知道网易云音乐一首歌曲的 id，我们可以通过下面的方式来获取音乐详细信息：

.. code:: python

   from fuocore.netease import provider
   song = provider.Song.get(song_id)

如果我们需要以特定的身份来访问音乐资源，我们可以使用 provider 的 ``auth`` 方法：

.. code:: python

   from fuocore.netease import provider
   user_a = obj  # UserModel
   provider.auth(user_a)

   # 使用 auth_as 来临时切换用户身份
   with provider.auth_as(user_b):
      provider.Song.get(song_id)


播放器模块
----------
暂时略，可以参考播放器 :doc:`./api`

歌词模块
--------
暂时略，可以参考歌词模块 :doc:`./api`
