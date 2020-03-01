from bisect import bisect
from string import Formatter


widths = [
    (0, 1),
    (126, 1), (159, 0), (687, 1), (710, 0), (711, 1),
    (727, 0), (733, 1), (879, 0), (1154, 1), (1161, 0),
    (4347, 1), (4447, 2), (7467, 1), (7521, 0), (8369, 1),
    (8426, 0), (9000, 1), (9002, 2), (11021, 1), (12350, 2),
    (12351, 1), (12438, 2), (12442, 0), (19893, 2), (19967, 1),
    (55203, 2), (63743, 1), (64106, 2), (65039, 1), (65059, 0),
    (65131, 2), (65279, 1), (65376, 2), (65500, 1), (65510, 2),
    (120831, 1), (262141, 2), (1114109, 1),
]
points = [w[0] for w in widths]


def char_len(c):
    ord_code = ord(c)
    if ord_code == 0xe or ord_code == 0xf:
        return 0
    i = bisect(points, ord_code)
    return widths[i][1]


def _fit_text(text, length, filling=True):
    assert 80 >= length >= 5

    text_len = 0
    len_index_map = {}
    for i, c in enumerate(text):
        text_len += char_len(c)
        len_index_map[text_len] = i

    if text_len <= length:
        if filling:
            return text + (length - text_len) * ' '
        return text

    remain = length - 1
    if remain in len_index_map:
        return text[:(len_index_map[remain] + 1)] + '…'
    else:
        return text[:(len_index_map[remain - 1] + 1)] + ' …'


class WideFormatter(Formatter):
    """
    Custom string formatter that handles new format parameters:
    '_': _fit_text(*, filling=False)
    '+': _fit_text(*, filling=True)
    """

    def format(self, format_string, *args, **kwargs):
        return super().vformat(format_string, args, kwargs)

    def format_field(self, value, format_spec):
        if value is None:
            value = 'null'
        fmt_type = format_spec[0] if format_spec else None
        if fmt_type == "_":
            return _fit_text(value, int(format_spec[1:]), filling=False)
        elif fmt_type == "+":
            return _fit_text(value, int(format_spec[1:]), filling=True)
        return super().format_field(value, format_spec)
