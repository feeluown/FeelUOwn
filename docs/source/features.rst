特性
=========

安装相对简单，新手友好
----------------------------

  参考 :doc:`quickstart` 文档进行安装。

提供各音乐平台插件
---------------------------

  - `Youtube Music <https://github.com/feeluown/feeluown-ytmusic>`_
  - `网易云音乐 <https://github.com/feeluown/feeluown-netease>`_
  - `QQ 音乐 <https://github.com/feeluown/feeluown-qqmusic>`_
  - `Bilibili <https://github.com/feeluown/feeluown-bilibili>`_

自动寻找播放资源
----------------------------

  在搜索框输入 ``==> 我怀念的 - 孙燕姿`` ，播放器会自动匹配歌曲并进行播放。
  当你播放 A 平台的 VIP/收费歌曲时，播放器会尝试从其它平台为你寻找免费资源（你需要安装各音乐平台插件）。

自然语言转歌单（AI）
----------------------------

    .. image:: https://github.com/user-attachments/assets/8afa13e6-8ff9-4b4f-9ca7-ad1f5661d8cb

基于文本的歌单
----------------------------

  将下面内容拷贝到文件 ``~/.FeelUOwn/collections/library.fuo`` 中，重启 FeelUOwn 就可以看到此歌单::

     fuo://netease/songs/16841667  # No Matter What - Boyzone
     fuo://netease/songs/65800     # 最佳损友 - 陈奕迅
     fuo://xiami/songs/3406085     # Love Story - Taylor Swift
     fuo://netease/songs/5054926   # When You Say Noth… - Ronan Keating
     fuo://qqmusic/songs/97773     # 晴天 - 周杰伦
     fuo://qqmusic/songs/102422162 # 给我一首歌的时间 … - 周杰伦,蔡依林
     fuo://xiami/songs/1769834090  # Flower Dance - DJ OKAWARI

  你可以通过 gist 来分享自己的歌单，也可以通过 Dropbox 或 git 来在不同设备上同步这些歌单。

支持读取 fuorc 文件
----------------------------

  你配置过 ``.emacs`` 或者 ``.vimrc`` 吗？ ``.fuorc`` 和它们一样强大！
  参考 :doc:`fuorc` 文档来编写自己的 rc 文件吧～

提供基于 TCP 的控制协议
----------------------------

  比如::

     查看播放器状态 echo status | nc localhost 23333
     暂停播放      echo status | nc localhost 23333
     搜索歌曲      echo "search 周杰伦" | nc localhost 23333

  因此，它 **可以方便的与 Tmux, Emacs, Slack 等常用程序和软件集成**

    - `Emacs 简单客户端 <https://github.com/feeluown/emacs-fuo>`_ ，
      `DEMO 演示视频 <https://www.youtube.com/watch?v=-JFXo0J5D9E>`_
    - Tmux 集成截图

      .. image:: https://user-images.githubusercontent.com/4962134/43565894-1586891e-965f-11e8-9cde-50973acfb573.png

    - Slack 集成截图 `(在 fuorc 添加配置) <https://github.com/cosven/rcfiles/blob/498dcef385a20d5e0e5fbf06473f75769112d30c/.fuorc#L19>`_

      .. image:: https://user-images.githubusercontent.com/4962134/43578665-0d148af6-9682-11e8-9d95-4cd1d3c1e0b9.png

支持无 GUI 模式启动
---------------------------
