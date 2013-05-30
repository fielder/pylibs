import struct


class BinaryRead(object):
    """
    Object wrapping a bit of struct, making reading binary values from
    raw bytes a little prettier.
    """

    def __init__(self, buf, offset=0):
        self._buf = buf
        self._pos = 0

        # toss bytes if caller wants to start in the middle of the data
        self.readBytes(offset)

    def readFormat(self, fmt):
        u = struct.unpack(fmt, self.readBytes(struct.calcsize(fmt)))
        if len(u) == 1:
            # if it looks like the caller just wanted one item, pull it
            # off the front of the one-item tuple
            u = u[0]
        return u

    def readBytes(self, count):
        if self._pos + count > len(self._buf):
            raise IndexError("underflow on %d bytes" % count)
        ret = self._buf[self._pos:self._pos + count]
        self._pos += count
        return ret

    def readByte(self):
        return self.readFormat("<b")

    def readUByte(self):
        return self.readFormat("<B")

    def readShort(self):
        return self.readFormat("<h")

    def readUShort(self):
        return self.readFormat("<H")

    def readInt(self):
        return self.readFormat("<i")

    def readUInt(self):
        return self.readFormat("<I")

    def readFloat(self):
        return self.readFormat("<f")

    def readString(self):
        start = self._pos
        while self._pos < len(self._buf) and self._buf[self._pos] != "\x00":
            self._pos += 1
        if self._pos == len(self._buf):
            raise ValueError("no string terminator")
        ret = self._buf[start:self._pos]
        self._pos += 1
        return ret

    def readKeyPair(self):
        s = self.readString()
        cidx = s.index(":")
        return (s[:cidx].strip(), s[cidx + 1:].strip())
