fuocore
=======

fuocore 提供了音乐播放器依赖的一些常见模块，
它主要是为 `feeluown <https://github.com/cosven/feeluown>`_ 播放器而设计的，
所以名字为 fuocore，意为 feeluown core。
它主要包含以下几个部分：

- 音乐资源管理模块：抽象、统一并管理各音乐平台资源
- 播放器模块：播放媒体资源
- 歌词模块：歌词解析、计算实时歌词等
- 一些工具：PubsubServer、TcpServer 等

.. note::

   理论上其它音乐播放器也可以使用 fuocore 作为其基础模块。

此外，fuocore 也包含了网易云音乐、虾米音乐、本地音乐的扩展，实现了对这些平台的音乐资源的访问，
并根据音乐资源管理模块对其进行了抽象和管理。
以这几个扩展为参考样例，我们可以轻松的编写 last.fm、豆瓣 FM、
soundcloud 等音乐平台的扩展，欢迎有兴趣的童鞋一起来 hack。

使用示例
--------
::

  >>> # use MpvPlayer to play mp3
  >>> from fuocore.player import MpvPlayer
  >>> player = MpvPlayer()
  >>> player.initialize()
  >>> player.play('./data/fixtures/ybwm-ts.mp3')
  >>> player.stop()

  >>> # play netease song
  >>> from fuocore.netease import provider
  >>> result = provider.search('谢春花')
  >>> song = result.songs[0]
  >>> print(song.title)
  >>> player.play(song.url)

  >>> # show live lyric
  >>> from fuocore.live_lyric import LiveLyric
  >>> player.stop()
  >>> live_lyric = LiveLyric()
  >>> player.position_changed.connect(live_lyric.on_position_changed)
  >>> player.playlist.song_changed.connect(live_lyric.on_song_changed)
  >>> player.play_song(song)
  >>> def cb(s):
  ...     print(s)
  ...
  >>> live_lyric.sentence_changed.connect(cb)


.. note::

    fuocore 提供的 MpvPlayer 是依赖 mpv 播放器的，在 Debian 发行版中，我们需要安装 libmpv1，
    在 macOS 上，我们需要安装 mpv 播放器。

    .. code::

       sudo apt-get install libmpv1  # Debian or Ubuntu
       brew install mpv              # macOS

.. toctree::
   :maxdepth: 1
   :caption: 详细文档

   design
   api
   research
   glossary
