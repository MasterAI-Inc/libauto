###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

"""
Connects to the AutoAuto server.

Built-in behavior:
 - Sends application-layer pings to the server every so often, and the server responds
with an application-layer pong. Also responds to pings from the server by sending a pong.
 - Responds to a 'whothere' message for legacy purposes.

Of course it also publishes a simple send/receive interface so that you can do whatever
else you want with it.
"""

from websocket import create_connection
from threading import Thread, Lock
from collections import defaultdict

import queue
import time
import random
import json
import socket
import struct
import io
import traceback

from util import set_hostname

from auto import print_all

from auto import logger
log = logger.init(__name__, terminal=True)


LOG_ALL_MESSAGES = False

PING_INTERVAL_SECONDS = 20
SOCKET_READ_TIMEOUT_SECONDS = 60
reconnect_delay_seconds = lambda: (10 + random.randint(2, 8))


class WebSocketConnection:

    def __init__(self, delegate, token_func, baseurl):
        self.delegate = delegate
        self.token_func = token_func
        self.baseurl = baseurl
        self.stop = False
        self.thread = None
        self.didstop = True
        self.last_ping = None
        self.send_queue = None

    def _get_url(self):
        token = self.token_func()
        while token is None:
            time.sleep(1)    # <-- safe to block since it's called from a dedicated thread who only proceeds when we have the token
            token = self.token_func()
        return self.baseurl + '/' + token

    def start(self):
        assert(self.thread is None)

        self.stop = False
        self.didstop = False
        self.send_queue = queue.Queue()

        def _go():
            self._connect()

        log.info("Starting Connection to AutoAuto Server...")

        self.thread = Thread(target=_go)
        self.thread.deamon = True
        self.thread.start()

    def _connect(self):
        ws = None
        send_thread = None

        def _send_from_queue():
            try:
                while True:
                    msg = self.send_queue.get()
                    if msg is False:
                        break
                    ws.send(msg)
                    if LOG_ALL_MESSAGES:
                        log.info("> {}".format(msg))
            except Exception as e:
                log.info("Send thread terminated with Exception: {}".format(e))
                output = io.StringIO()
                traceback.print_exc(file=output)
                log.info(output.getvalue())

        try:
            read_timeout_opt = (socket.SOL_SOCKET, socket.SO_RCVTIMEO, struct.pack('LL', SOCKET_READ_TIMEOUT_SECONDS, 0))
            tcp_nodelay_opt = (socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            url = self._get_url()
            ws = create_connection(url, sockopt=[read_timeout_opt, tcp_nodelay_opt])
            self.onOpen(url)

            send_thread = Thread(target=_send_from_queue)
            send_thread.start()

            while not self.stop:
                msg = ws.recv()
                if msg != '':
                    try:
                        msg = json.loads(msg)
                    except:
                        log.info("failed to parse JSON: {}".format(msg))
                        raise
                    self.onMessage(msg)

        except Exception as e:
            self.onError(e)

        if send_thread:
            self.send_queue.put(False)
            send_thread.join()
            send_thread = None

        if ws:
            ws.close()
            ws = None
            self.onClose()

        self.didstop = True

    def send(self, msg):
        if isinstance(msg, str):
            self.send_queue.put(msg)
        elif isinstance(msg, dict):
            self.send_queue.put(json.dumps(msg))
        else:
            log.info("Trying to send unknown type: " + str(type(msg)))

    def send_ping(self):
        now = time.time()
        if self.last_ping is None or now - self.last_ping > PING_INTERVAL_SECONDS:
            self.send({'ping': True})
            self.last_ping = now

    def close(self):
        self.stop = True
        if self.thread:
            self.thread.join()
            self.thread = None

    def onOpen(self, url):
        log.info("Connected: {}...".format(url[:44]))
        if hasattr(self.delegate, 'onOpen'):
            try:
                self.delegate.onOpen()
            except Exception as e:
                log.info("delegate's onOpen callback threw error: {}".format(e))
                output = io.StringIO()
                traceback.print_exc(file=output)
                log.info(output.getvalue())

    def onClose(self):
        log.info("Closing...")
        if hasattr(self.delegate, 'onClose'):
            try:
                self.delegate.onClose()
            except Exception as e:
                log.info("delegate's onClose callback threw error: {}".format(e))
                output = io.StringIO()
                traceback.print_exc(file=output)
                log.info(output.getvalue())

    def onMessage(self, msg):
        if LOG_ALL_MESSAGES:
            log.info("< {}".format(msg))
        if 'whothere' in msg:
            self.send({'me': True})
            return
        if 'ping' in msg:
            self.send({'pong': True})
            return
        if hasattr(self.delegate, 'onMessage'):
            self.delegate.onMessage(msg)

    def onError(self, e):
        log.info("onError callback got error: {}".format(e))
        output = io.StringIO()
        traceback.print_exc(file=output)
        log.info(output.getvalue())
        if hasattr(self.delegate, 'onError'):
            try:
                self.delegate.onError(e)
            except Exception as e:
                log.info("delegate's onError callback threw error: {}".format(e))
                output = io.StringIO()
                traceback.print_exc(file=output)
                log.error(output.getvalue())


class StandardDelegate:

    def __init__(self, consumers, send_queue):
        self.known_lock = Lock()
        self.known_usernames = defaultdict(set)
        self.known_user_sessions = set()
        self.consumers = consumers
        self.send_queue = send_queue
        self.did_error = False

    def add_user_with_session(self, username, user_session):
        with self.known_lock:
            if user_session not in self.known_user_sessions:
                self.known_user_sessions.add(user_session)
                self.known_usernames[username].add(user_session)
                return True
            return False

    def remove_user_with_session(self, username, user_session):
        with self.known_lock:
            if user_session in self.known_user_sessions:
                self.known_user_sessions.remove(user_session)
                self.known_usernames[username].remove(user_session)
                return True
            return False

    def knows_user_session(self, user_session):
        with self.known_lock:
            return (user_session in self.known_user_sessions)

    def user_has_sessions(self, username):
        with self.known_lock:
            return len(self.known_usernames[username]) > 0

    def has_any_sessions(self):
        with self.known_lock:
            return len(self.known_user_sessions) > 0

    def smart_send(self, msg):
        if isinstance(msg, str):
            msg = json.loads(msg)

        if 'to_user_session' in msg:
            user_session = msg['to_user_session']
            if not self.knows_user_session(user_session):
                # We do not send messages that are destined for a
                # user session that no longer exists!
                return False
        elif 'to_username' in msg:
            username = msg['to_username']
            if not self.user_has_sessions(username):
                # We don't send to a user who has zero user sessions
                # right now.
                return False
        else:
            if not self.has_any_sessions():
                # If a device falls in the woods...
                return False

        # If we didn't bail about above, then queue the message.
        self.send_queue.put(json.dumps(msg))
        return True

    def onMessage(self, msg):
        if 'origin' in msg:
            if msg['origin'] == 'server' and 'connect' in msg and msg['connect'] == 'user':
                username = msg['username']
                user_session = msg['user_session']
                if self.add_user_with_session(username, user_session):
                    for c in self.consumers:
                        c.new_user_session(username, user_session)
            elif msg['origin'] == 'server' and 'disconnect' in msg and msg['disconnect'] == 'user':
                username = msg['username']
                user_session = msg['user_session']
                if self.remove_user_with_session(username, user_session):
                    for c in self.consumers:
                        c.end_user_session(username, user_session)

            elif msg['origin'] == 'server' and 'hello' in msg:
                info = msg['yourinfo']
                vin = info['vin']
                name = info['name']
                description = info['description']  # <-- Where should we display this?
                print_all('Device Name: {}'.format(name))
                print_all('Device VIN:  {}'.format(vin))
                output = set_hostname(name)
                log.info("Set hostname, output is: {}".format(output))

        for c in self.consumers:
            c.got_message(msg, self.smart_send)

    def onOpen(self):
        for c in self.consumers:
            c.connected_cdp()
        print_all('Connected to CDP. Standing by...')
        self.did_error = False

    def onClose(self):
        for c in self.consumers:
            c.disconnected_cdp()
        print_all('Connection to CDP lost. Reconnecting...')

    def onError(self, e):
        if not self.did_error:
            print_all('Attempting to connect...')
            self.did_error = True   # We only want to print on the _first_ error.


def run_forever(conn, send_queue):

    while True:

        conn.start()

        while not conn.didstop:
            conn.send_ping()
            try:
                send_this = send_queue.get(timeout=0.1)
                conn.send(send_this)
            except queue.Empty:
                continue

        conn.close()

        sleep_time = reconnect_delay_seconds()
        log.info("Sleeping random amount: {} seconds".format(sleep_time))
        time.sleep(sleep_time)

        log.info("Restarting...")

        # Clear the queue of the stuff that didn't get sent. We don't guarantee message delivery!
        while not send_queue.empty():
            try:
                send_queue.get(False)
            except queue.Empty:
                break

