# -*- coding=utf8 -*-

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtNetwork import *

from constants import ICON_PATH, PLAYLIST_FAVORITE, PLAYLIST_MINE


class SpreadWidget(QWidget):
    """支持展开和收缩动画的widget"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout()

        self.fold_animation = QPropertyAnimation(self, QByteArray(b'maximumHeight'))
        self.spread_animation = QPropertyAnimation(self, QByteArray(b'maximumHeight'))
        self.maximum_height = 2000  # 大点，字不会挤到一起

        self.Qss = False

        self._init_signal_binding()
        self._set_prop()
        self.set_widget_prop()
        self.set_layout_prop()
        self.setLayout(self._layout)

    def paintEvent(self, event):
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

    def _init_signal_binding(self):
        self.spread_animation.finished.connect(self.show)
        self.fold_animation.finished.connect(self.hide)

    def _set_prop(self):
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

    def set_layout_prop(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._layout.addStretch(1)

    def add_widget(self, *args, **kw):
        self._layout.addWidget(*args, **kw)

    def empty_layout(self):
        while self.layout().takeAt(0):
            item = self.layout().takeAt(0)
            del item


class _BaseItem(QFrame):
    """左边是图案，右边是文字按钮的widget"""

    signal_text_btn_clicked = pyqtSignal()

    active_item = []

    active_qss = """
        QFrame#playlist_container {
            border-top: 0px;
            border-bottom: 0px;
            padding-left: 11px;
            border-left:4px solid #993333;
            background-color: #333;
        }
        """
    normal_qss = """
        QFrame#playlist_container {
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

    def __init__(self, parent=None):
        super().__init__(parent)
        self._icon_label = QLabel(self)
        self._text_btn = QPushButton(self)
        self._layout = QHBoxLayout(self)
        self.setLayout(self._layout)

        self._icon_width = 16
        self._whole_width = 200
        self._whole_height = 30

        self._icon_label.setFixedSize(self._icon_width, self._icon_width)
        self.setFixedSize(self._whole_width, self._whole_height)
        self._text_btn.setFixedSize(self._whole_width-self._icon_width-10,
                                    self._whole_height)

        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self._icon_label)
        self._layout.addSpacing(10)
        self._layout.addWidget(self._text_btn)

        self._text_btn.clicked.connect(self.on_text_btn_clicked)
        self._text_btn.setObjectName('playlist_name')   # in order to apply css
        self.setObjectName('playlist_container')

    @classmethod
    def set_active(cls, w):
        """控制当前active的playlistitem

        :param w: 将被active的playlistitem
        :return: 如果当前item已经是active，return False
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

    @pyqtSlot()
    def on_text_btn_clicked(self):
        if _BaseItem.set_active(self):
            self.signal_text_btn_clicked.emit()

    def set_btn_text(self, text):
        self._text_btn.setText(text)

    def set_icon_pixmap(self, pixmap):
        self._icon_label.setPixmap(pixmap)


class PlaylistItem(_BaseItem):
    signal_text_btn_clicked = pyqtSignal([int], name='text_btn_clicked')

    def __init__(self, parent=None):
        super().__init__(parent)

        self.data = {}

    @pyqtSlot()
    def on_text_btn_clicked(self):
        if PlaylistItem.set_active(self):
            self.signal_text_btn_clicked.emit(self.data['id'])

    def set_playlist_item(self, playlist_model):
        self.data = playlist_model
        if playlist_model['type'] == 5:
            self._icon_label.setObjectName('playlist_img_favorite')
        else:
            self._icon_label.setObjectName('playlist_img_mine')

        metrics = QFontMetrics(self._text_btn.font())
        text = metrics.elidedText(playlist_model['name'], Qt.ElideRight,
                                  self._text_btn.width()-40)
        self._text_btn.setToolTip(playlist_model['name'])
        self._text_btn.setText(text)


class RecommendItem(_BaseItem):
    def __init__(self, parent=None, text=None, pixmap=None):
        super().__init__(parent)
        if text:
            self.set_btn_text(text)
        if pixmap:
            self.set_icon_pixmap(pixmap)
