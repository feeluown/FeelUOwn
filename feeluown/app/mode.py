from enum import IntFlag


class AppMode(IntFlag):
    """
    When server mode is on, rpc server and pubsub server are both started.
    When gui mode is on, GUI window is created and shown. Server and gui mode
    can be both on. When cli mode is on, server and gui modes are off (currently).

    cli mode is *experimental* feature temporarily.
    """
    server = 0x0001  # 开启 Server
    gui = 0x0010     # 显示 GUI
    cli = 0x0100     # 命令行模式
