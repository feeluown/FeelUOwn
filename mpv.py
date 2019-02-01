# -*- coding: utf-8 -*-
#
# Python MPV library module
# Copyright (C) 2017 Sebastian Götte <code@jaseg.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Modified by cosven <cosven.yin@gmail.com>.

from ctypes import *
import ctypes.util
import threading
import os
import sys
from warnings import warn
from functools import partial

# vim: ts=4 sw=4 et

if os.name == 'nt':
    backend = CDLL(ctypes.util.find_library('mpv-1.dll'))
    fs_enc = 'utf-8'
else:
    backend = CDLL(ctypes.util.find_library('mpv'))
    fs_enc = sys.getfilesystemencoding()


class MpvHandle(c_void_p):
    pass

class MpvOpenGLCbContext(c_void_p):
    pass


class ErrorCode(object):
    """ For documentation on these, see mpv's libmpv/client.h """
    SUCCESS                 = 0
    EVENT_QUEUE_FULL        = -1
    NOMEM                   = -2
    UNINITIALIZED           = -3
    INVALID_PARAMETER       = -4
    OPTION_NOT_FOUND        = -5
    OPTION_FORMAT           = -6
    OPTION_ERROR            = -7
    PROPERTY_NOT_FOUND      = -8
    PROPERTY_FORMAT         = -9
    PROPERTY_UNAVAILABLE    = -10
    PROPERTY_ERROR          = -11
    COMMAND                 = -12

    EXCEPTION_DICT = {
             0:     None,
            -1:     lambda *a: MemoryError('mpv event queue full', *a),
            -2:     lambda *a: MemoryError('mpv cannot allocate memory', *a),
            -3:     lambda *a: ValueError('Uninitialized mpv handle used', *a),
            -4:     lambda *a: ValueError('Invalid value for mpv parameter', *a),
            -5:     lambda *a: AttributeError('mpv option does not exist', *a),
            -6:     lambda *a: TypeError('Tried to set mpv option using wrong format', *a),
            -7:     lambda *a: ValueError('Invalid value for mpv option', *a),
            -8:     lambda *a: AttributeError('mpv property does not exist', *a),
            -9:     lambda *a: TypeError('Tried to set mpv property using wrong format', *a),
            -10:    lambda *a: AttributeError('mpv property is not available', *a),
            -11:    lambda *a: ValueError('Invalid value for mpv property', *a),
            -12:    lambda *a: SystemError('Error running mpv command', *a)
        }

    @staticmethod
    def default_error_handler(ec, *args):
        return ValueError(_mpv_error_string(ec).decode('utf-8'), ec, *args)

    @classmethod
    def raise_for_ec(kls, func, *args):
        ec = func(*args)
        ec = 0 if ec > 0 else ec
        ex = kls.EXCEPTION_DICT.get(ec , kls.default_error_handler)
        if ex:
            raise ex(ec, *args)


class MpvFormat(c_int):
    NONE        = 0
    STRING      = 1
    OSD_STRING  = 2
    FLAG        = 3
    INT64       = 4
    DOUBLE      = 5
    NODE        = 6
    NODE_ARRAY  = 7
    NODE_MAP    = 8

    def __repr__(self):
        return ['NONE', 'STRING', 'OSD_STRING', 'FLAG', 'INT64', 'DOUBLE', 'NODE', 'NODE_ARRAY', 'NODE_MAP'][self.value]



class MpvEventID(c_int):
    NONE                    = 0
    SHUTDOWN                = 1
    LOG_MESSAGE             = 2
    GET_PROPERTY_REPLY      = 3
    SET_PROPERTY_REPLY      = 4
    COMMAND_REPLY           = 5
    START_FILE              = 6
    END_FILE                = 7
    FILE_LOADED             = 8
    TRACKS_CHANGED          = 9
    TRACK_SWITCHED          = 10
    IDLE                    = 11
    PAUSE                   = 12
    UNPAUSE                 = 13
    TICK                    = 14
    SCRIPT_INPUT_DISPATCH   = 15
    CLIENT_MESSAGE          = 16
    VIDEO_RECONFIG          = 17
    AUDIO_RECONFIG          = 18
    METADATA_UPDATE         = 19
    SEEK                    = 20
    PLAYBACK_RESTART        = 21
    PROPERTY_CHANGE         = 22
    CHAPTER_CHANGE          = 23

    ANY = ( SHUTDOWN, LOG_MESSAGE, GET_PROPERTY_REPLY, SET_PROPERTY_REPLY, COMMAND_REPLY, START_FILE, END_FILE,
            FILE_LOADED, TRACKS_CHANGED, TRACK_SWITCHED, IDLE, PAUSE, UNPAUSE, TICK, SCRIPT_INPUT_DISPATCH,
            CLIENT_MESSAGE, VIDEO_RECONFIG, AUDIO_RECONFIG, METADATA_UPDATE, SEEK, PLAYBACK_RESTART, PROPERTY_CHANGE,
            CHAPTER_CHANGE )

class MpvSubApi(c_int):
    MPV_SUB_API_OPENGL_CB   = 1

class MpvEvent(Structure):
    _fields_ = [('event_id', MpvEventID),
                ('error', c_int),
                ('reply_userdata', c_ulonglong),
                ('data', c_void_p)]

    def as_dict(self):
        dtype = {MpvEventID.END_FILE:               MpvEventEndFile,
                MpvEventID.PROPERTY_CHANGE:         MpvEventProperty,
                MpvEventID.GET_PROPERTY_REPLY:      MpvEventProperty,
                MpvEventID.LOG_MESSAGE:             MpvEventLogMessage,
                MpvEventID.SCRIPT_INPUT_DISPATCH:   MpvEventScriptInputDispatch,
                MpvEventID.CLIENT_MESSAGE:          MpvEventClientMessage
            }.get(self.event_id.value, None)
        return {'event_id': self.event_id.value,
                'error': self.error,
                'reply_userdata': self.reply_userdata,
                'event': cast(self.data, POINTER(dtype)).contents.as_dict() if dtype else None}

class MpvEventProperty(Structure):
    _fields_ = [('name', c_char_p),
                ('format', MpvFormat),
                ('data', c_void_p)]
    def as_dict(self):
        if self.format.value == MpvFormat.STRING:
            proptype, _access = ALL_PROPERTIES.get(self.name, (str, None))
            return {'name': self.name.decode('utf-8'),
                    'format': self.format,
                    'data': self.data,
                    'value': proptype(cast(self.data, POINTER(c_char_p)).contents.value.decode('utf-8'))}
        else:
            return {'name': self.name.decode('utf-8'),
                    'format': self.format,
                    'data': self.data}

class MpvEventLogMessage(Structure):
    _fields_ = [('prefix', c_char_p),
                ('level', c_char_p),
                ('text', c_char_p)]

    def as_dict(self):
        return { 'prefix': self.prefix.decode('utf-8'),
                 'level':  self.level.decode('utf-8'),
                 'text':   self.text.decode('utf-8').rstrip() }

class MpvEventEndFile(c_int):
    EOF_OR_INIT_FAILURE = 0
    RESTARTED           = 1
    ABORTED             = 2
    QUIT                = 3

    def as_dict(self):
        return {'reason': self.value}

class MpvEventScriptInputDispatch(Structure):
    _fields_ = [('arg0', c_int),
                ('type', c_char_p)]

    def as_dict(self):
        pass # TODO

class MpvEventClientMessage(Structure):
    _fields_ = [('num_args', c_int),
                ('args', POINTER(c_char_p))]

    def as_dict(self):
        return { 'args': [ self.args[i].value for i in range(self.num_args.value) ] }

WakeupCallback = CFUNCTYPE(None, c_void_p)

OpenGlCbUpdateFn = CFUNCTYPE(None, c_void_p)
OpenGlCbGetProcAddrFn = CFUNCTYPE(None, c_void_p, c_char_p)

