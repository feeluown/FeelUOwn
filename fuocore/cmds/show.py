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


def noexception_handler_default(obj_name, obj_identifier, obj):
    if obj is None:
        return "{} identified by {} is not found"\
            .format(obj_name, obj_identifier)
    return obj


def noexception_handler_lyric(obj_name, obj_identifier, obj):
    song, sid = obj, obj_identifier
    if song is None:
        return "{} identified by {} is not found"\
            .format(obj_name, sid)

    if song.lyric is None:
        return "no lyric for this song, enjoy it ~"

    return song.lyric.content


def noexception_handler_user(obj_name, obj_identifier, obj):
    user, uid = obj, obj_identifier
    if user is not None:
        return user
    elif uid == 'me':
        return "User is not logged in in current session(plugin)"
    else:
        return "No {} with uid {} ".format(obj_name, uid)


def noexception_handler_readerlist(obj_name, obj_identifier, obj):
    if obj is None:
        return "No {} found by {} "\
            .format(obj_name, obj_identifier)

    # quick and dirty implement
    if obj_name == 'playlists':
        return reader_to_list(to_reader(obj, "songs"))
    else:
        return reader_to_list(to_reader(obj, "albums"))


def get_from_provider(
        req,
        provider,
        obj_identifier,
        obj_name,
        handler=noexception_handler_default):
    provider_path_name = provider
    provider = req.ctx['library'].get(provider)

    if provider is None:
        return "No such provider : {}".format(provider_path_name)

    try:
        if obj_name == 'songs':
            obj = provider.Song.get(obj_identifier)
        elif obj_name == 'artists':
            obj = provider.Artist.get(obj_identifier)
        elif obj_name == 'ablums':
            obj = provider.Album.get(obj_identifier)
        elif obj_name == 'playlists':
            obj = provider.Playlist.get(obj_identifier)
        elif obj_name == 'users':
            if obj_identifier == 'me':
                obj = provider._user
            else:
                obj = provider.User.get(obj_identifier)
        else:
            obj = None
    except Exception:
        return "resource-{} identified by {} is unavailable in {}"\
            .format(obj_name, obj_identifier, provider.name)
    else:
        return handler(obj_name, obj_identifier, obj)


@route('/')
def list_providers(req):
    return req.ctx['library'].list()


@route('/<provider>/songs/<sid>')
def song_detail(req, provider, sid):
    return get_from_provider(req, provider, sid, "songs")


@route('/<provider>/songs/<sid>/lyric')
def lyric(req, provider, sid):
    return get_from_provider(req, provider, sid, "songs", noexception_handler_lyric)


@route('/<provider>/artists/<aid>')
def artist_detail(req, provider, aid):
    return get_from_provider(req, provider, aid, "artists")


@route('/<provider>/albums/<bid>')
def album_detail(req, provider, bid):
    return get_from_provider(req, provider, bid, "albums")


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
    return get_from_provider(req, provider, uid, "users", noexception_handler_user)


@route('/<provider>/playlists/<pid>')
def playlist_detail(req, provider, pid):
    return get_from_provider(req, provider, pid, "playlists")


@route('/<provider>/playlists/<pid>/songs')
def playlist_songs(req, provider, pid):
    return get_from_provider(
        req,
        provider,
        pid,
        "playlists",
        noexception_handler_readerlist
    )


'''
Issue #317
Description: fuo show enhancement -- show all albums of an artist identified by aid
example : fuo show fuo://<provider>/artists/<aid>/albums
'''


@route('/<provider>/artists/<aid>/albums')
def albums_of_artist(req, provider, aid):
    return get_from_provider(
        req,
        provider,
        aid,
        "artists",
        noexception_handler_readerlist
    )
