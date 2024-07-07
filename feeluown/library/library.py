# mypy: disable-error-code=type-abstract
import logging
import warnings
from functools import partial
from typing import Optional, TypeVar, List, TYPE_CHECKING

from feeluown.media import Media
from feeluown.utils.aio import run_fn, as_completed
from feeluown.utils.dispatch import Signal
from .base import SearchType, ModelType
from .provider import Provider
from .excs import MediaNotFound, ProviderAlreadyExists, ModelNotFound, ResourceNotFound
from .flags import Flags as PF
from .models import (
    ModelFlags as MF, BaseModel,
    BriefVideoModel, BriefSongModel, SongModel,
    LyricModel, VideoModel, BriefAlbumModel, BriefArtistModel
)
from .model_state import ModelState
from .provider_protocol import (
    check_flag as check_flag_impl,
    SupportsSongLyric, SupportsSongMV, SupportsSongMultiQuality,
    SupportsVideoMultiQuality, SupportsSongWebUrl, SupportsVideoWebUrl,
)

if TYPE_CHECKING:
    from .ytdl import Ytdl


logger = logging.getLogger(__name__)

FULL_SCORE = 10
MIN_SCORE = 5
T_p = TypeVar('T_p')


def raise_(e):
    raise e


def default_score_fn(origin, standby):

    # TODO: move this function to utils module
    def duration_ms_to_duration(ms):
        if not ms:  # ms is empty
            return 0
        m, s = ms.split(':')
        return int(m) * 60 + int(s)

    score = FULL_SCORE
    if origin.artists_name_display != standby.artists_name_display:
        score -= 3
    if origin.title_display != standby.title_display:
        score -= 2
    if origin.album_name_display != standby.album_name_display:
        score -= 2

    origin_duration = duration_ms_to_duration(origin.duration_ms_display)
    standby_duration = duration_ms_to_duration(standby.duration_ms_display)
    if abs(origin_duration - standby_duration) / max(origin_duration, 1) > 0.1:
        score -= 3

    # Debug code for score function
    # print(f"{score}\t('{standby.title_display}', "
    #       f"'{standby.artists_name_display}', "
    #       f"'{standby.album_name_display}', "
    #       f"'{standby.duration_ms_display}')")
    return score