def _handle_func(name, args=[], res=None, context=MpvHandle):
    func = getattr(backend, name)
    if res is not None:
        func.restype = res
    func.argtypes = [context] + args
    def wrapper(*args):
        if res is not None:
            return func(*args)
        else:
            ErrorCode.raise_for_ec(func, *args)
    globals()['_'+name] = wrapper

def _handle_gl_func(name, args=[], res=None):
    _handle_func(name, args, res, MpvOpenGLCbContext)

backend.mpv_client_api_version.restype = c_ulong
def _mpv_client_api_version():
    ver = backend.mpv_client_api_version()
    return ver>>16, ver&0xFFFF

backend.mpv_free.argtypes = [c_void_p]
_mpv_free = backend.mpv_free

backend.mpv_create.restype = MpvHandle
_mpv_create = backend.mpv_create

_handle_func('mpv_create_client', [c_char_p], MpvHandle)
_handle_func('mpv_client_name', [], c_char_p)
_handle_func('mpv_initialize')
_handle_func('mpv_detach_destroy', [], c_int)
_handle_func('mpv_terminate_destroy', [], c_int)
_handle_func('mpv_load_config_file', [c_char_p])
_handle_func('mpv_suspend', [], c_int)
_handle_func('mpv_resume', [], c_int)
_handle_func('mpv_get_time_us', [], c_ulonglong)

_handle_func('mpv_set_option', [c_char_p, MpvFormat, c_void_p])
_handle_func('mpv_set_option_string', [c_char_p, c_char_p])

_handle_func('mpv_command', [POINTER(c_char_p)])
_handle_func('mpv_command_string', [c_char_p, c_char_p])
_handle_func('mpv_command_async', [c_ulonglong, POINTER(c_char_p)])

_handle_func('mpv_set_property', [c_char_p, MpvFormat, c_void_p])
_handle_func('mpv_set_property_string', [c_char_p, c_char_p])
_handle_func('mpv_set_property_async', [c_ulonglong, c_char_p, MpvFormat, c_void_p])
_handle_func('mpv_get_property', [c_char_p, MpvFormat, c_void_p])
_handle_func('mpv_get_property_string', [c_char_p], c_char_p)
_handle_func('mpv_get_property_osd_string', [c_char_p], c_char_p)
_handle_func('mpv_get_property_async', [c_ulonglong, c_char_p, MpvFormat])
_handle_func('mpv_observe_property', [c_ulonglong, c_char_p, MpvFormat])
_handle_func('mpv_unobserve_property', [c_ulonglong])

backend.mpv_event_name.restype = c_char_p
backend.mpv_event_name.argtypes = [c_int]
_mpv_event_name = backend.mpv_event_name

backend.mpv_error_string.restype = c_char_p
backend.mpv_error_string.argtypes = [c_int]
_mpv_error_string = backend.mpv_error_string

_handle_func('mpv_request_event', [MpvEventID, c_int])
_handle_func('mpv_request_log_messages', [c_char_p])
_handle_func('mpv_wait_event', [c_double], POINTER(MpvEvent))
_handle_func('mpv_wakeup', [], c_int)
_handle_func('mpv_set_wakeup_callback', [WakeupCallback, c_void_p], c_int)
_handle_func('mpv_get_wakeup_pipe', [], c_int)

_handle_func('mpv_get_sub_api', [MpvSubApi], c_void_p)

_handle_gl_func('mpv_opengl_cb_set_update_callback', [OpenGlCbUpdateFn, c_void_p])
_handle_gl_func('mpv_opengl_cb_init_gl', [c_char_p, OpenGlCbGetProcAddrFn, c_void_p], c_int)
_handle_gl_func('mpv_opengl_cb_draw', [c_int, c_int, c_int], c_int);
_handle_gl_func('mpv_opengl_cb_render', [c_int, c_int], c_int);
_handle_gl_func('mpv_opengl_cb_report_flip', [c_ulonglong], c_int);
_handle_gl_func('mpv_opengl_cb_uninit_gl', [], c_int);


