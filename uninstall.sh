#! /bin/bash

##############################
#   代码贡献: fitmewell(http://git.oschina.net/fitmewell)
#   相关issue: http://git.oschina.net/zjuysw/NetEaseMusic/issues/3
##############################

echo "主人，FeelUOwn正在准备卸载 .. , 此操作将会删除系统中 FeelUOwn 程序图标文件" 
echo "确认: 'y/n'"
echo -n "> "
read flag
if [ "$flag" = "y" ]; then
    desktopFilename='FeelUOwn.desktop'
    currentPath=`dirname $(readlink -f $0)`

    echo "准备删除桌面图标....."
    if [ -d ~/桌面 ];then
        echo "猜测：中文系统"
        cd ~/桌面
        sudo rm +x $desktopFilename
    fi

    if [ -d ~/Desktop ];then
        echo "猜测：英文系统"
        cd ~/Desktop
        sudo rm +x $desktopFilename

    fi

    echo -n "正在删除系统中的FeelUOwn图标...，它的路径是:"
    echo ~/.local/share/applications/$desktopFilename

    if [ -f ~/.local/share/applications/$desktopFilename ]; then
        sudo rm ~/.local/share/applications/$desktopFilename
    fi
    
    echo "==============================="
    
    if [ $? -eq 0 ]; then
        echo "全部完成! 已经从系统的各个角落移除了和FeelUOwn相关的文件 ..."
    else
        echo "貌似出现了什么错误..."
    fi
else
    echo "取消卸载 ^_^"
fi

