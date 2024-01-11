from PyQt5.QtWidgets import QLabel, QMenu

from feeluown.utils.aio import run_afn
from feeluown.media import MediaType


class SongSourceTag(QLabel):
    default_text = '音乐来源'

    def __init__(self, app, font_size=12, parent=None):
        super().__init__(text=SongSourceTag.default_text, parent=parent)
        self._app = app

        font = self.font()
        font.setPixelSize(font_size)
        self.setFont(font)

        self._app.player.metadata_changed.connect(
            self.on_metadata_changed, aioqueue=True)

    def contextMenuEvent(self, e):
        # pylint: disable=unnecessary-direct-lambda-call
        # FIXME(wuliaotc): 在切换provider时禁用menu
        song = self._app.playlist.current_song
        if song is None:
            return

        menu = QMenu()
        submenu = menu.addMenu('“智能”替换')
        for provider in self._app.library.list():
            pid = provider.identifier
            if pid == song.source:
                continue
            action = submenu.addAction(provider.name)
            action.triggered.connect(
                (lambda x: lambda: run_afn(self._switch_provider, x))(pid)
            )
        menu.exec(e.globalPos())

    def on_metadata_changed(self, metadata):
        if not metadata:
            self.setText(SongSourceTag.default_text)
            return

        text = '未知来源'

        # Fill source name.
        source = metadata.get('source', '')
        if source:
            source_name_map = {p.identifier: p.name
                               for p in self._app.library.list()}
            text = source_name_map.get(source, text)

        # Fill audio bitrate info if available.
        media = self._app.player.current_media
        if media is not None and media.type_ == MediaType.audio:
            props = media.props
            if props.bitrate:
                text = f'{text} • {props.bitrate}kbps'

        self.setText(text)

    async def _switch_provider(self, provider_id):
        song = self._app.playlist.current_song
        songs = await self._app.library.a_list_song_standby_v2(
            song, source_in=[provider_id])
        if songs:
            standby, media = songs[0]
            assert standby != song
            self._app.show_msg(f'使用 {standby} 替换当前歌曲')
            self._app.playlist.pure_set_current_song(standby, media)
            self._app.playlist.remove(song)
        else:
            self._app.show_msg(f'提供方 “{provider_id}” 没有找到可用的相似歌曲')
