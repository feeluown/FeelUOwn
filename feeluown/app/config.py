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
    config.deffield('MPV_AUDIO_DEVICE', default='auto', desc='MPV 播放设备')
    config.deffield('COLLECTIONS_DIR',  desc='本地收藏所在目录')
    config.deffield('FORCE_MAC_HOTKEY', desc='强制开启 macOS 全局快捷键功能',
                    warn='Will be remove in version 3.0')
    config.deffield('LOG_TO_FILE', desc='将日志输出到文件中')
    config.deffield('AUDIO_SELECT_POLICY', default='hq<>')
    config.deffield('VIDEO_SELECT_POLICY', default='hd<>')
    config.deffield('ALLOW_LAN_CONNECT', type_=bool, default=False, desc='是否可以从局域网连接服务器')
    config.deffield('PROVIDERS_STANDBY', type_=list, default=None, desc='')
    config.deffield('ENABLE_TRAY', type_=bool, default=True, desc='启用系统托盘')
    config.deffield('NOTIFY_ON_TRACK_CHANGED', type_=bool, default=False,
                    desc='切换歌曲时显示桌面通知')
    config.deffield('NOTIFY_DURATION', type_=int, default=3000, desc='桌面通知保留时长(ms)')
    return config
