import logging
import sys

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout, \
    QSizePolicy, QScrollArea, QFrame

from feeluown.excs import ProviderNotFound, ModelCannotUpgrade
from feeluown.library import (
    SupportsSongHotComments, SupportsSongSimilar, SupportsSongWebUrl,
    NotSupported, SupportsSongLyric
)
from feeluown.models.uri import reverse, resolve
from feeluown.player import parse_lyric_text
from feeluown.utils import aio
from feeluown.utils.reader import create_reader
from feeluown.gui.helpers import BgTransparentMixin, fetch_cover_wrapper, resize_font
from feeluown.gui.widgets.header import LargeHeader, MidHeader
from feeluown.gui.widgets.textbtn import TextButton
from feeluown.gui.widgets.cover_label import CoverLabelV2
from feeluown.gui.widgets.comment_list import CommentListView, CommentListModel
from feeluown.gui.widgets.song_minicard_list import (
    SongMiniCardListDelegate, SongMiniCardListModel, SongMiniCardListView
)

logger = logging.getLogger(__name__)

# Error message template for NotSupported
err_msg_tpl = ('<p style="color: grey; font: small;">该提供方暂不支持{feature}。'
               '<br/> 给它实现一下 {interface} 接口来支持该功能吧 ~'
               '</p>')


def or_unknown(x):
    return x or '未知'


async def render(req, **kwargs):  # pylint: disable=too-many-locals,too-many-branches
    app = req.ctx['app']
    song = req.ctx['model']

    try:
        provider = app.library.get_or_raise(song.source)
    except ProviderNotFound as e:
        view = InlineErrorMessageView()
        view.show_msg(f'无法展示歌曲详情：{repr(e)}')
        app.ui.right_panel.set_body(view)
        return

    # TODO: Initialize the view with song object, and it should reduce
    # the code complexity.
    view = SongExploreView(app=app)
    app.ui.right_panel.set_body(view)

    try:
        upgraded_song = await aio.run_fn(app.library.song_upgrade, song)
    except (NotSupported, ModelCannotUpgrade):
        upgraded_song = None
    if upgraded_song is not None:
        song = upgraded_song

    # Before fetching more data, show some widgets.
    view.title_label.setText(song.title)
    view.play_btn.clicked.connect(lambda: app.playlist.play_model(song))

    # Show other widgets.
    await view.maybe_show_web_url_btn(provider, song)

    # Fetch album.
    album = upgraded_song.album if upgraded_song is not None else None
    if album is not None:
        try:
            upgraded_album = await aio.run_fn(app.library.album_upgrade, song.album)
        except (NotSupported, ModelCannotUpgrade):
            upgraded_album = None
    else:
        upgraded_album = None
    if upgraded_album is not None:
        album = upgraded_album

    await view.show_song_wiki(song, album)
    await view.maybe_show_song_similar(provider, song)
    await view.maybe_show_song_hot_comments(provider, song)
    await view.maybe_show_song_lyric(song)
    await view.maybe_show_album_cover(upgraded_album)


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
        self.setAlignment(Qt.AlignHCenter)
        font = self.font()
        resize_font(font, 0)
        self.setFont(font)
        self.setTextFormat(Qt.RichText)


class SongWikiLabel(QLabel):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app
        self.setTextFormat(Qt.RichText)
        self.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.linkActivated.connect(self.on_link_activated)
        self.setWordWrap(True)

    async def show_song(self, song, album):
        artists_str_list = []
        for artist in song.artists:
            artists_str_list.append(
                f'<a href="{reverse(artist)}">{artist.name_display}</a>'
            )
        artists_str = ' / '.join(artists_str_list)
        # Only show the date, like yyyy-mm-dd. Do not show hour/minutes/seconds.
        date = song.date or album.released
        date_fmted = date[:10] if date else ''
        kvs = [
            ('歌手', artists_str),
            ('所属专辑', f'<a href="{reverse(album)}">{album.name_display}</a>'),
            ('发行日期', or_unknown(date_fmted)),
            ('曲风', or_unknown(song.genre)),
        ]
        lines = []
        for k, v in kvs:
            line = f"<span style='color: grey'>{k}：</span>" + v
            lines.append(line)
        self.setText('<br/>'.join(lines))

    def on_link_activated(self, url):
        model = resolve(url)
        self._app.browser.goto(model=model)


class LeftCon(QWidget, BgTransparentMixin):
    def sizeHint(self):
        size_hint = super().sizeHint()
        return QSize(600, size_hint.height())


class RightCon(QWidget):
    def sizeHint(self):
        size_hint = super().sizeHint()
        return QSize(100, size_hint.height())


