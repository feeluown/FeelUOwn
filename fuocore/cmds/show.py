"""
fuocore.cmds.show
~~~~~~~~~~~~~~~~~

处理 ``show`` 命令::

    show fuo://               # 列出所有 provider
    show fuo://local/songs    # 显示本地所有歌曲
    show fuo://local/songs/1  # 显示一首歌的详细信息
"""
import logging
from urllib.parse import urlparse

from fuocore.router import Router
from fuocore.utils import reader_to_list, to_reader
from fuocore.cmds.helpers import RenderNode

from .base import AbstractHandler

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
        rv = router.dispatch(path, {'library': self.library})
        return rv


@route('/')
def list_providers(req):
    class ProviderDisplay:
        def __init__(self, provider):
            self.name = provider.name
            self.identifier = provider.identifier

        def to_dict(self, **_):
            return {"uri": str(self),
                    "name": self.name}

        def to_str(self, **_):
            return self.name

        def __str__(self):
            return "fuo://" + self.identifier

    # noinspection PyTypeChecker
    return [RenderNode(ProviderDisplay(provider))
            for provider in req.ctx["library"].list()]


@route('/<provider>/songs/<sid>')
def song_detail(req, provider, sid):
    provider = req.ctx['library'].get(provider)
    song = provider.Song.get(sid)
    if song is not None:
        return song


@route('/<provider>/songs/<sid>/lyric')
def lyric(req, provider, sid):
    provider = req.ctx['library'].get(provider)
    song = provider.Song.get(sid)
    if song.lyric:
        return song.lyric.content
    return ''


@route('/<provider>/artists/<aid>')
def artist_detail(req, provider, aid):
    provider = req.ctx['library'].get(provider)
    artist = provider.Artist.get(aid)
    return artist


@route('/<provider>/albums/<bid>')
def album_detail(req, provider, bid):
    provider = req.ctx['library'].get(provider)
    album = provider.Album.get(bid)
    return album


@route('/<provider>/users/<uid>')
def user_detail(req, provider, uid):
    provider = req.ctx['library'].get(provider)
    user = provider.User.get(uid)
    return user


@route('/<provider>/playlists/<pid>')
def playlist_detail(req, provider, pid):
    provider = req.ctx['library'].get(provider)
    playlist = provider.Playlist.get(pid)
    return playlist


@route('/<provider>/playlists/<pid>/songs')
def playlist_songs(req, provider, pid):
    provider = req.ctx['library'].get(provider)
    playlist = provider.Playlist.get(pid)
    songs = reader_to_list(to_reader(playlist, "songs"))
    return songs or []
