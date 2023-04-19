###############################################################################
#
# Copyright (c) 2017-2020 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

import os
import re
import sys
import pwd
import time
import base64

import fcntl
import struct
import termios
import signal
import traceback

import asyncio

from contextlib import contextmanager

from auto import logger
log = logger.init(__name__, terminal=True)


READ_BUF_SIZE = 4096*8


CONTEST_SESSION_NAME = 'contest_session'


class PtyManager:

    def __init__(self, system_up_user, console):
        self.system_up_user = system_up_user
        self.console = console
        log.info("Will run the PTY manager using the unprivileged user: {}".format(system_up_user))

    async def init(self):
        cmds = [
            "tmux new-session -d -s bootup_session".split(),
            "tmux send-keys -t bootup_session python3 SPACE boot.py ENTER".split(),
        ]
        for cmd in cmds:
            await _run_subprocess(cmd, self.system_up_user)

    async def connected_cdp(self):
        self.xterm_lookup = {}    # map xterm_guid to (task, queue, start_time, user_session)

    async def new_device_session(self, vin):
        pass

    async def new_user_session(self, username, user_session):
        pass

    async def got_message(self, msg, send_func):
        if 'origin' in msg and msg['origin'] == 'user' and 'type' in msg:
            type_ = msg['type']

            if type_ in ('new_session', 'attach_session', 'start_process'):
                xterm_guid = msg['xterm_guid']
                user_session = msg['user_session']
                if xterm_guid in self.xterm_lookup:
                    log.error('The xterm_guid={} already exists; invalid for type={}'.format(xterm_guid, type_))
                    return
                queue = asyncio.Queue()
                queue.put_nowait(msg)
                coro = _pty_process_manager(xterm_guid, user_session, queue, send_func, self.system_up_user, self.console)
                task = asyncio.create_task(coro)
                self.xterm_lookup[xterm_guid] = (task, queue, time.time(), user_session)

            elif type_ in ('kill_process', 'xterm_resized', 'send_input_to_pty'):
                xterm_guid = msg['xterm_guid']
                if xterm_guid not in self.xterm_lookup:
                    log.error('The xterm_guid={} does not exist; invalid for type={}'.format(xterm_guid, type_))
                    return
                task, queue, _, _ = self.xterm_lookup[xterm_guid]
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
                await self._list_running(send_func, user_session)

            elif type_ == 'clear_screen':
                coro = _clear_console(self.console)
                asyncio.create_task(coro)

        elif 'origin' in msg and msg['origin'] == 'server' and 'type' in msg:
            type_ = msg['type']

            if type_ == 'start_contest':
                coro = self._start_contest(msg, send_func)
                asyncio.create_task(coro)

            elif type_ == 'end_contest':
                coro = self._end_contest(msg, send_func)
                asyncio.create_task(coro)

    async def end_device_session(self, vin):
        pass

    async def end_user_session(self, username, user_session):
        """
        We need to kill all ptys started by this user_session.
        Note: If you kill a `tmux` process which is attached to some session,
              it will just detach from the underlying tmux session (which is
              what we want).
        """
        needs_delete = []
        for xterm_guid, (task, queue, start_time, user_session_here) in self.xterm_lookup.items():
            if user_session_here == user_session:
                needs_delete.append(xterm_guid)
                task.cancel()
        for xterm_guid in needs_delete:
            del self.xterm_lookup[xterm_guid]

    async def disconnected_cdp(self):
        pass

    async def _list_running(self, send_func, user_session):
        running = []

        for xterm_guid, (task, queue, start_time, user_session_here) in self.xterm_lookup.items():
            x = {
                'xterm_guid':   xterm_guid,
                'start_time':   start_time,
                'user_session': user_session_here,
                'description':  '',  # TODO pty.description,
                'cmd':          '',  # TODO pty.cmd,
            }
            running.append(x)

        await send_func({
            'type': 'running_list',
            'running': running,
            'curtime': time.time(),
            'to_user_session': user_session,
        })

    async def _start_contest(self, msg, send_func):
        uid, gid, home = await _user_uid_gid_home(self.system_up_user)
        filepath = os.path.join(home, 'contest.py')
        if 'submission' in msg:
            with open(filepath, 'w') as f:
                f.write(msg['submission'])
        else:
            try:
                os.remove(filepath)
            except FileNotFoundError:
                pass
        cmds = [
            f"tmux kill-session -t {CONTEST_SESSION_NAME}".split(),
            f"tmux new-session -d -s {CONTEST_SESSION_NAME}".split(),
            f"tmux send-keys -t {CONTEST_SESSION_NAME} python3 SPACE {filepath} ENTER".split(),
        ]
        for cmd in cmds:
            await _run_subprocess(cmd, self.system_up_user)
        await send_func({
            'type': 'contest_session_started',
            'session_name': CONTEST_SESSION_NAME,
            'contest_guid': msg.get('contest_guid', None),
        })

    async def _end_contest(self, msg, send_func):
        cmds = [
            f"tmux kill-session -t {CONTEST_SESSION_NAME}".split(),
        ]
        for cmd in cmds:
            await _run_subprocess(cmd, self.system_up_user)


