# mypy: disable-error-code=type-abstract
import logging
import warnings
from collections import Counter
from typing import Optional, TypeVar, List, TYPE_CHECKING

from feeluown.media import Media
from feeluown.utils.aio import run_fn, as_completed
from feeluown.utils.dispatch import Signal
from feeluown.library.base import SearchType, ModelType
from feeluown.library.provider import Provider
from feeluown.library.excs import (
    MediaNotFound, ProviderAlreadyExists, ModelNotFound, ResourceNotFound,
)
from feeluown.library.flags import Flags as PF
from feeluown.library.models import (
    ModelFlags as MF, BaseModel, SimpleSearchResult,
    BriefVideoModel, BriefSongModel, SongModel,
    LyricModel, VideoModel, BriefAlbumModel, BriefArtistModel,
    AlbumModel,
)
from feeluown.library.model_state import ModelState
from feeluown.library.provider_protocol import (
    check_flag as check_flag_impl,
    SupportsSongLyric, SupportsSongMV, SupportsSongMultiQuality,
    SupportsVideoMultiQuality, SupportsSongWebUrl, SupportsVideoWebUrl,
    SupportsAlbumSongsReader, SupportsUserAutoLogin,
)
from feeluown.library.standby import (
    get_standby_score,
    STANDBY_DEFAULT_MIN_SCORE,
    STANDBY_FULL_SCORE,
)

if TYPE_CHECKING:
    from feeluown.ai import AI
    from feeluown.library.ytdl import Ytdl

logger = logging.getLogger(__name__)

T_p = TypeVar('T_p')


def raise_(e):
    raise e


