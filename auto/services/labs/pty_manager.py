###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

import os
import re
import pwd
import time
import base64

import fcntl
import struct
import termios

import asyncio

from contextlib import contextmanager


NAGLE_STYLE_DELAY = 0.1

TMUX_LOCK = asyncio.Lock()   # lock to protect tmux commands; we only want to execute one at a time


class PtyManager:

    def __init__(self, system_up_user, console):
        self.system_up_user = system_up_user
        self.console = console
        log.info("Will run the PTY manager using the unprivileged user: {}".format(system_up_user))

    async def init(self):
        pass

    async def connected_cdp(self):
        self.xterm_lookup = {}    # map xterm_guid to (task, queue)

    async def new_user_session(self, username, user_session):
        pass

    async def got_message(self, msg, send_func):
        if 'origin' in msg and msg['origin'] == 'user' and 'type' in msg:
            type_ = msg['type']

            if type_ in ('new_session', 'attach_session', 'start_process'):
                xterm_guid = msg['xterm_guid']
                if xterm_guid in self.xterm_lookup:
                    log.error('The xterm_guid={} already exists; invalid for type={}'.format(xterm_guid, type_))
                    return
                queue = asyncio.Queue()
                queue.put_nowait(msg)
                coro = _pty_process_manager(xterm_guid, queue, send_func, self.system_up_user)
                task = asyncio.create_task(coro)
                self.xterm_lookup[xterm_guid] = (task, queue)

            elif type_ in ('kill_process', 'xterm_resized', 'send_input_to_pty'):
                xterm_guid = msg['xterm_guid']
                if xterm_guid not in self.xterm_lookup:
                    log.error('The xterm_guid={} does not exist; invalid for type={}'.format(xterm_guid, type_))
                    return
                task, queue = self.xterm_lookup[xterm_guid]
                if type_ == 'kill_process':
                    task.cancel()
                    del self.xterm_lookup[xterm_guid]
                else:
                    queue.put_nowait(msg)

            elif type_ == 'kill_session':
                session_name = msg['session_name']
                coro = _kill_session(session_name, self.system_up_user)
                asyncio.create_task(coro)

            elif type_ == 'list_sessions':
                user_session = msg['user_session']
                coro = _list_sessions(send_func, user_session, self.system_up_user)
                asyncio.create_task(coro)

            elif type_ == 'list_running':
                user_session = msg['user_session']
                coro = _list_running(send_func, user_session)
                asyncio.create_task(coro)

            elif type_ == 'clear_screen':
                coro = _clear_console(self.console)
                asyncio.create_task(coro)

    async def end_user_session(self, username, user_session):
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

    async def disconnected_cdp(self):
        self.end_user_session(None, None)   # <-- flag to end ALL sessions

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
                pass
                #await _clear_console(self.console)  <-- TODO UNCOMMNET

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



    async def _write_code_from_cdp(self, xterm_guid, code_str):
        uid, gid, home = await _user_uid_gid_home(self.system_up_user)
        with _switch_to_user(uid, gid):
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


@contextmanager
def _switch_to_user(uid, gid):
    sgid = os.getgid()  # the "saved" gid
    suid = os.getuid()  # the "saved" uid
    try:
        os.setegid(gid)
        os.seteuid(uid)
        yield
    finally:
        os.setegid(sgid)
        os.seteuid(suid)


async def _user_uid_gid_home(system_user):
    pw_record = await loop.run_in_executor(None, pwd.getpwnam, system_user)
    uid = pw_record.pw_uid
    gid = pw_record.pw_gid
    home = pw_record.pw_dir
    return uid, gid, home


def setwinsize(stdin, rows, cols):
    s = struct.pack('HHHH', rows, cols, 0, 0)
    fcntl.ioctl(stdin, termios.TIOCSWINSZ, s)


