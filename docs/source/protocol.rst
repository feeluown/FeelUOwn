fuo 协议
===============

**fuo 协议** 是 feeluown 播放器的控制协议，它主要是用来提升 feeluown 的可扩展性。

fuo 协议在设计时优先考虑以下几点：

1. 可读性好
2. 请求简单（使用 netcat 工具可以轻松发送请求）
3. 解析代码简单

feeluown 以默认参数启动时，会相应的启动一个 TCP 服务，监听 23333 端口，
我们可以使用 fuo 协议，通过该 TCP 服务来与播放器通信。比如：

.. code::sh

    ~ > nc localhost 23333
    OK feeluown 1.0.0

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

    fuo://{res_provider}/{res_type}/{res_identifier}
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

带有简单描述的资源标识符
'''''''''''''''''''''''''''
一个 uri 虽然可以标识一个资源，但是 uri 能够携带的信息往往不够，客户端拿到 uri 后，
肉眼识别不出来这是个什么东西，所以我们可以给 uri 附上一个简短描述，对于 **歌曲** 来说：

.. code:: text

    {song uri}{      }# {title}-{artists_name}-{album_name}-{duration_ms}
                |      |                   |
          空格或者\t  分割符#       描述（所有字段均为可选，但必须按照顺序）

用户，歌手，专辑格式定义分别如下：

.. code:: text

    {user uri}       # {name}
    {artist uri}     # {name}
    {album uri}      # {album_name}-{artist_name}

注：之后可以考虑支持带有复杂描述的资源标识符，可能类似（待研究和讨论）

.. code:: text

    fuo://{provider}/songs/{identifier} <<EOF
      title:     hello world
      artist:    fuo://{provider}/artists/{identifier}  # {name}
      album:     fuo://{provider}/artists/{identifier}  # {album_name}-{artists_name}
      duration:  123.01
      url:       http://xxx/yyy.mp3
    EOF


RPC 服务
------------

fuo 协议定义了一些语义化的命令，客户端和 fuo (服务端) 可以通过一问一答的方式来进行通信。
（注：fuo 协议不依赖 TCP 传输，不过目前 feeluown daemon 启动时只提供了基于 tcp 的 transport。）

在客户端连接上服务端时，服务端会建立一个会话，并发送类似 ``OK feeluown 1.0.0\n`` 的信息，
客户端接收到这个消息后，就可以正常的发送请求了。在一个会话中，服务端会依次响应接收到的请求。

注：下面写的很多设计目前都没有实现，算是一个 RFC 草稿。

消息（Message）
'''''''''''''''''''
和 HTTP 消息类似，fuo 消息是 feeluown 服务端和客户端之间交换数据的方式。
有两种类型的消息：

- 请求：由客户端发送用来触发服务端的一个动作
- 响应：服务端对请求的应答


请求（Request）
'''''''''''''''''''
请求可以是一行文本，也可以是多行。

当请求为一行文本时，它以 ``\r\n`` 或者 ``\n`` 结束，具体结构如下：

.. code::

   {cmd}    {param} [{options}]        #:   {req_options}  \r\n
     |        |         |             |         |
   命令      参数    命令选项          分隔     请求选项

这一行，我们称之为 ``request-line`` 。其中，
命令是必须项。参数和命令选项都是视具体命令而定，有的是可选，有的则必须提供。
命令选项由 ``[]`` 包裹，选项都是 key-value 形式，比如 ``[artist="linkin park",json=true]`` 。

举几个例子：

.. code::

   # 查看服务端状态，只需要提供命令即可
   status

   # 播放一首歌曲，必须提供一个参数
   play fuo://local/songs/1
   play "晴天 - 周杰伦"

   # 搜索关键字为晴天、歌手为周杰伦、来源为网易云的歌曲
   # 搜索命令必须提供一个参数，命令选项可选
   # （注：该功能目前还未实现，欢迎 PR）
   search 晴天 [artist=周杰伦,source=netease]


请求选项由 ``#:`` 与命令选项分隔。而请求选项格式和命令选项格式是相同的，
都是 key=value 形式。在我们设计中，请求选项可能包含以下（目前均未实现，欢迎 PR）：

- 输出格式： ``format=json``
- 分页输出： ``less=true`` 可以简写为 ``less``

举几个例子：

.. code::


   # 搜索纵观线关键字，结果可以分多次返回（设置了请求选项）
   # 这里 less 请求选项是 less=true 的简写
   search 纵贯线  #: less

   # 使用 JSON 格式返回
   search 纵贯线 #: format=json,less


请求消息也可以是多行文本，使用多行文本时，需要遵守下面的格式（类似 bash here document）

.. code::

   {cmd} [{options}]  #: {req_options} <<EOF
   document
   EOF


在多行文本表示的命令中，document 即是命令的参数，这种命令只能接收一个参数。
举个例子

.. code::

   # 让服务端执行代码
   exec <<EOF
   print('hello, feeluown')
   player.pause()
   EOF

   # 它基本相当于
   exec "print('hello, feeluown'); player.pause()"

响应（Response）
''''''''''''''''''''
响应体分为两个部分：头(``status-line``) 和内容(``body``)，以 ``\r\n`` 为一个响应的结束。

**头** : 头是响应体的第一行。头中会告诉客户端请求成功或者失败，body 长度，请求选项。
客户端应该根据 length 信息来拆分响应。

.. code::

   # 成功
   ACK ok {length} #: more,json
   {body}

   # 失败
   ACK oops {length}
   {err_type}: {err_msg}

   # 示例
   ACK ok 0


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

消息服务
----------------
除了 RPC 服务外，FeelUOwn 默认还会启动一个消息服务，其监听端口为 23334。FeelUOwn
会通过该服务来向外发送实时消息。

该服务的通信协议 ``1.0`` 版本设计非常简单，主要关注可读性，只用在“观看实时歌词”
的功能中。即客户端连接到 23334 端口后，发送 ``sub topic.live_lyric`` 加换行符到服务端，
客户端即可收到实时的歌词文本流。

在 FeelUown v3.8.3 版本之后，它提供 ``2.0`` 版本的通信协议。在 2.0 版本中，
消息有固定的结构，客户端可以根据该结构来拆分消息

.. code::

   MSG {topic} {body_length}\r\n
   {body}
   \r\n

客户端可以在连接建立之后，通过 ``set`` 指令来切换通信协议。2.0 版本协议更关注
机器的“可读性”，复用了 RPC 服务的 2.0 版本通信协议的格式设计。
