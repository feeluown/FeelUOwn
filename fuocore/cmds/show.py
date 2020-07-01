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

from fuocore.utils import reader_to_list, to_reader
from fuocore.router import Router

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
    return req.ctx['library'].list()


@route('/<provider>/songs/<sid>')
def song_detail(req, provider, sid):
    provider_path_name = provider
    provider = req.ctx['library'].get(provider)

    try:
        song = provider.Song.get(sid)
    except AttributeError:
        return "No such provider : {}-{}".format(provider.name, provider_path_name)
    # marshallow exception -- Validation Error
    except Exception:
        return "song identified by {} is unavailable in {} ".format(sid, provider.name)
    else:
        if song is None:
            return "song {} is not in local library".format(sid)
        return song


@route('/<provider>/songs/<sid>/lyric')
def lyric(req, provider, sid):
    provider_path_name = provider
    provider = req.ctx['library'].get(provider)

    try:
        song = provider.Song.get(sid)
    except AttributeError:
        return "No such provider : {}-{}".format(provider.name, provider_path_name)
    # marshallow exception -- Validation Error
    except Exception:
        return "song identified by {} is unavailable in {} ".format(sid, provider.name)
    else:
        if song is None:
            return "song {} is not in local library".format(sid)
        if song.lyric:
            return song.lyric.content
        return 'no lyric, enjoy it~'


@route('/<provider>/artists/<aid>')
def artist_detail(req, provider, aid):
    provider_path_name = provider
    provider = req.ctx['library'].get(provider)

    try:
        artist = provider.Artist.get(aid)
    except AttributeError:
        return "No such provider : {}-{}".format(provider.name, provider_path_name)
    except Exception:
        return "artist identified by {} is not found in {}".format(aid, provider.name)
    else:
        if artist is None:
            return "artist {} is not in local library".format(aid)
        return artist


@route('/<provider>/albums/<bid>')
def album_detail(req, provider, bid):
    provider_path_name = provider
    provider = req.ctx['library'].get(provider)

    try:
        album = provider.Album.get(bid)
    except AttributeError:
        return "No such provider : {}-{}".format(provider.name, provider_path_name)
    except Exception:
        return "album identified by {} in {} is unavailable".format(bid, provider.name)
    else:
        if album is None:
            return "album identified by {} in {} is unavailable"\
                .format(bid, provider.name)
        return album


'''
------------------------------------
Original Route -- get User by uid
example : fuo show fuo://<provider>/users/12345678
------------------------------------
Issue #317
Description: fuo show nehancement -- show info about current user
example : fuo show fuo://<provider>/users/me
'''


@route('/<provider>/users/<uid>')
def user_detail(req, provider, uid):
    provider_path_name = provider
    provider = req.ctx['library'].get(provider)

    try:
        if uid == 'me':
            user = provider._user
        else:
            user = provider.User.get(uid)
    except AttributeError:
        return "No such provider : {}-{}".format(provider.name, provider_path_name)
    except Exception:
        return "No user identified by {} in {}".format(uid, provider.name)
    else:
        if user is not None:
            return user
        elif uid == 'me':
            return "User is not logged in in current session(plugin) {}-{}"\
                .format(provider.name, provider_path_name)
        else:
            return "No user in local"


@route('/<provider>/playlists/<pid>')
def playlist_detail(req, provider, pid):
    provider_path_name = provider
    provider = req.ctx['library'].get(provider)

    try:
        playlist = provider.Playlist.get(pid)
    except AttributeError:
        return "No such provider : {}-{}".format(provider.name, provider_path_name)
    except Exception:
        return "No playlist found by {} in {} ".format(pid, provider.name)
    else:
        if playlist is None:
            return "No playlist found by {} in {} ".format(pid, provider.name)
        return playlist


@route('/<provider>/playlists/<pid>/songs')
def playlist_songs(req, provider, pid):
    provider_path_name = provider
    provider = req.ctx['library'].get(provider)

    try:
        playlist = provider.Playlist.get(pid)
    except AttributeError:
        return "No such provider : {}-{}".format(provider.name, provider_path_name)
    except Exception:
        return "No playlist found by {} in {} ".format(pid, provider.name)
    else:
        if playlist is None:
            return "No playlist found by {} in {} ".format(pid, provider.name)
        songs = reader_to_list(to_reader(playlist, "songs"))
        return songs


'''
Issue #317
Description: fuo show enhancement -- show all albums of an artist identified by aid
example : fuo show fuo://<provider>/artists/<aid>/albums
'''


@route('/<provider>/artists/<aid>/albums')
def albums_of_artist(req, provider, aid):
    provider_path_name = provider
    provider = req.ctx['library'].get(provider)

    try:
        artist = provider.Artist.get(aid)
    except AttributeError:
        return "No such provider : {}-{}".format(provider.name, provider_path_name)
    except Exception:
        return "artist identified by {} is not found in {}".format(aid, provider.name)
    else:
        if artist is not None:
            albums = reader_to_list(to_reader(artist, "albums"))
            return albums
        return "artist identified by {} is not found in {}".format(aid, provider.name)