async def _clear_console(console):
    await console.clear_text()
    await console.big_clear()
    await console.clear_image()


async def _user_uid_gid_home(system_user):
    loop = asyncio.get_running_loop()
    pw_record = await loop.run_in_executor(None, pwd.getpwnam, system_user)
    uid = pw_record.pw_uid
    gid = pw_record.pw_gid
    home = pw_record.pw_dir
    return uid, gid, home


async def _write_code(xterm_guid, code_str, system_user):
    uid, gid, home = await _user_uid_gid_home(system_user)
    subdirs = xterm_guid[0:2], xterm_guid[2:4], xterm_guid[4:6], xterm_guid[6:8], xterm_guid
    directory = os.path.join(home, '.labs_code', *subdirs)
    if not os.path.exists(directory):
        os.makedirs(directory)
    code_path = os.path.join(directory, 'main.py')
    with open(code_path, 'w') as f:
        f.write(code_str)
    return code_path


async def _run_subprocess(cmd, system_user):
    # This runs a command _without_ a TTY.
    # Use `_run_pty_cmd_background()` when you need a TTY.
    cmd = ['sudo', '-u', system_user, '-i'] + cmd
    p = None
    try:
        p = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await p.communicate()
        p = None
        if stderr:
            stderr = stderr.decode('utf-8')
            log.error('Command {} wrote to stderr: {}'.format(repr(cmd), repr(stderr)))
        return stdout.decode('utf-8')
    except:
        if p is not None:
            p.kill()
            await p.wait()
        raise


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
        candiate_name = 'labs_{}'.format(i)
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
    return output


async def _list_sessions(send_func, user_session, system_user):
    session_names = await _tmux_ls(system_user)
    await send_func({
        'type': 'session_list',
        'session_names': session_names,
        'to_user_session': user_session,
    })


class PtyProcess:
    """
    Expose the relevant behavior of this process.

    FUTURE TODO: It would be nice if we didn't rely on executors in this, but
                 I've yet to figure out how to plug these FDs into they asyncio
                 event loop properly... ugh.
    """
    def __init__(self, stdin, stdout, stderr, p, loop):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.p = p
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
        if fd is None:
            return b''
        try:
            return await self.loop.run_in_executor(None, os.read, fd, READ_BUF_SIZE)
        except OSError:
            # PTYs throw OSError when they hit EOF, for some reason.
            # Pipes and regular files don't throw, so PTYs are unique.
            return b''

    async def close_fds(self):
        """Close the underlying file descriptors; don't leak FDs!"""
        for fd in set([self.stdin, self.stdout, self.stderr]):
            if fd is not None:
                os.close(fd)

    def setwinsize(self, rows, cols):
        try:
            s = struct.pack('HHHH', rows, cols, 0, 0)
            fcntl.ioctl(self.stdin, termios.TIOCSWINSZ, s)
            self.p.send_signal(signal.SIGWINCH)
        except Exception as e:
            log.error('Failed to `setwinsize`: {}'.format(e))
            traceback.print_exc(file=sys.stderr)

    async def gentle_kill(self):
        self.p.send_signal(signal.SIGHUP)
        try:
            await asyncio.wait_for(self.p.wait(), 2.0)
        except asyncio.TimeoutError:
            self.p.send_signal(signal.SIGTERM)
            try:
                await asyncio.wait_for(self.p.wait(), 2.0)
            except asyncio.TimeoutError:
                self.p.kill()
                await self.p.wait()


