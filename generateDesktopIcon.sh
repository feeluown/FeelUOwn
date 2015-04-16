#! /bin/bash

##############################
#   代码贡献: fitmewell(http://git.oschina.net/fitmewell)
#   相关issue: http://git.oschina.net/zjuysw/NetEaseMusic/issues/3
##############################

echo "正在生成图标......"

desktopFilename='NetEaseMusic.desktop'
touch $desktopFilename
currentPath=`dirname $(readlink -f $0)`

echo "#!/usr/bin/env xdg-open
[Desktop Entry]
Type=Application
Name=NetEaseMusic
Comment=NetEaseMusic Launcher
Exec=$currentPath/main.py
Icon=$currentPath/icons/format.png
Terminal=false
StartupNotify=true
" > $desktopFilename
echo "尝试生成桌面图标..."
sudo cp $desktopFilename ~/Desktop

echo "让程序可以被系统搜索..."
sudo cp $desktopFilename ~/.local/share/applications/

if [ $? -eq 0 ]; then
    echo "全部完成!"
else
    echo "貌似出现了什么错误..."
fi

