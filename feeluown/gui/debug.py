from contextlib import contextmanager
from unittest.mock import MagicMock

from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout


@contextmanager
def simple_qapp():
    qapp = QApplication([])
    yield qapp
    qapp.exec()


@contextmanager
def mock_app():
    app = MagicMock()
    yield app


@contextmanager
def simple_layout(cls=QHBoxLayout):
    with simple_qapp():
        main = QWidget()
        layout = cls(main)
        yield layout
        main.show()
