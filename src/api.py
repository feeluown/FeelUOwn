# -*- coding: utf8 -*-


from plugin.NetEase.normalize import NetEaseAPI as Api


"""
class Api(object):
    
    interfaces = ('netease', )

    def __init__(self):
        super().__init__()
        self.ne = NetEaseAPI()

    def login(self, username, pw, phone=False, is_remember=True):
        return self.ne.login(username, pw, phone)

    def get_song_detail(self, mid):
        return self.ne.song_detail(mid)

    def get_playlist_detail(self, pid):
        return self.ne.playlist_detail(pid)

"""