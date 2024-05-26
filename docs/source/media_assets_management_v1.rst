(Deprecated) 媒体资源管理 v1
=================================

feeluown 一个设计目标是让用户能够合理整合并高效使用自己在各个音乐平台能获取的资源。
而每个平台提供资源数据的方式都有差异。有的可能已经公开的 RESTful API，它可以获取到资源的元信息，
并且也有接口可以获取到资源的链接；而有的平台则没有公开的可用接口，但是通过一些技术手段（如爬虫），
也可以获取到平台的资源。另外，每个平台的资源模型也有差异。有的平台会用一个非常大的结构体来表示一首歌曲；
而有的平台会有很多个小结构体，来拼凑出一首歌曲的全部信息。这些平台的差异给 feeluown 的架构设计带来了一些挑战，
feeluown 通过“媒体资源管理”子系统来解决这些困难。

音乐库是媒体资源管理子系统的入口。音乐库部分负责管理 feeluown 的音乐资源，包括歌曲、歌手、专辑详情获取，
专辑、歌单封面获取及缓存（这是设计目标，部分逻辑目前未实现）。它主要由几个部分组成：
音乐对象模型(*Model*)、音乐提供方(*Provider*)、提供方管理(*Library*)。

.. code::

    +-------------------------------------------------------------------------+
    |  +---------+                                                            |
    |  | Library |                                                            |
    |  +---------+                +--------+                                  |
    |   |                         | Models |                                  |
    |   |  +-------------------+  | Song   |                                  |
    |   |--| provider(netease) | -| Artist |----                              |
    |   |  +-------------------+  | Album  |   |             +--------------+ |
    |   |                         | ...    |   |             | Model Spec   | |
    |   |                         +--------+   | duck typing | (Base Model) | |
    |   |                                      |-------------|              | |
    |   |                      +--------+      |             | BaseSong     | |
    |   |  +-----------------+ | Models |      |             | BaseArtist   | |
    |   |--| provider(xiami) |-| Song   |-------             | ...          | |
    |   |  +-----------------+ | ...    |                    +--------------+ |
    |   |                      +--------+                                     |
    |   |                                                                     |
    |   |--...                                                                |
    |                                                                         |
    +-------------------------------------------------------------------------+


.. _library:

音乐库
~~~~~~~~~~~~~~

音乐库模块管理资源提供方(*Provider*)。

.. code::

    # 注册一个资源提供方
    library.register(provider)

    # 获取资源提供方实例
    provider = library.get(provider.identifier)

    # 列出所有资源提供方
    library.list()

    # 在音乐库中搜索关键词
    library.search('linkin park')


.. autoclass:: feeluown.library.Library
   :members:


资源提供方
~~~~~~~~~~~~~~~~~~~~
歌曲等音乐资源都来自于某一个提供方。比如，我们认为本地音乐的提供方是本地，
网易云音乐资源的提供方是网易，等等。对应到程序设计上，每个提供方都对应一个 provider 实例。
provider 是我们访问具体一个音乐平台资源音乐的入口。

在 feeluown 生态中，每个音乐资源提供方都对应着一个插件，我们现在有 feeluown-local/feeluown-netease
等许多插件，这些插件在启动时，会注册一个 provider 实例到 feeluown 的音乐库模块上。
注册完成之后，音乐库和 feeluown 其它模块就能访问到这个提供方的资源

举个栗子，feeluown-local 插件在启动时就创建了一个 *identifier* 为 ``local`` 的 provider 实例，
并将它注册到音乐库中，这样，当我们访问音乐库资源时，就能访问到本地音乐资源。

这个过程抽象为代码的话，它就类似：

.. code:: python

   result = library.serach()
   # we will see nothing in result because library has no provider

   from fuo_local import provider
   library.register(provider)

   result = library.search('keyword')
   # we may see that some local songs are in the search result

每个 provider 实例，它都需要提供访问具体资源的入口。举个栗子，

.. code:: python

   from fuo_local import provider

   # we can get a song instance by a song identifier
   song = provider.Song.get(song_id)

   # we can also get a artist instance by a artist identifier
   artist = provider.Artist.get(artist_id)


下面是音乐资源提供方的抽象基类，我们推荐大家基于此来实现一个 Provider 类。

.. autoclass:: feeluown.library.AbstractProvider
   :members:


当我们访问一个音乐提供方的资源时，不同的用户对不同资源的权限也是不一样的。
如果我们需要以特定的身份来访问音乐资源，我们可以使用 provider 的 ``auth`` 和 ``auth_as`` 方法：

.. code:: python

   from fuo_netease import provider
   user_a = obj  # UserModel
   provider.auth(user_a)

   # 使用 auth_as 来临时切换用户身份
   with provider.auth_as(user_b):
      provider.Song.get(song_id)