class SongExploreView(QWidget):
    def __init__(self, app):
        super().__init__(parent=None)
        self._app = app

        self.title_label = LargeHeader()
        self.similar_songs_header = MidHeader('相似歌曲')
        self.comments_header = MidHeader('热门评论')
        self.lyric_label = LyricLabel()
        self.play_btn = TextButton('播放')
        self.copy_web_url_btn = TextButton('复制网页地址')
        self.cover_label = CoverLabelV2(app=app)
        self.song_wiki_label = SongWikiLabel(app)
        self.comments_view = CommentListView(reserved=0)
        self.similar_songs_view = SongMiniCardListView(row_height=60, no_scroll_v=True)
        delegate = SongMiniCardListDelegate(
            self.similar_songs_view,
            card_min_width=150,
            card_height=40,
            card_padding=(5 + SongMiniCardListDelegate.img_padding, 5, 0, 5),
            card_right_spacing=10,
        )
        self.similar_songs_view.setItemDelegate(delegate)

        self._lyric_scrollarea = ScrollArea(self._app)
        self._lyric_scrollarea.setWidget(self.lyric_label)
        self._setup_ui()

        self.similar_songs_view.play_song_needed.connect(
            app.playlist.play_model)

    def _setup_ui(self):
        self.lyric_label.setSizePolicy(QSizePolicy.Preferred,
                                       QSizePolicy.Expanding)
        self.cover_label.setFixedSize(160, 160)
        self.cover_label.setSizePolicy(QSizePolicy.Preferred,
                                       QSizePolicy.Preferred)

        self._left_con = LeftCon(self)  #: left container
        self._left_con_scrollarea = ScrollArea(self._app)
        self._left_con_scrollarea.setWidget(self._left_con)
        self._right_con = RightCon(self)
        self._left_layout = QVBoxLayout(self._left_con)
        self._right_layout = QVBoxLayout(self._right_con)
        self._layout = QHBoxLayout(self)

        self._left_top_layout = QHBoxLayout()
        self._song_meta_layout = QVBoxLayout()
        self._btns_layout = QHBoxLayout()

        self._layout.setSpacing(0)
        self._layout.setContentsMargins(10, 20, 10, 0)

        self._layout.addWidget(self._left_con_scrollarea, 3)
        self._layout.addSpacing(30)
        self._layout.addWidget(self._right_con, 1)

        self._left_layout.addLayout(self._left_top_layout)
        self._left_layout.addSpacing(10)
        self._left_layout.addWidget(self.comments_header)
        self._left_layout.addWidget(self.comments_view)
        self._left_layout.addWidget(self.similar_songs_header)
        self._left_layout.addWidget(self.similar_songs_view)
        self._left_layout.addSpacing(10)

        self._left_top_layout.addWidget(self.cover_label, alignment=Qt.AlignTop)
        self._left_top_layout.addSpacing(10)
        self._left_top_layout.addLayout(self._song_meta_layout)

        self._song_meta_layout.addWidget(self.title_label)
        self._song_meta_layout.addStretch(0)
        self._song_meta_layout.addWidget(self.song_wiki_label, alignment=Qt.AlignTop)
        self._song_meta_layout.addStretch(0)
        self._song_meta_layout.addLayout(self._btns_layout)

        self._btns_layout.addWidget(self.play_btn)
        self._btns_layout.addSpacing(6)
        self._btns_layout.addWidget(self.copy_web_url_btn)
        self._btns_layout.addStretch(0)

        self._right_layout.addWidget(self._lyric_scrollarea)

    async def maybe_show_web_url_btn(self, provider, song):
        if isinstance(provider, SupportsSongWebUrl):
            async def copy_song_web_url():
                web_url = await aio.run_fn(provider.song_get_web_url, song)
                QGuiApplication.clipboard().setText(web_url)
                self._app.show_msg(f'已经复制：{web_url}')

            self.copy_web_url_btn.clicked.connect(lambda: aio.run_afn(copy_song_web_url))
            # TODO: Open url in browser when alt key is pressed. Use
            # QDesktopServices.openUrl to open url in browser, and
            # you may use QGuiApplication::keyboardModifiers to check
            # if alt key is pressed.
            #
            # NOTE(cosven): Since switching from applications is inconvenience,
            # the default behaviour of button is url-copy instead of url-open.
        else:
            self.copy_web_url_btn.hide()

    async def show_song_wiki(self, song, album):
        aio.run_afn(self.song_wiki_label.show_song, song, album)

    async def maybe_show_song_similar(self, provider, song):
        if isinstance(provider, SupportsSongSimilar):
            songs = await aio.run_fn(provider.song_list_similar, song)
            model = SongMiniCardListModel(create_reader(songs),
                                          fetch_cover_wrapper(self._app))
            self.similar_songs_view.setModel(model)
        else:
            msg = err_msg_tpl.format(feature='查看相似歌曲',
                                     interface=SupportsSongSimilar.__name__)
            self.similar_songs_header.setText(msg)

    async def maybe_show_song_hot_comments(self, provider, song):
        if isinstance(provider, SupportsSongHotComments):
            comments = await aio.run_fn(provider.song_list_hot_comments, song)
            comments_reader = create_reader(comments)
            self.comments_view.setModel(CommentListModel(comments_reader))
        else:
            msg = err_msg_tpl.format(feature='查看歌曲评论',
                                     interface=SupportsSongHotComments.__name__)
            self.comments_header.setText(msg)

    async def maybe_show_song_lyric(self, song):
        try:
            lyric = self._app.library.song_get_lyric(song)
        except NotSupported:
            msg = err_msg_tpl.format(feature='查看歌曲歌词',
                                     interface=SupportsSongLyric.__name__)
            self.lyric_label.setText(msg)
        else:
            if lyric is not None:
                ms_sentence_map = parse_lyric_text(lyric.content)
                sentences = []
                for _, sentence in sorted(ms_sentence_map.items(),
                                          key=lambda item: item[0]):
                    sentences.append(sentence)
                lyric = '<br>'.join(sentences)
                self.lyric_label.setText(f'<p style="line-height: 120%">{lyric}</p>')

    async def maybe_show_album_cover(self, album):
        if album:
            aio.run_afn(self.cover_label.show_cover,
                        album.cover,
                        reverse(album))


class InlineErrorMessageView(QLabel):
    """Error message view
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAlignment(Qt.AlignCenter)

    def show_msg(self, msg):
        self.setText(msg)
