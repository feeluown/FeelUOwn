def can_convert_chinese():
    try:
        import inlp.convert.chinese  # noqa
    except ImportError:
        return False
    return True


def convert_chinese(s: str, lang):
    """Simple to traditional, or reverse.

    Please ensure can_convert_chinese is True before invoke this function.

    Note, this feature is available only if the `inlp` package is installed.
    """

    import inlp.convert.chinese as cv  # noqa

    try:
        # I don't know what 'auto' refers to.
        assert lang in ['auto', 'cn', 'tc']

        if lang == 'cn':
            return cv.t2s(s)
        elif lang == 'tc':
            return cv.s2t(s)
        return s
    except:  # noqa
        return s
