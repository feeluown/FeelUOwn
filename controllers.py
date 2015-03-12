# -*- coding=utf8 -*-
__author__ = 'cosven'

import sys

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from api import NetEase
from models import DataModel

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

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super(LoginDialog, self).__init__(parent)
        self.username_lable = QLabel()
        self.password_lable = QLabel()
        self.hint_label = QLabel()
        self.username_widget = QLineEdit()
        self.password_widget = QLineEdit()
        self.login_btn = QPushButton()
        self.layout = QVBoxLayout()
        self.ne = NetEase()

        self.set_signal_binding()
        self.set_widgets_prop()
        self.set_layouts_prop()
        self.set_me()

    def set_signal_binding(self):
        self.login_btn.clicked.connect(self.login)

    def login(self, test=False):
        username = str(self.username_widget.text())
        password = str(self.password_widget.text())
        data = self.ne.login(username, password)
        if data['code'] is 200:
            uid = data['profile']['userId']
            self.emit(SIGNAL('loginsuccess'), uid)
            self.close()
        else:
            self.hint_label.setText(u'登陆失败')
        return

    def set_me(self):
        self.setLayout(self.layout)

    def set_widgets_prop(self):
        self.login_btn.setText(u'登陆')

        self.username_lable.setText(u'用户名')
        self.password_lable.setText(u'密码')
        self.username_widget.setPlaceholderText(u'请输入用户名')
        self.password_widget.setPlaceholderText(u'请输入密码')
        self.password_widget.setEchoMode(QLineEdit.Password)

    def set_layouts_prop(self):
        self.layout.addWidget(self.username_lable)
        self.layout.addWidget(self.username_widget)
        self.layout.addWidget(self.password_lable)
        self.layout.addWidget(self.password_widget)
        self.layout.addWidget(self.hint_label)
        self.layout.addWidget(self.login_btn)


