###############################################################################
#
# Copyright (c) 2017-2023 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

import asyncio
import serial
import struct
import threading
import queue
import time
import math


N_CMD_TRIES = 4


class Proto:
    def __init__(self, log):
        self.log = log
        self.loop = asyncio.get_running_loop()
        self.fd = serial.Serial('/dev/serial0', 115200, parity=serial.PARITY_NONE, timeout=5)
        self.next_cmdid = 0
        self.cmd_waiters = {}
        self.voltages = 0.0, 0.0, 0.0
        self.loop_freq = 0
        self.buzzer_lock = asyncio.Lock()
        self.buzzer_listeners = set()
        self.imu_counter_lock = asyncio.Lock()
        self.imu_use_counter = 0
        self.imu_last_update = None
        self.imu_event = asyncio.Event()
        self.is_maybe_stationary = True
        self.gyrovals = 0.0, 0.0, 0.0
        self.gyroaccumvals = 0.0, 0.0, 0.0
        self.accelvals = 0.0, 0.0, 1.0
        self.quaternion = 1.0, 0.0, 0.0, 0.0
        self.write_queue = queue.Queue()
        self.write_thread = threading.Thread(target=self._writer)
        self.write_thread.start()
        self.read_thread = threading.Thread(target=self._reader)
        self.read_thread.start()

    def close(self):
        if self.write_thread is not None:
            self.write_queue.put(None)
            self.write_thread.join()
            self.write_thread = None
            self.log.info('write thread joined')
        if self.fd is not None:
            self.fd.close()
            if hasattr(self.fd, 'cancel_read'):
                self.fd.cancel_read()
            if self.read_thread is not None:
                self.read_thread.join()
                self.read_thread = None
                self.log.info('read thread joined')
            self.fd = None
            self.imu_event.set()

    def _writer(self):
        while True:
            item = self.write_queue.get()
            if item is None:
                break
            self.fd.write(item)

    def _reader(self):
        fd = self.fd
        framer = MsgFramer()
        while fd.is_open:
            try:
                data = fd.read(fd.in_waiting or 1)
            except serial.SerialException as e:
                self.log.error(f'serial reader thread error: {e}')
                break
            if not data:
                self.log.info(f'serial reader closing on emtpy buffer: {data}')
                break
            for byte in data:
                if framer.put(byte):
                    msg = framer.extract_message()
                    self.loop.call_soon_threadsafe(self._dispatch_msg, msg)

    def _dispatch_msg(self, msg):
        command = msg[0]

        if command == ord('S'):
            cmdid, = struct.unpack('!H', msg[1:3])
            if cmdid in self.cmd_waiters:
                obj = self.cmd_waiters[cmdid]
                obj['response'] = msg[3:]
                obj['event'].set()

        elif command == ord('i'):
            self._handle_imu_msg(msg)

        elif command == ord('v'):
            vbatt1, vbatt2, vchrg = struct.unpack('!HHH', msg[1:])
            vbatt1 = 1000 * 3.3 * vbatt1 / 1023
            vbatt2 = 1000 * 3.3 * vbatt2 / 1023
            vchrg = 1000 * 3.3 * vchrg / 1023
            self.voltages = vbatt1, vbatt2, vchrg

        elif command == ord('r'):
            counter, = struct.unpack('!H', msg[1:])
            self.loop_freq = counter

        elif command == ord('b'):
            buzzer_is_playing = (msg[1] != 0x00)
            for f in self.buzzer_listeners:
                f(buzzer_is_playing)

        else:
            self.log.warning(f'unhandled message: {msg}')

    def _handle_imu_msg(self, msg):
        now = time.time()
        if self.imu_last_update is not None:
            dt_s = now - self.imu_last_update
        else:
            dt_s = 0.0
        self.imu_last_update = now
        flags = msg[1]
        self.is_maybe_stationary = bool(flags & 0b10000)
        #is_floats = bool(flags & 0b1000)
        #has_gyro = bool(flags & 0b100)
        #has_accel = bool(flags & 0b10)
        #has_ahrs = bool(flags & 0b1)
        #assert is_floats and has_gyro and has_accel and has_ahrs
        self.gyrovals = [math.degrees(v) for v in struct.unpack('<fff', msg[2:14])]
        self.gyroaccumvals = [(a + b*dt_s) for a, b in zip(self.gyroaccumvals, self.gyrovals)]
        self.accelvals = struct.unpack('<fff', msg[14:26])
        self.quaternion = struct.unpack('<ffff', msg[26:42])
        self.imu_event.set()
        self.imu_event = asyncio.Event()

    def _next_cmdid(self):
        while True:
            cmdid = self.next_cmdid
            self.next_cmdid += 1
            if self.next_cmdid > 65535:
                self.next_cmdid = 0
            if cmdid not in self.cmd_waiters:
                break
        return cmdid, struct.pack('!H', cmdid)

    async def __submit_cmd(self, cmd, args, timeout=None):
        cmdid, cmdid_bytes = self._next_cmdid()
        msg = _frame_msg(cmd + cmdid_bytes + args)
        event = asyncio.Event()
        self.cmd_waiters[cmdid] = {
            'response': None,
            'event': event,
        }
        try:
            self.write_queue.put(msg)
            await asyncio.wait_for(event.wait(), timeout=(timeout or 0.1))
            return self.cmd_waiters[cmdid]['response']
        finally:
            del self.cmd_waiters[cmdid]

    async def _submit_cmd(self, cmd, args, timeout=None):
        for _ in range(N_CMD_TRIES - 1):
            try:
                return await self.__submit_cmd(cmd, args, timeout=timeout)
            except asyncio.TimeoutError:
                # We'll loop back and retry...
                self.log.warning('CMD TIMEOUT')

        # Last attempt is allowed to throw anything:
        return await self.__submit_cmd(cmd, args, timeout=timeout)

    async def init(self):
        # TODO query all of the EEPROM
        await self.set_imu_enabled(False)

    async def version(self, timeout=None):
        res = await self._submit_cmd(b'v', b'', timeout=timeout)
        major, minor = struct.unpack('!2B', res)
        return major, minor

    async def play(self, freqHz, durationMS):
        async with self.buzzer_lock:
            freqHz = int(round(freqHz)) if freqHz is not None else 0
            durationMS = int(round(durationMS))
            if freqHz >= 40 and durationMS >= 10:
                msg = struct.pack('!2H', freqHz, durationMS)
                waiter = asyncio.Event()
                def listener(is_playing):
                    if not is_playing:
                        waiter.set()
                self.buzzer_listeners.add(listener)
                try:
                    _ = await self._submit_cmd(b'b', msg)
                    try:
                        await asyncio.wait_for(waiter.wait(), timeout=((durationMS / 1000) + 0.1))
                    except asyncio.TimeoutError:
                        # We'll just assume the buzzer stopped and that we missed the
                        # message that told us so.
                        self.log.warning('BUZZER TIMEOUT')
                finally:
                    self.buzzer_listeners.remove(listener)
            else:
                await asyncio.sleep(max(durationMS / 1000, 0))

    async def set_imu_enabled(self, enabled):
        await self._submit_cmd(b'i', struct.pack('!B', enabled))

    async def imu_acquire(self):
        async with self.imu_counter_lock:
            self.imu_use_counter += 1
            if self.imu_use_counter == 1:
                await self.set_imu_enabled(True)
                self.log.info('started IMU streaming')

    async def imu_release(self):
        async with self.imu_counter_lock:
            self.imu_use_counter -= 1
            if self.imu_use_counter == 0:
                await self.set_imu_enabled(False)
                self.imu_last_update = None
                self.log.info('stop IMU streaming')

    async def wait_imu_tick(self):
        await self.imu_event.wait()


