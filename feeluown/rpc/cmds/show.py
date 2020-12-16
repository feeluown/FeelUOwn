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

from feeluown.utils.utils import to_readall_reader
from feeluown.utils.router import Router, NotFound
from feeluown.models.uri import NS_TYPE_MAP, TYPE_NS_MAP
from feeluown.models import ModelType

from .base import AbstractHandler
from .excs import CmdException

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
        path = '/{}{}'.format(r.netloc, r.path)
        logger.debug('请求 path: {}'.format(path))
        try:
            rv = router.dispatch(path, {'library': self.library})
        except NotFound:
            raise CmdException(f'path {path} not found')
        return rv


def get_model_or_raise(provider, model_type, model_id):
    ns = TYPE_NS_MAP[model_type]
    model_cls = provider.get_model_cls(model_type)
    model = model_cls.get(model_id)
    if model is None:
        raise CmdException(
            f'{ns}:{model_id} not found in provider:{provider.identifier}')
    return model


def use_provider(func):
    @wraps(func)
    def wrapper(req, **kwargs):
        provider_id = kwargs.pop('provider')
        provider = req.ctx['library'].get(provider_id)
        if provider is None:
            raise CmdException(f'provider:{provider_id} not found')
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
                    raise CmdException(
                        f'log in provider:{provider.identifier} first')
                return user
        model = get_model_or_raise(provider, model_type, model_id)
        return model


@route('/')
def list_providers(req):
    return req.ctx['library'].list()


for ns, model_type in NS_TYPE_MAP.items():
    create_model_handler(ns, model_type)


@route('/<provider>/songs/<sid>/lyric')
@use_provider
def lyric(req, provider, sid):
    song = get_model_or_raise(provider, ModelType.song, sid)
    if song.lyric is not None:
        return song.lyric.content
    return ''


@route('/<provider>/playlists/<pid>/songs')
@use_provider
def playlist_songs(req, provider, pid):
    playlist = get_model_or_raise(provider, ModelType.playlist, pid)
    return to_readall_reader(playlist, 'songs').readall()


@route('/<provider>/artists/<aid>/albums')
@use_provider
def albums_of_artist(req, provider, aid):
    """show all albums of an artist identified by artist id"""
    artist = get_model_or_raise(provider, ModelType.artist, aid)
    return to_readall_reader(artist, 'albums').readall()
