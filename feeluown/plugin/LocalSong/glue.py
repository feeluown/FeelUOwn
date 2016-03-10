# -*- coding: utf-8 -*-


from feeluown.controller_api import ControllerApi
from feeluown.logger import LOG
from feeluown.widgets.playlist_widget import _BaseItem
from feeluown.view_api import ViewOp

from .parse import Parser


class LocalSongItem(_BaseItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.set_btn_text(u'本地歌曲')
        self.set_icon_text(u'◈')


class Ui(object):
    def __init__(self):
        self.local_song_item = LocalSongItem()

        self.setup_ui()
        self.alias()

    def setup_ui(self):
        ViewOp.ui.LEFT_WIDGET.central_widget.recommend_list_widget.layout()\
            .addWidget(self.local_song_item)

    def alias(self):
        ViewOp.ui.LOCAL_SONG_ITEM = self.local_song_item


class Glue(object):
    def __init__(self):
        self.local_song_parser = Parser()
        self.ui = Ui()

        self._songs = []
        self.bind_signal()

    def get_songs(self, path):
        LOG.info('scaning local songs.')
        song_paths = self.local_song_parser.scan(path)
        for song_path in song_paths:
            song = self.local_song_parser.analysis(song_path)
            self._songs.append(song)

    def bind_signal(self):
        ViewOp.ui.LOCAL_SONG_ITEM.signal_text_btn_clicked.connect(
            self.show_songs)

    def show_songs(self):
        ViewOp.ui.WEBVIEW.load_songs(self._songs)
        ControllerApi.state['current_pid'] = 0
