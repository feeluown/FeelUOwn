import re

from .cmd import Cmd
from .excs import HandlerException
from .base import AbstractHandler


class SubHandler(AbstractHandler):
    cmds = ('sub', )

    def handle(self, cmd: Cmd):
        return self.handle_sub(*cmd.args)

    def handle_sub(self, *topics):
        pubsub_gateway = self._app.pubsub_gateway

        matched_topics = []
        for topic in topics:
            # Keep backward compatibility.
            if topic.startswith('topic.'):
                topic = topic[6:]

            p = re.compile(rf'{topic}')
            for topic_name in pubsub_gateway.topics:
                m = p.match(topic_name)
                if m is not None and m.group(0) == topic_name:
                    matched_topics.append(topic_name)

            if matched_topics:
                for each in matched_topics:
                    pubsub_gateway.link(each, self.session)
            else:
                raise HandlerException(f"{topic}: topic not found")
