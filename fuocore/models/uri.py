"""
model/uri transform

TODO: move fuocore.protocol.model_parser to fuocore.models.parser

.. warn::

   currently, the design of uri module is under investigation,
   we should only use only it in local provider.

experience:

1. Models should explicitly tell user what they support.
For exmaple: if a artist model support '/albums?type=eq',
the model should desclare they support type filter.
Currently, there is not way to achieve this.
"""

import asyncio
import re


class ResolverNotFound(Exception):
    pass


class NoReverseMatch(Exception):
    pass


class Resolver:

    loop = None
    library = None

    @classmethod
    def setup_aio_support(cls):
        cls.loop = asyncio.get_event_loop()


def resolve(uri, model=None):
    if model is None:
        library = Resolver.library
        parser = ModelParser(library)

        pids = [provider.identifier for provider in library.list()]
        ns_list = list(TYPE_NS_MAP.values())
        # currently, only allow local uri
        p = re.compile(r'^fuo://({})/({})/(\w+)'
                       .format('|'.join(pids), '|'.join(ns_list)))
        m = p.match(uri)
        if not m:
            raise ResolverNotFound('resolver-not-found for {}'.format(uri))
        model = parser.parse_line(m.group())
        path = uri[m.end():]
    else:
        path = uri
    for path_ in model.meta.paths:
        if path_ == path:
            method_name = 'resolve_' + path.replace('/', '_')
            handler = getattr(model, method_name)
            return handler()
    raise ResolverNotFound('resolver-not-found for {}/{}'.format(str(model), path))


def reverse(model, path=''):
    if path:
        if path not in model.meta.paths and path[1:] not in model.meta.fields:
            raise NoReverseMatch('no-reverse-match for model:{} path:{}'
                                 .format(model, path))
    return get_url(model) + (path if path else '')


from fuocore.protocol.model_parser import (
    get_url,
    ModelParser,
    TYPE_NS_MAP,
)  # noqa
