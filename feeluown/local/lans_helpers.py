import logging


logger = logging.getLogger(__name__)


def core_lans(str, lans):
    try:
        assert lans in ['auto', 'cn', 'tc']
        if lans in ['cn', 'tc']:
            import inlp.convert.chinese as cv
            return cv.t2s(str) if lans == 'cn' else cv.s2t(str)
        else:
            return str
    except Exception as e:
        logger.warning(e)
        return str
