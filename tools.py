# -*- coding:utf8 -*-
'''
# =============================================================================
#      FileName: tools.py
#          Desc: 模拟浏览器
#        Author: cosven
#         Email: yinshaowen241@gmail.com
#      HomePage: www.cosven.com
#       Version: 0.0.1
#    LastChange: 2015-03-27 00:59:24
#       History:
# =============================================================================
'''


import urllib
import urllib2
import cookielib


class MyWeb():
    """
        模拟一个浏览器
    """
    def __init__(self):
        self.header = {
            'Host': 'music.163.com',
            'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
            'Referer': 'http://music.163.com/song?id=26599525',
            "User-Agent": "Opera/8.0 (Macintosh; PPC Mac OS X; U; en)"
        }
        self.cookie = cookielib.LWPCookieJar()
        self.cookie_support = urllib2.HTTPCookieProcessor(self.cookie)
        self.opener = urllib2.build_opener(self.cookie_support,
                                           urllib2.HTTPHandler)
        urllib2.install_opener(self.opener)

    def post(self, posturl, dictdata):
        """
        模拟post请求

        :param string posturl: url地址
        :param dict dictdata: 发送的数据
        """

        postdata = urllib.urlencode(dictdata)
        request = urllib2.Request(posturl, postdata, self.header)
        try:
            content = urllib2.urlopen(request)
            return content
        except Exception, e:
            print ("post:" + str(e))
            return None

    def get(self, url):
        """
        模拟get请求

        :param url: url地址
        :return content: 常使用read的方法来读取返回数据
        :rtype : instance or None
        """
        request = urllib2.Request(url, None, self.header)
        try:
            content = urllib2.urlopen(request)
            return content
        except Exception, e:
            print ("open:" + str(e))
            return None


if __name__ == "__main__":
    import hashlib
    web = MyWeb()
    url = 'http://music.163.com/api/login/'
    data = {
        'username': 'username',  # email
        'password': hashlib.md5('password').hexdigest(),  # password
        'rememberLogin': 'true'
    }
    res = web.post(url, data)
    print res.read()
    # url_add = 'http://music.163.com/api/playlist/manipulate/tracks'
    # data_add = {
    #     'tracks': '26599525', # music id
    #     'pid': '16199365',    # playlist id
    #     'trackIds': '["26599525"]', # music id str
    #     'op': 'add'   # opation
    # }
    # res_add = web.post(url_add, data_add)
    # print res_add.read()

    # 完了可以试着查看自己网易云音乐相应列表歌曲
