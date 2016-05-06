# FeelUOwn 开发版说明文档

## 手动安装（推荐）

```
git clone https://github.com/cosven/FeelUOwn.git
git checkout dev    # 使用开发版
cd FeelUOwn

sudo apt-get install python3-pyqt5.qtmultimedia libqt5multimedia5-plugins -y    # 播放音乐需要
sudo apt-get install fcitx-frontend-qt5 -y  # 输入中文需要
sudo apt-get install gstreamer0.10-plugins-good gstreamer0.10-plugins-bad gstreamer0.10-plugins-ugly -y   # 系统依赖

# 这些东西很多系统已经有了，以防万一，也安装一次
sudo apt-get install python3-setuptools
sudo easy_install3 pip
pip3 install -r requirements.txt  # 可能需要 加 sudo

```

## 生成桌面图标


## 运行

```
make run
```
