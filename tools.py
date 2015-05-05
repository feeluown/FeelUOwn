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


import urllib.request, urllib.parse, urllib.error
import http.cookiejar


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
        self.cookie = http.cookiejar.LWPCookieJar()
        self.cookie_support = urllib.request.HTTPCookieProcessor(self.cookie)
        self.opener = urllib.request.build_opener(self.cookie_support,
                                                  urllib.request.HTTPHandler)
        urllib.request.install_opener(self.opener)

    def post(self, posturl, dictdata):
        """
        模拟post请求

        :param string posturl: url地址
        :param dict dictdata: 发送的数据
        """

        postdata = urllib.parse.urlencode(dictdata)
        postdata = postdata.encode('utf-8')
        request = urllib.request.Request(posturl, postdata, self.header)
        try:
            content = urllib.request.urlopen(request)
            return content
        except Exception as e:
            print(str(e))
            return None

    def get(self, url):
        """
        模拟get请求

        :param url: url地址
        :return content: 常使用read的方法来读取返回数据
        :rtype : instance or None
        """
        request = urllib.request.Request(url, None, self.header)
        try:
            content = urllib.request.urlopen(request)
            return content
        except:
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
