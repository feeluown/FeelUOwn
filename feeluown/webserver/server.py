import asyncio
import json
import logging
from typing import List
from dataclasses import dataclass

from sanic import Sanic, json as jsonify, Websocket

from feeluown.app import get_app
from feeluown.serializers import serialize
from feeluown.server.pubsub import Gateway as PubsubGateway
from feeluown.server.handlers.cmd import Cmd
from feeluown.server.handlers.status import StatusHandler

logger = logging.getLogger(__name__)

sanic_app = Sanic('FeelUOwn')


def resp(js):
    return jsonify({
        'code': 200,
        'msg': 'ok',
        'data': js
    })


@sanic_app.route('/api/v1/status')
async def status(request):
    cmd = Cmd('status')
    app = get_app()
    handler = StatusHandler(app)
    rv = handler.handle(cmd)
    return resp(serialize('python', rv, brief=False))


@sanic_app.websocket('/signal/v1')
async def signal(request, ws: Websocket):
    queue = asyncio.Queue()

    class Subscriber:
        def write_topic_msg(self, topic, msg):
            queue.put_nowait(json.dumps({'topic': topic, 'data': msg, 'format': 'json'}))

    subscriber = Subscriber()

    pubsub_gateway: PubsubGateway = get_app().pubsub_gateway
    for topic in pubsub_gateway.topics:
        pubsub_gateway.link(topic, subscriber)

    while True:
        data = await queue.get()
        await ws.send(data)


async def run_sanic_app(host, port):
    server = await sanic_app.create_server(host, port, return_asyncio_server=True)
    await server.startup()
    await server.serve_forever()
