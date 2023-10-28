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


class Proto:
    def __init__(self, log):
        self.log = log
        self.loop = asyncio.get_running_loop()
        self.fd = serial.Serial('/dev/serial0', 115200, parity=serial.PARITY_NONE, timeout=10)
        self.cmd_id = 0
        self.cmd_waiters = {}
        self.voltage_values = 0.0, 0.0, 0.0
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
            if self.read_thread is not None:
                self.read_thread.join()
                self.read_thread = None
                self.log.info('read thread joined')
            self.fd = None

    def _writer(self):
        time.sleep(1)
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

        elif command == ord('v'):
            vbatt1, vbatt2, vchrg = struct.unpack('!HHH', msg[1:])
            vbatt1 = 1000 * 3.3 * vbatt1 / 1023
            vbatt2 = 1000 * 3.3 * vbatt2 / 1023
            vchrg = 1000 * 3.3 * vchrg / 1023
            self.voltage_values = vbatt1, vbatt2, vchrg

        else:
            self.log.warning(f'unhandled message: {msg}')

    def _next_cmd_id(self):
        while True:
            cmdid = self.cmd_id
            self.cmd_id += 1
            if self.cmd_id > 65535:
                self.cmd_id = 0
            if cmdid not in self.cmd_waiters:
                break
        return cmdid, struct.pack('!H', cmdid)

    async def _submit_cmd(self, cmd, args):
        cmdid, cmdid_bytes = self._next_cmd_id()
        msg = _frame_msg(cmd + cmdid_bytes + args)
        event = asyncio.Event()
        self.cmd_waiters[cmdid] = {
            'response': None,
            'event': event,
        }
        try:
            self.write_queue.put(msg)
            await event.wait()
            return self.cmd_waiters[cmdid]['response']
        finally:
            del self.cmd_waiters[cmdid]

    async def init(self):
        pass

    async def version(self):
        res = await self._submit_cmd(b'v', b'')
        major, minor = struct.unpack('!2B', res)
        return major, minor

    async def voltages(self):
        return self.voltage_values


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

