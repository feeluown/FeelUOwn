# -*- coding=utf8 -*-
__author__ = 'cosven'

import sys

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest

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
        self.test_btn = QPushButton()
        self.layout = QVBoxLayout()
        self.ne = NetEase()

        self.set_signal_binding()
        self.set_widgets_prop()
        self.set_layouts_prop()
        self.set_me()

    def set_signal_binding(self):
        self.login_btn.clicked.connect(self.login)
        self.test_btn.clicked.connect(self.test)

    def login(self, test=False):
        phone_login = False      # 0: 网易通行证, 1: 手机号登陆
        username = str(self.username_widget.text())     # 包含中文会出错
        password = str(self.password_widget.text())

        # judget if logining by using phone number
        try:
            int(username)
            phone_login = True
        except ValueError:
            pass

        data = self.ne.login(username, password, phone_login)

        # judge if login successfully
        # if not, why
        print data['code'], type(data['code'])
        if data['code'] == 200:
            self.hint_label.setText(u'登陆成功')
            self.emit(SIGNAL('loginsuccess'), data)
            self.close()
        elif data['code'] == 502:
            self.hint_label.setText(u'用户名或密码错误')
        elif data['code'] == 408:
            self.hint_label.setText(u'网络连接超时')

    def test(self):
        self.emit(SIGNAL('logintest'), False)
        self.close()

    def set_me(self):
        self.setObjectName('login_dialog')
        self.setLayout(self.layout)

    def set_widgets_prop(self):
        self.login_btn.setText(u'登陆')
        self.test_btn.setText(u'使用测试账号登录')

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
        self.layout.addStretch(1)
        # self.layout.addWidget(self.test_btn)


