import sys
import os, json

from PyQt5.QtCore import Qt, QRectF, QRect, QSize, pyqtSignal
from PyQt5.QtGui import QPalette, QColor, QTextOption, QPainter, \
    QKeySequence
from PyQt5.QtWidgets import QLabel, QWidget,\
    QVBoxLayout, QSizeGrip, QHBoxLayout, QColorDialog, \
    QMenu, QAction, QFontDialog, QShortcut
from feeluown.consts import CONFIG_DIR

from feeluown.gui.helpers import resize_font


IS_MACOS = sys.platform == 'darwin'

LYRIC_CONFIG_FILE = CONFIG_DIR + '/lyric-ui.json'

class Window(QWidget):

    play_previous_needed = pyqtSignal()
    play_next_needed = pyqtSignal()

    def __init__(self):
        super().__init__(parent=None)
        if IS_MACOS:
            # On macOS, Qt.Tooltip widget can't accept focus and it will hide
            # when the application window is actiavted. Qt.Tool widget can't
            # keep staying on top. Neither of them work well on macOS.
            flags = Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint
        else:
            # TODO: use proper flags on other platforms
            # see #413 for more details
            flags = Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.c = Container(self)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self.c)

        self._old_pos = None

        QShortcut(QKeySequence.ZoomIn, self).activated.connect(self.zoomin)
        QShortcut(QKeySequence.ZoomOut, self).activated.connect(self.zoomout)
        QShortcut(QKeySequence('Ctrl+='), self).activated.connect(self.zoomin)
        QShortcut(QKeySequence.Cancel, self).activated.connect(self.hide)

        self.setToolTip('''
* 右键可以弹出设置菜单
* Ctrl+= 或者 Ctrl++ 可以增大字体
* Ctrl+- 可以减小字体
* 鼠标前进后退键可以播放前一首/下一首
''')

    def set_sentence(self, text):
        if self.isVisible():
            self.c.label.setText(text)

    def mousePressEvent(self, e):
        self._old_pos = e.globalPos()

    def mouseMoveEvent(self, e):
        # NOTE: e.button() == Qt.LeftButton don't work on Windows
        # on Windows, even I drag with LeftButton, the e.button() return 0,
        # which means no button
        if self._old_pos is not None:
            delta = e.globalPos() - self._old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self._old_pos = e.globalPos()

    def mouseReleaseEvent(self, e):
        if not self.rect().contains(e.pos()):
            return
        if e.button() == Qt.BackButton:
            self.play_previous_needed.emit()
        elif e.button() == Qt.ForwardButton:
            self.play_next_needed.emit()

    def zoomin(self):
        label = self.c.label
        font = label.font()
        resize_font(font, +1)
        label.setFont(font)

    def zoomout(self):
        label = self.c.label
        font = label.font()
        resize_font(font, - 1)
        label.setFont(font)

    def sizeHint(self):
        return QSize(500, 60)


