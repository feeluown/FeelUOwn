# -*- coding=utf8 -*-
__author__ = 'cosven'

import sys

from PyQt4.QtGui import *
from PyQt4.QtCore import *

try:
    from PyQt4.phonon import Phonon
except ImportError:
    app = QApplication(sys.argv)
    QMessageBox.critical(None, "NetEaseMusic-ThirdParty",
            "Your Qt installation does not have Phonon support.",
            QMessageBox.Ok | QMessageBox.Default,
            QMessageBox.NoButton)
    sys.exit(1)

from views import UiMainWidget

class MainWidget(QWidget):
    def __init__(self, parent=None):
        super(MainWidget, self).__init__(parent)
        self.ui = UiMainWidget()
        self.ui.setup_ui(self)
        # before mediaObject was created
        QCoreApplication.setApplicationName("NetEaseMusic-ThirdParty");
        self.player = Phonon.createPlayer(Phonon.MusicCategory)

        self.set_signal_binding()
        self.set_self_prop()
        self.load_favorite_music_list()

    def set_self_prop(self):
        self.resize(800, 480)

    def set_signal_binding(self):
        self.ui.info_widget.music_table_widget.itemDoubleClicked.connect(
            self.play_music)

    def load_favorite_music_list(self):
        # from setting import username, password
        # self.user.login(username, password)
        # pid = self.user.get_favorite_playlist_id()
        data = [{'title': 'way back into love',
                 'url': 'http://m1.music.126.net/KfNqSlCW2eoJ1LXtvpLThg==/1995613604419370.mp3'}]

        # data = self.user.get_music_title_and_url(pid)
        table_widget = self.ui.info_widget.music_table_widget
        row_count = len(data)
        table_widget.setRowCount(row_count)
        row = 0
        for music in data:
            music_item = QTableWidgetItem(music['title'])
            # to get pure dict from qvariant, so pay attension !
            # stackoverflow: how to get the original python data from qvariant
            music = QVariant((music, ))
            music_item.setData(Qt.UserRole, music)
            table_widget.setItem(row, 0, music_item)
            row += 1

    def play_music(self, item):
        print 'play'
        data = item.data(Qt.UserRole)
        music = data.toPyObject()[0]
        # emit signal
        self.player.setCurrentSource(Phonon.MediaSource(music['url']))
        self.player.play()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    musicbox = MainWidget()
    musicbox.show()
    sys.exit(app.exec_())
