接口参考手册
==============

这个参考手册描述了 feeluown 的几大组成部分，各组成部分的主要模块，
以及模块的相对稳定接口。

.. _media_player:

播放模块
-----------------

播放模块由两部分组成：播放列表(*Playlist*)和播放器(*Player*)。

播放列表维护了一个媒体资源集合，并提供若干资源获取接口，播放器通过接口获取资源，
然后进行播放。这些接口包括： ``current_song``, ``next_song``, ``previous_song`` 。

播放列表吐资源给播放器的时候，是有一定的顺序的，我们称之为回放模式(*PlaybackMode*)。
回放模式有四种：单曲循环；顺序；循环；随机。上述三个资源访问接口吐资源的顺序都会受回放模式影响。

当播放列表 ``current_song`` 变化时，它会发出 ``song_changed`` 信号，播放器会监听该信号，
从而播放、停止（song 为空时）或者切换歌曲。播放歌曲时，播放器的状态(*State*)会发生变化，
当没有歌曲播放的时候，播放器为停止(stopped)状态，有歌曲播放的时候，为正在播放状态。
当一首歌开始播放后，播放器会发出 ``media_changed`` 信号，
当一首歌曲播放完毕时，播放器会发出 ``song_finished`` 信号。

播放列表和播放器之间的调用关系如下::

    Playlist                                         (Mpv)Player

        current_song.setter ---[song_changed]---> play_song
           ^                                      |
           |                                      | <song==None>
           |<- play_song                          |--------------> stop
           |<- play_next/play_previous            |
           |<- play_next <-|                  prepare_media
           |<- replay    <-| <mode==one_loop>     |
                           |                      v
                           |                    play ---[media_changed]--->
                     [song_finished]
                           |
                           |
                           ---- event(END_FILE)
                                       ^
                                       |
                                    MpvPlayer

.. automodule:: feeluown.player
   :members:

通用管理模块
----------------

.. automodule:: feeluown.task
   :members:

.. automodule:: feeluown.version


GUI 相关管理模块
-----------------

.. note::

   目前，大部分 GUI 组件的接口都不稳定，我们在实现插件时，如果需要从操作 GUI 组件，
   请调用以下模块的接口。如果我们想实现的功能通过以下接口在暂时实现不了，
   请和 @cosven 联系。

.. automodule:: feeluown.gui.browser
   :members:

.. automodule:: feeluown.gui.hotkey
   :members:

.. automodule:: feeluown.gui.image
   :members:

.. automodule:: feeluown.gui.uimodels.provider
   :members:

.. automodule:: feeluown.gui.uimodels.my_music
   :members:

.. automodule:: feeluown.gui.uimodels.playlist
   :members:

GUI 组件
-------------------

.. autoclass:: feeluown.gui.widgets.login.LoginDialog
   :members:

.. autoclass:: feeluown.gui.widgets.login.CookiesLoginDialog
   :members:

异常
-------------------

.. automodule:: feeluown.excs
   :members:
