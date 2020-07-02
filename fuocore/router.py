import re
from collections import namedtuple
from urllib.parse import parse_qsl, urlsplit


class NotFound(Exception):
    """
    No matched rule for path
    """


def match(url, rules):
    """找到 path 对应的 rule，并解析其中的参数

    >>> match('/local/songs', rules=['/<p>/songs'])
    ('/<p>/songs', {'p': 'local'}, {})
    >>> match('/search?q=hello+world', rules=['/search'])
    ('/search', {}, {'q': 'hello world'})

    :return: (rule, params) or None
    """
    split_result = urlsplit(url)
    path = split_result.path
    qs = split_result.query
    for rule in rules:
        url_regex = regex_from_rule(rule)
        match = url_regex.match(path)
        if match:
            # parse_qsl 的结果有可能是 [('a', 'b'), ('a', 'c')],
            # 对应的 query string 是 a=b&a=c, 我们这里暂时不允许这种情况，
            # 所以这里暂时直接将解析的结果转换成字典
            query = dict(parse_qsl(qs))
            params = match.groupdict()
            return rule, params, query
    raise NotFound(f"No matched rule for {path}")


def _validate_rule(rule):
    """简单的对 rule 进行校验

    TODO: 代码实现需要改进
    """
    if rule:
        if rule == '/':
            return
        parts = rule.split('/')
        if parts.count('') == 1:
            return
    raise ValueError('Invalid rule: {}'.format(rule))


def regex_from_rule(rule):
    r"""为一个 rule 生成对应的正则表达式

    >>> regex_from_rule('/<provider>/songs')
    re.compile('^/(?P<provider>[^\\/]+)/songs$')
    """
    kwargs_regex = re.compile(r'(<.*?>)')
    pattern = re.sub(
        kwargs_regex,
        lambda m: r'(?P<{}>[^\/]+)'.format(m.group(0)[1:-1]),
        rule
    )
    regex = re.compile(r'^{}$'.format(pattern))
    return regex


Request = namedtuple('Request', ['uri', 'rule', 'params', 'query', 'ctx'])


class Router(object):
    def __init__(self):
        self.rules = []
        self.handlers = {}

    def register(self, rule, handler):
        self.rules.append(rule)
        # TODO: 或许可以使用 weakref?
        self.handlers[rule] = handler

    def route(self, rule):
        """show handler router decorator

        example::

            @route('/<provider_name>/songs')
            def show_songs(provider_name):
                pass
        """
        _validate_rule(rule)

        def decorator(func):
            self.register(rule, func)

            def wrapper(*args, **kwargs):
                func(*args, **kwargs)
            return wrapper
        return decorator

    def dispatch(self, uri, ctx):
        rule, params, query = match(uri, self.rules)
        handler = self.handlers[rule]
        req = Request(uri=uri, rule=rule, params=params, query=query, ctx=ctx)
        return handler(req, **params)
