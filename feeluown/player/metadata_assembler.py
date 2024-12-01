import logging
from typing import TYPE_CHECKING

from feeluown.excs import ResourceNotFound, ModelNotFound
from feeluown.library import reverse, SongModel
from feeluown.player import Metadata, MetadataFields
from feeluown.utils import aio

if TYPE_CHECKING:
    from feeluown.app import App

logger = logging.getLogger(__name__)


class MetadataAssembler:
    """Cook and fetch metadata for songs and videos"""
    def __init__(self, app: 'App'):
        self._app = app

    @staticmethod
    def cook_basic_metadata_for_song(song):
        return Metadata({
            MetadataFields.uri: reverse(song),
            MetadataFields.source: song.source,
            MetadataFields.title: song.title_display or '',
            # The song.artists_name should return a list of strings
            MetadataFields.artists: [song.artists_name_display or ''],
            MetadataFields.album: song.album_name_display or '',
        })

    async def fetch_from_song(self, song):
        empty_result = ('', '', None)
        try:
            usong: SongModel = await aio.wait_for(
                aio.run_fn(self._app.library.song_upgrade, song),
                timeout=1,
            )
        except ResourceNotFound:
            return empty_result
        except TimeoutError:  # noqa
            logger.warning(f"fetching song's meta timeout, song:'{song.title}'")
            return empty_result
        except:  # noqa
            logger.exception(f"fetching song's meta failed, song:'{song.title}'")
            return empty_result
        return usong.pic_url, usong.date, usong.album

    async def fetch_from_album(self, album):
        empty_result = ('', '')
        try:
            album = await aio.wait_for(
                aio.run_fn(self._app.library.album_upgrade, album),
                timeout=1
            )
        except ResourceNotFound:
            return empty_result
        except TimeoutError:  # noqa
            logger.warning(f"fetching album's meta timeout, album:'{album.name}'")
            return empty_result
        except:  # noqa
            logger.exception(f"fetching album meta failed, album:'{album.name}'")
            return empty_result
        return album.cover, album.released

    async def prepare_for_song(self, song):
        metadata = self.cook_basic_metadata_for_song(song)

        artwork, released, album = await self.fetch_from_song(song)
        if not (artwork and released) and album is not None:
            album_cover, album_released = await self.fetch_from_album(album)
            # Try to use album meta first.
            artwork = album_cover or artwork
            released = album_released or released
        metadata[MetadataFields.artwork] = artwork
        metadata[MetadataFields.released] = released

        return metadata

    async def prepare_for_video(self, video):
        metadata = Metadata({
            # The value of model v1 title_display may be None.
            MetadataFields.title: video.title_display or '',
            MetadataFields.source: video.source,
            MetadataFields.uri: reverse(video),
        })
        try:
            video = await aio.run_fn(self._app.library.video_upgrade, video)
        except ModelNotFound as e:
            logger.warning(f"can't get cover of video due to {str(e)}")
        else:
            metadata[MetadataFields.artwork] = video.cover
        return metadata
