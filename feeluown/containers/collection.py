from PyQt5.QtWidgets import QFrame, QHBoxLayout, QSplitter
from PyQt5.QtGui import QPixmap, QImage

from feeluown.utils import aio
from feeluown.utils.reader import wrap
from feeluown.media import Media, MediaType
from feeluown.models.uri import reverse
from feeluown.gui.helpers import async_run

from feeluown.widgets.collection import CollectionTOCView, CollectionTOCModel, \
    CollectionBody
from feeluown.widgets.songs import SongListModel


class CollectionContainer(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent=parent)
        self._app = app

        self._splitter = QSplitter(self)
        self.collection_toc = CollectionTOCView(self._app, self._splitter)
        self.collection_body = CollectionBody(self._app, self._splitter)

        self.collection_toc.show_album_needed.connect(
            lambda album: aio.create_task(self.show_album(album)))
        self.collection_toc.play_song_needed.connect(
            self._app.player.play_song)
        self.collection_body.song_list_view.play_song_needed.connect(
            self._app.player.play_song)

        self._layout = QHBoxLayout(self)

        self._setup_ui()

    def _setup_ui(self):
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._splitter.setHandleWidth(0)
        self._splitter.addWidget(self.collection_toc)
        self._splitter.addWidget(self.collection_body)
        self._layout.addWidget(self._splitter)

    def show_collection(self, coll):
        model = CollectionTOCModel(coll)
        self.collection_toc.setModel(model)

        self.collection_body.song_list_view.hide()
        meta_widget = self.collection_body.meta_widget
        meta_widget.clear()
        meta_widget.title = coll.name
        meta_widget.updated_at = coll.updated_at
        meta_widget.created_at = coll.created_at

    async def show_album(self, album):
        meta_widget = self.collection_body.meta_widget
        meta_widget.clear()
        meta_widget.title = album.name_display
        meta_widget.creator = album.artists_name_display
        songs = await async_run(lambda: album.songs)
        meta_widget.songs_count = len(songs)
        reader = wrap(songs)
        model = SongListModel(reader)
        self.collection_body.song_list_view.show()
        self.collection_body.song_list_view.setModel(model)
        meta_widget.desc = await async_run(lambda: album.desc)
        meta_widget.title = await async_run(lambda: album.name)
        meta_widget.creator = await async_run(lambda: album.artists_name)
        cover = await async_run(lambda: album.cover)
        if cover:
            aio.create_task(self.show_cover(cover, reverse(album, '/cover')))

    async def show_cover(self, cover, cover_uid):
        meta_widget = self.collection_body.meta_widget
        cover = Media(cover, MediaType.image)
        cover = cover.url
        app = self._app
        content = await app.img_mgr.get(cover, cover_uid)
        img = QImage()
        img.loadFromData(content)
        pixmap = QPixmap(img)
        if not pixmap.isNull():
            meta_widget.set_cover_pixmap(pixmap)
