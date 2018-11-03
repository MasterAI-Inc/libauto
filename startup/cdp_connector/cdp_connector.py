###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

BASE_URL = "wss://labs.autoauto.ai/autopair/device"
#BASE_URL = "ws://192.168.0.11:8000/autopair/device"

from wsc import WebSocketConnection, StandardDelegate, run_forever

from rpyc.utils.server import ThreadedServer
import rpyc

from threading import Thread
import queue
import sys

from pty_manager import PtyManager
from verification_method import Verification
from dashboard import Dashboard

from auto.db import secure_db
STORE = secure_db()

from auto import logger
log = logger.init('cdp_connector', terminal=True)


def get_token():
    device_token = STORE.get('DEVICE_TOKEN', None)
    if device_token is None:
        log.info('Device token is not set.')
        return None
    return device_token


class CdpService(rpyc.Service):

    def __init__(self):
        pass

    def on_connect(self, conn):
        self.conn = conn
        self.conn_name = self.conn._config["connid"]
        log.info("New client: {}".format(self.conn_name))

    def on_disconnect(self, conn):
        log.info("Dead client: {}".format(self.conn_name))

    def exposed_send(self, msg):
        log.info('Will send to CDP from RPC, message: {}...'.format(msg[:10]))
        delegate.smart_send(msg)


if __name__ == '__main__':

    up_user = sys.argv[1]   # the "UnPrivileged" user name.
    log.info("Will run the PTY manager using the unprivileged user: {}".format(up_user))

    consumers = [
        PtyManager(up_user),
        Verification(),
        Dashboard(),
    ]

    send_queue = queue.Queue(maxsize=100)

    delegate = StandardDelegate(consumers, send_queue)

    ws_connection = WebSocketConnection(delegate, get_token, BASE_URL)

    ws_thread = Thread(target=run_forever, args=(ws_connection, send_queue))
    ws_thread.deamon = True
    ws_thread.start()

    rpc_server = ThreadedServer(CdpService, port=18864)

    prc_server_thread = Thread(target=rpc_server.start)
    prc_server_thread.deamon = True
    prc_server_thread.start()

    prc_server_thread.join()
    ws_thread.join()

