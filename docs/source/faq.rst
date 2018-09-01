常见问题
========

使用相关问题
------------

安装完成后，运行 feeluown 提示 Command 'feeluown' not found
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
一般来说，安装之后， feeluown 命令会在 `~/.local/bin/` 目录下。

可以通过下面命令查看目录下是否有 feeluown::

  ls -l ~/.local/bin/feeluown

如果输出正常则说明安装已经成功了， 大家可以修改 PATH 环境变量即可。

如果是使用 bash 或者 zsh，大家可以在 ~/.bashrc 或者 ~/.zshrc 文件中加入一行::

  export PATH=~/.local/bin:$PATH

然后重新进入 shell，下次就可以直接运行 feeluown 了。

开发相关问题
------------
