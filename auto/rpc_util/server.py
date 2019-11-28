import asyncio
import websockets
import json

from auto.rpc_util.serialize_interface import serialize_interface


def _build_server_func(iface, impl):
    iface_json = json.dumps(iface)

    async def serve_func(websocket, path):
        await websocket.send(iface_json)

        try:
            while True:
                cmd = await websocket.recv()
                cmd = cmd.strip()
                if cmd:
                    path, args = json.loads(cmd)
                    func = impl[path]
                    result = func(*args)
                    result_json = json.dumps(result)
                    await websocket.send(result_json)

        except websockets.exceptions.ConnectionClosed:
            print('...closed...')

    return serve_func


def serve(root, inet_addr='localhost', inet_port=7000):
    iface, impl = serialize_interface(root, name='root')

    serve_func = _build_server_func(iface, impl)

    start_server = websockets.serve(serve_func, inet_addr, inet_port)

    loop = asyncio.get_event_loop()

    loop.run_until_complete(start_server)
    loop.run_forever()


if __name__ == '__main__':

    class Thing:
        def export_foo(self, x):
            print('I am foo.')
            return x ** 3

    thing = Thing()

    serve(thing)