async def _run_pty_cmd_background(cmd, system_user, env_override=None, start_dir_override=None, size=None):
    loop = asyncio.get_running_loop()

    pw_record = await loop.run_in_executor(None, pwd.getpwnam, system_user)

    if start_dir_override is None:
        start_dir_override = pw_record.pw_dir

    env = {}

    whitelist = ['MAI_IS_VIRTUAL']
    blacklist_prefixes = ['MAI_', 'AWS_', 'ECS_']

    for k, v in os.environ.items():
        okay = True
        if k not in whitelist:
            for prefix in blacklist_prefixes:
                if k.startswith(prefix):
                    okay = False
                    break
        if okay:
            env[k] = v

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
    try:
        p = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=fd_slave_io,
                stdout=fd_slave_io,
                stderr=fd_slave_io,
                cwd=start_dir_override,
                env=env,
                preexec_fn=switch_user,
        )
    except:
        os.close(fd_master_io)
        os.close(fd_slave_io)
        raise

    os.close(fd_slave_io)

    stdin = fd_master_io
    stdout = fd_master_io
    stderr = None

    proc = PtyProcess(stdin, stdout, stderr, p, loop)

    if size is None:
        size = (24, 80)
    else:
        size = (size['rows'], size['cols'])
    proc.setwinsize(*size)

    return proc


async def _new_session(xterm_guid, user_session, send_func, settings, system_user):
    session_name = await _next_tmux_session_name(system_user)
    start_dir = '~' if 'start_dir' not in settings else settings['start_dir']
    cmd = ['tmux', 'new-session', '-c', start_dir, '-s', session_name]
    if 'cmd' in settings:
        cmd.extend(settings['cmd'])  # <-- becomes the shell argument to tmux
    size = settings.get('size', None)
    proc = None
    try:
        proc = await _run_pty_cmd_background(
                cmd=cmd,
                system_user=system_user,
                size=size
        )
        proc.description = "Attached session: {}".format(session_name)
        proc.cmd = cmd
        await send_func({
            'type': 'new_session_name_announcement',
            'session_name': session_name,
            'xterm_guid': xterm_guid,
            'to_user_session': user_session,
        })
        return proc
    except:
        if proc is not None:
            proc.p.kill()
            await proc.p.wait()
            await proc.close_fds()
        raise


async def _attach_session(session_name, settings, system_user):
    session_name = re.sub(r'[^A-Za-z0-9_]', '', session_name)  # safe string
    cmd = ['tmux', 'attach', '-d', '-t', session_name]
    size = settings.get('size', None)
    proc = await _run_pty_cmd_background(
            cmd=cmd,
            system_user=system_user,
            size=size
    )
    proc.description = "Attached session: {}".format(session_name)
    proc.cmd = cmd
    return proc


async def _start_process(xterm_guid, user_session, settings, system_user, console):
    if 'clear_screen' in settings and settings['clear_screen']:
        await _clear_console(console)

    if 'code_to_run' in settings:
        code_path = await _write_code(xterm_guid, settings['code_to_run'], system_user)
        cmd = ['python3', code_path]
        description = 'Running Code'
    else:
        cmd = settings['cmd']
        description = 'Custom Command'

    env_override = settings.get('env', {})
    env_override['TO_USER_SESSION'] = user_session

    start_dir_override = settings.get('start_dir', None)
    size = settings.get('size', None)

    proc = await _run_pty_cmd_background(
            cmd=cmd,
            system_user=system_user,
            env_override=env_override,
            start_dir_override=start_dir_override,
            size=size
    )
    proc.description = description
    proc.cmd = cmd
    return proc


