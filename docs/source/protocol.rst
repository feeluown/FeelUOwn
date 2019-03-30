fuo 协议
===============

**fuo 协议** 是 feeluown 播放器的控制协议，它主要是用来提升 feeluown 的可扩展性。

feeluown 以默认参数启动时，会相应的启动一个 TCP 服务，监听 23333 端口，
我们可以使用 fuo 协议，通过该 TCP 服务来与播放器通信。比如：

.. code::sh

    ~ > nc localhost 23333
    OK feeluown 1.0.0
    status
    ACK status
    repeat:    1
    random:    0
    volume:    100
    state:     stopped
    OK

目前（3.0 版本），协议主要包含两个方面的内容：

1. 资源标识：比如 fuo://netease/songs/289530 标识了一首歌
2. 命令控制：播放、暂停、下一首、执行代码等控制命令

资源标识
-----------

feeluown 使用 :ref:`design-library` 来管理音乐提供方的资源，接入音乐库的资源都有一个特征，
这些资源都有一个唯一的资源标识符，我们称之为 **fuo uri** 。

对于大部分 fuo uri 来说，它们由几个部分组成：scheme, provider, type, identifier。
scheme 统一为 fuo。

.. code::

    fuo//{res_provider}/{res_type}/{res_identifier}
             |              |              |
         资源提供方 id     资源类型         资源id

举个例子：

- ``fuo://local/songs/12`` 代表的资源就是 **本地** (资源提供方) 提供的 id 为 **12** 的 **歌曲** (资源类别)。
- ``fuo://netease/artists/46490`` 代表的资源时 **网易云音乐** 提供的 id 为 **46490** 的 **歌手**

资源提供方都是以插件的形式存在，目前已知的资源插件有 本地音乐(local)、qq 音乐(qqmusic)、
虾米音乐(xiami)、网易云音乐(netease)，我们可以在 `这里 <https://github.com/feeluown/>`_ 找到它们。
实现一个资源提供方也很简单，有兴趣的话，可以参考上面的例子。

目前支持的资源类型有：

- 用户： ``fuo://{provider}/users/{identifier}``
- 歌曲： ``fuo://{provider}/songs/{identifier}``
- 歌手： ``fuo://{provider}/artists/{identifier}``
- 专辑： ``fuo://{provider}/album/{identifier}``
- 歌词： ``fuo://{provider}/songs/{identifier}/lyric``

注：除了这类标识资源的 uri，我们以后可能会有其它格式的 uri。

命令控制
------------

fuo 协议定义了一些语义化的命令，客户端和 fuo (服务端) 可以通过一问一答的方式来进行通信。

请求（Request）
''''''''''''''''

.. code::

   {cmd} [param] [options]

注：目前客户端需要等待服务端返回才能发起第二个请求，否则会把收到的请求合并成一个，
造成无法识别的问题（后续会改进这个问题）。

回答（Response）
''''''''''''''''''''

.. code::

   # 成功
   ACK {cmd} [param] [options]
   ...
   OK

   # 失败
   ACK {cmd} [param] [options]
   ...
   Oops

注：目前没有设计分包的处理，之后会考虑这个问题。

下面是目前支持的所有命令：

========    ==================   =======================
命令         意义                 示例
========    ==================   =======================
status      播放器当前状态           ``status``
play        播放一首歌曲            ``play fuo://xiami/songs/1769099772``
pause       暂停播放                ``pause``
resume      恢复播放                ``resume``
toggle      暂停/恢复               ``toggle``
stop        停止播放                ``stop``
next        下一首                  ``next``
previous    上一首                  ``previous``
search      搜索                    ``search "我家门前有大海 - 张震岳"``
show        展示资源详情             ``show fuo://xiami/songs/1769099772``
list        显示当前播放列表         ``list``
clear       清空当前播放列表         ``clear``
remove      从播放列表移除歌曲       ``remove fuo://xiami/songs/1769099772``
add         添加歌曲到播放列表       ``add fuo://xiami/songs/1769099772``
exec        执行 Python 代码        ``exec <<EOF\n print('hello world') \nEOF``
========    ==================   =======================
