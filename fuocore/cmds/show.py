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

from .base import AbstractHandler
from .helpers import (
    show_song, show_song_json, show_artist, show_album, show_user,
    show_playlist
)

logger = logging.getLogger(__name__)


router = Router()
route = router.route


class ShowHandler(AbstractHandler):
    cmds = 'show'

    def handle(self, cmd, output_format):
        if cmd.args:
            furi = cmd.args[0]
        else:
            furi = 'fuo://'
        r = urlparse(furi)
        path = '/{}{}'.format(r.netloc, r.path)
        logger.debug('请求 path: {}'.format(path))
        rv = router.dispatch(path, {'library': self.library, 'output_format': output_format})
        return rv


@route('/')
def list_providers(req):
    provider_names = (provider.name for provider in
                      req.ctx['library'].list())
    return '\n'.join(('fuo://' + name for name in provider_names))


@route('/<provider>/songs/<sid>')
def song_detail(req, provider, sid):
    provider = req.ctx['library'].get(provider)
    song = provider.Song.get(sid)
    if song is not None:
        output_format = req.ctx['output_format']
        if output_format == "plain":
            return show_song(song)
        else:
            return show_song_json(song)


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
    return show_artist(artist)


@route('/<provider>/albums/<bid>')
def album_detail(req, provider, bid):
    provider = req.ctx['library'].get(provider)
    album = provider.Album.get(bid)
    return show_album(album)


@route('/<provider>/users/<uid>')
def user_detail(req, provider, uid):
    provider = req.ctx['library'].get(provider)
    user = provider.User.get(uid)
    return show_user(user)


@route('/<provider>/playlists/<pid>')
def playlist_detail(req, provider, pid):
    provider = req.ctx['library'].get(provider)
    playlist = provider.Playlist.get(pid)
    return show_playlist(playlist)
