import sys

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout, \
    QSizePolicy, QScrollArea, QFrame

from feeluown.models.uri import reverse, resolve
from feeluown.library import ProviderFlags as PF
from feeluown.lyric import parse
from feeluown.utils import aio
from feeluown.utils.reader import create_reader
from feeluown.gui.helpers import BgTransparentMixin, resize_font
from feeluown.gui.widgets.textbtn import TextButton
from feeluown.gui.widgets.cover_label import CoverLabelV2
from feeluown.gui.widgets.comment_list import CommentListView, CommentListModel
from feeluown.gui.widgets.songs import SongListView, SongListModel


async def render(req, **kwargs):  # pylint: disable=too-many-locals
    app = req.ctx['app']
    song = req.ctx['model']

    # TODO: Initialize the view with song object, and it should reduce
    # the code complexity.
    view = SongExploreView(app=app)
    app.ui.right_panel.set_body(view)

    # show song album cover
    song = await aio.run_fn(app.library.song_upgrade, song)

    # bind signals
    view.play_btn.clicked.connect(lambda: app.player.play_song(song))
    if app.library.check_flags_by_model(song, PF.web_url):
        async def copy_song_web_url():
            web_url = await aio.run_fn(app.library.song_get_web_url, song)
            app.show_msg(f'已经复制：{web_url}')
            QGuiApplication.clipboard().setText(web_url)

        view.copy_web_url_btn.clicked.connect(lambda: aio.run_afn(copy_song_web_url))
        # TODO: Open url in browser when alt key is pressed. Use
        # QDesktopServices.openUrl to open url in browser, and
        # you may use QGuiApplication::keyboardModifiers to check
        # if alt key is pressed.
        #
        # NOTE(cosven): Since switching from applications is inconvenience,
        # the default behaviour of button is url-copy instead of url-open.
    else:
        view.copy_web_url_btn.hide()

    album = app.library.cast_model_to_v1(song.album)
    view.header_label.setText(f'<h1>{song.title}</h1>')
    aio.create_task(view.album_info_label.show_song(song))

    if app.library.check_flags_by_model(song, PF.similar):
        songs = await aio.run_fn(app.library.song_list_similar, song)
        model = SongListModel(create_reader(songs))
        view.similar_songs_view.setModel(model)
    else:
        view.similar_songs_header.setText('<span>该提供方暂不支持查看相似歌曲，555</span>')

    if app.library.check_flags_by_model(song, PF.hot_comments):
        comments = await aio.run_fn(app.library.song_list_hot_comments, song)
        comments_reader = create_reader(comments)
        view.comments_view.setModel(CommentListModel(comments_reader))
    else:
        view.comments_header.setText('<span>该提供方暂不支持查看歌曲评论，555</span>')

    song_v1 = app.library.cast_model_to_v1(song)
    lyric = await aio.run_fn(lambda: song_v1.lyric)
    if lyric and lyric.content:
        ms_sentence_map = parse(lyric.content)
        sentences = []
        for _, sentence in sorted(ms_sentence_map.items(),
                                  key=lambda item: item[0]):
            sentences.append(sentence)
        view.lyric_label.set_lyric('\n'.join(sentences))

    # Show album cover in the end since it's an expensive CPU/IO operation.
    cover = await aio.run_fn(lambda: album.cover)
    aio.create_task(view.cover_label.show_cover(cover, reverse(album)))


class ScrollArea(QScrollArea, BgTransparentMixin):
    def __init__(self, app, parent=None):
        super().__init__(parent=parent)

        self._app = app

        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)

        # As far as I know, KDE and GNOME can't auto hide the scrollbar,
        # and they show an old-fation vertical scrollbar.
        # HELP: implement an auto-hide scrollbar for Linux
        if sys.platform.lower() != 'darwin':
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)


class HeaderLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setTextFormat(Qt.RichText)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)


