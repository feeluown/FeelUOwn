# pylint: disable=import-error
from AppKit import NSImage, NSMakeRect, NSCompositingOperationSourceOver
from Foundation import NSMutableDictionary
from MediaPlayer import (
    MPMediaItemArtwork, MPNowPlayingInfoCenter, MPMediaItemPropertyArtwork,
)

from feeluown.utils import aio


class MacosMixin:

    def update_song_metadata(self, meta):
        super().update_song_metadata(meta)

        artwork = meta.get('artwork', '')
        artwork_uid = meta.get('uri', artwork)
        self._update_artwork(artwork, artwork_uid)

    def _update_artwork(self, artwork, artwork_uid):

        async def task():
            b = await self._app.img_mgr.get(artwork, artwork_uid)
            set_artwork(self.info_center, b)

        aio.run_afn(task)


def artwork_from_bytes(b: bytes) -> MPMediaItemArtwork:
    img = NSImage.alloc().initWithData_(b)

    def resize(size):
        new = NSImage.alloc().initWithSize_(size)
        new.lockFocus()
        img.drawInRect_fromRect_operation_fraction_(
            NSMakeRect(0, 0, size.width, size.height),
            NSMakeRect(0, 0, img.size().width, img.size().height),
            NSCompositingOperationSourceOver,
            1.0,
        )
        new.unlockFocus()
        return new

    art = MPMediaItemArtwork.alloc() \
        .initWithBoundsSize_requestHandler_(img.size(), resize)
    return art


def set_artwork(info_center: MPNowPlayingInfoCenter, b):
    current_nowplaying_info = info_center.nowPlayingInfo()
    if current_nowplaying_info is None:
        nowplaying_info = NSMutableDictionary.dictionary()
    else:
        nowplaying_info = current_nowplaying_info.mutableCopy()
    if b:
        nowplaying_info[MPMediaItemPropertyArtwork] = artwork_from_bytes(b)
    info_center.setNowPlayingInfo_(nowplaying_info)
    return True