MSG_FRAMER_BUF_SIZE = 128  # must be a power of 2


class MsgFramer:
    def __init__(self):
        self.m_buf = [0 for _ in range(MSG_FRAMER_BUF_SIZE)]
        self.m_size = 0
        self.m_pos = 0

    def put(self, byte):
        # Store the new value in the circular buffer:
        next_ = (self.m_pos + self.m_size) & (MSG_FRAMER_BUF_SIZE - 1)
        self.m_buf[next_] = byte
        self.m_size += 1

        # If we overfload, pop the front off to make room.
        if self.m_size > MSG_FRAMER_BUF_SIZE:
            self.m_size -= 1
            self.m_pos = (self.m_pos + 1) & (MSG_FRAMER_BUF_SIZE - 1)

        # Check if we have a valid message.
        return self._is_valid_message()

    def extract_message(self):  # <-- only call when `put` returns true!
        # Pop the preamble:
        self.m_size -= 1
        self.m_pos = (self.m_pos + 1) & (MSG_FRAMER_BUF_SIZE - 1)

        # Pop the message size:
        size = self.m_buf[self.m_pos]
        self.m_size -= 1
        self.m_pos = (self.m_pos + 1) & (MSG_FRAMER_BUF_SIZE - 1)

        # Pop the message:
        buf = []
        for i in range(size):
            buf.append(self.m_buf[self.m_pos])
            self.m_size -= 1
            self.m_pos = (self.m_pos + 1) & (MSG_FRAMER_BUF_SIZE - 1)

        # Pop the crc and epilog:
        for i in range(3):
            self.m_size -= 1
            self.m_pos = (self.m_pos + 1) & (MSG_FRAMER_BUF_SIZE - 1)

        return bytes(buf)

    def _is_valid_message(self):
        while True:
            while self.m_buf[self.m_pos] != 0xA6 and self.m_size > 0:
                # Pop until we find the preamble:
                self.m_size -= 1
                self.m_pos = (self.m_pos + 1) & (MSG_FRAMER_BUF_SIZE - 1)

            if self.m_size < 5:
                # All messages are at least 5 bytes, so bail.
                return False

            size = self.m_buf[(self.m_pos + 1) & (MSG_FRAMER_BUF_SIZE - 1)]
            if self.m_size < size + 5:
                # We don't have the full message yet.
                return False

            epilog = self.m_buf[(self.m_pos + size + 4) & (MSG_FRAMER_BUF_SIZE - 1)];
            if epilog != 0x59:
                # Epilog failed, so pop once and start over.
                self.m_size -= 1
                self.m_pos = (self.m_pos + 1) & (MSG_FRAMER_BUF_SIZE - 1)
                continue

            crc = 0x0000
            for i in range(size + 4):
                crc = _crc_xmodem_update(crc, self.m_buf[(self.m_pos + i) & (MSG_FRAMER_BUF_SIZE - 1)])
            if crc != 0:
                # CRC failed, so pop once and start over.
                self.m_size -= 1
                self.m_pos = (self.m_pos + 1) & (MSG_FRAMER_BUF_SIZE - 1)
                continue

            return True


def _crc_xmodem_update(crc, data):
    crc = (crc ^ (data << 8)) & 0xFFFF
    for i in range(8):
        if crc & 0x8000:
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF
        else:
            crc = (crc << 1) & 0xFFFF
    return crc


def _put_integrity(buf):
    assert len(buf) >= 2
    crc = 0x0000
    for byte in buf:
        crc = _crc_xmodem_update(crc, byte)
    return buf + bytes([ ((crc >> 8) & 0xFF), (crc & 0xFF) ])


def _frame_msg(buf):
    msg = b'\xA6' + bytes([len(buf)]) + buf
    return _put_integrity(msg) + b'\x59'