class Library:
    """Resource entrypoints."""

    def __init__(self, providers_standby=None, enable_ai_standby_matcher=True):
        """

        :type app: feeluown.app.App
        """
        self._providers_standby = providers_standby
        self._providers = set()
        self.ytdl: Optional['Ytdl'] = None
        self.ai: Optional['AI'] = None

        self.provider_added = Signal()  # emit(AbstractProvider)
        self.provider_removed = Signal()  # emit(AbstractProvider)
        self.enable_ai_standby_matcher = enable_ai_standby_matcher

    def setup_ytdl(self, *args, **kwargs):
        from .ytdl import Ytdl

        self.ytdl = Ytdl(*args, **kwargs)

    def setup_ai(self, ai):
        self.ai = ai

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

        if isinstance(provider, SupportsUserAutoLogin):
            logger.debug(f"Auto login for {provider.identifier} ...")
            run_fn(provider.auto_login)

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
                       type_in=None, return_err=False,
                       **_):
        """async version of search

        .. versionchanged:: 4.1.9
            Add `return_err` parameter.

        TODO: add Happy Eyeballs requesting strategy if needed
        """
        type_in = SearchType.batch_parse(type_in) if type_in else [SearchType.so]

        # Wrap the search function to associate the result with source.
        def wrap_search(pvd, kw, t):
            def search():
                try:
                    res = pvd.search(kw, type_=t)
                except Exception as e:  # noqa
                    if return_err:
                        logger.exception('One provider search failed')
                        return SimpleSearchResult(
                            q=keyword,
                            source=pvd.identifier,  # noqa
                            err_msg=f'{type(e)}',
                        )
                    raise e
                # When a provider does not implement search method, it returns None.
                if res is not None and (
                    res.songs or res.albums or
                    res.artists or res.videos or res.playlists
                ):
                    return res
                return SimpleSearchResult(
                    q=keyword, source=pvd.identifier, err_msg='结果为空')
            return search

        fs = []  # future list
        for provider in self._filter(identifier_in=source_in):
            for type_ in type_in:
                future = run_fn(wrap_search(provider, keyword, type_))
                fs.append(future)
        for task_ in as_completed(fs, timeout=timeout):
            try:
                result = await task_
            except Exception as e:  # noqa
                logger.exception('One search task failed due to asyncio')
            else:
                yield result

    async def a_song_prepare_media_no_exc(self, standby, policy):
        media = None
        try:
            media = await run_fn(self.song_prepare_media, standby, policy)
        except MediaNotFound as e:
            logger.debug(f'standby media not found: {e}')
        except:  # noqa
            logger.exception(f'get standby:{standby} media failed')
        return media

    async def a_list_song_standby_v2(
            self, song, audio_select_policy='>>>', source_in=None,
            score_fn=None, min_score=STANDBY_DEFAULT_MIN_SCORE, limit=1):
        """list song standbys and their media

        .. versionadded:: 3.7.8
        """
        if source_in is None:
            pvd_ids = self._providers_standby or [pvd.identifier for pvd in self.list()]
        else:
            pvd_ids = [pvd.identifier for pvd in self._filter(identifier_in=source_in)]
        if score_fn is None:
            score_fn = get_standby_score
        limit = max(limit, 1)

        q = '{} {}'.format(song.title_display, song.artists_name_display)
        standby_score_list = []  # [(standby, score), (standby, score)]
        song_media_list = []  # [(standby, media), (standby, media)]
        top2_standby = []
        async for result in self.a_search(q, source_in=pvd_ids):
            if result is None:
                continue
            # Only check the first 3 songs
            for i, standby in enumerate(result.songs):
                # HACK(cosven): I think the local provider should not be included,
                #   because the search algorithm of local provider is so bad.
                if i < 2 and standby.source != 'local':
                    top2_standby.append(standby)
                score = score_fn(song, standby)
                if score == STANDBY_FULL_SCORE:
                    media = await self.a_song_prepare_media_no_exc(
                        standby,
                        audio_select_policy
                    )
                    if media is None:
                        continue
                    logger.info(f'Find full score standby for song:{q}')
                    song_media_list.append((standby, media))
                    if len(song_media_list) >= limit:
                        # Return as early as possible to get better performance
                        return song_media_list
                elif score >= min_score:
                    standby_score_list.append((standby, score))
        if standby_score_list:
            standby_pvd_id_set = {standby.source for standby, _ in standby_score_list}
            logger.info(f"Find {len(standby_score_list)} similar songs "
                        f"from {','.join(standby_pvd_id_set)}. Try to get a valid media")
            max_per_source = 2
            standby_score_list_2 = []
            counter = Counter()
            for s, score in standby_score_list:
                if counter[s.source] >= max_per_source:
                    continue
                counter[s.source] += 1
                standby_score_list_2.append((s, score))

            assert len(standby_score_list_2) <= max_per_source * len(standby_pvd_id_set)
            sorted_standby_score_list = sorted(
                standby_score_list_2,
                key=lambda song_score: song_score[1],
                reverse=True,
            )
            for standby, _ in sorted_standby_score_list:
                # TODO: send multiple requests at a time.
                media = await self.a_song_prepare_media_no_exc(
                    standby,
                    audio_select_policy
                )
                if media is not None:
                    song_media_list.append((standby, media))
                    if len(song_media_list) >= limit:
                        return song_media_list
            if song_media_list:
                return song_media_list
        if self.enable_ai_standby_matcher and self.ai and top2_standby:
            from feeluown.library.ai_standby import AIStandbyMatcher  # noqa

            logger.info(f'Try to use AI to match standby for song {song}')
            matcher = AIStandbyMatcher(
                self.ai, self.a_song_prepare_media_no_exc, 60, audio_select_policy)
            song_media_list = await matcher.match(song, top2_standby)
            word = 'found a' if song_media_list else 'found no'
            logger.info(f'AI {word} standby for song:{song}')
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
                media = self.ytdl.select_audio(song_web_url, policy, source=song.source)
                found = media is not None
                logger.debug(f'ytdl select audio for {song_web_url} finished, '
                             f'found: {found}')
            if not media:
                raise MediaNotFound('provider returns empty media')
        return media

    def song_get_web_url(self, song: BriefSongModel) -> str:
        """Get song web url

        :raises ResourceNotFound: provider/song/web_url is not found
        :raises ProviderIOError: provider raises error during get_web_url

        .. versionadded:: 4.1.8
        """
        provider = self.get(song.source)
        if provider is None:
            raise ResourceNotFound(f'provider({song.source}) not found')
        if isinstance(provider, SupportsSongWebUrl):
            return provider.song_get_web_url(song)
        raise ResourceNotFound(reason=ResourceNotFound.Reason.not_supported)

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

    def album_list_songs(self, album: BriefAlbumModel):
        """
        :raises ResourceNotFound:
        :raises ProviderIOError:

        .. versionadded:: 4.1.11
        """
        if not isinstance(album, AlbumModel):
            ualbum = self.album_upgrade(album)
        else:
            ualbum = album
        if ualbum.song_count == 0:
            return []
        if ualbum.songs:
            return ualbum.songs
        provider = self.get(ualbum.source)
        if isinstance(provider, SupportsAlbumSongsReader):
            return list(provider.album_create_songs_rd(ualbum))
        raise ResourceNotFound(reason=ResourceNotFound.Reason.not_supported)

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
