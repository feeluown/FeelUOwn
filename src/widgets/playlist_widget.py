# -*- coding=utf8 -*-

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtNetwork import *

from setting import ICON_PATH, PLAYLIST_FAVORITE, PLAYLIST_MINE
from api import get_url_type


class PlaylistWidget_(QListWidget):
    """
    非常不好用！！！
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.set_widget_prop()

    def paintEvent(self, QPaintEvent):
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

    def set_widget_prop(self):
        self.setWordWrap(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.setMinimumHeight(10)
        self.resize(160, 10)

    def add_playlist_item(self, playlist_model):
        icon_path = PLAYLIST_MINE
        if playlist_model['type'] == 5:
            icon_path = PLAYLIST_FAVORITE
        item = QListWidgetItem(QIcon(icon_path), playlist_model['name'])
        self.addItem(item)


class PlaylistWidget(QWidget):
    """自定义widget

    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()

        self.set_widget_prop()
        self.set_layout_prop()
        self.setLayout(self.layout)

        self.debug()

    def paintEvent(self, QPaintEvent):
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

    def set_widget_prop(self):
        self.setContextMenuPolicy(Qt.CustomContextMenu)

    def debug(self):
        playlists = [{'type': 5, 'id': 16199365, 'uid': 18731323, 'name': 'cosven喜欢的音乐', 'coverImgUrl': 'http://p4.music.126.net/UG1j3uqi9W0LSmPTLzjG5Q==/7968160766807079.jpg'}, {'type': 0, 'id': 80263692, 'uid': 18731323, 'name': 'Great', 'coverImgUrl': 'http://p3.music.126.net/rkfbIVgA_wXQ6YtKORxGtA==/567347999940758.jpg'}, {'type': 0, 'id': 79355836, 'uid': 18731323, 'name': 'try', 'coverImgUrl': 'http://p4.music.126.net/vs7nj_Hz7XoHmXPQ-CfRUg==/7990150999209065.jpg'}, {'type': 0, 'id': 78602730, 'uid': 18731323, 'name': 'zhuangBi', 'coverImgUrl': 'http://p4.music.126.net/C4gzevIBJTmHSLDLNeqeKA==/6670737047021864.jpg'}, {'type': 0, 'id': 50574433, 'uid': 18731323, 'name': 'emotion', 'coverImgUrl': 'http://p4.music.126.net/WtjokoddBGgxj1NsD3xkEA==/7714173581366072.jpg'}, {'type': 0, 'id': 48379311, 'uid': 18731323, 'name': 'cosven的红心歌曲', 'coverImgUrl': 'http://p4.music.126.net/Hq9fhulUsErR0udjZg6CmA==/7839517906161495.jpg'}, {'type': 0, 'id': 2141843, 'uid': 1275229, 'name': 'ACG经典神曲目ヽ(≧Д≦)ノ（动漫游戏经典', 'coverImgUrl': 'http://p4.music.126.net/ur8wCGN9ggy7BlATPDtyFw==/5703166813277204.jpg'}, {'type': 0, 'id': 37870505, 'uid': 16560306, 'name': '怎能不爱的外语歌【百首英文好歌】', 'coverImgUrl': 'http://p3.music.126.net/R26rv2FEUiAB6B2HJn189g==/3227066628613438.jpg'}, {'type': 0, 'id': 36173014, 'uid': 17870068, 'name': '这么经典都没人听不科学啊！-呵呵，你懂？', 'coverImgUrl': 'http://p4.music.126.net/AucoCTgo3OsHKA5NLQh7KQ==/2532175279779141.jpg'}]
        for playlist in playlists:
            w = PlaylistItem(self)
            w.set_playlist_item(playlist)
            self.layout.addWidget(w)

    def set_layout_prop(self):
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.layout.addStretch(1)


class PlaylistItem(QFrame):

    active_item = []

    @classmethod
    def set_active(cls, w):
        if len(cls.active_item) != 0:
            cls.active_item[0].setObjectName('playlist_container')
            cls.active_item.pop()
        w.setObjectName('playlist_container_active')
        cls.active_item.append(w)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon_label = QLabel()
        self.text_label = QPushButton()
        self.layout = QHBoxLayout()

        self.icon_width = 16
        self.whole_width = 200
        self.whole_height = 30

        self.init()

    def mousePressEvent(self, event):
        # PlaylistItem.set_active(self)
        print('press')
        return True

    def mouseDoubleClickEvent(self, event):
        print('doubel')

    def paintEvent(self, event):
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

    def init(self):
        self.set_widgets_props()
        self.set_layout_props()
        self.set_objects_name()
        self.setLayout(self.layout)

    def set_playlist_item(self, playlist_model):
        if playlist_model['type'] == 5:
            self.icon_label.setObjectName('playlist_img_favorite')
            self.setObjectName('playlist_container_active')
        else:
            self.icon_label.setObjectName('playlist_img_mine')

        metrics = QFontMetrics(self.text_label.font())
        text = metrics.elidedText(playlist_model['name'], Qt.ElideRight, self.text_label.width()-40)
        self.text_label.setToolTip(playlist_model['name'])
        self.text_label.setText(text)
        # self.text_label.setText(playlist_model['name'])

    def set_objects_name(self):
        self.text_label.setObjectName('playlist_name')
        self.setObjectName('playlist_container')

    def set_widgets_props(self):
        self.icon_label.setFixedSize(self.icon_width, self.icon_width)
        self.setFixedSize(self.whole_width, self.whole_height)
        self.text_label.setFixedSize(self.whole_width-self.icon_width-10, self.whole_height)
        # self.text_label.setWordWrap(True)

    def set_layout_props(self):
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.icon_label)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.text_label)


if __name__ == "__main__":
    import sys, os
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(ICON_PATH + 'format.ico'))
    path = sys.path[0]
    os.chdir(path)
    all = PlaylistWidget()

    w = PlaylistItem()
    w.icon_label.setPixmap(QPixmap('../../icons/playlist.png'))
    w.text_label.setText('dsfasdfaname')
    all.layout.addWidget(w)
    w = PlaylistItem()
    w.icon_label.setPixmap(QPixmap('../../icons/playlist.png'))
    w.text_label.setText('dsfasdfaname')
    all.layout.addWidget(w)
    w.move((QApplication.desktop().width() - w.width())/2, (QApplication.desktop().height() - w.height())/2)
    all.show()
    sys.exit(app.exec_())