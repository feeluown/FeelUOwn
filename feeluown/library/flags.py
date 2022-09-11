from enum import IntFlag


class Flags(IntFlag):
    """
    NOTE: the flag value maybe changed in the future
    """
    none = 0x00000000

    get = 0x00000001
    batch = 0x00000002

    # Reader
    songs_rd = 0x00000010
    albums_rd = 0x00000020
    artists_rd = 0x00000040
    playlists_rd = 0x00000080

    multi_quality = 0x0001000
    similar = 0x00002000
    hot_comments = 0x00008000
    web_url = 0x00010000
    model_v2 = 0x00004000

    current_user = 0x00100000

    # Impl: x_add_song(x, song)
    add_song = 0x01000000
    remove_song = 0x02000000

    # Flags for Song
    lyric = 0x100000000000
    mv = 0x200000000000