class LyricLabel(QLabel, BgTransparentMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWordWrap(True)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        font = self.font()
        resize_font(font, -1)
        self.setFont(font)
        self.setTextFormat(Qt.RichText)

    def set_lyric(self, text):
        text = text.replace("\n", "<br>")
        self.setText(f'<p style="line-height: 120%">{text}</p>')


class SongAlbumLabel(QLabel):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app
        self.setTextFormat(Qt.RichText)
        self.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.linkActivated.connect(self.on_link_activated)
        self.setWordWrap(True)

    async def show_song(self, song):
        album = song.album
        artists_str_list = []
        for artist in song.artists:
            artists_str_list.append(
                f'<a href="{reverse(artist)}">{artist.name_display}</a>'
            )
        artists_str = ' / '.join(artists_str_list)
        self.setText(f'''\
专辑名：<a href="{reverse(album)}">{album.name_display}</a>
<br/>
歌手：{artists_str}
''')

    def on_link_activated(self, url):
        model = resolve(url)
        self._app.browser.goto(model=model)


class LeftCon(QWidget, BgTransparentMixin):
    def sizeHint(self):
        size_hint = super().sizeHint()
        return QSize(500, size_hint.height())


class RightCon(QWidget):
    def sizeHint(self):
        size_hint = super().sizeHint()
        return QSize(260, size_hint.height())


class SongExploreView(QWidget):
    def __init__(self, app):
        super().__init__(parent=None)
        self._app = app

        self._left_con = LeftCon(self)  #: left container
        self._left_con_scrollarea = ScrollArea(self._app)
        self._left_con_scrollarea.setWidget(self._left_con)
        self._right_con = RightCon(self)
        self._left_layout = QVBoxLayout(self._left_con)
        self._left_h1_layout = QHBoxLayout()
        self._left_h2_layout = QHBoxLayout()
        self._right_layout = QVBoxLayout(self._right_con)

        self.header_label = HeaderLabel()
        self.lyric_header = HeaderLabel('<h3>歌词：</h3>')
        self.comments_header = HeaderLabel('<h2>热门评论</h2>')
        self.similar_songs_header = HeaderLabel('<h2>相似歌曲</h2>')
        self.lyric_label = LyricLabel()
        self.play_btn = TextButton('播放')
        self.copy_web_url_btn = TextButton('复制网页地址')
        self.cover_label = CoverLabelV2(app=app)
        self.album_info_label = SongAlbumLabel(app)
        self.comments_view = CommentListView(reserved=0)
        self.similar_songs_view = SongListView(reserved=0)

        self._lyric_scrollarea = ScrollArea(self._app)
        self._lyric_scrollarea.setWidget(self.lyric_label)
        self.lyric_label.setSizePolicy(QSizePolicy.Preferred,
                                       QSizePolicy.Expanding)

        self.header_label.setTextFormat(Qt.RichText)
        self.cover_label.setSizePolicy(QSizePolicy.Preferred,
                                       QSizePolicy.Preferred)

        self._layout = QHBoxLayout(self)
        self._setup_ui()

        self.similar_songs_view.play_song_needed.connect(
            lambda song: app.player.play_song(song))

    def _setup_ui(self):
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(10, 0, 10, 0)

        self._layout.addWidget(self._left_con_scrollarea, 2)
        # Assume the max screen height is about 1080.
        self._right_con.setMaximumWidth(360)
        self._layout.addWidget(self._right_con, 1)

        self._left_layout.addWidget(self.header_label)
        self._left_layout.addLayout(self._left_h1_layout)
        self._left_layout.addLayout(self._left_h2_layout)
        self._left_layout.addWidget(self.similar_songs_header)
        self._left_layout.addWidget(self.similar_songs_view)
        self._left_layout.addWidget(self.comments_header)
        self._left_layout.addWidget(self.comments_view)
        self._left_layout.addSpacing(10)

        self._left_h2_layout.addWidget(self.play_btn)
        self._left_h2_layout.addSpacing(10)
        self._left_h2_layout.addWidget(self.copy_web_url_btn)
        self._left_h2_layout.addStretch(0)
        # self._left_layout.addStretch(0)

        self._right_layout.addWidget(self.cover_label)
        self._right_layout.addWidget(self.album_info_label)
        self._right_layout.addWidget(self.lyric_header)
        self._right_layout.addWidget(self._lyric_scrollarea)
        # self._right_layout.addStretch(0)
