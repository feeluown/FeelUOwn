配置文件
================

类似 Vim 的 ``.vimrc`` 、Emacs 的 ``init.el`` ，feeluown 也有自己的配置文件 ``.fuorc`` 。

fuorc 文件是一个 Python 脚本，它位于 ``~/.fuorc`` 目录下，我们可以在其中使用任意 Python 语法。
feeluown 启动时，第一步就是加载并解析该配置文件。通常，我们可以在配置文件中作以下事情：

1. 配置部分选项
2. 定制一些小功能

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

  when('app.player.playlist.song_changed', notify_song_changed)

  # 让编辑器识别这是一个 Python 文件
  #
  # Local Variables:
  # mode: python
  # End:
  #
  # vim: ft=python


原理简述
--------------

feeluown 使用 Python 的 exec 方法来加载（执行）配置文件。执行时，
会暴露 config 对象和部分函数到这个作用域中。

函数
~~~~~~~~

目前暴露到该作用域的函数有

.. autofunction:: feeluown.fuoexec.add_hook

.. autofunction:: feeluown.fuoexec.rm_hook

.. autofunction:: feeluown.fuoexec.source

config 对象
~~~~~~~~~~~~~

``config`` 是 :class:`feeluown.config.Config` 的实例，常见使用场景有两种::

  >>> theme = config.THEME  # 获取配置项的值
  >>> config.THEME = 'dark'  # 设置配置项的值

目前支持的配置项如下

**通用配置项**

====================       =========  ============    =========
名称                         类型        默认值           描述
====================       =========  ============    =========
DEBUG                       ``bool``   ``False``      是否为调试模式
MODE                        ``str``    ``0x0000``     CLI or GUI 模式
THEME                       ``str``    ``auto``       auto/light/dark
COLLECTIONS_DIR             ``str``    ``''``         本地收藏所在目录
LOG_TO_FILE                 ``bool``   ``True``       将日志输出到文件中
AUDIO_SELECT_POLICY         ``str``    ``hq<>``       :class:`fuocore.media.Quality.SortPolicy`
VIDEO_SELECT_POLICY         ``str``    ``hd<>``       :class:`fuocore.media.Quality.SortPolicy`
====================       =========  ============    =========

**MPV 播放器配置项** (使用 MPV 做为播放引擎时生效)

====================       =========  ============    =========
名称                         类型        默认值           描述
====================       =========  ============    =========
MPV_AUDIO_DEVICE            ``str``    ``auto``       MPV 播放设备
====================       =========  ============    =========


.. autoclass:: feeluown.config.Config
