媒体资源管理
=========================

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


.. autoclass:: fuocore.library.Library
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

.. autoclass:: fuocore.provider.AbstractProvider
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


资源模型
~~~~~~~~~~~~~~~~~

在 feeluown 中，我们为各种音乐资源定义了各自的模型标准，
每个资源提供方的创建的资源实例都应该遵守这个标准。

模型类型
'''''''''''''

我们预定义的音乐资源相关的模型有 6 种：歌曲，歌手，专辑，歌单，歌词，用户。

.. autoclass:: fuocore.models.ModelType
   :members:
   :undoc-members:


模型基类及其元信息
''''''''''''''''''''''''

这几种模型定义都继承于一个模型基类 ``BaseModel`` 。
而每个模型都会有自己的的元信息，比如：这个模型是什么类型？有哪些字段？
有哪些方法？这些元信息都会记录在模型的 inner class ``Meta`` 中。

.. autoclass:: fuocore.models.BaseModel

   .. py:class:: Meta

      模型元信息。模型的实例可以通过 ``meta`` 属性来访问模型元信息。
      此 Meta 类的设计借鉴于 `Django Model Meta Options`_ 。

      .. py:attribute:: model_type

         模型类型，默认为 ModelType.dummy

      .. py:attribute:: fields

         模型的字段，所有模型都必须有一个 identifier 字段

除了类型和字段这两个基本的元信息之外，模型还会有一些其它的元信息也会被记录在 Meta
类中，不同类型的模型，元信息可能也会不同，后面我们会陆续介绍。

一个模型示例
''''''''''''''''''''''''''

我们以 **歌曲模型** 为例，来看看一个真正的模型通常都由哪些部分组成::

     # 继承 BaseModel
     class SongModel(BaseModel):

         # 定义歌曲模型的元信息
         class Meta:
             # 类型为 ModelType.song
             model_type = ModelType.song

             # 定义模型字段
             fields = ['album', 'artists', 'lyric', 'comments', 'title', 'url',
                       'duration', 'mv']

             # 定义模型展示字段
             fields_display = ['title', 'artists_name', 'album_name', 'duration_ms']

         # 除了上述定义的模型字段外，歌曲模型实例也总是会有下面三个 property
         @property
         def artists_name(self):
             return _get_artists_name(self.artists or [])

         @property
         def album_name(self):
             return self.album.name if self.album is not None else ''

         @property
         def duration_ms(self):
             if self.duration is not None:
                 seconds = self.duration / 1000
                 m, s = seconds / 60, seconds % 60
             return '{:02}:{:02}'.format(int(m), int(s))


这个模型有几个方面的意义：

1. 它定义了该模型的类型(*model_type*) 为 ``ModelType.song``

2. 它定义了一首歌曲应该有哪些字段(*fields*)。在这个例子中，也就是：
   ``album``, ``artists``, ``lyric``, ``comments``, ``title``, ``url`` ,
   ``duration``, ``mv`` 8 个字段。

   另外，它还有 ``artists_name``, ``album_name``, ``duration_ms`` 这 3 个属性。

   其它模块在使用 model 实例时，总是可以访问这 8 个字段以及 3 个属性。
   举个例子，在程序的其它模块中，当我们遇到 song 对象时，我们可以确定，
   这个对象一定 **会有 title 属性** 。这也要求资源提供方在实现它们的资源模型时，
   要严格按照规范来进行。

3. 它定义了一首歌曲的展示字段(*fields_display*)。我们在后面会详细介绍它。


.. _visit-model-fields:

访问模型字段
''''''''''''''''''

模型定义了一个模型实例应该具有哪些字段，但访问实例字段的时候，
我们需要注意两个问题：

1. **字段的值不一定是可用的** 。比如一首歌可能没有歌词，
也没有评论，这时，我们访问这首歌 ``song.lyric`` 时，得到的就是一个空字符串，
访问 ``song.comments`` 属性时，得到的是一个空列表，但不会是 None 。

2. **第一次获取字段的值的时候可能会产生网络请求** 。以歌曲为例，
我们只要 identifier 就可以实例化一个歌曲模型，这时它的 url/lyric 等字段值都没有，
当我们第一次获取歌曲 ``url`` , ``lyric`` , ``comments`` 等属性时，
model 可能会触发一个网络请求，从资源提供方的服务端来获取资源的信息。
**也意味着简单的属性访问可能会触发网络或者文件 IO** 。

