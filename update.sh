#! /bin/sh

echo "---------------------------"
echo "这些脚本适用于Debian系的Linux"
echo "---------------------------"

echo "正在检查你是否安装一些更新需要的工具..."

git --version > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo ""
else
    echo "您还没有安装过git工具，现在为您安装git？"
    echo -n "确认: 'y/n' "
    echo -n "> "
    read flag
    if [ "$flag" = "y" ]; then
        sudo apt-get install git
    else
        echo "您选择取消安装git工具，更新中断..."
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
  git init  > /dev/null 2>&1
  git remote add origin https://github.com/cosven/FeelUOwn.git > /dev/null 2>&1
  git remote set-url origin https://github.com/cosven/FeelUOwn.git > /dev/null 2>&1
  git fetch --all  > /dev/null 2>&1
  git reset --hard origin/master > /dev/null 2>&1
  if [ $? -eq 0 ]; then
    echo "已经更新到最新版 !"
  else
    echo "貌似出现了什么错误..."
    exit 0
  fi
else
  echo "取消更新!"
fi

echo ""

echo "重新生成桌面图标"
./install.sh

exit 0
