#! /bin/sh


echo "正在检查你是否安装一些系统工具..."

git --version > /dev/null
if [ $? -eq 0 ]; then
    echo "好消息：您已经安装过 git 工具"
else
    echo "您还没有安装过git工具，现在为您安装git？"
    echo "确认: 'y/n'"
    echo -n "> "
    read flag
    if [ "$flag" = "y" ]; then
        sudo apt-get install git
    else
        echo "取消安装git工具，更新中断..."
        exit 0
    fi
fi

vlc --version > /dev/null
if [ $? -eq 0 ]; then
    echo "好消息：您已经安装了 VLC 播放器"
else
    echo "VLC播放器可以用来播放MV，您还没有安装过，如果您使用Ubuntu，建议您安装它；如果您使用Deepin，你可以不安装"
    echo "现在为您安装VLC播放器吗 ？"
    echo "确认: 'y/n'"
    echo -n "> "
    read flag
    if [ "$flag" = "y" ]; then
        sudo apt-get install vlc
    else
        echo "取消安装 VLC播放器"
    fi
fi


echo "正在更新 FeelUOwn"
echo "这个操作会删除你在本地对代码的更改, 确定请输入 y"
echo "确认: 'y/n'"
echo -n "> "
read flag
if [ "$flag" = "y" ]; then
  echo "更新中......"
  git init  > /dev/null
  git remote add origin https://github.com/cosven/FeelUOwn.git > /dev/null
  git remote set-url origin https://github.com/cosven/FeelUOwn.git > /dev/null
  git fetch --all  > /dev/null
  git reset --hard origin/master > /dev/null
  if [ $? -eq 0 ]; then
    echo "已经更新到最新版 !"
  else
    echo "貌似出现了什么错误..."
    exit 0
  fi
else
  echo "取消更新!"
fi
echo "正在重新生成桌面图标..."
./install.sh

exit 0
