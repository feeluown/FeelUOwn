"""
feeluown.app.config
~~~~~~~~~~~~~~~~~

App configuration items.
"""

from feeluown.config import Config


def create_config() -> Config:
    config = Config()
    config.deffield('DEBUG', type_=bool, desc='是否为调试模式')
    config.deffield('VERBOSE', default=0, type_=int, desc='日志详细程度')
    config.deffield('RPC_PORT', default=23333, type_=int, desc='RPC 端口')
    config.deffield('PUBSUB_PORT', default=23334, type_=int, desc='PUBSUB 端口')
    config.deffield('WEB_PORT', default=23332, type_=int, desc='WEB 服务端口')
    config.deffield('ENABLE_WEB_SERVER', default=False, type_=bool)
    config.deffield('MODE', default=0x0000, desc='CLI or GUI 模式')
    config.deffield('THEME', default='auto', desc='auto/light/dark')
    config.deffield('ENABLE_NEW_HOMEPAGE', default=True, type_=bool)
    config.deffield(
        'NEW_HOMEPAGE_SETTINGS',
        type_=dict,
        default={
            'contents': [
                {'name': 'RecListDailySongs', 'provider': 'netease'},
                # {'name': 'RecACollectionOfSongs', 'provider': 'qqmusic'},
                {'name': 'RecListDailyPlaylists', 'provider': 'qqmusic'},
                {'name': 'RecACollectionOfVideos', 'provider': 'bilibili'},
            ]
        },
        desc='主页配置'
    )
    config.deffield('MPV_AUDIO_DEVICE', default='auto', desc='MPV 播放设备')
    config.deffield('COLLECTIONS_DIR', desc='本地收藏所在目录')
    config.deffield(
        'FORCE_MAC_HOTKEY',
        desc='强制开启 macOS 全局快捷键功能',
        warn='Will be remove in version 3.0'
    )
    config.deffield('LOG_TO_FILE', desc='将日志输出到文件中')
    config.deffield('AUDIO_SELECT_POLICY', default='hq<>')
    config.deffield('VIDEO_SELECT_POLICY', default='hd<>')
    config.deffield('ALLOW_LAN_CONNECT', type_=bool, default=False, desc='是否可以从局域网连接服务器')
    config.deffield('PROVIDERS_STANDBY', type_=list, default=None, desc='')

    # YTDL related fields are deprecated since v4.1.9. Disable them by default.
    config.deffield(
        'ENABLE_YTDL_AS_MEDIA_PROVIDER',
        type_=bool,
        default=False,
        desc='(Deprecated) YTDL 作为备用资源'
    )
    # For example::
    #    [
    #        {
    #            'name': 'match_source',
    #            'pattern': 'ytmusic',
    #            'http_proxy': 'http://127.0.0.1:7890',
    #            'ytdl_options': {
    #                'socket_timeout': 2,
    #            },
    #        },
    #    ]
    config.deffield('YTDL_RULES', type_=list, default=None, desc='(Deprecated)')

    # TODO(cosven): maybe
    # 1. when it is set to 2, find standby from other providers first.
    # 2. when it is set to 3, play it's MV model instead of using MV's media.
    config.deffield('ENABLE_MV_AS_STANDBY', type_=int, default=1, desc='MV 作为备用资源')
    config.deffield('ENABLE_TRAY', type_=bool, default=True, desc='启用系统托盘')
    config.deffield(
        'NOTIFY_ON_TRACK_CHANGED', type_=bool, default=False, desc='切换歌曲时显示桌面通知'
    )
    config.deffield('NOTIFY_DURATION', type_=int, default=3000, desc='桌面通知保留时长(ms)')
    config.deffield('PLAYBACK_CROSSFADE', type_=bool, default=False, desc='播放暂停淡入淡出')
    config.deffield(
        'PLAYBACK_CROSSFADE_DURATION', type_=int, default=500, desc='淡入淡出持续时间'
    )
    config.deffield(
        'OPENAI_API_BASEURL',
        type_=str,
        default='',
        desc='OpenAI API base url'
    )
    config.deffield('OPENAI_API_KEY', type_=str, default='', desc='OpenAI API key')
    config.deffield('OPENAI_MODEL', type_=str, default='', desc='OpenAI model name')
    # Not sure if AI_STANDBY_MATCHER may be activated unexpectedly.
    # And it may burn some money, let user enable it manually.
    config.deffield('ENABLE_AI_STANDBY_MATCHER', type_=bool, default=False, desc='')
    config.deffield(
        'AI_RADIO_PROMPT',
        type_=str,
        default='''\
你是一个音乐推荐系统。你根据用户的歌曲列表分析用户的喜好，给用户推荐一些歌。默认推荐5首歌。

有几个注意点
1. 不要推荐与用户播放列表中一模一样的歌曲。不要推荐用户不喜欢的歌曲。不要重复推荐。
2. 你返回的内容只应该有 JSON，其它信息都不需要。也不要用 markdown 格式返回。
3. 你推荐的歌曲需要使用类似这样的 JSON 格式
    [{"title": "xxx", "artists": ["yyy", "zzz"], "description": "推荐理由"}]
''',
        desc='AI 电台功能的提示词'
    )
    return config
