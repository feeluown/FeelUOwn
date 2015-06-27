#! /bin/sh


echo "正在检查你是否安装一些系统工具..."

git --version

if [ $? -eq 0 ]; then
    echo "您已经安装过 git 工具"
else
    echo "您还没有安装过git工具，现在为您安装git？"
    echo "确认: 'y/n'"
    echo -n "> "
    read flag
    if [ "$flag" = "y" ]; then
        sudo apt-get install git
    else
        echo "取消安装git工具，更新中断"
        exit 0
    fi
fi

echo "正在更新 FeelUOwn"
echo "这个操作会删除你在本地对代码的更改, 确定请输入 y"
echo "确认: 'y/n'"
echo -n "> "
read flag
if [ "$flag" = "y" ]; then
  echo "更新中......"
  git init
  git remote add origin https://github.com/cosven/FeelUOwn.git
  git remote set-url origin https://github.com/cosven/FeelUOwn.git
  git fetch --all
  git reset --hard origin/master
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
