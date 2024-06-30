配置文件
================

类似 Vim 的 ``.vimrc`` 、Emacs 的 ``init.el`` ，feeluown 也有自己的配置文件 ``.fuorc`` 。

fuorc 文件是一个 Python 脚本，它位于 ``~/.fuorc`` ，我们可以在其中使用任意 Python 语法。
feeluown 启动时，第一步就是加载并解析该配置文件，结合 Python 的灵活性，意味着你可以对
feeluown 的行为进行完完全全的控制。通常，你可以在配置文件中作以下事情：

1. 配置选项
2. 功能定制


一个🌰
-----------------

一个 fuorc 文件示例::

  import os

  # 自定义配置
  config.THEME = 'dark'
  config.COLLECTIONS_DIR = '~/Dropbox/public/music'
  config.AUDIO_SELECT_POLICY = '>>>'


  # 一个小功能：切换歌曲时，发送系统通知
  def notify_song_changed(song):
      if song is not None:
          title = song.title_display
          artists_name = song.artists_name_display
          song_str = f'{title}-{artists_name}'
          os.system(f'notify-send "{song_str}"')

  when('app.playlist.song_changed', notify_song_changed)

  # 让编辑器识别这是一个 Python 文件
  #
  # Local Variables:
  # mode: python
  # End:
  #
  # vim: ft=python

配置选项
-------------

通用配置项如下

=======================    =========  ============    =========
名称                         类型        默认值           描述
=======================    =========  ============    =========
RPC_PORT                    ``int``    ``23333``      RPC 服务端口
PUBSUB_PORT                 ``int``    ``23334``      PUBSUB 服务端口
ALLOW_LAN_CONNECT           ``bool``   ``False``      是否可以从局域网连接 RPC 服务
THEME                       ``str``    ``auto``       auto/light/dark
COLLECTIONS_DIR             ``str``    ``''``         本地收藏所在目录
LOG_TO_FILE                 ``bool``   ``True``       将日志输出到文件中
AUDIO_SELECT_POLICY         ``str``    ``hq<>``       :class:`feeluown.media.Quality.SortPolicy`
VIDEO_SELECT_POLICY         ``str``    ``hd<>``       :class:`feeluown.media.Quality.SortPolicy`
NOTIFY_ON_TRACK_CHANGED     ``bool``   ``False``      切换歌曲时显示桌面通知
NOTIFY_DURATION             ``int``    ``3000``       桌面通知保留时长(ms)
PROVIDERS_STANDBY           ``list``   ``None``       候选歌曲提供方（默认：所有提供方）
=======================    =========  ============    =========

实验特性的配置项

=============================    =========  ============    =========
名称                              类型        默认值           描述
=============================    =========  ============    =========
ENABLE_WEB_SERVER                ``bool``    ``False``      开启 WEB 服务
WEB_PORT                         ``int``     ``23332``      WEB 服务端口
ENABLE_NEW_HOMEPAGE              ``bool``    ``False``      开启新版主页
ENABLE_MV_AS_STANDBY             ``bool``    ``True``       使用 MV 作为歌曲资源
PLAYBACK_CROSSFADE               ``bool``    ``False``      开启淡入淡出
PLAYBACK_CROSSFADE_DURATION      ``int``     ``500``        淡入淡出持续时间
ENABLE_YTDL_AS_MEDIA_PROVIDER    ``int``     ``False``      使用 YTDL 作为媒体资源提供方
YTDL_RULES                       ``list``    ``None``       YTDL 的命中规则
=============================    =========  ============    =========

MPV 播放器配置项 (使用 MPV 做为播放引擎时生效)

====================       =========  ============    =========
名称                         类型        默认值           描述
====================       =========  ============    =========
MPV_AUDIO_DEVICE            ``str``    ``auto``       MPV 播放设备
====================       =========  ============    =========

你可以查看下述函数的源代码来查看完整列表。

.. autofunction:: feeluown.app.config.create_config


功能定制
--------------

feeluown 使用 Python 的 exec 方法来加载（执行）配置文件。执行时，
会暴露 ``config`` 对象和部分函数（如 ``add_hook``, ``rm_hook`` 等）到这个作用域中。
通过 ``add_hook`` （这个函数有个别名是 ``when`` ），你可以对程序大部分事件进行监听。

常见的事件有

1. ``app.player.metadata_changed`` 歌曲元信息变化时（通常发生于歌曲切换时）
2. ``app.initialized`` 应用初始化完毕（未启动）
3. ``app.started`` 应用已经启动
4. ``app.ui.songs_table.about_to_show_menu`` 右键显示歌曲菜单

你可以参考示例 `cosven-fuorc <https://github.com/cosven/rcfiles/blob/master/fuorc>`_

函数
~~~~~~~~

函数的文档可以参考

.. autofunction:: feeluown.fuoexec.add_hook
.. autofunction:: feeluown.fuoexec.rm_hook
.. autofunction:: feeluown.fuoexec.source
