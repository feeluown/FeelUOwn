# -*- coding=utf8 -*-
__author__ = 'cosven'

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.phonon import Phonon

from higherapi import User


class UserWidget(QWidget):
    def __init__(self):
        super(UserWidget, self).__init__()
        self.text_label = QLabel(u'用戶名')
        self.layout = QVBoxLayout()

        self.set_widgets_prop()
        self.set_layouts_prop()
        self.set_me()

    def set_me(self):
        self.setLayout(self.layout)

    def set_widgets_prop(self):
        self.text_label.setAlignment(Qt.AlignCenter)

    def set_layouts_prop(self):
        self.layout.addWidget(self.text_label)


class PlayWidget(QWidget):
    def __init__(self):
        super(PlayWidget, self).__init__()
        self.last_music_btn = QPushButton(u"上一首")
        self.next_music_btn = QPushButton(u"下一首")
        self.play_pause_btn = QPushButton(u"播放")
        self.layout = QHBoxLayout()

        self.play_pause_btn.clicked.connect(self.play)

        self.set_me()
        self.set_layouts_prop()

    def set_me(self):
        self.setLayout(self.layout)

    def set_widgets_size(self):
        pass

    def set_layouts_prop(self):
        self.layout.addWidget(self.last_music_btn)
        self.layout.addWidget(self.play_pause_btn)
        self.layout.addWidget(self.next_music_btn)

    def play(self):
        self.emit(SIGNAL('play'))

class InfoWidget(QWidget):
    def __init__(self):
        super(InfoWidget, self).__init__()
        self.layout = QVBoxLayout()
        self.music_table_widget = QTableWidget(1, 1)

        self.music_table_widget.itemDoubleClicked.connect(self.play_music)

        self.set_me()
        self.set_widgets_prop()
        self.set_widgets_size()
        self.set_layouts_prop()

    def set_me(self):
        self.setLayout(self.layout)

    def set_widgets_size(self):
        pass

    def set_widgets_prop(self):
        self.music_table_widget.horizontalHeader().setResizeMode(0, QHeaderView.Stretch)
        self.music_table_widget.setHorizontalHeaderLabels([u'歌曲名'])
        self.music_table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def set_layouts_prop(self):
        self.layout.addWidget(self.music_table_widget)

    def play_music(self, item):
        data = item.data(Qt.UserRole)
        music = data.toPyObject()[0]
        # emit signal
        self.emit(SIGNAL('play'), music['url'])

class MainWidget(QWidget):
    def __init__(self):
        super(MainWidget, self).__init__()
        self.info_widget = InfoWidget()
        self.user_widget = UserWidget()
        self.play_widget = PlayWidget()
        self.info_layout = QVBoxLayout()
        self.user_layout = QVBoxLayout()
        self.play_layout = QHBoxLayout()
        self.top_container = QHBoxLayout()
        self.bottom_container = QHBoxLayout()
        self.layout = QVBoxLayout()
        self.user = User()
        self.player = Phonon.createPlayer(Phonon.MusicCategory)

        self.connect(self.info_widget, SIGNAL('play'), self.play)
        self.connect(self.play_widget, SIGNAL('play'), self.play)

        self.set_me()
        self.set_widgets_size()
        self.set_layouts_prop()
        self.load_favorite_music_list()

    def set_me(self):
        self.setLayout(self.layout)
        self.resize(800, 480)

    def set_widgets_size(self):
        self.play_widget.setFixedHeight(100)
        self.user_widget.setFixedWidth(200)

    def set_layouts_prop(self):
        self.info_layout.addWidget(self.info_widget)
        self.user_layout.addWidget(self.user_widget)
        self.play_layout.addWidget(self.play_widget)
        self.top_container.addLayout(self.user_layout)
        self.top_container.addLayout(self.info_layout)
        self.bottom_container.addLayout(self.play_layout)
        self.layout.addLayout(self.top_container)
        self.layout.addLayout(self.bottom_container)

    def load_favorite_music_list(self):
        from setting import username, password
        self.user.login(username, password)
        pid = self.user.get_favorite_playlist_id()
        # data = [{'title': 'way back into love',
        #          'url': 'http://m1.music.126.net/KfNqSlCW2eoJ1LXtvpLThg==/1995613604419370.mp3'}]

        data = self.user.get_music_title_and_url(pid)
        table_widget = self.info_widget.music_table_widget
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

    def load_userinfo(self):
        pass

    def play(self, url=None):
        if url is not None:
            # double click one item
            self.player.stop()
            self.player.setCurrentSource(Phonon.MediaSource(url))
            self.player.play()
            self.play_widget.play_pause_btn.setText(u'暫停')
        else:
            # click play_pause button
            # do not use 'is' to do the judgement
            if self.player.state() == Phonon.PlayingState:    # play state
                print 'pause'
                self.player.pause()
                self.play_widget.play_pause_btn.setText(u'播放')
            elif self.player.state() == Phonon.PausedState:    # pause state
                print 'play'
                self.player.play()
                self.play_widget.play_pause_btn.setText(u'暫停')
            else:   # other state
                print 'no music'

