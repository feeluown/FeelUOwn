from mutagen.id3 import _specs


def patch_mutagen():
    old_decode_terminated = _specs.decode_terminated

    def decode_terminated(data, encoding, strict=True):
        """
        国内部分歌曲的 id3 信息是使用 GBK 编码，但是它的元信息显示自己是
        latin1 编码，所以 mutagen 解析的时候会返回不正确的结果。

        这里，我们没有选择重新实现原函数，而是对原函数的返回进行加工，
        这样可以比较好地确保我们的实现不会影响到 mutagen 的其它逻辑。
        但这样实现有一个问题，原函数已经进行过 decode 和 encode，我们这里又重复
        encode 和 decode，理论上会带来一定的性能损耗，欢迎有兴趣的同鞋进行优化。

        ps: 根据 id3 2.3/2.4 的规范，gbk 编码 *似乎* 本来就是非法的，
        规范上说只支持这四种： latin1, utf16, utf_16_be, utf8，
        mutagen 确实也是按照 spec 来实现的，但现实很残酷。
        """
        orig_value, data = old_decode_terminated(data, encoding, strict)
        value = orig_value
        if encoding == 'latin1':
            value = orig_value.encode('latin1')
            # 参考 deepin-music-player 项目 easymp3.py 实现
            for codec in ['gbk', 'big5', 'utf-8', 'iso-8559-15', 'cp1251']:
                try:
                    value = value.decode(codec)
                except (UnicodeDecodeError, LookupError):
                    # decode failed or codec not found
                    pass
                else:
                    break
            else:
                value = orig_value
        return value, data

    _specs.decode_terminated = decode_terminated
