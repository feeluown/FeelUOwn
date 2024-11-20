音乐库
=====================

.. _library:

音乐库模块管理资源提供方(*Provider*)。音乐库还提供了一些通用接口，简化了对资源提供方的访问。

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
