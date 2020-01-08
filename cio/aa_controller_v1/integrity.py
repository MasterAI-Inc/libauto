###############################################################################
#
# Copyright (c) 2017-2020 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################


def _crc_xmodem_update(crc, data):
    """
    See `integrity.cpp` for details on this function.
    """
    crc = (crc ^ (data << 8)) & 0xFFFF
    for i in range(8):
        if crc & 0x8000:
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF
        else:
            crc = (crc << 1) & 0xFFFF
    return crc


def put_integrity(buf, type_=bytes):
    """
    Put integrity bytes into `buf`.
    Return a new buffer of type `type_` having the
    integrity bytes appended.
    """
    if len(buf) == 0:
        return type_([0xAA])
    elif len(buf) == 1:
        return type_([buf[0], buf[0] ^ 0xD6])
    else:
        crc = 0x0000
        for byte in buf:
            crc = _crc_xmodem_update(crc, byte)
        return type_(buf) + type_([ ((crc >> 8) & 0xFF), (crc & 0xFF) ])


def check_integrity(buf):
    """
    Check the integrity of `buf`. Return `None` if `buf`
    has no integrity, else return a new buffer having
    the integrity bytes removed.
    """
    if len(buf) == 0:
        return None
    elif len(buf) == 1:
        if buf[0] != 0xAA:
            return None
        return buf[:-1]
    elif len(buf) == 2:
        if buf[0] ^ buf[1] ^ 0xD6:
            return None
        return buf[:-1]
    elif len(buf) == 3:
        return None
    else:
        crc = 0x0000
        for byte in buf:
            crc = _crc_xmodem_update(crc, byte)
        if crc == 0:
            return buf[:-2]
        return None


def read_len_with_integrity(n):
    """
    Return the number of bytes needed to read
    a buffer of length `n` where the buffer
    that is read will have integrity bytes added.
    """
    if n == 0:
        return 1
    elif n == 1:
        return 2
    else:
        return n+2


if __name__ == "__main__":

    def to_list(line):
        line = line.replace("<done>", "")
        line = line.strip()
        return [int(b) for b in line.split()]

    with open("integrity_tests.txt") as f:
        while True:
            one = f.readline()
            two = f.readline()
            if not one: break
            orig = to_list(one)
            encoded = to_list(two)
            print(orig)
            print(encoded)
            print()

            assert(put_integrity(orig, list) == encoded)
            assert(check_integrity(encoded) == orig)
            assert(read_len_with_integrity(len(orig)) == len(encoded))

