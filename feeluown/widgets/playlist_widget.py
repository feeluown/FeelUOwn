# -*- coding:utf8 -*-

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtNetwork import *

from feeluown.controller_api import ControllerApi


class SpreadWidget(QWidget):
    """支持展开和收缩动画的widget"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout()

        self.fold_animation = QPropertyAnimation(self, QByteArray(b'maximumHeight'))
        self.spread_animation = QPropertyAnimation(self, QByteArray(b'maximumHeight'))
        self.maximum_height = 2000  # 大点，字不会挤到一起

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

    def empty_layout(self):
        while self.layout().takeAt(0):
            item = self.layout().takeAt(0)
            del item


class _BaseItem(QFrame):
    """左边是图案，右边是文字按钮的widget"""

    signal_text_btn_clicked = pyqtSignal()

    active_item = []
    items = []

    active_qss = """
        QFrame#playlist_container {
            border-top: 0px;
            border-bottom: 0px;
            padding-left: 11px;
            border-left:4px solid #993333;
            background-color: #333;
        }
        QFrame#playlist_container:focus {
            background-color: #444;
        }
        """
    normal_qss = """
        QFrame#playlist_container {
            border-top: 0px;
            border-bottom: 0px;
            padding-left: 15px;
            border: 0px solid #993333;
        }
        QFrame#playlist_container:focus {
            background-color: #444;
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
        self.setFocusPolicy(Qt.StrongFocus)
        self.setObjectName('playlist_container')
        self.setStyleSheet(self.normal_qss)

        _BaseItem.items.append(self)

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

    def focus_next(self):
        index = self.items.index(self)
        if index == len(self.items) - 1:
            next_index = 0
        else:
            next_index = index + 1
        self.items[next_index].setFocus()

    def focus_previous(self):
        index = self.items.index(self)
        if index == 0:
            pre_index = len(self.items) - 1
        else:
            pre_index = index - 1
        self.items[pre_index].setFocus()

    @pyqtSlot()
    def on_text_btn_clicked(self):
        self.setFocus()
        if _BaseItem.set_active(self):
            self.signal_text_btn_clicked.emit()

    def set_btn_text(self, text):
        self._text_btn.setText(text)

    def set_icon_pixmap(self, pixmap):
        self._icon_label.setPixmap(pixmap)

    def _bind_select_shortcut(self, event):
        key_code = event.key()
        if key_code == Qt.Key_J:
            self.focus_next()
        elif key_code == Qt.Key_K:
            self.focus_previous()
        elif key_code in (Qt.Key_Enter, Qt.Key_Return):
            self.on_text_btn_clicked()

    def _ensure_visible(self):
        '''hack'''
        scrollarea = self.parent().parent().parent().parent()
        y = self.y()
        height = self.height()
        p_y = self.parent().y()
        p_p_y = self.parent().parent().y()
        # scrollarea central widget's height
        p_p_p_height = self.parent().parent().parent().height()

        dis = (p_p_p_height + p_p_y) - (y + p_y + height)
        if dis - 20 <= 0:
            scrollarea.verticalScrollBar().setValue(-dis)
        else:
            scrollarea.verticalScrollBar().setValue(0)

    def keyPressEvent(self, event):
        self._bind_select_shortcut(event)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self._ensure_visible()


class PlaylistItem(_BaseItem):
    signal_text_btn_clicked = pyqtSignal([int], name='text_btn_clicked')

    def __init__(self, parent=None):
        super().__init__(parent)

        self._edit_widget = QLineEdit(self)
        self._layout.addWidget(self._edit_widget)
        self._edit_widget.close()
        self._edit_widget.setObjectName('playlist_name_edit')

        self.data = {}
        self._menu = QMenu(self)
        self.edit_action = QAction(u"编辑歌单名字", self)
        self.delete_action = QAction(u'删除歌单', self)
        self.update_action = QAction(u'更新歌单', self)
        self._menu.addAction(self.edit_action)
        self._menu.addAction(self.update_action)
        self._menu.addAction(self.delete_action)

        self.edit_action.triggered.connect(self.edit_mode)
        self.delete_action.triggered.connect(self.delete_playlist)
        self.update_action.triggered.connect(self.update_playlist)
        self._edit_widget.returnPressed.connect(self.update_playlist_name)

    @pyqtSlot()
    def on_text_btn_clicked(self):
        self.setFocus()
        if PlaylistItem.set_active(self):
            self.signal_text_btn_clicked.emit(self.data['id'])

    def set_playlist_item(self, playlist_model):
        self.data = playlist_model
        if ControllerApi.api.is_favorite_playlist(playlist_model):
            self._icon_label.setObjectName('playlist_img_favorite')
        else:
            self._icon_label.setObjectName('playlist_img_mine')

        metrics = QFontMetrics(self._text_btn.font())
        text = metrics.elidedText(playlist_model['name'], Qt.ElideRight,
                                  self._text_btn.width()-40)
        self._text_btn.setText(text)

    def update_playlist_name(self):
        text = self._edit_widget.text()
        if text == '':
            self._edit_widget.setPlaceholderText(u'歌单名字不能为空')
            return
        self._edit_widget.close()
        self._text_btn.show()
        self._text_btn.setText(text)
        ControllerApi.api.update_playlist_name(self.data['id'], text)

    def update_playlist(self, clicked=True):
        pid = self.data['id']
        ControllerApi.api.get_playlist_detail(pid, cache=False)
        ControllerApi.view.ui.STATUS_BAR.showMessage(u'正在后台更新歌单歌曲列表', 5000)

    def delete_playlist(self):
        m = QMessageBox(QMessageBox.Warning, '警告', '确认删除歌单么 ?',
                        QMessageBox.Yes | QMessageBox.No)
        if m.exec() != QMessageBox.Yes:
            return False

        pid = self.data['id']
        flag = ControllerApi.api.delete_playlist(pid)
        if flag:
            ControllerApi.notify_widget.show_message('◕◡◔', '删除歌单成功')
            self.close()
            self.deleteLater()
            return True
        else:
            ControllerApi.notify_widget.show_message('◕◠◔', '删除歌单失败')
            return False

    def edit_mode(self):
        playlist_name = self._text_btn.text()
        self._text_btn.close()
        self._edit_widget.show()
        self._edit_widget.setText(playlist_name)
        self._edit_widget.setFocus()

    def _display_mode(self):
        self._text_btn.show()
        self._edit_widget.close()

    def contextMenuEvent(self, event):
        if ControllerApi.api.is_playlist_mine(self.data):
            self._menu.exec(event.globalPos())

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        key_code = event.key()
        if key_code == Qt.Key_Escape:
            text = self._edit_widget.text()
            if text == '':
                self._edit_widget.setPlaceholderText(u'歌单名字不能为空')
                return event
            self._display_mode()


class RecommendItem(_BaseItem):
    def __init__(self, parent=None, text=None, pixmap=None):
        super().__init__(parent)
        if text:
            self.set_btn_text(text)
        if pixmap:
            self.set_icon_pixmap(pixmap)
