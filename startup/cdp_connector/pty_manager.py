###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

from ptyprocess import PtyProcess         # <-- read/write in binary
from ptyprocess import PtyProcessUnicode  # <-- read/write in unicode

from auto import console

from contextlib import contextmanager
from threading import Thread, Lock
from queue import Queue, Empty
import pwd
import base64
import subprocess
import os
import time
import re

NAGLE_STYLE_DELAY = 0.1


@contextmanager
def switch_to_user(uid, gid):
    sgid = os.getgid()  # the "saved" gid
    suid = os.getuid()  # the "saved" uid
    try:
        os.setegid(gid)
        os.seteuid(uid)
        yield
    finally:
        os.setegid(sgid)
        os.seteuid(suid)


class PtyManager:

    def __init__(self, system_up_user, system_priv_user):
        self.pty_lookup_lock = Lock()
        self.pty_lookup = {}
        self.system_up_user = system_up_user
        self.system_priv_user = system_priv_user


    def _user_uid_gid_home(self, system_user):
        pw_record = pwd.getpwnam(system_user)
        uid = pw_record.pw_uid
        gid = pw_record.pw_gid
        home = pw_record.pw_dir
        return uid, gid, home


    def _run_subprocess(self, cmd, system_user):
        # This runs a command without a TTY, which is fine for most commands.
        # If you need a TTY, you should call `_run_pty_cmd_background` instead.
        cmd = ['sudo', '-u', system_user, '-i'] + cmd
        output = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode('utf-8')
        return output


    def connected_cdp(self):
        pass


    def new_user_session(self, username, user_session):
        pass


    def got_message(self, msg, send_func):
        if 'origin' in msg and msg['origin'] == 'user' and 'type' in msg:
            if msg['type'] == 'new_session':
                self._new_session(msg['xterm_guid'], msg['username'], msg['user_session'], send_func, msg)

            elif msg['type'] == 'attach_session':
                self._attach_session(msg['xterm_guid'], msg['session_name'], msg['username'], msg['user_session'], send_func, msg)

            elif msg['type'] == 'start_process':
                self._start_process(msg['xterm_guid'], msg['username'], msg['user_session'], msg.get('cmd', None), send_func, msg)

            elif msg['type'] == 'kill_process':
                self._kill_process(msg['xterm_guid'])

            elif msg['type'] == 'xterm_resized':
                self._xterm_resized(msg['xterm_guid'], msg['size'])

            elif msg['type'] == 'send_input_to_pty':
                self._send_input_to_pty(msg['xterm_guid'], msg['input'])

            elif msg['type'] == 'kill_session':
                self._kill_session(msg['session_name'])

            elif msg['type'] == 'list_sessions':
                self._list_sessions(send_func, msg['user_session'])

            elif msg['type'] == 'list_running':
                self._list_running(send_func, msg['user_session'])

            elif msg['type'] == 'clear_screen':
                self._clear_screen()


    def end_user_session(self, username, user_session):
        """
        We need to kill all ptys started by this user_session.
        Note: If you kill a `tmux` process which is attached to some session,
              it will just detach from the underlying tmux session (which is
              what we want).
        """
        need_close = []
        with self.pty_lookup_lock:
            for xterm_guid, pty in self.pty_lookup.items():
                if user_session is None or pty.user_session == user_session:
                    need_close.append(pty)
        for pty in need_close:
            pty.terminate(force=True)  # <-- does SIGHUP, SIGINT, then SIGKILL


    def disconnected_cdp(self):
        self.end_user_session(None, None)   # <-- flag to end ALL sessions


    def _tmux_ls(self):
        output = self._run_subprocess(['tmux', 'ls'], self.system_up_user)
        if output.startswith('no server'):
            return []
        session_names = []
        for line in output.split('\n'):
            parts = line.split(': ')
            if len(parts) == 2:
                session_names.append(parts[0])
        return sorted(session_names)


    def _next_tmux_session_name(self):
        """Like OS FDs, finds the first unused tmux number."""
        curr_names = set(self._tmux_ls())
        i = 0
        while True:
            candiate_name = 'cdp_{}'.format(i)
            if candiate_name not in curr_names:
                return candiate_name
            i += 1


    def _run_pty_main(self, xterm_guid, pty, send_func, user_session):
        queue = Queue()

        def buffered_write():
            def flush(big_buf):
                send_func({
                    'type': 'pty_output', 'xterm_guid': xterm_guid,
                    'output': base64.b64encode(big_buf).decode('utf-8'),
                    'to_user_session': user_session,
                })
            last_sent_time = -1
            to_send = []
            while True:
                wait_time = NAGLE_STYLE_DELAY - (time.time() - last_sent_time)
                if wait_time > 0:
                    try:
                        buf = queue.get(timeout=wait_time)
                        if buf is False:
                            if len(to_send) > 0:
                                flush(b''.join(to_send))
                            return
                        to_send.append(buf)
                        continue
                    except Empty:
                        # We waited the `wait_time` and got nothing new.
                        pass
                if len(to_send) == 0:
                    # We could send something... but we have nothing to send. Block until we get something.
                    buf = queue.get()
                    if buf is False:
                        return
                    to_send.append(buf)
                # Finally, we have something to send for sure, and we are allowed to send it.
                flush(b''.join(to_send))
                last_sent_time = time.time()
                to_send = []

        write_thread = Thread(target=buffered_write)
        write_thread.start()

        try:
            while True:
                buf = pty.read()
                queue.put(buf)

        except Exception as e:  # <-- we expect to catch EOFError (normally) and ValueError if the fd is closed while we're still tyring to read here.
            queue.put(False)
            write_thread.join()

            send_func({
                'type': 'pty_output_closed',
                'xterm_guid': xterm_guid,
                'to_user_session': user_session,
            })
            exitcode = pty.wait()
            send_func({
                'type': 'pty_program_exited',
                'xterm_guid': xterm_guid,
                'exitcode': exitcode,
                'signalcode': pty.signalstatus,
                'to_user_session': user_session,
            })

            with self.pty_lookup_lock:
                del self.pty_lookup[xterm_guid]


    def _run_pty_cmd_background(self, cmd, xterm_guid, send_func, username, user_session, system_user,
                                env_override=None, start_dir_override=None, size=None):
        env = dict(os.environ.copy())

        env['TERM'] = 'xterm-256color'   # background info: https://unix.stackexchange.com/a/198949

        if env_override is not None:
            env.update(env_override)

        if size is None:
            size = (24, 80)
        else:
            size = (size['rows'], size['cols'])

        pw_record = pwd.getpwnam(system_user)

        if start_dir_override is None:
            start_dir_override = pw_record.pw_dir

        env['HOME'    ] = pw_record.pw_dir
        env['LOGNAME' ] = pw_record.pw_name
        env['USER'    ] = pw_record.pw_name
        env['USERNAME'] = pw_record.pw_name
        env['SHELL'   ] = pw_record.pw_shell
        env['UID'     ] = str(pw_record.pw_uid)
        env['PWD'     ] = start_dir_override
        if 'OLDPWD' in env: del env['OLDPWD']
        if 'MAIL'   in env: del env['MAIL']

        env = {k: v for k, v in env.items() if not k.startswith('SUDO_') and not k.startswith('XDG_')}

        def switch_user():
            os.setgid(pw_record.pw_gid)
            os.initgroups(system_user, pw_record.pw_gid)
            os.setuid(pw_record.pw_uid)

        pty = PtyProcess.spawn(
                cmd,
                env=env,
                cwd=start_dir_override,
                dimensions=size,
                preexec_fn=switch_user,
        )  # See: http://pexpect.readthedocs.io/en/latest/FAQ.html#whynotpipe   and   https://stackoverflow.com/a/20509641

        pty.delayafterclose     = 2   # <-- override the default which is 0.1
        pty.delayafterterminate = 2   # <-- override the default which is 0.1
        self.pty_lookup[xterm_guid] = pty
        Thread(target=self._run_pty_main, args=(xterm_guid, pty, send_func, user_session)).start()
        pty.start_time = time.time()
        return pty


    def _new_session(self, xterm_guid, username, user_session, send_func, settings):
        with self.pty_lookup_lock:
            if xterm_guid in self.pty_lookup:
                # This pty already exists... :/
                return

            session_name = self._next_tmux_session_name()
            start_dir = '~' if 'start_dir' not in settings else settings['start_dir']
            cmd = 'tmux new -c {} -s {}'.format(start_dir, session_name)
            cmd = cmd.split(' ')   # <-- safe because we only take input from our trusted CDP, which only takes input from authorized users
            if 'cmd' in settings:
                cmd.extend(settings['cmd'])  # <-- becomes the shell argument
            size = settings.get('size', None)
            pty = self._run_pty_cmd_background(
                    cmd=cmd,
                    xterm_guid=xterm_guid,
                    send_func=send_func,
                    username=username,
                    user_session=user_session,
                    system_user=self.system_up_user,
                    size=size
            )
            pty.user_session = user_session
            pty.description = "Attached session: {}".format(session_name)
            pty.cmd = cmd
            send_func({
                'type': 'new_session_name_announcement',
                'session_name': session_name,
                'xterm_guid': xterm_guid,
                'to_user_session': user_session,
            })


    def _attach_session(self, xterm_guid, session_name, username, user_session, send_func, settings):
        with self.pty_lookup_lock:
            if xterm_guid in self.pty_lookup:
                # This pty already exists... :/
                return

            session_name = re.sub(r'[^A-Za-z0-9_]', '', session_name)  # safe string
            cmd = 'tmux attach -d -t {}'.format(session_name)
            cmd = cmd.split(' ')   # <-- only take input from our trusted CDP, which only takes input from authorized users
            size = settings.get('size', None)
            pty = self._run_pty_cmd_background(
                    cmd=cmd,
                    xterm_guid=xterm_guid,
                    send_func=send_func,
                    username=username,
                    user_session=user_session,
                    system_user=self.system_up_user,
                    size=size
            )
            pty.user_session = user_session
            pty.description = "Attached session: {}".format(session_name)
            pty.cmd = cmd


    def _start_process(self, xterm_guid, username, user_session, cmd, send_func, settings):
        with self.pty_lookup_lock:
            if xterm_guid in self.pty_lookup:
                # This pty already exists... :/
                return

            if 'clear_screen' in settings and settings['clear_screen']:
                self._clear_screen()

            if 'code_to_run' in settings:
                code_path = self._write_code_from_cdp(xterm_guid, settings['code_to_run'])
                cmd = ['python', code_path]
                description = 'Running Code'
            else:
                description = 'Custom Command'

            env_override = settings.get('env', {})
            env_override['TO_USER_SESSION'] = user_session

            start_dir_override = settings.get('start_dir', None)
            size = settings.get('size', None)

            pty = self._run_pty_cmd_background(
                    cmd=cmd,
                    xterm_guid=xterm_guid,
                    send_func=send_func,
                    username=username,
                    user_session=user_session,
                    system_user=self.system_up_user,
                    env_override=env_override,
                    start_dir_override=start_dir_override,
                    size=size
            )
            pty.user_session = user_session
            pty.description = description
            pty.cmd = cmd


    def _kill_process(self, xterm_guid):
        with self.pty_lookup_lock:
            if xterm_guid not in self.pty_lookup:
                # Why are you killing an unknown pty?
                return
            pty = self.pty_lookup[xterm_guid]

        pty.terminate(force=True)  # <-- does SIGHUP, SIGINT, then SIGKILL


    def _xterm_resized(self, xterm_guid, size):
        with self.pty_lookup_lock:
            if xterm_guid not in self.pty_lookup:
                # Why are you resizing to an unknown pty?
                return
            pty = self.pty_lookup[xterm_guid]

        pty.setwinsize(size['rows'], size['cols'])


    def _send_input_to_pty(self, xterm_guid, input_):
        with self.pty_lookup_lock:
            if xterm_guid not in self.pty_lookup:
                # Why are you sending input to an unknown pty?
                return
            pty = self.pty_lookup[xterm_guid]

        input_buf = base64.b64decode(input_)
        pty.write(input_buf)


    def _kill_session(self, session_name):
        # Since we do everything through tmux, we'll just ask tmux to kill the session.
        # Interesting info here though, for those who want to learn something:
        #     https://github.com/jupyter/terminado/blob/master/terminado/management.py#L74
        #     https://unix.stackexchange.com/a/88742
        cmd = "tmux kill-session -t".split(' ') + [session_name]
        output = self._run_subprocess(cmd, self.system_up_user)


    def _list_sessions(self, send_func, user_session):
        with self.pty_lookup_lock:
            session_names = self._tmux_ls()
        send_func({
            'type': 'session_list',
            'session_names': session_names,
            'to_user_session': user_session,
        })


    def _write_code_from_cdp(self, xterm_guid, code_str):
        uid, gid, home = self._user_uid_gid_home(self.system_up_user)
        with switch_to_user(uid, gid):
            subdirs = xterm_guid[0:2], xterm_guid[2:4], xterm_guid[4:6], xterm_guid[6:8], xterm_guid
            directory = os.path.join(home, '.cdp_runs', *subdirs)
            if not os.path.exists(directory):
                os.makedirs(directory)
            code_path = os.path.join(directory, 'main.py')
            with open(code_path, 'w') as f:
                f.write(code_str)
        return code_path


    def _list_running(self, send_func, user_session):
        running = []

        with self.pty_lookup_lock:
            for xterm_guid, pty in self.pty_lookup.items():
                x = {
                    'xterm_guid': xterm_guid,
                    'start_time': pty.start_time,
                    'user_session': pty.user_session,
                    'description': pty.description,
                    'cmd': pty.cmd,
                }
                running.append(x)

        send_func({
            'type': 'running_list',
            'running': running,
            'curtime': time.time(),
            'to_user_session': user_session,
        })


    def _clear_screen(self):
        console.clear()


if __name__ == '__main__':
    """Demo"""

    from tornado.ioloop import IOLoop

    import tty
    from functools import partial

    tty.setraw(0)

    pty = PtyProcess.spawn(['python'])

    def pty_read(io_loop, fd, events):
        if events & IOLoop.READ:
            buf = pty.read(1000)
            os.write(1, buf)
        if events & IOLoop.ERROR:
            io_loop.remove_handler(fd)
            io_loop.stop()

    def stdin_read(io_loop, fd, events):
        if events & IOLoop.READ:
            buf = os.read(0, 1000)
            pty.write(buf)
        if events & IOLoop.ERROR:
            io_loop.remove_handler(fd)

    io_loop = IOLoop.current()
    io_loop.add_handler(pty.fd, partial(pty_read, io_loop), io_loop.READ)
    io_loop.add_handler(0, partial(stdin_read, io_loop), io_loop.READ)
    io_loop.start()

    tty.setraw(1)
    # Note: This doesn't resport the tty fully to its original state. We'll have
    # to do other things to restore the tty to how we found it, before our pty
    # passthrough messed it up.

