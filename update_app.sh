#! /bin/sh
echo "正在更新 NetEaseMusic For Linux - ThirdParty"
echo "这个操作会删除你在本地对代码的更改, 确定请输入 y"
echo "确认: 'y/n'"
echo -n "> "
read flag
if [ "$flag" = "y" ]; then
  echo "更新中......"
  git fetch --all
  git reset --hard origin/master
else
  echo "取消更新!"
fi

echo '更新完毕'
exit 0
