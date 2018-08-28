"""
fuocore.protocol.handlers.show
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

处理 ``show`` 命令::

    show fuo://               # 列出所有 provider
    show fuo://local/songs    # 显示本地所有歌曲
    show fuo://local/songs/1  # 显示一首歌的详细信息
"""
import logging
import re
from urllib.parse import urlparse

from .handlers import AbstractHandler
from .helpers import (
    show_song, show_artist, show_album, show_user,
    show_playlist
)

logger = logging.getLogger(__name__)


class NotFound(Exception):
    pass


class Router(object):
    rules = []
    handlers = {}

    @classmethod
    def register(cls, rule, handler):
        cls.rules.append(rule)
        cls.handlers[rule] = handler

    @classmethod
    def get_handler(cls, rule):
        return cls.handlers[rule]


def _validate_rule(rule):
    """简单的对 rule 进行校验

    TODO: 代码实现需要改进
    """
    if rule:
        if rule == '/':
            return
        parts = rule.split('/')
        if parts.count('') == 1:
            return
    raise ValueError('Invalid rule: {}'.format(rule))


def route(rule):
    """show handler router decorator

    example::

        @route('/<provider_name>/songs')
        def show_songs(provider_name):
            pass
    """
    _validate_rule(rule)

    def decorator(func):
        Router.register(rule, func)

        def wrapper(*args, **kwargs):
            func(*args, **kwargs)
        return wrapper
    return decorator


def regex_from_rule(rule):
    """为一个 rule 生成对应的正则表达式
    >>> regex_from_rule('/<provider>/songs')
    re.compile('^/(?P<provider>[^\\\/]+)/songs$')
    """
    kwargs_regex = re.compile(r'(<.*?>)')
    pattern = re.sub(
        kwargs_regex,
        lambda m: '(?P<{}>[^\/]+)'.format(m.group(0)[1:-1]),
        rule
    )
    regex = re.compile(r'^{}$'.format(pattern))
    return regex


def match(path, rules=Router.rules):
    """找到 path 对应的 rule，并解析其中的参数

    >>> match('/local/songs', rules=['/<p>/songs'])
    ('/<p>/songs', {'p': 'local'})

    :return: (rule, params) or None
    """
    for rule in rules:
        url_regex = regex_from_rule(rule)
        match = url_regex.match(path)
        if match:
            params = match.groupdict()
            return rule, params
    raise NotFound


def dispatch(req, rule, params):
    handler = Router.get_handler(rule)
    return handler(req, **params)


class ShowHandler(AbstractHandler):

    def handle(self, cmd):
        if cmd.args:
            furi = cmd.args[0]
        else:
            furi = 'fuo://'
        r = urlparse(furi)
        path = '/{}{}'.format(r.netloc, r.path)
        logger.debug('请求 path: {}'.format(path))
        try:
            rule, params = match(path)
        except NotFound as e:
            # FIXME: 抛一个合理的异常
            raise Exception('uri 不能被正确识别')
        return dispatch(self, rule, params)


@route('/')
def list_providers(req):
    provider_names = (provider.name for provider in
                      req.app.library.list())
    return '\n'.join(('fuo://' + name for name in provider_names))


@route('/<provider>/songs/<sid>')
def song_detail(req, provider, sid):
    provider = req.app.library.get(provider)
    song = provider.Song.get(sid)
    return show_song(song)


@route('/<provider>/songs/<sid>/lyric')
def lyric(req, provider, sid):
    provider = req.app.library.get(provider)
    song = provider.Song.get(sid)
    if song.lyric:
        return song.lyric.content
    return ''


@route('/<provider>/artists/<aid>')
def artist_detail(req, provider, aid):
    provider = req.app.library.get(provider)
    artist = provider.Artist.get(aid)
    return show_artist(artist)


@route('/<provider>/albums/<bid>')
def album_detail(req, provider, bid):
    provider = req.app.library.get(provider)
    album = provider.Album.get(bid)
    return show_album(album)


@route('/<provider>/users/<uid>')
def user_detail(req, provider, uid):
    provider = req.app.library.get(provider)
    user = provider.User.get(uid)
    return show_user(user)


@route('/<provider>/playlists/<pid>')
def playlist_detail(req, provider, pid):
    provider = req.app.library.get(provider)
    playlist = provider.Playlist.get(pid)
    return show_playlist(playlist)