class ynbool(object):
    def __init__(self, val=False):
        self.val = bool(val and val not in (b'no', 'no'))

    def __bool__(self):
        return bool(self.val)
    # Python 2 only:
    __nonzero__ = __bool__

    def __str__(self):
        return 'yes' if self.val else 'no'

    def __repr__(self):
        return str(self.val)

    def __eq__(self, other):
        return str(self) == other or bool(self) == other

def _ensure_encoding(possibly_bytes):
    return possibly_bytes.decode('utf-8') if type(possibly_bytes) is bytes else possibly_bytes


def _event_generator(handle):
    while True:
        event = _mpv_wait_event(handle, -1).contents
        if event.event_id.value == MpvEventID.NONE:
            raise StopIteration()
        yield event

def load_lua():
    """ Use this function if you intend to use mpv's built-in lua interpreter. This is e.g. needed for playback of
    youtube urls. """
    CDLL('liblua.so', mode=RTLD_GLOBAL)


def _event_loop(event_handle, playback_cond, event_callbacks, property_handlers, log_handler):
    for event in _event_generator(event_handle):
        try:
            devent = event.as_dict() # copy data from ctypes
            eid = devent['event_id']
            if eid in (MpvEventID.SHUTDOWN, MpvEventID.END_FILE):
                with playback_cond:
                    playback_cond.notify_all()
            if eid == MpvEventID.PROPERTY_CHANGE:
                pc, handlerid  = devent['event'], devent['reply_userdata']&0Xffffffffffffffff
                if handlerid in property_handlers:
                    name = pc['name']
                    if 'value' in pc:
                        proptype, _access = ALL_PROPERTIES[name]
                        property_handlers[handlerid](name, proptype(_ensure_encoding(pc['value'])))
                    else:
                        property_handlers[handlerid](name, pc['data'], pc['format'])
            if eid == MpvEventID.LOG_MESSAGE and log_handler is not None:
                ev = devent['event']
                log_handler(ev['level'], ev['prefix'], ev['text'])
            for callback in event_callbacks:
                callback(devent)
            if eid == MpvEventID.SHUTDOWN:
                _mpv_detach_destroy(event_handle)
                return
        except:
            pass # It seems that when this thread runs into an exception, the MPV core is not able to terminate properly
                 # anymore. FIXME

