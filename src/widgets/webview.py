# -*- coding: utf8 -*-
import json

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebKitWidgets import QWebView
from PyQt5.QtWebKit import QWebSettings

from constants import MODE, PUBLIC_PATH, DEBUG, HTML_PATH

from base.logger import LOG


class WebView(QWebView):
    """

    """

    """这个类的实例可能发出的信号。（也就是说，controller只能绑定这些信号，其他信号尽量不要绑定）
    loadProgress(int)
    """
    signal_play = pyqtSignal([int])
    signal_play_songs = pyqtSignal([list])
    signal_search_artist = pyqtSignal([int])
    signal_search_album = pyqtSignal([int])
    signal_play_mv = pyqtSignal([int])

    def __init__(self, parent=None):
        super().__init__(parent)

        self.init()

        self.js_queue = []  # 保存页面load完，要执行的js代码

    def init(self):
        self.init_singal_binding()
        if MODE == DEBUG:
            self.settings().setAttribute(QWebSettings.DeveloperExtrasEnabled, True)
        else:
            self.setContextMenuPolicy(Qt.NoContextMenu)

    def init_singal_binding(self):
        self.loadFinished.connect(self.on_load_finished)
        self.linkClicked.connect(self.on_link_clicked)

    def load_css(self):
        all_css = QFileInfo(PUBLIC_PATH + 'all.css').absoluteFilePath()
        self.settings().setUserStyleSheetUrl(QUrl.fromLocalFile(all_css))

    @pyqtSlot(QUrl)
    def on_link_clicked(self, url):
        print(url)
        return False

    @pyqtSlot()
    def on_load_finished(self):
        self.page().mainFrame().addToJavaScriptWindowObject('js_python', self)
        for js_code in self.js_queue:
            self.page().mainFrame().evaluateJavaScript(js_code)
        self.js_queue.clear()

    """给js调用的函数, 需要加上pyqtSlot装饰器
    """
    @pyqtSlot(int)
    def play(self, mid):
        """
        """
        LOG.debug("play music: the music_id is " + str(mid))
        self.signal_play.emit(mid)

    @pyqtSlot(int)
    def play_mv(self, mvid):
        LOG.debug("play mv: the mv_id is " + str(mvid))
        self.signal_play_mv.emit(mvid)

    @pyqtSlot(str)
    def play_songs(self, songs_str):
        LOG.debug("play songs")
        songs = json.loads(songs_str)
        tracks = songs['tracks']
        self.signal_play_songs.emit(tracks)

    @pyqtSlot(int)
    def search_artist(self, aid):
        LOG.debug("search artist info, the artist id is: " + str(aid))
        self.signal_search_artist.emit(aid)

    @pyqtSlot(int)
    def search_album(self, aid):
        LOG.debug("search album info, the album id is: " + str(aid))
        self.signal_search_album.emit(aid)

    def run_js_interface(self, data=None):
        """

        :param data: string, such as json.dumps(dict)
        :return:
        """
        pass

    """下面都是给controller调用的函数，最好不要在其他地方调用
    """

    def show_loading_animation(self):
        self.load_htmlfile("loading.html")

    def load_htmlfile(self, filename):
        path = QFileInfo(HTML_PATH + filename).absoluteFilePath()
        self.load(QUrl.fromLocalFile(path))

    def load_playlist(self, playlist_data):
        """
        :param playlist_data:
        :return:
        """
        data = json.dumps(playlist_data)
        path = QFileInfo(HTML_PATH + 'playlist.html').absoluteFilePath()
        js_code = 'window.fill_playlist(%s)' % data
        self.js_queue.append(js_code)
        self.load(QUrl.fromLocalFile(path))
        self.page().mainFrame().addToJavaScriptWindowObject('js_python', self)

    def load_album(self, album_detail):
        data = json.dumps(album_detail)
        path = QFileInfo(HTML_PATH + 'album.html').absoluteFilePath()
        js_code = 'window.fill_album(%s)' % data
        self.js_queue.append(js_code)
        self.load(QUrl.fromLocalFile(path))
        self.page().mainFrame().addToJavaScriptWindowObject('js_python', self)

    def load_artist(self, artist_detail):
        data = json.dumps(artist_detail)
        path = QFileInfo(HTML_PATH + 'artist.html').absoluteFilePath()
        js_code = 'window.fill_artist(%s)' % data
        self.js_queue.append(js_code)
        self.load(QUrl.fromLocalFile(path))
        self.page().mainFrame().addToJavaScriptWindowObject('js_python', self)

    def load_search_result(self, songs):
        data = json.dumps(songs)
        path = QFileInfo(HTML_PATH + 'search.html').absoluteFilePath()
        js_code = 'window.fill_search(%s)' % data
        self.js_queue.append(js_code)
        self.load(QUrl.fromLocalFile(path))
        self.page().mainFrame().addToJavaScriptWindowObject('js_python', self)

    def load_mv(self, mv_model):
        url = mv_model['url_middle']
        path = QFileInfo(HTML_PATH + 'mv.html').absoluteFilePath()
        js_code = 'window.play_mv("%s")' % url
        self.js_queue.append(js_code)
        self.load(QUrl.fromLocalFile(path))
        self.page().mainFrame().addToJavaScriptWindowObject('js_python', self)