.. note::

   访问模型字段和访问一个 python 对象属性不同，它里面有非常多的黑魔法。
   这些黑魔法对我们来说有利有弊，这样设计的缘由可以参考 :ref:`research-model` 。

   黑魔法：我们重写了 BaseModel 的 ``__getattribute__`` 方法，
   当我们访问实例的一个字段时，如果这个字段值为 None (没有初始化的字段的值都是 None)，
   实例会调用自己模型的 ``get`` 类方法来初始化自己，我们认为 get 方法可以初始化所有字段
   （前面我们也提到 get方法应该尽可能初始化所有字段，get 方法往往是一次 IO 操作，比如网络请求），
   调用 get 方法后，从而进入下一 *生命阶段* gotten。
   这样，调用方在访问这个字段时，就总是能得到一个初始化后的值，

   模型实例生命阶段更多细节可以参考 :ref:`model-stage` 。

.. autoclass:: fuocore.models.BaseModel

   .. automethod:: __getattribute__


模型的展示字段
'''''''''''''''''''

对于一首歌曲而言，我们认为 ``歌曲标题+歌手名+专辑名+时长`` 可以较好的代表一首歌曲，
因为用户（人类）看到这四个字段，往往就能大概率的确定这是哪首歌。如果只有歌曲标题，
我们则不那么确定，因为一首歌可能被许多歌手唱过；只有标题和歌手名，我们同样不能确定。

不像计算机，或者说软件，它会使用 identifier 字段来标识区分一个资源，而用户（人类）
往往会通过一些 **可读的** 特征字段来标识一个资源，软件在展示一个资源的时候，
往往主要也会展示这些 **特征** 字段 ，我们将这些字段称之为 *展示字段* 。

对于一个模型来说，展示字段会有一个展示值，我们可以在字段后加上 ``_display``
来访问展示值。比如访问歌曲标题的展示值： ``song.title_display`` ，
歌曲的歌手名称的展示值： ``song.artists_name_display`` 。

展示字段的展示值有一些特点：

1. 展示值的类型总是字符串
2. 访问展示值总是安全的，不会触发网络请求。当值为空时，返回空字符串。
3. 展示值和对应字段真正的值可能不一样（从第 2 点可以推断出来）

分页读
'''''''''''''''''
服务端提供大数据集时往往会采用分页技术。对于服务端（API），接口一般有两种设计：

1. offset + limit
2. page + pageSize

这两种设计没有根本区别，只是编程的时候会不同，一般来说，大家认为 offset + limit 更直观。
而对于前端或者说客户端，UX(User Experience) 一般有两种设计：

1. 流式分页（常见于信息流，比如知乎的个人关注页）
2. 电梯式分页（常见于搜索结果，比如百度搜索的结果页）

这两种设计各有优劣，在 UI 上，feeluown 目前也是使用流式分页。比如一个歌单有上千首，
则用户需要一直往下拉。在接口层面，fuocore 模块提供了 SequentialReader 来帮助实现流式分页。

.. autoclass:: fuocore.reader.SequentialReader

流式分页存在一个问题，必须按照顺序来获取数据。而有些场景，我们希望根据 index 来获取数据。
举个例子，假设一个播放列表有 3000 首歌曲，在随机播放模式下，系统需要随机选择了 index
为 2500 的歌曲，这时候，我们不能去把 index<2500 的歌曲全部拉取下来。
feeluown 提供了 RandomReader 类来实现这个功能

.. autoclass:: fuocore.reader.RandomReader
   :members:
   :special-members: __init__

.. autoclass:: fuocore.reader.RandomSequentialReader


模型实例化
'''''''''''''''''

模型实例化有三种常见方法，它们分别适用于不同场景。

第一种：当我们知道资源的准确信息时，可以通过构造函数来创建一个实例::

    song = SongModel(identifier=123,
                     title='Love Story',
                     url='http://xxx.mp3',
                     duration=1000.12)

资源提供方通常会使用这种方法来创建一个实例，因为资源提供方拥有准确且全面的信息。

第二种：我们也可以通过展示字段和 ``identifier`` 来创建一个资源实例

.. autoclass:: fuocore.models.BaseModel()

   .. automethod:: create_by_display