class MPV(object):
    """ See man mpv(1) for the details of the implemented commands. """
    def __init__(self, log_handler=None, **kwargs):
        """ Create an MPV instance.

        Any kwargs given will be passed to mpv as options. """

        self.handle = _mpv_create()

        _mpv_set_option_string(self.handle, b'audio-display', b'no')
        istr = lambda o: ('yes' if o else 'no') if type(o) is bool else str(o)
        for k,v in kwargs.items():
            _mpv_set_option_string(self.handle, k.replace('_', '-').encode('utf-8'), istr(v).encode('utf-8'))
        _mpv_initialize(self.handle)

        self.event_callbacks = []
        self._property_handlers = {}
        self._playback_cond = threading.Condition()
        self._event_handle = _mpv_create_client(self.handle, b'mpv-python-event-handler-thread')
        loop = partial(_event_loop,
                self._event_handle, self._playback_cond, self.event_callbacks, self._property_handlers, log_handler)
        self._event_thread = threading.Thread(target=loop, name='MPVEventHandlerThread')
        self._event_thread.setDaemon(True)
        self._event_thread.start()

        if log_handler is not None:
            self.set_loglevel('terminal-default')

    def wait_for_playback(self):
        """ Waits until playback of the current title is paused or done """
        with self._playback_cond:
            self._playback_cond.wait()

    def __del__(self):
        if self.handle:
            self.terminate()

    def terminate(self):
        self.handle, handle = None, self.handle
        _mpv_terminate_destroy(handle)
        self._event_thread.join()

    def set_loglevel(self, level):
        _mpv_request_log_messages(self._event_handle, level.encode('utf-8'))

    def command(self, name, *args):
        """ Execute a raw command """
        args = [name.encode('utf-8')] + [ (arg if type(arg) is bytes else str(arg).encode('utf-8'))
                for arg in args if arg is not None ] + [None]
        _mpv_command(self.handle, (c_char_p*len(args))(*args))

    def seek(self, amount, reference="relative", precision="default-precise"):
        self.command('seek', amount, reference, precision)

    def revert_seek(self):
        self.command('revert_seek');

    def frame_step(self):
        self.command('frame_step')

    def frame_back_step(self):
        self.command('frame_back_step')

    def _set_property(self, name, value):
        self.command('set_property', name, str(value))

    def _add_property(self, name, value=None):
        self.command('add_property', name, value)

    def _cycle_property(self, name, direction='up'):
        self.command('cycle_property', name, direction)

    def _multiply_property(self, name, factor):
        self.command('multiply_property', name, factor)

    def screenshot(self, includes='subtitles', mode='single'):
        self.command('screenshot', includes, mode)

    def screenshot_to_file(self, filename, includes='subtitles'):
        self.command('screenshot_to_file', filename.encode(fs_enc), includes)

    def playlist_next(self, mode='weak'):
        self.command('playlist_next', mode)

    def playlist_prev(self, mode='weak'):
        self.command('playlist_prev', mode)

    def loadfile(self, filename, mode='replace'):
        self.command('loadfile', filename.encode(fs_enc), mode)

    def loadlist(self, playlist, mode='replace'):
        self.command('loadlist', playlist.encode(fs_enc), mode)

    def playlist_clear(self):
        self.command('playlist_clear')

    def playlist_remove(self, index='current'):
        self.command('playlist_remove', index)

    def playlist_move(self, index1, index2):
        self.command('playlist_move', index1, index2)

    def run(self, command, *args):
        self.command('run', command, *args)

    def quit(self, code=None):
        self.command('quit', code)

    def quit_watch_later(self, code=None):
        self.command('quit_watch_later', code)

    def sub_add(self, filename):
        self.command('sub_add', filename.encode(fs_enc))

    def sub_remove(self, sub_id=None):
        self.command('sub_remove', sub_id)

    def sub_reload(self, sub_id=None):
        self.command('sub_reload', sub_id)

    def sub_step(self, skip):
        self.command('sub_step', skip)

    def sub_seek(self, skip):
        self.command('sub_seek', skip)

    def toggle_osd(self):
        self.command('osd')

    def show_text(self, string, duration='-', level=None):
        self.command('show_text', string, duration, level)

    def show_progress(self):
        self.command('show_progress')

    def discnav(self, command):
        self.command('discnav', command)

    def write_watch_later_config(self):
        self.command('write_watch_later_config')

    def overlay_add(self, overlay_id, x, y, file_or_fd, offset, fmt, w, h, stride):
        self.command('overlay_add', overlay_id, x, y, file_or_fd, offset, fmt, w, h, stride)

    def overlay_remove(self, overlay_id):
        self.command('overlay_remove', overlay_id)

    def script_message(self, *args):
        self.command('script_message', *args)

    def script_message_to(self, target, *args):
        self.command('script_message_to', target, *args)

    def observe_property(self, name, handler):
        hashval = c_ulonglong(hash(handler))
        self._property_handlers[hashval.value] = handler
        _mpv_observe_property(self._event_handle, hashval, name.encode('utf-8'), MpvFormat.STRING)

    def unobserve_property(self, handler):
        handlerid = hash(handler)
        _mpv_unobserve_property(self._event_handle, handlerid)
        if handlerid in self._property_handlers:
            del self._property_handlers[handlerid]

    @property
    def metadata(self):
        raise NotImplementedError

    @property
    def chapter_metadata(self):
        raise NotImplementedError

    @property
    def vf_metadata(self):
        raise NotImplementedError

    # Convenience functions
    def play(self, filename):
        self.loadfile(filename)

    # Complex properties

    _VIDEO_PARAMS_LIST = (
            ('pixelformat',     str),
            ('w',               int),
            ('h',               int),
            ('dw',              int),
            ('dh',              int),
            ('aspect',          float),
            ('par',             float),
            ('colormatrix',     str),
            ('colorlevels',     str),
            ('chroma-location', str),
            ('rotate',          int))

    @property
    def video_params(self):
        return self._get_dict('video-params/', self._VIDEO_PARAMS_LIST)

    @property
    def video_out_params(self):
        return self._get_dict('video-out-params/', self._VIDEO_PARAMS_LIST)

    @property
    def playlist(self):
        return self._get_list('playlist/', (('filename', str),))
    @property
    def track_list(self):
        return self._get_list('track-list/', (
                         ('id',                 int),
                         ('type',               str),
                         ('src-id',             int),
                         ('title',              str),
                         ('lang',               str),
                         ('albumart',           ynbool),
                         ('default',            ynbool),
                         ('external',           ynbool),
                         ('external-filename',  str),
                         ('codec',              str),
                         ('selected',           ynbool)))
    @property
    def chapter_list(self):
        return self._get_dict('chapter-list/', (('title', str), ('time', float)))

    def _get_dict(self, prefix, props):
        return { name: proptype(_ensure_encoding(_mpv_get_property_string(self.handle, (prefix+name).encode('utf-8')))) for name, proptype in props }

    def _get_list(self, prefix, props):
        count = int(_ensure_encoding(_mpv_get_property_string(self.handle, (prefix+'count').encode('utf-8'))))
        return [ self._get_dict(prefix+str(index)+'/', props) for index in range(count)]

    # TODO: af, vf properties
    # TODO: edition-list
    # TODO property-mapped options

ALL_PROPERTIES = {
        'osd-level':                   (int,    'rw'),
        'osd-scale':                   (float,  'rw'),
        'loop':                        (str,    'rw'),
        'loop-file':                   (str,    'rw'),
        'speed':                       (float,  'rw'),
        'filename':                    (str,    'r'),
        'file-size':                   (int,    'r'),
        'path':                        (str,    'r'),
        'media-title':                 (str,    'r'),
        'stream-pos':                  (int,    'rw'),
        'stream-end':                  (int,    'r'),
        'length':                      (float,  'r'),
        'duration':                    (float,  'r'),
        'avsync':                      (float,  'r'),
        'total-avsync-change':         (float,  'r'),
        'drop-frame-count':            (int,    'r'),
        'percent-pos':                 (float,  'rw'),
        'ratio-pos':                   (float,  'rw'),
        'time-pos':                    (float,  'rw'),
        'time-start':                  (float,  'r'),
        'time-remaining':              (float,  'r'),
        'playtime-remaining':          (float,  'r'),
        'chapter':                     (int,    'rw'),
        'edition':                     (int,    'rw'),
        'disc-titles':                 (int,    'r'),
        'disc-title':                  (str,    'rw'),
        'disc-menu-active':            (ynbool, 'r'),
        'chapters':                    (int,    'r'),
        'editions':                    (int,    'r'),
        'angle':                       (int,    'rw'),
        'pause':                       (ynbool, 'rw'),
        'core-idle':                   (ynbool, 'r'),
        'cache':                       (int,    'r'),
        'cache-size':                  (int,    'rw'),
        'pause-for-cache':             (ynbool, 'r'),
        'eof-reached':                 (ynbool, 'r'),
        'pts-association-mode':        (str,    'rw'),
        'hr-seek':                     (ynbool, 'rw'),
        'volume':                      (float,  'rw'),
        'mute':                        (ynbool, 'rw'),
        'audio-delay':                 (float,  'rw'),
        'audio-format':                (str,    'r'),
        'audio-codec':                 (str,    'r'),
        'audio-bitrate':               (float,  'r'),
        'audio-samplerate':            (int,    'r'),
        'audio-channels':              (str,    'r'),
        'aid':                         (str,    'rw'),
        'audio':                       (str,    'rw'), # alias for aid
        'balance':                     (float,  'rw'),
        'fullscreen':                  (ynbool, 'rw'),
        'deinterlace':                 (str,    'rw'),
        'colormatrix':                 (str,    'rw'),
        'colormatrix-input-range':     (str,    'rw'),
        'colormatrix-output-range':    (str,    'rw'),
        'colormatrix-primaries':       (str,    'rw'),
        'ontop':                       (ynbool, 'rw'),
        'border':                      (ynbool, 'rw'),
        'framedrop':                   (str,    'rw'),
        'gamma':                       (float,  'rw'),
        'brightness':                  (int,    'rw'),
        'contrast':                    (int,    'rw'),
        'saturation':                  (int,    'rw'),
        'hue':                         (int,    'rw'),
        'hwdec':                       (ynbool, 'rw'),
        'panscan':                     (float,  'rw'),
        'video-format':                (str,    'r'),
        'video-codec':                 (str,    'r'),
        'video-bitrate':               (float,  'r'),
        'width':                       (int,    'r'),
        'height':                      (int,    'r'),
        'dwidth':                      (int,    'r'),
        'dheight':                     (int,    'r'),
        'fps':                         (float,  'r'),
        'estimated-vf-fps':            (float,  'r'),
        'window-scale':                (float,  'rw'),
        'video-aspect':                (str,    'rw'),
        'osd-width':                   (int,    'r'),
        'osd-height':                  (int,    'r'),
        'osd-par':                     (float,  'r'),
        'vid':                         (str,    'rw'),
        'video':                       (str,    'rw'), # alias for vid
        'video-align-x':               (float,  'rw'),
        'video-align-y':               (float,  'rw'),
        'video-pan-x':                 (float,  'rw'),
        'video-pan-y':                 (float,  'rw'),
        'video-zoom':                  (float,  'rw'),
        'video-unscaled':              (ynbool, 'w'),
        'program':                     (int,    'w'),
        'sid':                         (str,    'rw'),
        'sub':                         (str,    'rw'), # alias for sid
        'secondary-sid':               (str,    'rw'),
        'sub-delay':                   (float,  'rw'),
        'sub-pos':                     (int,    'rw'),
        'sub-visibility':              (ynbool, 'rw'),
        'sub-forced-only':             (ynbool, 'rw'),
        'sub-scale':                   (float,  'rw'),
        'ass-use-margins':             (ynbool, 'rw'),
        'ass-vsfilter-aspect-compat':  (ynbool, 'rw'),
        'ass-style-override':          (str,    'rw'),
        'stream-capture':              (str,    'rw'),
        'tv-brightness':               (int,    'rw'),
        'tv-contrast':                 (int,    'rw'),
        'tv-saturation':               (int,    'rw'),
        'tv-hue':                      (int,    'rw'),
        'playlist-pos':                (int,    'rw'),
        'playlist-count':              (int,    'r'),
        'quvi-format':                 (str,    'rw'),
        'seekable':                    (ynbool, 'r')}

def bindproperty(MPV, name, proptype, access):
    def getter(self):
        cval = _mpv_get_property_string(self.handle, name.encode('utf-8'))
        if cval is None:
            return None
        rv = proptype(cval.decode('utf-8'))
#        _mpv_free(cval) FIXME
        return rv
    def setter(self, value):
        _mpv_set_property_string(self.handle, name.encode('utf-8'), str(proptype(value)).encode('utf-8'))
    def barf(*args):
        raise NotImplementedError('Access denied')
    setattr(MPV, name.replace('-', '_'), property(getter if 'r' in access else barf, setter if 'w' in access else barf))

for name, (proptype, access) in ALL_PROPERTIES.items():
    bindproperty(MPV, name, proptype, access)
