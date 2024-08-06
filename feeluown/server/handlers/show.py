"""
feeluown.cmds.show
~~~~~~~~~~~~~~~~~

处理 ``show`` 命令::

    show fuo://               # 列出所有 provider
    show fuo://local/songs    # 显示本地所有歌曲
    show fuo://local/songs/1  # 显示一首歌的详细信息
"""
import logging
from functools import wraps
from urllib.parse import urlparse

from feeluown.utils.router import Router, NotFound
from feeluown.library import (
    ResourceNotFound, NS_TYPE_MAP, ModelType,
    SupportsPlaylistSongsReader, SupportsArtistAlbumsReader,
)

from .base import AbstractHandler
from .excs import HandlerException

logger = logging.getLogger(__name__)


router = Router()
route = router.route


class ShowHandler(AbstractHandler):
    cmds = 'show'

    def handle(self, cmd):
        if cmd.args:
            furi = cmd.args[0]
        else:
            furi = 'fuo://'
        r = urlparse(furi)
        path = f'/{r.netloc}{r.path}'
        logger.debug(f'请求 path: {path}')
        try:
            rv = router.dispatch(path, {'library': self.library,
                                        'session': self.session})
        except NotFound:
            raise HandlerException(f'path {path} not found') from None
        except ResourceNotFound as e:
            raise HandlerException(str(e)) from e
        return rv


def get_model_or_raise(library, provider, model_type, model_id):
    model = library.model_get(provider.identifier, model_type, model_id)
    return model


def use_provider(func):
    @wraps(func)
    def wrapper(req, **kwargs):
        provider_id = kwargs.pop('provider')
        provider = req.ctx['library'].get(provider_id)
        if provider is None:
            raise HandlerException(f'provider:{provider_id} not found')
        return func(req, provider, **kwargs)
    return wrapper


def create_model_handler(ns, model_type):
    @route(f'/<provider>/{ns}/<model_id>')
    @use_provider
    def handle(req, provider, model_id):
        # special cases:
        # fuo://<provider>/users/me -> show current logged user
        if model_type == ModelType.user:
            if model_id == 'me':
                user = getattr(provider, '_user', None)
                if user is None:
                    raise HandlerException(
                        f'log in provider:{provider.identifier} first')
                return user
        model = get_model_or_raise(
            req.ctx['library'], provider, model_type, model_id)
        return model


@route('/')
def list_providers(req):
    return req.ctx['library'].list()


@route('/server/sessions/me')
def current_session(req):
    """
    Currently only used for debugging.
    """
    session = req.ctx['session']
    options = session.options
    result = []
    result.append(f'   rpc_version: {options.rpc_version}')
    result.append(f'pubsub_version: {options.pubsub_version}')
    return '\n'.join(result)


for ns_, model_type_ in NS_TYPE_MAP.items():
    create_model_handler(ns_, model_type_)


@route('/<provider>/songs/<sid>/lyric')
@use_provider
def lyric_(req, provider, sid):
    library = req.ctx['library']
    song = get_model_or_raise(library, provider, ModelType.song, sid)
    lyric = library.song_get_lyric(song)
    if lyric is None:
        return ''
    return lyric.content


@route('/<provider>/playlists/<pid>/songs')
@use_provider
def playlist_songs(req, provider, pid):
    playlist = get_model_or_raise(req.ctx['library'], provider, ModelType.playlist, pid)
    if isinstance(provider, SupportsPlaylistSongsReader):
        reader = provider.playlist_create_songs_rd(playlist)
        return reader.readall()
    raise HandlerException(f"provider:{provider.identifier} does not support"
                           f" {SupportsPlaylistSongsReader}")


@route('/<provider>/artists/<aid>/albums')
@use_provider
def albums_of_artist(req, provider, aid):
    """show all albums of an artist identified by artist id"""
    artist = get_model_or_raise(req.ctx['library'], provider, ModelType.artist, aid)
    if isinstance(provider, SupportsArtistAlbumsReader):
        reader = provider.artist_create_albums_rd(artist)
        return reader.readall()
    raise HandlerException(f"provider:{provider.identifier} does not support"
                           f" {SupportsArtistAlbumsReader}")
