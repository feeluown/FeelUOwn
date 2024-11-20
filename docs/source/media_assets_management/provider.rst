资源提供方
=====================

歌曲等音乐资源都来自于某一个提供方。比如，我们认为本地音乐的提供方是本地，
网易云音乐资源的提供方是网易，等等。对应到程序设计上，每个提供方都对应一个 provider 实例。
provider 是我们访问具体一个音乐平台资源音乐的入口。

在 feeluown 生态中，每个音乐资源提供方都对应着一个插件，我们现在有 feeluown-local/feeluown-netease
等许多插件，这些插件在启动时，会注册一个 provider 实例到 feeluown 的音乐库模块上。
注册完成之后，音乐库和 feeluown 其它模块就能访问到这个提供方的资源

举个栗子，feeluown-local 插件在启动时就创建了一个 *identifier* 为 ``local`` 的 provider 实例，
并将它注册到音乐库中，这样，当我们访问音乐库资源时，就能访问到本地音乐资源。

详细信息请参考 :doc:`provider`。

定义一个资源提供方
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: feeluown.library.AbstractProvider
   :members:

.. autoclass:: feeluown.library.Provider
   :members:

协议
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: feeluown.library.provider_protocol
   :members:

