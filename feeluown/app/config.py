"""
feeluown.app.config
~~~~~~~~~~~~~~~~~

App configuration items.
"""

from feeluown.config import Config
from feeluown.i18n import t


def create_config() -> Config:
    config = Config()
    config.deffield(
        "DEBUG",
        type_=bool,
        desc=t("debug-desc"),
    )
    config.deffield(
        "VERBOSE",
        default=0,
        type_=int,
        desc=t("verbose-desc"),
    )
    config.deffield(
        "RPC_PORT",
        default=23333,
        type_=int,
        desc=t("rpc-port-desc"),
    )
    config.deffield(
        "PUBSUB_PORT",
        default=23334,
        type_=int,
        desc=t("pubsub-port-desc"),
    )
    config.deffield(
        "WEB_PORT",
        default=23332,
        type_=int,
        desc=t("web-port-desc"),
    )
    config.deffield(
        "ENABLE_WEB_SERVER",
        default=False,
        type_=bool,
    )
    config.deffield(
        "MODE",
        default=0x0000,
        desc=t("mode-desc"),
    )
    config.deffield(
        "THEME",
        default="auto",
        desc=t("theme-desc"),
    )
    config.deffield(
        "ENABLE_NEW_HOMEPAGE",
        default=True,
        type_=bool,
    )
    config.deffield(
        "NEW_HOMEPAGE_SETTINGS",
        type_=dict,
        default={
            "contents": [
                {"name": "RecListDailySongs", "provider": "netease"},
                # {'name': 'RecACollectionOfSongs', 'provider': 'qqmusic'},
                {"name": "RecListDailyPlaylists", "provider": "qqmusic"},
                {"name": "RecACollectionOfVideos", "provider": "bilibili"},
            ]
        },
        desc=t("new-homepage-settings-desc"),
    )
    config.deffield(
        "MPV_AUDIO_DEVICE",
        default="auto",
        desc=t("mpv-audio-device-desc"),
    )
    config.deffield(
        "COLLECTIONS_DIR",
        desc=t("collections-dir-desc"),
    )
    config.deffield(
        "FORCE_MAC_HOTKEY",
        desc=t("force-mac-hotkey-desc"),
        warn="Will be remove in version 3.0",
    )
    config.deffield(
        "LOG_TO_FILE",
        desc=t("log-to-file-desc"),
    )
    config.deffield(
        "AUDIO_SELECT_POLICY",
        default="hq<>",
    )
    config.deffield(
        "VIDEO_SELECT_POLICY",
        default="hd<>",
    )
    config.deffield(
        "ALLOW_LAN_CONNECT",
        type_=bool,
        default=False,
        desc=t("allow-lan-connect-desc"),
    )
    config.deffield(
        "PROVIDERS_STANDBY",
        type_=list,
        default=None,
        desc="",
    )

    # YTDL related fields are deprecated since v4.1.9. Disable them by default.
    config.deffield(
        "ENABLE_YTDL_AS_MEDIA_PROVIDER",
        type_=bool,
        default=False,
        desc=t("enable-ytdl-as-media-provider-desc"),
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
    config.deffield(
        "YTDL_RULES",
        type_=list,
        default=None,
        desc=t("ytdl-rules-desc"),
    )

    # TODO(cosven): maybe
    # 1. when it is set to 2, find standby from other providers first.
    # 2. when it is set to 3, play it's MV model instead of using MV's media.
    config.deffield(
        "ENABLE_MV_AS_STANDBY",
        type_=int,
        default=1,
        desc=t("enable-mv-as-standby-desc"),
    )
    config.deffield(
        "ENABLE_TRAY",
        type_=bool,
        default=True,
        desc=t("enable-tray-desc"),
    )
    config.deffield(
        "NOTIFY_ON_TRACK_CHANGED",
        type_=bool,
        default=False,
        desc=t("notify-on-track-changed-desc"),
    )
    config.deffield(
        "NOTIFY_DURATION",
        type_=int,
        default=3000,
        desc=t("notify-duration-desc"),
    )
    config.deffield(
        "PLAYBACK_CROSSFADE",
        type_=bool,
        default=False,
        desc=t("playback-crossfade-desc"),
    )
    config.deffield(
        "PLAYBACK_CROSSFADE_DURATION",
        type_=int,
        default=500,
        desc=t("playback-crossfade-desc"),
    )
    config.deffield(
        "OPENAI_API_BASEURL",
        type_=str,
        default="",
        desc=t("openai-api-baseurl-desc"),
    )
    config.deffield(
        "OPENAI_API_KEY",
        type_=str,
        default="",
        desc=t("openai-api-key-desc"),
    )
    config.deffield(
        "OPENAI_MODEL",
        type_=str,
        default="",
        desc=t("openai-model-desc"),
    )
    # Not sure if AI_STANDBY_MATCHER may be activated unexpectedly.
    # And it may burn some money, let user enable it manually.
    config.deffield(
        "ENABLE_AI_STANDBY_MATCHER",
        type_=bool,
        default=False,
        desc="",
    )
    config.deffield(
        "AI_RADIO_PROMPT",
        type_=str,
        default="你是一个音乐播放器智能助手。",
        desc=t("ai-radio-prompt-desc"),
    )
    config.deffield(
        "ENABLE_REPLACE_PLAYLIST_ON_DBLCLICK",
        type_=bool,
        default=True,
        desc=t("enable-replace-playlist-on-dblclick-desc"),
    )
    return config