class MainWidget(QWidget):
    def __init__(self, parent=None):
        super(MainWidget, self).__init__(parent)
        # set app name before mediaObject was created to avoid phonon problem
        QCoreApplication.setApplicationName("NetEaseMusic-ThirdParty")
        self.ui = UiMainWidget()
        self.ui.setup_ui(self)

        self.player = Phonon.createPlayer(Phonon.MusicCategory)
        self.current_playing_widget = QTableWidget()
        self.sources = []
        self.net_ease = NetEase()
        self.model = DataModel()

        self.set_signal_binding()
        self.set_self_prop()
        # self.load_user_playlist()

    def set_self_prop(self):
        self.resize(800, 480)
        self.setWindowIcon(QIcon('icons/format.ico'))
        qss = "basic.qss"
        with open(qss, "r") as qssfile:
            self.setStyleSheet(qssfile.read())

    def set_signal_binding(self):
        self.ui.info_widget.music_table_widget.itemDoubleClicked.connect(
            self.play_music)
        self.ui.user_widget.list_widget.itemDoubleClicked.connect(
            self.set_tablewidget_playlist)
        self.player.setTickInterval(1000)
        self.player.tick.connect(self.tick)
        self.player.stateChanged.connect(self.state_changed)
        self.player.currentSourceChanged.connect(self.source_changed)
        self.player.aboutToFinish.connect(self.about_to_finish)
        self.ui.play_widget.play_pause_btn.clicked.connect(self.play_pause)
        self.ui.play_widget.last_music_btn.clicked.connect(
            self.last_music)
        self.ui.play_widget.next_music_btn.clicked.connect(
            self.next_music)
        self.ui.play_widget.seek_slider.setMediaObject(self.player)
        self.ui.user_widget.login_btn.clicked.connect(self.show_login_widget)
        self.ui.user_widget.test_btn.clicked.connect(self.login)

    def play_pause(self):
        if self.player.state() == Phonon.PlayingState:
            self.player.pause()
        elif self.player.state() == Phonon.PausedState:
            self.player.play()

    def show_login_widget(self):
        d = LoginDialog(self)
        self.connect(d, SIGNAL('loginsuccess'), self.login)
        d.show()

    def login(self, uid):
        if uid is False:
            uid = '18731323'
        self.ui.user_widget.login_btn.setText(u'当前登陆ID:%s' % uid)
        self.load_user_playlist(uid)

    def load_user_playlist(self, uid):
        playlists = self.net_ease.user_playlist(uid)
        list_widget = self.ui.user_widget.list_widget
        list_widget.clear()
        if playlists is not []:
            for playlist in playlists:
                datamodel = self.model.playlist()
                datamodel = self.model.set_datamodel_from_data(playlist, datamodel)
                item = QListWidgetItem(datamodel['name'])
                list_widget.addItem(item)
                data = QVariant((datamodel, ))
                item.setData(Qt.UserRole, data)
        else:
            print 'network error'

    def set_tablewidget_playlist(self, item):
        data = item.data(Qt.UserRole)
        playlist = data.toPyObject()[0]
        plid = playlist['id']

        data = [{'title': 'way back into love',
                 'url': 'http://m1.music.126.net/KfNqSlCW2eoJ1LXtvpLThg==/1995613604419370.mp3'}]

        # data = self.user.get_music_title_and_url(pid)
        data = self.net_ease.playlist_detail(plid)
        table_widget = self.ui.info_widget.music_table_widget
        # table_widget.clear()
        if data is not []:
            row_count = len(data)
            table_widget.setRowCount(0)
            table_widget.setRowCount(row_count)
            row = 0
            for music in data:
                datamodel = self.model.music()
                datamodel = self.model.set_datamodel_from_data(music, datamodel)
                music_item = QTableWidgetItem(datamodel['name'])
                # to get pure dict from qvariant, so pay attension !
                # stackoverflow: how to get the original python data from qvariant
                music = QVariant((datamodel, ))
                music_item.setData(Qt.UserRole, music)
                table_widget.setItem(row, 0, music_item)
                row += 1
        else:
            print 'network, no music, error plid'

    def play_music(self, item):
        """
        change the current_playlist to the playlist which the item is belong to
        :param item:
        :return:
        """
        self.player.clearQueue()

        music_table = self.ui.info_widget.music_table_widget
        self.current_playing_widget = music_table
        self.sources = []
        for row in range(music_table.rowCount()):
            tmp_item = music_table.item(row, 0)
            data = tmp_item.data(Qt.UserRole)
            music = data.toPyObject()[0]
            self.sources.append(Phonon.MediaSource(music['mp3Url']))
        current_row = music_table.row(item)
        self.player.stop()
        self.player.setCurrentSource(self.sources[current_row])
        self.player.play()

    def tick(self, time):
        time_lcd = self.ui.play_widget.time_lcd
        displayTime = QTime(0, (time / 60000) % 60, (time / 1000) % 60)
        time_lcd.display(displayTime.toString('mm:ss'))

    def state_changed(self, new_state, old_state):
        time_lcd = self.ui.play_widget.time_lcd
        play_pause_btn = self.ui.play_widget.play_pause_btn
        if new_state == Phonon.ErrorState:
            if self.player.errorType() == Phonon.FatalError:
                QMessageBox.warning(self, "Fatal Error",
                        self.player.errorString())
            else:
                QMessageBox.warning(self, "Error",
                        self.player.errorString())
        elif new_state == Phonon.PlayingState:
            play_pause_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        elif new_state == Phonon.StoppedState:
            time_lcd.display("00:00")
        elif new_state == Phonon.PausedState:
            play_pause_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def source_changed(self, source):
        """

        :param source:
        :return:
        """
        # set time lcd
        time_lcd = self.ui.play_widget.time_lcd
        time_lcd.display('00:00')
        # set text label
        row = self.sources.index(source)
        item = self.current_playing_widget.item(row, 0)
        data = item.data(Qt.UserRole)
        music = data.toPyObject()[0]
        text_label = self.ui.play_widget.text_label
        text_label.setText(music['name'])

    def about_to_finish(self):
        index = self.sources.index(self.player.currentSource()) + 1
        if len(self.sources) > index:
            self.player.enqueue(self.sources[index])
        else:
            self.player.enqueue(self.sources[0])

    def last_music(self):
        index = self.sources.index(self.player.currentSource()) - 1
        if index >= 0:
            self.player.setCurrentSource(self.sources[index])
        else:
            self.player.setCurrentSource(self.sources[0])
        self.player.play()

    def next_music(self):
        index = self.sources.index(self.player.currentSource()) + 1
        if len(self.sources) > index:
            self.player.setCurrentSource(self.sources[index])
        else:
            self.player.setCurrentSource(self.sources[0])
        self.player.play()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    musicbox = MainWidget()
    musicbox.show()
    sys.exit(app.exec_())
