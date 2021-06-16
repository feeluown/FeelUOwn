from enum import IntFlag


class Flags(IntFlag):
    """
    NOTE: the flag value maybe changed in the future
    """
    none = 0x00000000

    get = 0x00000001
    batch = 0x00000002

    # Reader
    songs_g = 0x00000010
    albums_g = 0x00000020
    artists_g = 0x00000040
    playlist_g = 0x00000080

    multi_quality = 0x0001000
    similar = 0x00002000
    hot_comments = 0x00008000
    web_url = 0x00010000
    model_v2 = 0x00004000
    """
    provider uses ModelV2 for a specific resource
    """

    current_user = 0x00100000