class Library:
    """Resource entrypoints."""

    def __init__(self, providers_standby=None):
        """

        :type app: feeluown.app.App
        """
        self._providers_standby = providers_standby
        self._providers = set()
        self.ytdl: Optional['Ytdl'] = None

        self.provider_added = Signal()  # emit(AbstractProvider)
        self.provider_removed = Signal()  # emit(AbstractProvider)

    def setup_ytdl(self, *args, **kwargs):
        from .ytdl import Ytdl

        self.ytdl = Ytdl(*args, **kwargs)

    def register(self, provider):
        """register provider

        :raises ProviderAlreadyExists:
        :raises ValueError:
        """
        if not isinstance(provider, Provider):
            raise ValueError('invalid provider instance')
        for _provider in self._providers:
            if _provider.identifier == provider.identifier:
                raise ProviderAlreadyExists
        self._providers.add(provider)
        self.provider_added.emit(provider)

    def deregister(self, provider) -> bool:
        """deregister provider

        .. versionchanged:: 4.0
           Do not raise exception anymore, return False instead.
        """
        if provider in self._providers:
            self._providers.remove(provider)
            self.provider_removed.emit(provider)
            return True
        return False

    def get(self, identifier) -> Optional[Provider]:
        """通过资源提供方唯一标识获取提供方实例"""
        for provider in self._providers:
            if provider.identifier == identifier:
                return provider
        return None

    def list(self) -> List[Provider]:
        """列出所有资源提供方"""
        return list(self._providers)

    def _filter(self, identifier_in=None):
        if identifier_in is None:
            return iter(self._providers)
        return filter(lambda p: p.identifier in identifier_in, self.list())

    def search(self, keyword, type_in=None, source_in=None, **kwargs):
        """search song/artist/album/playlist by keyword

        please use a_search method if you can.

        :param keyword: search keyword
        :param type_in: search type
        :param source_in: None or provider identifier list

        - TODO: support search with filters(by artist or by source)
        """
        type_in = SearchType.batch_parse(type_in) if type_in else [SearchType.so]
        for provider in self._filter(identifier_in=source_in):
            for type_ in type_in:
                try:
                    result = provider.search(keyword=keyword, type_=type_, **kwargs)
                except Exception:  # pylint: disable=broad-except
                    logger.exception('Search %s in %s failed.', keyword, provider)
                else:
                    if result is not None:
                        yield result

    async def a_search(self, keyword, source_in=None, timeout=None,
                       type_in=None,
                       **_):
        """async version of search

        TODO: add Happy Eyeballs requesting strategy if needed
        """
        type_in = SearchType.batch_parse(type_in) if type_in else [SearchType.so]

        fs = []  # future list
        for provider in self._filter(identifier_in=source_in):
            for type_ in type_in:
                future = run_fn(partial(provider.search, keyword, type_=type_))
                fs.append(future)

        for future in as_completed(fs, timeout=timeout):
            try:
                result = await future
            except:  # noqa
                logger.exception('search task failed')
                continue
            else:
                # When a provider does not implement search method, it returns None.
                if result is not None:
                    yield result

    async def a_list_song_standby_v2(self, song,
                                     audio_select_policy='>>>', source_in=None,
                                     score_fn=None, min_score=MIN_SCORE, limit=1):
        """list song standbys and their media

        .. versionadded:: 3.7.8

        """

        async def prepare_media(standby, policy):
            media = None
            try:
                media = await run_fn(self.song_prepare_media, standby, policy)
            except MediaNotFound as e:
                logger.debug(f'standby media not found: {e}')
            except:  # noqa
                logger.exception(f'get standby:{standby} media failed')
            return media

        if source_in is None:
            pvd_ids = self._providers_standby or [pvd.identifier for pvd in self.list()]
        else:
            pvd_ids = [pvd.identifier for pvd in self._filter(identifier_in=source_in)]
        if score_fn is None:
            score_fn = default_score_fn
        limit = max(limit, 1)

        q = '{} {}'.format(song.title_display, song.artists_name_display)
        standby_score_list = []  # [(standby, score), (standby, score)]
        song_media_list = []     # [(standby, media), (standby, media)]
        async for result in self.a_search(q, source_in=pvd_ids):
            if result is None:
                continue
            # Only check the first 3 songs
            for standby in result.songs:
                score = score_fn(song, standby)
                if score == FULL_SCORE:
                    media = await prepare_media(standby, audio_select_policy)
                    if media is None:
                        continue
                    logger.debug(f'find full mark standby for song:{q}')
                    song_media_list.append((standby, media))
                    if len(song_media_list) >= limit:
                        # Return as early as possible to get better performance
                        return song_media_list
                elif score >= min_score:
                    standby_score_list.append((standby, score))
        standby_pvd_id_set = {standby.source for standby, _ in standby_score_list}
        logger.debug(f"find {len(standby_score_list)} similar songs "
                     f"from {','.join(standby_pvd_id_set)}")
        # Limit try times since prapare_media is an expensive IO operation
        max_try = len(pvd_ids) * 2
        for standby, score in sorted(standby_score_list,
                                     key=lambda song_score: song_score[1],
                                     reverse=True)[:max_try]:
            media = await prepare_media(standby, audio_select_policy)
            if media is not None:
                song_media_list.append((standby, media))
                if len(song_media_list) >= limit:
                    return song_media_list
        return song_media_list

    def check_flags(self, source: str, model_type: ModelType, flags: PF) -> bool:
        """Check if a provider satisfies the specific ability for a model type

        .. note::

             Currently, we use ProviderFlags to define which ability a
             provider has. In the future, we may use typing.Protocol.
             So you should use :meth:`check_flags` method to check ability
             instead of compare provider flags directly.
        """
        provider = self.get(source)
        if provider is None:
            return False

        # Check each flag.
        for value in PF.__members__.values():
            if value in PF(flags):
                if check_flag_impl(provider, model_type, flags) is False:
                    return False
        return True

    def check_flags_by_model(self, model: BaseModel, flags: PF) -> bool:
        """Alias for check_flags"""
        warnings.warn('please use isinstance(provider, protocol_cls)')
        return self.check_flags(model.source,
                                ModelType(model.meta.model_type),
                                flags)

    # -----
    # Songs
    # -----
    def song_upgrade(self, song: BriefSongModel) -> SongModel:
        return self._model_upgrade(song)  # type: ignore

    def song_prepare_media(self, song: BriefSongModel, policy) -> Media:
        provider = self.get(song.source)
        if provider is None:
            raise MediaNotFound(f'provider({song.source}) not found')
        media = None
        if isinstance(provider, SupportsSongMultiQuality):
            try:
                media, _ = provider.song_select_media(song, policy)
            except MediaNotFound as e:
                if e.reason is MediaNotFound.Reason.check_children:
                    raise
                else:
                    media = None
        if not media:
            if self.ytdl is not None and isinstance(provider, SupportsSongWebUrl):
                song_web_url = provider.song_get_web_url(song)
                logger.info(f'use ytdl to get media for {song_web_url}')
                media = self.ytdl.select_audio(song_web_url, policy, source=song.source)
                found = media is not None
                logger.debug(f'ytdl select audio for {song_web_url} finished, '
                             f'found: {found}')
            if not media:
                raise MediaNotFound('provider returns empty media')
        return media

    def song_prepare_mv_media(self, song: BriefSongModel, policy) -> Media:
        """

        .. versionadded:: 3.7.5
        """
        mv = self.song_get_mv(song)
        if mv is not None:
            media = self.video_prepare_media(mv, policy)
            return media
        raise MediaNotFound('provider returns empty media')

    def song_get_mv(self, song: BriefSongModel) -> Optional[VideoModel]:
        """Get the MV model of a song."""
        provider = self.get(song.source)
        if isinstance(provider, SupportsSongMV):
            return provider.song_get_mv(song)
        return None

    def song_get_lyric(self, song: BriefSongModel) -> Optional[LyricModel]:
        """Get the lyric model of a song.

        Return None when lyric does not exist instead of raising exceptions,
        because it is predictable.
        """
        provider = self.get(song.source)
        if isinstance(provider, SupportsSongLyric):
            return provider.song_get_lyric(song)
        return None

    # --------
    # Album
    # --------
    def album_upgrade(self, album: BriefAlbumModel):
        return self._model_upgrade(album)

    # --------
    # Artist
    # --------
    def artist_upgrade(self, artist: BriefArtistModel):
        return self._model_upgrade(artist)

    # --------
    # Playlist
    # --------

    def playlist_upgrade(self, playlist):
        return self._model_upgrade(playlist)

    # -------------------------
    # generic methods for model
    # -------------------------
    def model_get(self, pid, mtype, mid):
        """Get a (normal) model instance.

        :param pid: provider id
        :param mtype: model type
        :param mid: model id
        :return: model

        :raise ResourceNotFound: model does not exist
        """
        provider = self.get(pid)
        if provider is None:
            raise ModelNotFound(f'provider:{pid} not found')
        return provider.model_get(mtype, mid)

    def model_get_cover(self, model):
        """Get the cover url of model

        :param model: model which has a 'cover' field.
        :return: cover url if exists, else ''.
        """
        if MF.normal not in model.meta.flags:
            try:
                um = self._model_upgrade(model)
            except ResourceNotFound:
                return ''
        else:
            um = model
        # FIXME: remove this hack lator.
        if ModelType(model.meta.model_type) is ModelType.artist:
            cover = um.pic_url
        else:
            cover = um.cover
        return cover

    def _model_upgrade(self, model):
        """Upgrade a model to normal model.

        :raises ModelNotFound: the model does not exist

        Note you may catch ResourceNotFound exception to simplify your code.

        .. versionchanged:: 3.8.11
            Raise ModelNotFound if the model does not exist.
            Before ModelCannotUpgrade was raised.
        """
        # Return model directly if it is already a normal(upgraded) model.
        if MF.normal in model.meta.flags:
            return model

        model_type = ModelType(model.meta.model_type)
        provider = self.get(model.source)
        if provider is None:
            raise ModelNotFound(f'provider:{model.source} not found')
        try:
            upgraded_model = provider.model_get(model_type, model.identifier)
        except ModelNotFound as e:
            if e.reason is ModelNotFound.Reason.not_found:
                model.state = ModelState.not_exists
            elif e.reason is ModelNotFound.Reason.not_supported:
                model.state = ModelState.cant_upgrade
            raise
        if upgraded_model is None:  # some provider does not implement
            raise ModelNotFound(f'{provider} implementation error, it returns None :(')
        return upgraded_model

    # --------
    # Video
    # --------
    def video_upgrade(self, video):
        return self._model_upgrade(video)

    def video_prepare_media(self, video: BriefVideoModel, policy) -> Media:
        """Prepare media for video.

        :param video: either a v1 MvModel or a v2 (Brief)VideoModel.
        """
        provider = self.get(video.source)
        try:
            if isinstance(provider, SupportsVideoMultiQuality):
                media, _ = provider.video_select_media(video, policy)
                if not media:
                    raise MediaNotFound('provider returns empty media')
            else:
                raise MediaNotFound('provider or video not found')
        except MediaNotFound:
            if self.ytdl is not None and isinstance(provider, SupportsVideoWebUrl):
                video_web_url = provider.video_get_web_url(video)
                logger.info(f'use ytdl to get media for {video_web_url}')
                media = self.ytdl.select_video(video_web_url,
                                               policy,
                                               source=video.source)
                found = media is not None
                logger.debug(f'ytdl select video for {video_web_url} finished, '
                             f'found: {found}')
            else:
                media = None
            if not media:
                raise
        return media