async def _handle_ouptput(xterm_guid, user_session, proc, send_func):
    async def send(stream_name, buf):
        await send_func({
            'type': 'pty_output', 'xterm_guid': xterm_guid,
            'output': base64.b64encode(buf).decode('utf-8'),
            'stream_name': stream_name,
            'to_user_session': user_session,
        })

    async def read_stream(stream_name, read_func):
        # TODO: Should we buffer these `send()` calls? E.g. The Naggle-style delays?
        while True:
            buf = await read_func()
            if buf == b'':
                break
            await send(stream_name, buf)

    stdout_task = asyncio.create_task(read_stream('stdout', proc.read_stdout))
    stderr_task = asyncio.create_task(read_stream('stdout', proc.read_stderr))

    try:
        _, _ = await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)

    except asyncio.CancelledError:
        for t in [stdout_task, stderr_task]:
            t.cancel()
            try:
                await t
            except asyncio.CancelledError:
                pass
        raise

    except Exception as e:
        log.error('Unknown exception: {}'.format(e))
        traceback.print_exc(file=sys.stderr)
        raise

    finally:
        await send_func({
            'type': 'pty_output_closed',
            'xterm_guid': xterm_guid,
            'to_user_session': user_session,
        })

        log.info('Process output closed; pid={}; description={}; cmd={}'.format(proc.p.pid, proc.description, proc.cmd[0]))


async def _handle_input(queue, proc):
    try:
        while True:
            msg = await queue.get()
            type_ = msg['type']

            if type_ == 'xterm_resized':
                size = msg['size']
                size = (size['rows'], size['cols'])
                proc.setwinsize(*size)

            elif type_ == 'send_input_to_pty':
                input_ = msg['input']
                input_buf = base64.b64decode(input_)
                await proc.write_stdin(input_buf)

            else:
                raise Exception('Unexpected type sent to process manager: {}'.format(repr(msg)))

    except asyncio.CancelledError:
        log.info('Process input closed; pid={}; description={}; cmd={}'.format(proc.p.pid, proc.description, proc.cmd[0]))
        raise


async def _pty_process_manager(xterm_guid, user_session, queue, send_func, system_user, console):
    proc = None

    output_task = None
    input_task = None

    try:
        msg = await queue.get()
        type_ = msg['type']

        if type_ == 'new_session':
            proc = await _new_session(xterm_guid, user_session, send_func, msg, system_user)

        elif type_ == 'attach_session':
            session_name = msg['session_name']
            proc = await _attach_session(session_name, msg, system_user)

        elif type_ == 'start_process':
            proc = await _start_process(xterm_guid, user_session, msg, system_user, console)

        else:
            raise Exception('Unexpected type sent to process manager: {}'.format(repr(msg)))

        log.info('Process started; pid={}; description={}; cmd={}'.format(proc.p.pid, proc.description, proc.cmd[0]))

        output_task = asyncio.create_task(_handle_ouptput(xterm_guid, user_session, proc, send_func))
        input_task  = asyncio.create_task(_handle_input(queue, proc))

        await output_task
        await proc.p.wait()

    except asyncio.CancelledError:
        if proc is None:
            log.info('Process canceled before it began.')
        else:
            log.info('Process canceled; pid={}; description={}; cmd={}'.format(proc.p.pid, proc.description, proc.cmd[0]))

    except Exception as e:
        log.error('Unknown exception: {}'.format(e))
        traceback.print_exc(file=sys.stderr)

    finally:
        exitcode, signalcode = await _cleanup(proc, output_task, input_task)

        await send_func({
            'type': 'pty_program_exited',
            'xterm_guid': xterm_guid,
            'exitcode': exitcode,
            'signalcode': signalcode,
            'to_user_session': user_session,
        })


async def _cleanup(proc, output_task, input_task):
    try:
        if output_task is not None:
            output_task.cancel()
            try:
                await output_task
            except asyncio.CancelledError:
                pass

        if input_task is not None:
            input_task.cancel()
            try:
                await input_task
            except asyncio.CancelledError:
                pass

        if proc is not None:
            if proc.p.returncode is None:
                await proc.gentle_kill()
            await proc.close_fds()
            returncode = proc.p.returncode
            assert returncode is not None
            exitcode = returncode if returncode >= 0 else None
            signalcode = -returncode if returncode < 0 else None
            log.info('Process exited; pid={}; description={}; cmd={}; exitcode={}'.format(proc.p.pid, proc.description, proc.cmd[0], (exitcode, signalcode)))
        else:
            exitcode = None
            signalcode = signal.SIGHUP.value   # <-- The use canceled the process before it could even begin. Simulate a SIGHUP.

        return exitcode, signalcode

    except Exception as e:
        log.error('Unknown exception: {}'.format(e))
        traceback.print_exc(file=sys.stderr)
        return 500, None

