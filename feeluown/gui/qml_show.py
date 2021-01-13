from PyQt5.QtCore import QUrl
from PyQt5.QtQuick import QQuickView
from PyQt5.QtWidgets import QWidget, QVBoxLayout


def qml_path():
    import os

    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'qml/img_list.qml'
    )


class QmlWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)

        self._view = QQuickView()
        container = self.createWindowContainer(self._view)
        self._view.setSource(QUrl(qml_path()))
        self._layout = QVBoxLayout(self)
        self._layout.addWidget(container)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    widget = QmlWidget(None)
    widget.show()
    widget.resize(600, 400)
    app.exec()
