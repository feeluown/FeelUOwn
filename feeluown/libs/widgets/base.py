# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QWidget, QFrame, QPushButton, QLabel, QSlider,\
    QScrollArea, QDialog, QLineEdit, QCheckBox, QTableWidget, QComboBox
from PyQt5.QtCore import QObject


class FButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_theme_style(self):
        pass


class FCheckBox(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)

    def set_theme_style(self):
        pass


class FComboBox(QComboBox):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

    def set_theme_style(self):
        pass


class FDialog(QDialog):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

    def set_theme_style(self):
        pass


class FFrame(QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_theme_style(self):
        self.setStyleSheet('background: transparent;')


class FLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_theme_style(self):
        pass


class FLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

    def set_theme_style(self):
        pass


class FObject(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

    def set_theme_style(self):
        pass


class FSlider(QSlider):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_theme_style(self):
        pass


class FScrollArea(QScrollArea):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_theme_style(self):
        pass


class FTableWidget(QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_theme_style(self):
        pass


class FWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_theme_style(self):
        pass