class Container(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self._border_radius = 10
        self.label = QLabel('...', self)
        self._size_grip = QSizeGrip(self)
        self._size_grip.setFixedWidth(self._border_radius * 2)

        font = self.font()
        self.fontSize = 20
        self.fontColor = {
            'r': 0,
            'g': 0,
            'b': 0,
            'alpha': 255,
        }
        self.bgColor = {
            'r': 255,
            'g': 255,
            'b': 255,
            'alpha': 255,
        }

        font.setPointSize(self.fontSize)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignBaseline | Qt.AlignVCenter | Qt.AlignHCenter)
        self.label.setWordWrap(False)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addSpacing(self._border_radius * 2)
        self._layout.addWidget(self.label)
        self._layout.addWidget(self._size_grip)
        self._layout.setAlignment(self._size_grip, Qt.AlignBottom)

        self.load_config()

    # 加载配置
    def load_config(self):
        config_file = LYRIC_CONFIG_FILE
        if not os.path.exists(config_file):
            return

        config_data:dict = json.load(open(config_file))
        # 字体
        font = self.font()
        font.setFamily(config_data.get("font", font))
        # 字体大小
        font.setPointSize(config_data.get("fontSize", 20))
        self.label.setFont(font)

        palette = self.palette()
        # 背景颜色
        bg_color = config_data.get("bgColor", self.bgColor)
        self.bgColor = bg_color
        bg_color = QColor.fromRgbF(
            bg_color.get('r', 0),
            bg_color.get('g', 0),
            bg_color.get('b', 0),
            bg_color.get('alpha', 255)
        )
        palette.setColor(QPalette.Active, QPalette.Window, bg_color)
        palette.setColor(QPalette.Active, QPalette.Base, bg_color)
        palette.setColor(QPalette.Inactive, QPalette.Window, bg_color)
        palette.setColor(QPalette.Inactive, QPalette.Base, bg_color)
        self.setPalette(palette)
        # 字体颜色
        font_color = config_data.get("fontColor", self.fontColor)
        self.fontColor = font_color
        font_color = QColor.fromRgbF(
            font_color.get('r', 255),
            font_color.get('g', 255),
            font_color.get('b', 255),
            font_color.get('alpha', 255)
        )
        palette.setColor(QPalette.Active, QPalette.WindowText, font_color)
        palette.setColor(QPalette.Active, QPalette.Text, font_color)
        palette.setColor(QPalette.Inactive, QPalette.WindowText, font_color)
        palette.setColor(QPalette.Inactive, QPalette.Text, font_color)
        self.label.setPalette(palette)

    # 保存配置
    def save_config(self):
        config_file = LYRIC_CONFIG_FILE
        f = open(config_file, "w+")
        config_data = {
            'font': self.label.font().family(),
            'fontSize': self.fontSize,
            'fontColor': self.fontColor,
            'bgColor': self.bgColor
        }
        config_data_ = json.dumps(config_data, ensure_ascii=False)
        # print(config_data_)
        f.write(config_data_)
        f.close()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.palette().color(QPalette.Window))
        painter.drawRoundedRect(self.rect(), self._border_radius, self._border_radius)
        painter.save()
        painter.setPen(QColor('white'))
        option = QTextOption()
        option.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        rect = QRect(self.mapToParent(self._size_grip.pos()), self._size_grip.size())
        painter.drawText(QRectF(rect), '●', option)
        painter.restore()

    def show_color_dialog(self, bg=True):

        def set_color(color):
            palette = self.palette()
            if bg:
                self.bgColor = {
                    'r': color.getRgbF()[0],
                    'g': color.getRgbF()[1],
                    'b': color.getRgbF()[2],
                    'alpha': color.getRgbF()[3]
                }
                palette.setColor(QPalette.Active, QPalette.Window, color)
                palette.setColor(QPalette.Active, QPalette.Base, color)
                palette.setColor(QPalette.Inactive, QPalette.Window, color)
                palette.setColor(QPalette.Inactive, QPalette.Base, color)
            else:
                self.fontColor = {
                    'r': color.getRgbF()[0],
                    'g': color.getRgbF()[1],
                    'b': color.getRgbF()[2],
                    'alpha': color.getRgbF()[3]
                }
                palette.setColor(QPalette.Active, QPalette.WindowText, color)
                palette.setColor(QPalette.Active, QPalette.Text, color)
                palette.setColor(QPalette.Inactive, QPalette.WindowText, color)
                palette.setColor(QPalette.Inactive, QPalette.Text, color)
            self.label.setPalette(palette)
            self.setPalette(palette)

        dialog = QColorDialog(self)
        dialog.currentColorChanged.connect(set_color)
        dialog.colorSelected.connect(set_color)
        dialog.setOption(QColorDialog.ShowAlphaChannel, True)
        dialog.exec()

    def show_font_dialog(self):
        dialog = QFontDialog(self.label.font(), self)
        dialog.currentFontChanged.connect(self.label.setFont)
        dialog.fontSelected.connect(self.label.setFont)
        dialog.exec()

    def contextMenuEvent(self, e):
        menu = QMenu()
        bg_color_action = QAction('背景颜色', menu)
        fg_color_action = QAction('文字颜色', menu)
        font_action = QAction('字体', menu)
        menu.addAction(bg_color_action)
        menu.addAction(fg_color_action)
        menu.addSeparator()
        menu.addAction(font_action)
        bg_color_action.triggered.connect(lambda: self.show_color_dialog(bg=True))
        fg_color_action.triggered.connect(lambda: self.show_color_dialog(bg=False))
        font_action.triggered.connect(self.show_font_dialog)
        menu.exec(e.globalPos())
        self.save_config()
