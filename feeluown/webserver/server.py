import asyncio
import json
import logging

from sanic import Sanic, json as jsonify, Websocket, Request

from feeluown.app import get_app
from feeluown.serializers import serialize
from feeluown.server.pubsub import Gateway as PubsubGateway
from feeluown.server.handlers.cmd import Cmd
from feeluown.server.handlers.status import StatusHandler
from feeluown.server.handlers.player import PlayerHandler
from feeluown.server.handlers.jsonrpc_ import handle


logger = logging.getLogger(__name__)

# Disable sanic's logging so that it can use feeluown's logging system.
sanic_app = Sanic('FeelUOwn', configure_logging=False)


def resp(js):
    return jsonify({'code': 200, 'msg': 'ok', 'data': js})


@sanic_app.route('/api/v1/status')
async def status(request):
    cmd = Cmd('status')
    app = get_app()
    handler = StatusHandler(app)
    rv = handler.handle(cmd)
    return resp(serialize('python', rv, brief=False))


@sanic_app.post('/api/v1/player/pause')
async def pause(request):
    cmd = Cmd('pause')
    app = get_app()
    rv = PlayerHandler(app).handle(cmd)
    return resp(serialize('python', rv, brief=False))


@sanic_app.post('/api/v1/player/resume')
async def resume(request):
    cmd = Cmd('resume')
    app = get_app()
    rv = PlayerHandler(app).handle(cmd)
    return resp(serialize('python', rv, brief=False))


@sanic_app.post('/api/v1/player/play')
async def play(request):
    js = request.json
    cmd = Cmd('play', js['uri'])
    app = get_app()
    rv = PlayerHandler(app).handle(cmd)
    return resp(serialize('python', rv, brief=False))


@sanic_app.post('/rpc/v1')
async def rpcv1(request: Request):
    js = handle(request.body)
    return jsonify(js)


@sanic_app.websocket('/signal/v1')
async def signal(request, ws: Websocket):
    # TODO: 优化这个代码，比如处理连接的关闭。
    queue = asyncio.Queue()

    class Subscriber:

        def write_topic_msg(self, topic, msg):
            # TODO: 这个结构体可能会变化，需要注意一下
            queue.put_nowait(json.dumps({'topic': topic, 'data': msg, 'format': 'json'}))

    subscriber = Subscriber()

    pubsub_gateway: PubsubGateway = get_app().pubsub_gateway
    for topic in pubsub_gateway.topics:
        pubsub_gateway.link(topic, subscriber)

    while True:
        data = await queue.get()
        await ws.send(data)


async def run_web_server(host, port):
    sanic_app.config.MOTD = False
    server = await sanic_app.create_server(host, port, return_asyncio_server=True)
    await server.startup()
    await server.serve_forever()
