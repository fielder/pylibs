#!/usr/bin/env python3

import struct


class ByteReader(object):
    """
    Simple binary data unpacker from a byte string.
    """

    DEFAULT_ENDIANESS = "<"

    def __init__(self, byte_string):
        self._idx = 0
        self._s = byte_string

    def seek(self, offset):
        if offset < 0 or offset >= len(self._s):
            raise ValueError("invalid offset {}".format(offset))

        self._idx = offset

    def get(self, fmt):
        """
        Read the next value from the string. The format is given in
        the same format as used in the struct module.
        """

        if fmt[0] not in "<>":
            fmt = self.DEFAULT_ENDIANESS + fmt

        sz = struct.calcsize(fmt)
        if self._idx + sz > len(self._s):
            raise Exception("read underflow for format \"{}\"".format(fmt))

        bytes_ = self._s[self._idx:self._idx + sz]
        self._idx += sz

        ret, = struct.unpack(fmt, bytes_)

        return ret

    def getByte(self):
        return self.get("b")

    def getUByte(self):
        return self.get("B")

    def getShort(self):
        return self.get("h")

    def getUShort(self):
        return self.get("H")

    def getInt(self):
        return self.get("i")

    def getUInt(self):
        return self.get("I")

    def getLong(self):
        return self.get("l")

    def getULong(self):
        return self.get("L")

    def getFloat(self):
        return self.get("f")

    def getDouble(self):
        return self.get("d")
