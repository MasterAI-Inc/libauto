###############################################################################
#
# Copyright (c) 2017-2020 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

"""
This script runs Jupyter in the background.
"""

import os
import sys
import time
import socket
import subprocess
from threading import Thread
from auto.capabilities import list_caps, acquire, release

from auto import logger
log = logger.init(__name__, terminal=True)


CURR_DIR = os.path.dirname(os.path.realpath(__file__))

JUPYTER_CONFIG_TEMPLATE = os.path.join(CURR_DIR, "jupyter_notebook_config_template.py")

JUPYTER_CONFIG_OUTPUT = "/tmp/jupyter_notebook_config.py"


def _write_config_file():
    caps = list_caps()

    if 'Credentials' not in caps:
        log.warning('Cannot obtain Jupyter password; will bail.')
        sys.exit(1)

    creds = acquire('Credentials')
    jupyter_password = None

    while True:
        jupyter_password = creds.get_jupyter_password()
        if jupyter_password is not None:
            break
        log.info('Waiting for Jupyter password to be set...')
        time.sleep(1)

    release(creds)

    log.info('Got Jupyter password.')

    with open(JUPYTER_CONFIG_TEMPLATE, 'r') as f_template:
        template = f_template.read()
        with open(JUPYTER_CONFIG_OUTPUT, 'w') as f_out:
            final_config = template.replace(r'<JUPYTER_PASSWORD>', repr(jupyter_password))
            f_out.write(final_config)


def _thread_main(run_as_user):
    _write_config_file()

    log.info('Write Jupyter config file; will launch Jupyter!')

    cmd = ['sudo', '-u', run_as_user, '-i', 'jupyter', 'notebook', '--config={}'.format(JUPYTER_CONFIG_OUTPUT)]

    proc = subprocess.run(cmd)  # stdin/out/err are inherited, and this command blocks until the subprocess exits


def _is_local_port_serving(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    if result == 0:
        return True
    else:
        return False


def run_jupyter_in_background(run_as_user):
    if _is_local_port_serving(8888):
        log.warning('Port 8888 is already in use. Is Jupyter already running from a previous invocation?')
        return

    thread = Thread(target=_thread_main, args=(run_as_user,))
    thread.daemon = True
    thread.start()
    return thread


if __name__ == '__main__':
    if len(sys.argv) > 1:
        run_as_user = sys.argv[1]
    else:
        run_as_user = os.environ['USER']

    thread = run_jupyter_in_background(run_as_user)
    if thread is not None:
        thread.join()

