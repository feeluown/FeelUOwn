from contextlib import contextmanager

from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout


@contextmanager
def simple_qapp():
    app = QApplication([])
    yield app
    app.exec()


@contextmanager
def simple_layout(cls=QHBoxLayout):
    with simple_qapp():
        main = QWidget()
        layout = cls(main)
        yield layout
        main.show()
