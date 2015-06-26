#! /bin/bash

##############################
#   代码贡献: fitmewell(http://git.oschina.net/fitmewell)
#   相关issue: http://git.oschina.net/zjuysw/NetEaseMusic/issues/3
##############################

echo "1. 正在生成图标......"

desktopFilename='FeelUOwn.desktop'
touch $desktopFilename
currentPath=`dirname $(readlink -f $0)`

echo "#!/usr/bin/env xdg-open
[Desktop Entry]
Type=Application
Name=FeelUOwn
Comment=FeelUOwn Launcher
Exec=$currentPath/src/main.py
Icon=$currentPath/icons/FeelUOwn.png
Categories=AudioVideo;Audio;Player;Qt;
Terminal=false
StartupNotify=true
" > $desktopFilename
echo "2. 尝试生成桌面图标..."
desktop_cn=""
desktop_en=""
if [ -d ~/桌面 ];then
    echo "猜测：中文系统"
    sudo cp $desktopFilename ~/桌面
    cd ~/桌面
    sudo chmod +x $desktopFilename

    if [ -f NetEaseMusic.desktop ]; then
        echo "检测到您的系统存在桌面图标NetEaseMusic，这很可能是之前过时的桌面图标文件"
        echo "您确定删除这个旧的图标文件么？ 确定请输入 y，否则输入 n"
        echo "确认: 'y/n'"
        echo -n "> "
        read flag
        if [ "$flag" = "y" ]; then
            sudo rm NetEaseMusic.desktop
            if [ -f ~/.local/share/applications/NetEaseMusic.desktop ]; then
                sudo rm ~/.local/share/applications/NetEaseMusic.desktop
            fi
        fi
    fi
fi
if [ -d ~/Desktop ];then
    echo "猜测：英文系统"
    sudo cp $desktopFilename ~/Desktop
    cd ~/Desktop
    sudo chmod +x $desktopFilename

    if [ -f NetEaseMusic.desktop ]; then
        echo "检测到您的系统存在桌面图标NetEaseMusic，这很可能是之前过时的桌面图标文件"
        echo "您确定删除这个旧的图标文件么？ 确定请输入 y，否则输入 n"
        echo "确认: 'y/n'"
        echo -n "> "
        read flag
        if [ "$flag" = "y" ]; then
            sudo rm NetEaseMusic.desktop
            if [ -f ~/.local/share/applications/NetEaseMusic.desktop ]; then
                sudo rm ~/.local/share/applications/NetEaseMusic.desktop
            fi
        fi
    fi
    
fi

echo "3. 让程序可以被系统搜索..."
sudo cp $desktopFilename ~/.local/share/applications/

echo "==============================="

if [ $? -eq 0 ]; then
    echo "全部完成!"
else
    echo "貌似出现了什么错误..."
fi
