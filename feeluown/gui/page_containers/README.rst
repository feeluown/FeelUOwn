feeluown.containers
===================


feeluown.containers 和 feeluown.gui.widgets 的区别
""""""""""""""""""""""""""""""""""""""""""""""

1. Container 知道 `app` 这个概念的存在，并且应该将它作为构造函数的
   第一个参数，而 widget 不应该知道 app 的存在，widget 通过信号
   将信息传送给 container，container 调用 widget 的方法来实现控制。
2. Container 一般主要负责 widget 的排列、显示隐藏等逻辑，而不会对应
   具体的功能。
