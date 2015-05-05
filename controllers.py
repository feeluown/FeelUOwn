# -*- coding:utf8 -*-
__author__ = 'cosven'

import sys

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest

from api import NetEase
from models import DataModel

from widgets.login_dialog import LoginDialog

from PyQt4.phonon import Phonon

from views import UiMainWidget
from player import Player


class MainWidget(QWidget):
    def __init__(self, parent=None):
        super(MainWidget, self).__init__(parent)
        # set app name before mediaObject was created to avoid phonon problem
        QCoreApplication.setApplicationName("NetEaseMusic-ThirdParty")
        self.ui = UiMainWidget()
        self.ui.setup_ui(self)

        self.audioOutput = Phonon.AudioOutput(Phonon.MusicCategory, self)
        self.player = Player(self)
        Phonon.createPath(self.player, self.audioOutput)

        self.net_manager = QNetworkAccessManager()
        self.searchShortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.sources = []
        self.net_ease = NetEase()
        self.model = DataModel()

        self.user = {
            'mode': 'normal',
            'uid': 18731323,
            'is_login': False,
            'favorite_pid': 0
        }  # uid, is_login, favorite_pid

        self.set_self_prop()
        self.set_signal_binding()
        self.init_table_widget()

    def normal_mode(func):
        def wrapper(*args):
            this = args[0]
            this.ui.status.showMessage(u'切换到正常模式', 4000)
            this.user['mode'] = 'normal'
            func(*args)
        return wrapper

    def init_table_widget(self):
        self.ui.info_widget.music_table_widget.close()
        self.ui.info_widget.music_search_widget.close()
        self.ui.info_widget.current_playing_widget.close()

    def set_self_prop(self):
        self.user['is_login'] = False
        self.hide_widget_when_unverificated()

        self.setWindowTitle('NetEaseMusic For Linux - ThirdParty')
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
            self.play_userplaylist_music)
        self.ui.info_widget.music_search_widget.itemDoubleClicked.connect(
            self.play_search_music)
        self.ui.info_widget.current_playing_widget.itemDoubleClicked.connect(
            self.play_currentplayinglist_music)
        self.ui.user_widget.list_widget.itemDoubleClicked.connect(
            self.play_userlist)
        self.ui.user_widget.list_widget.itemClicked.connect(
            self.set_tablewidget_userplaylist)
        self.ui.user_widget.radio_btn.clicked.connect(self.play_radio)
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
        self.ui.play_widget.show_current_list.clicked.connect(self.set_tablewidget_currentplayinglist)
        self.ui.play_widget.help_btn.clicked.connect(self.show_help_info)
        self.ui.play_widget.add_to_favorite.clicked.connect(self.set_music_favorite)
        self.net_manager.finished.connect(self.albumimg_load_finish)

    def play_radio(self):
        self.ui.status.showMessage(u'正在获取新的电台音乐...', 3000)
        data = self.net_ease.getRadioMusic()
        if data['code'] == 200:
            tracks = data['data']

            current_playing = self.ui.info_widget.current_playing_widget
            # 清空当前播放列表
            self.sources = []
            current_playing.setRowCount(0)

            for track in tracks:
                datamodel = self.model.music()
                music_model = self.model.set_datamodel_from_data(track, datamodel)

                mid = music_model['id']
                self.add_music_to_sources(mid)
                self.add_music_to_currentplayinglist(music_model)

            # 播放列表第一首歌
            item = current_playing.item(0, 0)
            self.play_currentplayinglist_music(item)

            # 显示当前播放列表
            self.init_table_widget()
            current_playing.show()

            # change play mode
            self.user['mode'] = 'radio'
            self.ui.status.showMessage(u'radio模式', 4000)

        elif data['code'] == 408:
            self.ui.status.showMessage(u'未知错误', 5000)

    def set_music_favorite(self):
        # 得到 favorite playlist id
        pid = self.user['favorite_pid']
        mid = self.player.getCurrentMusicId()
        add_to_favorite_btn = self.ui.play_widget.add_to_favorite
        if mid == 0:
            self.ui.status.showMessage(u'请先播放音乐')
            return
        else:
            op = ''
            # 点击之后，button会马上变状态
            if add_to_favorite_btn.isChecked() == False:
                op = 'del'
            else:
                op = 'add'
            data = self.net_ease.setMusicToPlaylist(mid, pid, op)
            if data['code'] == 200:
                if op == 'add':
                    self.ui.status.showMessage(u'加入喜欢列表成功', 3000)
                    add_to_favorite_btn.setChecked(True)
                elif op == 'del':
                    self.ui.status.showMessage(u'从喜欢列表中删除成功', 3000)
                    add_to_favorite_btn.setChecked(False)
            elif data['code'] == 408:
                self.ui.status.showMessage(u'网络连接失败')
            else:
                self.ui.status.showMessage(u'未知错误')
            return
    
    def isMusicInPlaylist(self, mid, pid):
        tracks = self.net_ease.playlist_detail(pid)
        for track in tracks:
            if track['id'] == mid:
                return True
        return False
    
    def show_help_info(self):
        with open('data/help.html') as f:
            text = f.read()
            text = text.decode('utf8')
            message = QMessageBox(self)
            message.setText(text)
            message.setTextFormat(Qt.RichText)
            message.show()

    @normal_mode
    def play_userlist(self, item):
        data = item.data(Qt.UserRole)
        # playlist = data.toPyObject()[0]
        playlist = data
        pid = playlist['id']
        res = self.net_ease.playlist_detail(pid)
        # table_widget.clear()
        if res is not []:
            current_playing = self.ui.info_widget.current_playing_widget

            # 清空当前播放列表
            self.sources = []
            current_playing.setRowCount(0)

            # 把歌曲全部加入列表
            for music in res:
                datamodel = self.model.music()
                music_model = self.model.set_datamodel_from_data(music, datamodel)

                mid = music_model['id']
                self.add_music_to_sources(mid)
                self.add_music_to_currentplayinglist(music_model)

            # 显示当前播放列表
            self.init_table_widget()
            current_playing.show()

            # 播放列表第一首歌
            item = current_playing.item(0, 0)
            self.play_currentplayinglist_music(item)
        else:
            # 具体详细提示信息需要根据后台返回进行判断
            # 以后可以进行优化
            self.ui.status.showMessage(u'当前列表为空', 3000)

    def play_currentplayinglist_music(self, item):
        current_playing = self.ui.info_widget.current_playing_widget
        current_row = current_playing.row(item)
        self.player.setCurrentMusicId(self.sources[current_row])

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
        d.show()

    def ready_load_avatar(self, avatarUrl):
        self.ui.status.showMessage(u'准备加载头像', 4000)
        self.net_manager.finished.disconnect(self.albumimg_load_finish)
        self.net_manager.finished.connect(self.avatar_load_finish)
        self.net_manager.get(QNetworkRequest(QUrl(avatarUrl)))

    def hide_widget_when_unverificated(self):
        self.ui.play_widget.add_to_favorite.close()
        self.ui.user_widget.radio_btn.close()

    def show_widget_when_verificated(self):
        self.ui.play_widget.add_to_favorite.show()
        self.ui.user_widget.radio_btn.show()

    def login(self, data):
        uid = data['account']['id']
        self.user['id'] = uid
        self.user['is_login'] = True
        self.show_widget_when_verificated()

        self.load_user_playlist(uid)
        try:
            avatarUrl = data['profile']['avatarUrl']
            self.ready_load_avatar(avatarUrl)
            return
        except:
            self.ui.status.showMessage(u'加载头像失败', 4000)

    def load_user_playlist(self, uid):
        playlists = self.net_ease.user_playlist(uid)
        list_widget = self.ui.user_widget.list_widget
        list_widget.clear()
        if playlists is not []:
            for playlist in playlists:
                if playlist['specialType'] == 5:
                    self.user['favorite_pid'] = playlist['id']
                datamodel = self.model.playlist()
                datamodel = self.model.set_datamodel_from_data(playlist, datamodel)
                item = QListWidgetItem(QIcon('icons/playlist_1.png'), datamodel['name'])
                list_widget.addItem(item)
                # data = QVariant((datamodel, ))
                data = datamodel
                item.setData(Qt.UserRole, data)

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
                self.set_tablewidget_search(songs)
                self.ui.status.showMessage(u'搜索到 ' + str(length) + u' 首 ' +
                                           text +u' 相关歌曲', 2000)
                return
            else:
                self.ui.status.showMessage(u'很抱歉，没有找到相关歌曲', 2000)
                return

    def set_tablewidget_search(self, songs):
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
            music_search.setRowItems(datamodel, row)
            row += 1


    def set_tablewidget_userplaylist(self, item):
        self.init_table_widget()
        table_widget = self.ui.info_widget.music_table_widget
        table_widget.show()

        data = item.data(Qt.UserRole)
        # playlist = data.toPyObject()[0]
        playlist = data
        plid = playlist['id']

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
                
                table_widget.setRowItems(datamodel, row)
                row += 1

    def play_specific_music(self, mid):
        """
        播放一首特定的歌曲(通常是搜索到的歌曲和用户列表中的歌曲)
        :param source: phonon media source
        """
        self.player.setCurrentMusicId(mid)

    def add_music_to_sources(self, mid):
        self.sources.append(mid)

    def add_music_to_currentplayinglist(self, music_model):
        """向当前播放列表中加入一首歌
        1. 向sources列表中加入相应的 music id
        2. 更新当前播放列表（current_play_widget）
        :param music_model: music 的标准数据model
        """
        current_playing = self.ui.info_widget.current_playing_widget
        rowCount = current_playing.rowCount()
        current_playing.setRowCount(rowCount + 1)

        current_playing.setRowItems(music_model, rowCount)

    @normal_mode
    def play_search_music(self, item):
        music_search = self.ui.info_widget.music_search_widget
        current_row = music_search.row(item)
        item = music_search.item(current_row, 0)    # only item 0 contain url
        data = item.data(Qt.UserRole)
        # song = data.toPyObject()[0]
        song = data
        musics = self.net_ease.song_detail(song['id'])
        datamodel = self.model.music()
        music_model = self.model.set_datamodel_from_data(musics[0], datamodel)
        mid = song['id']
        self.add_music_to_sources(mid)
        self.add_music_to_currentplayinglist(music_model)
        self.play_specific_music(mid)

    @normal_mode
    def play_userplaylist_music(self, item):
        music_table = self.ui.info_widget.music_table_widget
        current_row = music_table.row(item)
        data = item.data(Qt.UserRole)
        # music_model = data.toPyObject()[0]
        music_model = data

        mid = music_model['id']
        self.add_music_to_sources(mid)

        self.add_music_to_currentplayinglist(music_model)
        self.play_specific_music(mid)

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
            play_pause_btn.setIcon(QIcon('icons/pause_hover.png'))

    def source_changed(self, source):
        """
        """
        # set time lcd
        time_lcd = self.ui.play_widget.time_lcd
        time_lcd.setText('00:00')

        # set text label
        current_playing = self.ui.info_widget.current_playing_widget

        mid = self.player.getCurrentMusicId()
        row = self.sources.index(mid)

        if self.user['is_login'] == True:
            add_to_favorite_btn = self.ui.play_widget.add_to_favorite
            if self.isMusicInPlaylist(mid, self.user['favorite_pid']):
                add_to_favorite_btn.setChecked(True)
            else:
                add_to_favorite_btn.setChecked(False)

        item = current_playing.item(row, 0)
        current_playing.scrollToItem(item)
        current_playing.setCurrentItem(item)

        data = item.data(Qt.UserRole)
        # music = data.toPyObject()[0]
        music = data
        text_label = self.ui.play_widget.text_label
        text_label.setText(music['name'])
        self.ui.status.showMessage(u'正在播放 %s' % music['name'])
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
        self.ui.status.showMessage(u'加载头像成功', 2000)

    def about_to_finish(self):
        mid = self.set_next_music()
        if mid:
            self.player.addMusicToPlay(mid)
            return
        return

    def last_music(self):
        try:
            index = self.sources.index(self.player.getCurrentMusicId()) - 1
        except ValueError:
            self.ui.status.showMessage(u'当前播放列表为空', 2000)
            return
        if index >= 0:
            self.player.setCurrentMusicId(self.sources[index])
        else:
            self.player.setCurrentMusicId(self.sources[0])

    def set_next_music(self):
        """
        判断下首音乐, 设置mid, 或者play_radio
        """
        index = self.sources.index(self.player.getCurrentMusicId()) + 1
        if len(self.sources) > index:
            mid = self.sources[index]
            self.ui.status.showMessage(u'下一首音乐的ID: ' + str(mid), 3000)
            return mid
        else:
            if self.user['mode'] == 'normal':
                mid = self.sources[0]
                self.ui.status.showMessage(u'下一首音乐的ID: ' + str(mid), 3000)
                return mid
            else:   # radio mode
                self.play_radio()
                return 0

    def next_music(self):
        try:
            index = self.sources.index(self.player.getCurrentMusicId()) + 1
        except ValueError:
            self.ui.status.showMessage(u'当前播放列表为空', 2000)
            return
        mid = self.set_next_music()
        if mid:
            self.player.setCurrentMusicId(mid)

    def set_tablewidget_currentplayinglist(self):
        """
        显示当前播放列表，隐藏其他tablewidget
        """
        self.init_table_widget()
        self.ui.info_widget.current_playing_widget.show()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    musicbox = MainWidget()
    musicbox.show()
    sys.exit(app.exec_())
