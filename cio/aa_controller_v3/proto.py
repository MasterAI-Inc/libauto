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

EEPROM_NUM_BYTES = 256

MAX_DECIAMPS = 50

DEFAULT_LED_BRIGHTNESS = 0.5  # range [0.0, 1.0]
MAX_LED_BRIGHTNESS = 40       # range [0, 255]


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
        self.buttonstate = [(0, 0, False) for _ in range(3)]
        self.buttonlisteners = []
        self.photoresistor_counter_lock = asyncio.Lock()
        self.photoresistor_use_counter = 0
        self.photoresistor_vals = 0.0, 0.0
        self.photoresistor_event = asyncio.Event()
        self.encoder_e1_counter_lock = asyncio.Lock()
        self.encoder_e1_use_counter = 0
        self.encoder_e1_vals = 0, 0, 0, 0, 0
        self.encoder_e1_event = asyncio.Event()
        self.eeprom_vals = [None for _ in range(EEPROM_NUM_BYTES)]
        self.eeprom_event = asyncio.Event()
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
            self.photoresistor_event.set()
            self.encoder_e1_event.set()

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

        elif command == ord('p'):
            v, = struct.unpack('!H', msg[1:])
            v = 3.3 * v / 1023
            r = ((3.3 - v) * 470000) / v
            self.photoresistor_vals = 1000*v, r
            self.photoresistor_event.set()
            self.photoresistor_event = asyncio.Event()

        elif command == ord('e'):
            clicks, aCount, bCount, aUpTime, bUpTime = struct.unpack('<hHHII', msg[1:])
            self.encoder_e1_vals = clicks, aCount, bCount, aUpTime, bUpTime
            self.encoder_e1_event.set()
            self.encoder_e1_event = asyncio.Event()

        elif command == ord('r'):
            counter, = struct.unpack('!H', msg[1:])
            self.loop_freq = counter

        elif command == ord('b'):
            buzzer_is_playing = (msg[1] != 0x00)
            for f in self.buzzer_listeners:
                f(buzzer_is_playing)

        elif command == ord('B'):
            event = msg[1]
            events = []
            if event & 0b000001:
                self._button_was_released(2, events)
            if event & 0b000010:
                self._button_was_pressed(2, events)
            if event & 0b000100:
                self._button_was_released(1, events)
            if event & 0b001000:
                self._button_was_pressed(1, events)
            if event & 0b010000:
                self._button_was_released(0, events)
            if event & 0b100000:
                self._button_was_pressed(0, events)
            for listener in self.buttonlisteners:
                listener(events)

        elif command == ord('E'):
            addr, = struct.unpack('!H', msg[1:3])
            vals = msg[3:]
            for i, v in enumerate(vals):
                if addr + i < EEPROM_NUM_BYTES:
                    self.eeprom_vals[addr + i] = v
            self.eeprom_event.set()
            self.eeprom_event = asyncio.Event()

        else:
            self.log.warning(f'unhandled message: {msg}')

    def _button_was_pressed(self, button_index, events):
        events.append({'button': button_index, 'action': 'pressed'})
        npress, nrelease, ispressed = self.buttonstate[button_index]
        self.buttonstate[button_index] = (npress + 1, nrelease, True)

    def _button_was_released(self, button_index, events):
        events.append({'button': button_index, 'action': 'released'})
        npress, nrelease, ispressed = self.buttonstate[button_index]
        self.buttonstate[button_index] = (npress, nrelease + 1, False)

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
        await self.set_imu_enabled(False)
        await self.photoresistor_set_enabled(False)
        await self.encoder_e1_set_enabled(False)
        await self.read_all_eeprom()

    async def version(self, timeout=None):
        res = await self._submit_cmd(b'v', b'', timeout=timeout)
        major, minor = struct.unpack('!2B', res)
        return major, minor

    def is_charging(self):
        vbatt1, vbatt2, vchrg = self.voltages
        return vbatt2 < vchrg

    async def buzzer_play(self, freqHz, durationMS):
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

    async def buzzer_stop(self):
        await self._submit_cmd(b'n', b'')

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

    async def wait_imu_tick(self, timeout=None):
        if timeout is None:
            await self.imu_event.wait()
        else:
            await asyncio.wait_for(self.imu_event.wait(), timeout=timeout)

    async def set_led(self, index, val, brightness):
        if brightness is None:
            brightness = DEFAULT_LED_BRIGHTNESS
        else:
            brightness /= 255
        brightness *= MAX_LED_BRIGHTNESS
        val = [int(round(v*brightness)) for v in val]
        await self._submit_cmd(b'l', struct.pack('!4B', index, *val))

    async def photoresistor_set_enabled(self, enabled):
        await self._submit_cmd(b'p', struct.pack('!B', enabled))

    async def photoresistor_acquire(self):
        async with self.photoresistor_counter_lock:
            self.photoresistor_use_counter += 1
            if self.photoresistor_use_counter == 1:
                await self.photoresistor_set_enabled(True)
                self.log.info('started photoresistor streaming')

    async def photoresistor_release(self):
        async with self.photoresistor_counter_lock:
            self.photoresistor_use_counter -= 1
            if self.photoresistor_use_counter == 0:
                await self.photoresistor_set_enabled(False)
                self.log.info('stop photoresistor streaming')

    async def photoresistor_tick(self):
        await self.photoresistor_event.wait()

    async def encoder_e1_set_enabled(self, enabled):
        await self._submit_cmd(b'e', struct.pack('!B', enabled))

    async def encoder_e1_acquire(self):
        async with self.encoder_e1_counter_lock:
            self.encoder_e1_use_counter += 1
            if self.encoder_e1_use_counter == 1:
                await self.encoder_e1_set_enabled(True)
                self.log.info('started encoder_e1 streaming')

    async def encoder_e1_release(self):
        async with self.encoder_e1_counter_lock:
            self.encoder_e1_use_counter -= 1
            if self.encoder_e1_use_counter == 0:
                await self.encoder_e1_set_enabled(False)
                self.log.info('stop encoder_e1 streaming')

    async def encoder_e1_tick(self):
        await self.encoder_e1_event.wait()

    async def read_all_eeprom(self):
        addr = 0
        chunk_length = 32
        while addr < EEPROM_NUM_BYTES:
            len_here = min(chunk_length, EEPROM_NUM_BYTES - addr)
            event = self.eeprom_event
            await self._submit_cmd(b'r', struct.pack('!HB', addr, len_here))
            await event.wait()
            addr += len_here
        for v in self.eeprom_vals:
            assert v is not None
            assert isinstance(v, int)

    async def write_eeprom(self, addr, val):
        assert isinstance(val, int)
        if addr >= 0 and addr < EEPROM_NUM_BYTES:
            await self._submit_cmd(b'w', struct.pack('!HB', addr, val))
            self.eeprom_vals[addr] = val

    def eeprom_read_buf(self, addr, length):
        assert 0 <= addr < EEPROM_NUM_BYTES
        assert 0 < addr + length <= EEPROM_NUM_BYTES
        return bytes(self.eeprom_vals[addr:addr+length])

    async def set_steering(self, steering, channel=0):
        cmd = [b's', b't'][channel]
        await self._submit_cmd(cmd, struct.pack('!H', steering))

    async def set_throttle(self, throttle):
        if throttle == 0:
            await self._submit_cmd(b'd', struct.pack('!b', 0))  # set duty
            await self._submit_cmd(b'a', struct.pack('!B', 5))  # set max deciamps
        else:
            deciamps = int(round((abs(throttle) / 100) * MAX_DECIAMPS))
            duty = 127 if throttle > 0 else -127
            await self._submit_cmd(b'a', struct.pack('!B', deciamps))  # set max deciamps
            await self._submit_cmd(b'd', struct.pack('!b', duty))  # set duty


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