以上面的歌曲模型为例，我们可以这样来创建一个歌曲模型实例::

    identifier = 1
    title = 'in the end'
    artists_name = 'lp'  # linkin park
    album_name = 'unknown'
    # 如果不知道 duration，创建时可以忽略
    song = SongModel.create_by_display(identifier,
                                       title=title,
                                       artists_name=artists_name,
                                       album_name=album)

    assert song.title_display == 'in the end'

这时，我们并不需要知道歌曲特别准确的信息，只需要保证 identifier 准确皆可，
类似歌曲标题，我们可以不用在乎大小写；也不需要在意歌手名的全名。接着，
我们可以直接访问歌曲真实的标题::

    print(song.title)   # 可能会触发网络请求

**在获取到真实的标题之后，我们再次访问标题的展示值时，展示值会变成和真实值一样。**

第三种：通过 ``Model.get`` 方法来创建（获取）一个资源实例。
资源提供方在实现自己的资源模型时，可以在模型的元信息种声明自己是否支持 get 方法，
如果支持，则实现 get 方法，get 方法返回的资源实例的字段应该 **尽可能**
全部初始化，访问它的任何字段都应该 **尽可能** 不触发网络请求。

.. autoclass:: fuocore.models.BaseModel

   .. py:class:: Meta

      .. py:attribute:: allow_get

         是否可以通过 get 来获取一个实例

   .. automethod:: get

资源方应该尽可能实现 get 方法。

.. _model-stage:

实例生命周期
''''''''''''''''''''''

根据模型字段初始化的状态，我们定义了实例的生命周期，
上述三种实例化方法创建的实例处于生命周期的不同阶段(*stage*)。

一个实例的生命周期由三个阶段组成： display, inited, gotten。
通过构造函数创建的实例所处的阶段是 inited,
通过 create_by_display 方法创建的实例所处阶段是 dispaly，
通过 get 方法获取的实例处于 gotten 阶段。

::

    +---------+
    | dispaly | ----
    +---------+     \      +--------+
                     ----> | gotten |
    +--------+      /      +--------+
    | inited | -----
    +--------+

当实例处于 display 阶段时，它所有的字段可能都没有初始化，
当实例处于 inited 阶段时，它的某些字段可能还没有被初始化，
一般情况下，没初始化的字段的值是 None。

当我们访问模型实例字段的时候，实例可能会进行状态切换，详情可以参考 :ref:`visit-model-fields` 。


预定义的模型
''''''''''''''''''''
.. autoclass:: fuocore.models.BaseModel

   .. py:class:: Meta

      .. py:attribute:: model_type
         :annotation: = ModelType.dummy
      .. py:attribute:: allow_get
         :annotation: = True

         Model should implement get method as far as possible

      .. py:attribute:: allow_batch
         :annotation: = False
      .. py:attribute:: fields
         :annotation: =

         ==========   =====================   ======================
         name         type                    desc
         ==========   =====================   ======================
         identifier   :class:`str`            model instance identifier
         ==========   =====================   ======================

.. autoclass:: fuocore.models.SongModel
   :members: artists_name, album_name, duration_ms, filename
   :undoc-members:

   .. py:class:: Meta

      .. py:attribute:: model_type
         :annotation: = ModelType.song

      .. py:attribute:: fields
         :annotation: =

         ========  =====================   ======================
         name      type                    desc
         ========  =====================   ======================
         album     :class:`.AlbumModel`
         artists   :class:`.ArtistModel`
         comments  NOT DEFINED
         duration  :class:`float`          song duration (unit: mileseconds)
         lyric     :class:`.LyricModel`
         mv        :class:`.MvModel`
         title     :class:`str`            title
         url       :class:`str`            song url (http url or local filepath)
         ========  =====================   ======================

      .. py:attribute:: fields_display
         :annotation: = [title, artists_name, album_name, duration_ms]

.. autoclass:: fuocore.models.ArtistModel

   .. py:class:: Meta

      .. py:attribute:: model_type
         :annotation: = ModelType.artist

      .. py:attribute:: fields
         :annotation: =

         ========  =====================   ======================
         name      type                    desc
         ========  =====================   ======================
         albums    :class:`list`           list of :class:`.AlbumModel`
         cover     :class:`str`
         desc      :class:`str`
         name      :class:`str`
         songs     :class:`list`           list of :class:`.SongModel`
         ========  =====================   ======================

      .. py:attribute:: allow_create_songs_g
         :annotation: = False

         是否允许创建歌曲生成器，如果为 True，我们可以调用 ``create_song_g``
         方法来创建一个歌曲生成器。

         一个歌手可能会有上千首歌曲，这种情况下，一次性返回所有歌曲显然不是很合适。
         这时，资源提供方应该考虑实现这个接口，调用方也应该考虑使用。

      .. py:attribute:: fields_display
         :annotation: = [name]

         NOT IMPLEMENTED

   .. automethod:: create_songs_g


.. autoclass:: fuocore.models.AlbumType
   :members:
   :undoc-members:

.. autoclass:: fuocore.models.AlbumModel
   :members: artists_name
   :undoc-members:

   .. py:class:: Meta

      .. py:attribute:: model_type
         :annotation: = ModelType.album

      .. py:attribute:: fields
         :annotation: =

         ========  =====================   ======================
         name      type                    desc
         ========  =====================   ======================
         artists   :class:`list`           list of :class:`.ArtistModel`
         cover     :class:`str`
         desc      :class:`str`
         name      :class:`str`
         songs     :class:`list`           list of :class:`.SongModel`
         type      :class:`AlbumType`
         ========  =====================   ======================

.. autoclass:: fuocore.models.LyricModel

   .. py:class:: Meta

      .. py:attribute:: model_type
         :annotation: = ModelType.lyric

      .. py:attribute:: fields
         :annotation: =

         =============   =====================   ======================
         name            type                    desc
         =============   =====================   ======================
         content         :class:`str`            lyric text
         trans_content   :class:`str`            translated lyric text
         song            :class:`SongModel`      the related song
         =============   =====================   ======================


.. autoclass:: fuocore.models.MvModel

   .. py:class:: Meta

      .. py:attribute:: fields
         :annotation: =

         =============   =====================   ======================
         name            type                    desc
         =============   =====================   ======================
         artist          :class:`.ArtistModel`
         cover           :class:`str`
         desc            :class:`str`
         media           :class:`.Media`
         name            :class:`str`
         =============   =====================   ======================


.. autoclass:: fuocore.models.PlaylistModel

   .. py:class:: Meta

      .. py:attribute:: model_type
         :annotation: = ModelType.playlist

      .. py:attribute:: fields
         :annotation: =

         =============   =====================   ======================
         name            type                    desc
         =============   =====================   ======================
         cover           :class:`str`            playlist cover url
         desc            :class:`str`
         name            :class:`str`
         songs           :class:`list`
         =============   =====================   ======================

      .. py:attribute:: allow_create_songs_g
         :annotation: = False

   .. automethod:: add
   .. automethod:: remove


.. autoclass:: fuocore.models.SearchModel

   .. py:class:: Meta

      .. py:attribute:: fields
         :annotation: =

         =============   =====================   ======================
         name            type                    desc
         =============   =====================   ======================
         q               :class:`str`            search query string
         songs           :class:`list`
         =============   =====================   ======================


.. autoclass:: fuocore.models.UserModel

   .. py:class:: Meta

      .. py:attribute:: model_type
         :annotation: = ModelType.user

      .. py:attribute:: fields
         :annotation: =

         =============   =====================   ======================
         name            type                    desc
         =============   =====================   ======================
         name            :class:`str`
         fav_albums      :class:`list`           list of :class:`.AlbumModel`
         fav_artists     :class:`list`
         fav_playlists   :class:`list`           playlists collected by user
         fav_songs       :class:`list`
         playlists       :class:`list`           playlists created by user
         =============   =====================   ======================

      .. py:attribute:: allow_fav_songs_add
         :annotation: = False

      .. py:attribute:: allow_fav_songs_remove
         :annotation: = False

      .. py:attribute:: allow_fav_playlists_add
         :annotation: = False

      .. py:attribute:: allow_fav_playlists_remove
         :annotation: = False

      .. py:attribute:: allow_fav_albums_add
         :annotation: = False

      .. py:attribute:: allow_fav_albums_remove
         :annotation: = False

      .. py:attribute:: allow_fav_artists_add
         :annotation: = False

      .. py:attribute:: allow_fav_artists_remove
         :annotation: = False

   .. automethod:: add_to_fav_songs
   .. automethod:: remove_from_fav_songs
   .. automethod:: add_to_fav_playlists
   .. automethod:: remove_from_fav_playlists
   .. automethod:: add_to_fav_albums
   .. automethod:: remove_from_fav_albums
   .. automethod:: add_to_fav_artists
   .. automethod:: remove_from_fav_artists


.. _media:

资源文件
~~~~~~~~~~~~~~~

在 feeluown 中， :term:`media` 代表媒体实体资源，我们称 media 为资源文件。
上面我们有讲到歌曲和 MV 等资源模型，一个资源模型可以对应多个资源文件，
比如一首歌曲可以有多个音频文件、或者多个链接，这些音频文件的质量可能不一样（高中低），
文件格式可能也不一样（mp3,flac,wav）等。

在 feeluown 中，我们定义了三种媒体资源类型：音频，视频，图片。

.. autoclass:: fuocore.media.MediaType
   :members:
   :undoc-members:

每个资源都有特定的质量，对于音频，我们一般根据比特率来判断；对于视频，
我们根据分辨率来判断；对于图片，我们目前还没有设定标准。

在 feeluown 中，我们 *约定* **比特率** 为 320kbps 的音频文件质量为 ``hq`` (high quality),
大于 320kbps 的为 ``shq`` (super high quality)，一般是无损音乐，200kbps
左右的音频为 ``sq`` (standard quality)， 比特率小于 200kbps 的音频质量为 ``lq`` (low quality)。

.. autoclass:: fuocore.media.Quality.Audio
   :members:
   :undoc-members:

对于视频，根据视频分辨率来定义文件质量。规则如下：

============     ======================
分辨率              品质
============     ======================
4k                ``fhd`` (full high definition)
720p ~ 1080p      ``hd`` (high definition)
480p              ``sd`` (standard definition)
<480p             ``ld`` (low definition)
============     ======================

.. autoclass:: fuocore.media.Quality.Video
   :members:
   :undoc-members:

当资源提供方提供的资源有多种质量时，比如一首歌有多个播放链接，我们可以让
SongModel 继承 ``MultiQualityMixin`` 类，并实现 ``list_quality``
和 ``get_media`` 两个方法：

.. autoclass:: fuocore.media.MultiQualityMixin
   :members:

``select_media`` 方法的参数为 policy，policy 是一个符合一定规则的字符串，
由 ``SortPolicy`` 类负责解析。

::

   >>> policy = '>>>'
   >>> media = song.select_media(policy)
   >>> if media is None:
   >>>     player.stop()
   >>> else:
   >>>     player.play(media)

SortPolicy 类定义了 6 中规则，见如下的 rules 变量文档。

.. autoclass:: fuocore.media.Quality.SortPolicy

   .. py:attribute:: rules

      policy 字符串规则。这里 ``rlrl`` 的意思是 right left right left，
      它对应的规则是 ``r'(\w+)><'`` 规则中 ``\w`` 匹配的是质量字符串， ``>``
      代表向右 ``right`` ， ``<`` 代表向左 ``left`` 。

      举个例子，对于策略 ``hq><`` ，我们可以这样理解：我们有一个从高到低的排好序的列表
      ``[shq, hq, sq, lq]`` ， 以 hq 为中心，先向右看，为 sq，再向左看一位，
      为 shq, 重复向右和向左看的逻辑，就可以得到这样一个优先级： ``hq -> sq -> shq -> lq``

      ::

          rules = (
              ('rlrl', r'(\w+)><'),
              ('lrlr', r'(\w+)<>'),
              ('llr', r'(\w+)<<>'),
              ('rrl', r'(\w+)>><'),
              ('rrr', r'(\w+)?>>>'),
              ('lll', r'(\w+)?<<<'),
          )

media 对象中包含了资源文件的元信息，对于音频文件，有 bitrate, format
（以后会根据需要添加新属性，比如 size），这个元信息保存在 ``media.metadata`` 中，
metadata 是 ``AudioMeta`` 的实例。对于视频文件，metadata 则是 ``VideoMeta``
（暂时未实现） 的实例。

.. autoclass:: fuocore.media.AudioMeta


.. _media_assets_management_usage:

使用示例
~~~~~~~~~~~~~~~~~~



.. _Django Model Meta Options: https://docs.djangoproject.com/en/dev/ref/models/options/
