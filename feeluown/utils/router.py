import re
from collections import namedtuple
from urllib.parse import parse_qsl, urlsplit


class NotFound(Exception):
    """
    No matched rule for path
    """


def match(url, rules):
    """Find the rule corresponding to the path and parse its parameters.

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
            # The result of parse_qsl may be [('a', 'b'), ('a', 'c')],
            # corresponding to the query string a=b&a=c.
            # We currently do not allow this case, so here we
            # temporarily convert the parsed results directly into a dict
            query = dict(parse_qsl(qs))
            params = match.groupdict()
            return rule, params, query
    raise NotFound(f"No matched rule for {path}")


def _validate_rule(rule):
    """Simple validation of rule

    TODO: code implementation needs improvement
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
        # TODO: Perhaps we could use weakref?
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
