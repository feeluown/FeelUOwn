# feeluown-mpris2-plugin
mpris dbus interface implementation for feeluown

# 安装

```
sudo apt-get install python3-dbus
sudo apt-get install python3-dbus.mainloop.pyqt5
cd ~/.FeelUOwn/plugins
git clone https://github.com/cosven/feeluown-mpris2-plugin.git
```

## CHANGELOG

- `2019-12-16`: Fix player metadata not working in Plasma KDE
- `2019-04-25`: 支持 position 同步和 seek 操作
- `2019-04-20`: 适配 feeluown 3.0 版本
- `2018-07-08`: 适配 feeluown 2.0 版本（不兼容老版本）
- `2017-06-14`: 适配 feeluown 1.1.0 版本
- `2016-05-15`: 修复 xml 不完整的 bug. **严重**
