相关专业术语
============

下面是 feeluown 中项目使用的一些专业名词，这些专业名词会体现在文档、代码注释、
变量命名等各方面。

.. glossary::

   library
     音乐库

   provider
     资源提供方，提供媒体媒体资源的平台。

     比如 YouTube、网易云音乐、虾米等。

   source
     资源提供方标识。

     在 feeluown 中，歌曲、歌手等资源都有一个 source 属性来标识该资源的来源。

   media
     媒体实体资源

     Media 关注的点是“可播放”的实体资源。在 feeluown 中，Media 有两种类型，
     Audio 和 Video (以后可能会新增 Image)，它用来保存资源的元信息，
     对于 Audio 来说，有 bitrate, channel count 等元信息。对于 Video
     来说，有 framerate, codec 等信息。

     和 Song 不一样，Song 逐重强调一首歌的元信息部分，比如歌曲名称、歌手等。
     理论上，我们可以从 Media(Audio) 中解析出部分 Song 信息。

   FeelUOwn
     项目名，泛指 FeelUOwn 整个项目。从 GitHub repo 角度看，它指 github.com/feeluown
     目录下所有的项目。

   feeluown
     包名（Python 包），程序名。从 GitHub repo 角度看，
     它特指 github.com/feeluown/feeluown 这个项目。

   fuo
     程序名