class MainWidget(QWidget):
    def __init__(self, parent=None):
        super(MainWidget, self).__init__(parent)
        # set app name before mediaObject was created to avoid phonon problem
        QCoreApplication.setApplicationName("NetEaseMusic-ThirdParty")
        self.ui = UiMainWidget()
        self.ui.setup_ui(self)

        self.player = Phonon.createPlayer(Phonon.MusicCategory)
        self.net_manager = QNetworkAccessManager()
        self.searchShortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.sources = []
        self.net_ease = NetEase()
        self.model = DataModel()

        self.set_self_prop()
        self.set_signal_binding()
        self.init_table_widget()
        # self.load_user_playlist()

    def init_table_widget(self):
        self.ui.info_widget.music_table_widget.close()
        self.ui.info_widget.music_search_widget.close()
        self.ui.info_widget.current_playing_widget.close()

    def set_self_prop(self):
        self.setWindowTitle('NetEaseMusic For Linux')
        self.setObjectName('main_widget')
        self.resize(960, 580)
        self.setWindowIcon(QIcon('icons/format.ico'))

    def paintEvent(self, QPaintEvent):
        """
        self is derived from QWidget, Stylesheets don't work unless \
        paintEvent is reimplemented.
        at the same time, if self is derived from QFrame, this isn't needed.
        """
        option = QStyleOption()
        option.init(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

    def set_signal_binding(self):
        self.searchShortcut.activated.connect(self.set_search_focus)
        self.ui.info_widget.music_table_widget.itemDoubleClicked.connect(
            self.play_music)
        self.ui.info_widget.music_search_widget.itemDoubleClicked.connect(
            self.play_search_music)
        self.ui.info_widget.current_playing_widget.itemDoubleClicked.connect(
            self.play_current_music)
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
        self.ui.play_widget.login_btn.clicked.connect(self.show_login_widget)
        self.ui.play_widget.search_btn.clicked.connect(self.search)
        self.ui.play_widget.search_edit.returnPressed.connect(self.search)
        self.ui.play_widget.show_current_list.clicked.connect(self.show_current_playing_widget)

    def play_current_music(self, item):
        current_playing = self.ui.info_widget.current_playing_widget
        current_row = current_playing.row(item)
        self.player.stop()
        self.player.setCurrentSource(self.sources[current_row])
        self.player.play()

    def set_search_focus(self):
        self.ui.play_widget.search_edit.setFocus(True)

    def play_pause(self):
        if self.player.state() == Phonon.PlayingState:
            self.player.pause()
        elif self.player.state() == Phonon.PausedState:
            self.player.play()

    def show_login_widget(self):
        d = LoginDialog(self)
        self.connect(d, SIGNAL('loginsuccess'), self.login)
        self.connect(d, SIGNAL('logintest'), self.login)
        d.show()

    def login(self, data):
        if data is False:
            uid = '18731323'
        else:
            uid = data['account']['id']
            try:
                self.ui.status.showMessage(u'准备加载头像')
                avatarUrl = data['profile']['avatarUrl']
                self.net_manager.finished.connect(self.avatar_load_finish)
                self.load_user_playlist(uid)
                self.net_manager.get(QNetworkRequest(QUrl(avatarUrl)))
                return
            except:
                self.ui.status.showMessage(u'加载头像失败', 1000)
        self.load_user_playlist(uid)

    def load_user_playlist(self, uid):
        playlists = self.net_ease.user_playlist(uid)
        list_widget = self.ui.user_widget.list_widget
        list_widget.clear()
        if playlists is not []:
            for playlist in playlists:
                datamodel = self.model.playlist()
                datamodel = self.model.set_datamodel_from_data(playlist, datamodel)
                item = QListWidgetItem(QIcon('icons/playlist_1.png'), datamodel['name'])
                list_widget.addItem(item)
                data = QVariant((datamodel, ))
                item.setData(Qt.UserRole, data)
        else:
            print 'network error'

    def search(self):
        search_edit = self.ui.play_widget.search_edit
        text= search_edit.text()
        self.ui.status.showMessage(u'正在搜索: ' + text)
        if text != '':
            s = unicode(text.toUtf8(), 'utf8', 'ignore')
            data = self.net_ease.search(s.encode('utf8'))
            songs = list()
            if data['result']['songCount'] != 0:
                songs = data['result']['songs']
                length = len(songs)
                self.set_search_widget(songs)
                self.ui.status.showMessage(u'搜索到 ' + str(length) + u' 首 ' +
                                           text +u' 相关歌曲', 1000)
                return
            else:
                self.ui.status.showMessage(u'很抱歉，没有找到相关歌曲', 1000)
                return

    def set_search_widget(self, songs):
        self.init_table_widget()
        music_search = self.ui.info_widget.music_search_widget
        music_search.show()

        row_count = len(songs)
        music_search.setRowCount(0)
        music_search.setRowCount(row_count)
        row = 0
        for song in songs:
            datamodel = self.model.search_result()
            datamodel = self.model.set_datamodel_from_data(song, datamodel)
            musicItem = QTableWidgetItem(datamodel['name'])
            albumItem = QTableWidgetItem(datamodel['album']['name'])
            if len(song['artists']) > 0:
                artistName = song['artists'][0]['name']
            artistItem = QTableWidgetItem(artistName)

            music = QVariant((datamodel, ))
            musicItem.setData(Qt.UserRole, music)

            musicItem.setTextAlignment(Qt.AlignCenter)
            artistItem.setTextAlignment(Qt.AlignCenter)
            albumItem.setTextAlignment(Qt.AlignCenter)

            music_search.setItem(row, 0, musicItem)
            music_search.setItem(row, 1, artistItem)
            music_search.setItem(row, 2, albumItem)
            row += 1


    def set_tablewidget_playlist(self, item):
        self.init_table_widget()
        table_widget = self.ui.info_widget.music_table_widget
        table_widget.show()

        data = item.data(Qt.UserRole)
        playlist = data.toPyObject()[0]
        plid = playlist['id']

        data = [{'title': 'way back into love',
                 'url': 'http://m1.music.126.net/KfNqSlCW2eoJ1LXtvpLThg==/1995613604419370.mp3'}]

        # data = self.user.get_music_title_and_url(pid)
        data = self.net_ease.playlist_detail(plid)
        # table_widget.clear()
        if data is not []:
            row_count = len(data)
            table_widget.setRowCount(0)
            table_widget.setRowCount(row_count)
            row = 0
            for music in data:
                datamodel = self.model.music()
                datamodel = self.model.set_datamodel_from_data(music, datamodel)
                musicItem = QTableWidgetItem(datamodel['name'])
                musicItem = QTableWidgetItem(datamodel['name'])
                albumItem = QTableWidgetItem(datamodel['album']['name'])
                if len(datamodel['artists']) > 0:
                    artistName = datamodel['artists'][0]['name']
                artistItem = QTableWidgetItem(artistName)
                # to get pure dict from qvariant, so pay attension !
                # stackoverflow: how to get the original python data from qvariant
                music = QVariant((datamodel, ))
                musicItem.setData(Qt.UserRole, music)

                musicItem.setTextAlignment(Qt.AlignCenter)
                artistItem.setTextAlignment(Qt.AlignCenter)
                albumItem.setTextAlignment(Qt.AlignCenter)

                table_widget.setItem(row, 0, musicItem)
                table_widget.setItem(row, 1, artistItem)
                table_widget.setItem(row, 2, albumItem)
                row += 1
        else:
            print 'network, no music, error plid'

    def play_search_music(self, item):
        music_search = self.ui.info_widget.music_search_widget
        current_playing = self.ui.info_widget.current_playing_widget
        current_row = music_search.row(item)
        item = music_search.item(current_row, 0)    # only item 0 contain url
        data = item.data(Qt.UserRole)
        song = data.toPyObject()[0]
        musics = self.net_ease.song_detail(song['id'])
        source = Phonon.MediaSource(musics[0]['mp3Url'])
        curr = self.player.currentSource()
        # if str(curr.url().toString()) != '':
        #     index = self.sources.index(curr)
        #     self.sources.insert(index + 1, source)
        # else:
        self.sources.append(source)
        rowCount = current_playing.rowCount()
        current_playing.setRowCount(rowCount + 1)

        datamodel = self.model.music()
        datamodel = self.model.set_datamodel_from_data(musics[0], datamodel)

        musicItem = QTableWidgetItem(datamodel['name'])
        albumItem = QTableWidgetItem(datamodel['album']['name'])
        if len(datamodel['artists']) > 0:
            artistName = datamodel['artists'][0]['name']
        artistItem = QTableWidgetItem(artistName)
        # to get pure dict from qvariant, so pay attension !
        # stackoverflow: how to get the original python data from qvariant
        music = QVariant((datamodel, ))
        musicItem.setData(Qt.UserRole, music)

        musicItem.setTextAlignment(Qt.AlignCenter)
        artistItem.setTextAlignment(Qt.AlignCenter)
        albumItem.setTextAlignment(Qt.AlignCenter)

        current_playing.setItem(rowCount, 0, musicItem)
        current_playing.setItem(rowCount, 1, artistItem)
        current_playing.setItem(rowCount, 2, albumItem)

        self.player.stop()
        self.player.setCurrentSource(source)
        self.player.play()


    def play_music(self, item):
        """
        change the current_playlist to the playlist which the item is belong to
        :param item:
        :return:
        """

        music_table = self.ui.info_widget.music_table_widget
        current_row = music_table.row(item)
        data = item.data(Qt.UserRole)
        datamodel = data.toPyObject()[0]

        current_playing = self.ui.info_widget.current_playing_widget
        rowCount = current_playing.rowCount()
        current_playing.setRowCount(rowCount + 1)

        musicItem = QTableWidgetItem(datamodel['name'])
        albumItem = QTableWidgetItem(datamodel['album']['name'])
        if len(datamodel['artists']) > 0:
            artistName = datamodel['artists'][0]['name']
        artistItem = QTableWidgetItem(artistName)

        source = Phonon.MediaSource(datamodel['mp3Url'])
        curr = self.player.currentSource()
        # if str(curr.url().toString()) != '':
        #     index = self.sources.index(curr)
        #     self.sources.insert(index + 1, source)
        # else:
        self.sources.append(source)
        # to get pure dict from qvariant, so pay attension !
        # stackoverflow: how to get the original python data from qvariant
        music = QVariant((datamodel, ))
        musicItem.setData(Qt.UserRole, music)

        musicItem.setTextAlignment(Qt.AlignCenter)
        artistItem.setTextAlignment(Qt.AlignCenter)
        albumItem.setTextAlignment(Qt.AlignCenter)

        current_playing.setItem(rowCount, 0, musicItem)
        current_playing.setItem(rowCount, 1, artistItem)
        current_playing.setItem(rowCount, 2, albumItem)

        self.player.stop()
        self.player.setCurrentSource(source)
        self.player.play()

    def tick(self, time):
        time_lcd = self.ui.play_widget.time_lcd
        displayTime = QTime(0, (time / 60000) % 60, (time / 1000) % 60)
        time_lcd.setText(displayTime.toString('mm:ss'))

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
            play_pause_btn.setIcon(QIcon('icons/play_hover.png'))
        elif new_state == Phonon.StoppedState:
            time_lcd.setText("00:00")
        elif new_state == Phonon.PausedState:
            play_pause_btn.setIcon(QIcon('icons/pause.png'))

    def source_changed(self, source):
        """

        :param source:
        :return:
        """
        # set time lcd
        time_lcd = self.ui.play_widget.time_lcd
        time_lcd.setText('00:00')
        # set text label
        current_playing = self.ui.info_widget.current_playing_widget
        row = self.sources.index(source)
        item = current_playing.item(row, 0)
        current_playing.scrollToItem(item)
        data = item.data(Qt.UserRole)
        music = data.toPyObject()[0]
        text_label = self.ui.play_widget.text_label
        text_label.setText(music['name'])
        self.net_manager.get(QNetworkRequest(QUrl(music['album']['picUrl'])))

    def albumimg_load_finish(self, res):
        img_label = self.ui.play_widget.img_label
        img = QImage()
        img.loadFromData(res.readAll())
        img_label.setPixmap(QPixmap(img).scaled(50, 50))

    def avatar_load_finish(self, res):
        login_btn = self.ui.play_widget.login_btn
        img = QImage()
        img.loadFromData(res.readAll())
        login_btn.setIcon(QIcon(QPixmap(img).scaled(40, 40)))
        self.net_manager.finished.disconnect(self.avatar_load_finish)
        self.net_manager.finished.connect(self.albumimg_load_finish)
        self.ui.status.showMessage(u'加载头像成功', 1000)

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

    def show_current_playing_widget(self):
        self.init_table_widget()
        self.ui.info_widget.current_playing_widget.show()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    musicbox = MainWidget()
    musicbox.show()
    sys.exit(app.exec_())
