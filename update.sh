#! /bin/sh
echo "正在更新 NetEaseMusic For Linux - ThirdParty"
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
  fi
else
  echo "取消更新!"
fi
echo "正在重新生成桌面图标..."
./install.sh

exit 0
