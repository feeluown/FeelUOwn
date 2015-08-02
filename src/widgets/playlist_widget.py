# -*- coding=utf8 -*-

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtNetwork import *

from constants import ICON_PATH, PLAYLIST_FAVORITE, PLAYLIST_MINE


class PlaylistWidget(QWidget):
    """自定义widget

    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()

        self.fold_animation = QPropertyAnimation(self, QByteArray(b'maximumHeight'))
        self.spread_animation = QPropertyAnimation(self, QByteArray(b'maximumHeight'))
        self.maximum_height = 800 # 大点，字不会挤到一起

        self.Qss = False

        self.__init_signal_binding()
        self.__set_prop()
        self.set_widget_prop()
        self.set_layout_prop()
        self.setLayout(self.layout)

        # self.debug()

    def paintEvent(self, event):
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

    def __init_signal_binding(self):
        self.spread_animation.finished.connect(self.show)
        self.fold_animation.finished.connect(self.hide)
        pass

    def __set_prop(self):
        # set fold_animation properties
        self.fold_animation.setDuration(300)
        self.fold_animation.setStartValue(self.maximum_height)
        self.fold_animation.setEndValue(0)

        self.spread_animation.setDuration(300)
        self.spread_animation.setStartValue(0)
        self.spread_animation.setEndValue(self.maximum_height)

    def fold_spread_with_animation(self):

        if self.fold_animation.state() == QAbstractAnimation.Running:
            self.fold_animation.stop()

            self.spread_animation.setStartValue(self.height())
            self.spread_animation.start()
            return

        if self.isVisible():  # hide the widget
            if self.spread_animation.state() == QAbstractAnimation.Running:
                self.spread_animation.stop()
                self.fold_animation.setStartValue(self.height())
            else:
                self.fold_animation.setStartValue(self.maximum_height)

            # self.fold_animation.setStartValue(self.height)
            self.fold_animation.start()
        else:
            self.spread_animation.setStartValue(0)
            self.show()

    def showEvent(self, event):
        self.spread_animation.start()

    def hideEvent(self, event):
        self.parent().update()

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

    signal_text_btn_clicked = pyqtSignal([int], name='text_btn_clicked')  # 发送一个playlist的Id

    active_item = []

    active_qss = """
            QFrame {
                border-top: 0px;
                border-bottom: 0px;
                padding-left: 11px;
                border-left:4px solid #993333;
                background-color: #333;
            }
        """
    normal_qss = """
        QFrame {
            border-top: 0px;
            border-bottom: 0px;
            padding-left: 15px;
            border: 0px solid #993333;
        }
        QFrame#playlist_container:hover{
            background-color: #333;
            border-left:8px solid #993333;
            border-top: 10px solid #333;
            border-bottom: 10px solid #333;
        }
    """

    @classmethod
    def set_active(cls, w):
        """控制当前active的playlistitem
        :param w: 将被active的playlistitem
        """
        if len(cls.active_item) != 0:
            if w is cls.active_item[0]:     # 判断是否重复点击
                return False
            cls.active_item[0].setStyleSheet(cls.normal_qss)
            cls.active_item.pop()
        w.setStyleSheet(cls.active_qss)
        cls.active_item.append(w)
        return True

    @classmethod
    def de_active_all(cls):
        for item in cls.active_item:
            item.setStyleSheet(cls.normal_qss)
            cls.active_item.remove(item)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon_label = QLabel()
        self.text_btn = QPushButton()
        self.layout = QHBoxLayout()

        self.icon_width = 16
        self.whole_width = 200
        self.whole_height = 30

        self.data = {}

        self.init()

    def init(self):
        self.set_widgets_props()
        self.set_layout_props()
        self.set_objects_name()
        self.init_signal_binding()
        self.setLayout(self.layout)

    def init_signal_binding(self):
        self.text_btn.clicked.connect(self.on_text_clicked)

    def paintEvent(self, event):
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

    @pyqtSlot()
    def on_text_clicked(self):
        if PlaylistItem.set_active(self):
            self.signal_text_btn_clicked.emit(self.data['id'])  # 信号中包含一个playlist id

    def set_playlist_item(self, playlist_model):
        self.data = playlist_model
        if playlist_model['type'] == 5:
            self.icon_label.setObjectName('playlist_img_favorite')
        else:
            self.icon_label.setObjectName('playlist_img_mine')

        metrics = QFontMetrics(self.text_btn.font())
        text = metrics.elidedText(playlist_model['name'], Qt.ElideRight, self.text_btn.width()-40)
        self.text_btn.setToolTip(playlist_model['name'])
        self.text_btn.setText(text)
        # self.text_label.setText(playlist_model['name'])

    def set_objects_name(self):
        self.text_btn.setObjectName('playlist_name')
        self.setObjectName('playlist_container')

    def set_widgets_props(self):
        self.icon_label.setFixedSize(self.icon_width, self.icon_width)
        self.setFixedSize(self.whole_width, self.whole_height)
        self.text_btn.setFixedSize(self.whole_width-self.icon_width-10, self.whole_height)
        # self.text_label.setWordWrap(True)

    def set_layout_props(self):
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.icon_label)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.text_btn)


if __name__ == "__main__":
    import sys, os
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(ICON_PATH + 'format.ico'))
    path = sys.path[0]
    os.chdir(path)

    window = QWidget()
    layout = QVBoxLayout()
    window.setLayout(layout)

    button = QPushButton('Test')
    button_add = QPushButton('Add')
    bottom_label = QLabel('bottom')

    all = PlaylistWidget(window)

    w = PlaylistItem()
    w.icon_label.setPixmap(QPixmap('../../icons/playlist.png'))
    w.text_btn.setText('dsfasdfaname')
    all.layout.addWidget(w)

    w = PlaylistItem()
    w.icon_label.setPixmap(QPixmap('../../icons/playlist.png'))
    w.text_btn.setText('dsfasdfaname')
    all.layout.addWidget(w)

    w = PlaylistItem()
    w.icon_label.setPixmap(QPixmap('../../icons/playlist.png'))
    w.text_btn.setText('dsfasdfaname')
    all.layout.addWidget(w)

    w = PlaylistItem()
    w.icon_label.setPixmap(QPixmap('../../icons/playlist.png'))
    w.text_btn.setText('dsfasdfaname')
    all.layout.addWidget(w)

    w = PlaylistItem()
    w.icon_label.setPixmap(QPixmap('../../icons/playlist.png'))
    w.text_btn.setText('dsfasdfaname')
    all.layout.addWidget(w)

    w.move((QApplication.desktop().width() - w.width())/2, (QApplication.desktop().height() - w.height())/2)

    is_hidden = False

    def add_new_widget():
        global all
        w = PlaylistItem()
        w.icon_label.setPixmap(QPixmap('../../icons/playlist.png'))
        w.text_btn.setText('haha')
        all.layout.addWidget(w)

    button.clicked.connect(all.fold_spread_with_animation)
    button_add.clicked.connect(add_new_widget)

    layout.addWidget(button)
    layout.addWidget(button_add)
    layout.addWidget(all)
    layout.addWidget(bottom_label)
    layout.addStretch(1)

    window.show()
    sys.exit(app.exec_())