async def _run_subprocess(cmd, system_user):
    # This runs a command _without_ a TTY.
    # Use `_run_pty_cmd_background()` when you need a TTY.
    cmd = ['sudo', '-u', system_user, '-i'] + cmd
    proc = await asyncio.create_subprocess_exec(
            'tmux', 'ls',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if stderr:
        log.error('Command {} wrote to stderr: {}'.format(repr(cmd), repr(stderr)))
    return stdout


async def _tmux_ls(system_user):
    output = await _run_subprocess(['tmux', 'ls'], system_user)
    session_names = []
    for line in output.split('\n'):
        parts = line.split(': ')
        if len(parts) == 2:
            session_names.append(parts[0])
    return sorted(session_names)


async def _next_tmux_session_name(system_user):
    """Like OS FDs, finds the first unused tmux number."""
    curr_names = await _tmux_ls(system_user)
    curr_names = set(curr_names)
    i = 0
    while True:
        candiate_name = 'cdp_{}'.format(i)
        if candiate_name not in curr_names:
            return candiate_name
        i += 1


async def _kill_session(session_name, system_user):
    # Since we do everything through tmux, we'll just ask tmux to kill the session.
    # Interesting info here though, for those who want to learn something:
    #     https://github.com/jupyter/terminado/blob/master/terminado/management.py#L74
    #     https://unix.stackexchange.com/a/88742
    cmd = "tmux kill-session -t".split(' ') + [session_name]
    output = await _run_subprocess(cmd, system_user)


async def _list_sessions(send_func, user_session, system_user):
    session_names = await _tmux_ls(system_user)
    await send_func({
        'type': 'session_list',
        'session_names': session_names,
        'to_user_session': user_session,
    })


async def _clear_console(console):
    await console.clear_text()
    await console.big_clear()
    await console.clear_image()


class PtyProcess:
    """
    Expose the relevant behavior of this process.

    FUTURE TODO: It would be nice if we didn't rely on executors in this, but
                 I've yet to figure out how to plug these FDs into they asyncio
                 event loop properly... ugh.
    """
    def __init__(self, stdin, stdout, stderr, proc, loop):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.proc = proc
        self.loop = loop

    async def write_stdin(self, buf):
        """Write the buffer; don't return until the whole thing is written!"""
        n = 0
        while n < len(buf):
            n_here = await self.loop.run_in_executor(None, os.write, self.stdin, buf[n:])  # <-- Warning: O(n^2) in the worst case; but okay in typical case.
            n += n_here

    async def read_stdout(self):
        """Read a chunk of bytes from stdout; whatever is available first. Return an empty buffer on EOF."""
        return await self._read(self.stdout)

    async def read_stderr(self):
        """Read a chunk of bytes from stderr; whatever is available first. Return an empty buffer on EOF."""
        return await self._read(self.stderr)

    async def _read(self, fd):
        try:
            return await self.loop.run_in_executor(None, os.read, fd, 4096)
        except OSError:
            # PTYs throw OSError when they hit EOF, for some reason.
            # Pipes and regular files don't throw, so PTYs are unique.
            return b''

    async def close_func(self):
        """Close the underlying file descriptors; don't leak FDs!"""
        os.close(self.stdin)
        os.close(self.stdout)
        os.close(self.stderr)


async def _run_pty_cmd_background(cmd, system_user, env_override=None, start_dir_override=None, size=None):
    loop = asyncio.get_running_loop()

    pw_record = await loop.run_in_executor(None, pwd.getpwnam, system_user)

    if start_dir_override is None:
        start_dir_override = pw_record.pw_dir

    env = dict(os.environ.copy())

    env['TERM'] = 'xterm-256color'   # background info: https://unix.stackexchange.com/a/198949

    if env_override is not None:
        env.update(env_override)

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

    my_uid = os.getuid()

    def switch_user():
        if my_uid != pw_record.pw_uid:
            os.setgid(pw_record.pw_gid)
            os.initgroups(system_user, pw_record.pw_gid)
            os.setuid(pw_record.pw_uid)

    fd_master_io, fd_slave_io = os.openpty()
    fd_master_er, fd_slave_er = os.openpty()
    try:
        proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=fd_slave_io,
                stdout=fd_slave_io,
                stderr=fd_slave_er,
                cwd=start_dir_override,
                env=env,
                preexec_fn=switch_user,
        )
    except:
        os.close(fd_master_io)
        os.close(fd_slave_io)
        os.close(fd_master_er)
        os.close(fd_slave_er)
        raise

    os.close(fd_slave_io)
    os.close(fd_slave_er)

    stdin = fd_master_io
    stdout = os.dup(fd_master_io)
    stderr = fd_master_er

    if size is None:
        size = (24, 80)
    else:
        size = (size['rows'], size['cols'])
    setwinsize(stdin, *size)

    return PtyProcess(stdin, stdout, stderr, proc, loop)


async def _new_session(self, xterm_guid, username, user_session, send_func, settings):
    session_name = await _next_tmux_session_name(self.system_up_user)
    start_dir = '~' if 'start_dir' not in settings else settings['start_dir']
    cmd = ['tmux' 'new' '-c', start_dir, '-s', session_name]
    if 'cmd' in settings:
        cmd.extend(settings['cmd'])  # <-- becomes the shell argument to tmux
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


async def _pty_process_manager(xterm_guid, queue, send_func, system_user):
    try:
        msg = await queue.get()
        type_ = msg['type']

        if type_ == 'new_session':
            username = msg['username']
            user_session = msg['user_session']
            await _new_session(xterm_guid, username, user_session, send_func, msg)

        elif type_ == 'attach_session':
            session_name = msg['session_name']
            username = msg['username']
            user_session = msg['user_session']
            await _attach_session(xterm_guid, session_name, username, user_session, send_func, msg)

        elif type_ == 'start_process':
            username = msg['username']
            user_session = msg['user_session']
            cmd = msg.get('cmd', None)
            await _start_process(xterm_guid, username, user_session, cmd, send_func, msg)

        else:
            raise Exception('Unexpected type sent to process manager: {}'.format(repr(msg)))

        while True:
            msg = await queue.get()
            type_ = msg['type']

            if type_ == 'xterm_resized':
                size = msg['size']
                await _xterm_resized(xterm_guid, size)

            elif type_ == 'send_input_to_pty':
                input_ = msg['input']
                await _send_input_to_pty(xterm_guid, input_)

            else:
                raise Exception('Unexpected type sent to process manager: {}'.format(repr(msg)))

    except asyncio.CancelledError:
        # TODO
        pass
        #await _kill_process(xterm_guid)

