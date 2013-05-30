"""
Utility to load/save DOOM engine wad files.
"""

import types
import struct


def _pythonifyString(s):
    """
    Get rid of c-style string terminators.
    """

    if "\x00" in s:
        s = s[:s.index("\x00")]
    return s


def _wadifyString(s):
    """
    Pad a wad string out to a certain length, padding with empty bytes.
    Note the strings won't necessarily be terminated.
    """

    if len(s) < 8:
        s += "\x00" * (8 - len(s))
    return s


def writeWad(path, lumps):
    """
    Write lumps out to a wad. The lumps array should be tuples in
    (name, data) form.
    """

    fp = open(path, "wb")

    # dummy header, will get overwritten later
    fp.write("\x00" * 12)

    # lump data
    offs = []
    for lumpname, lumpdata in lumps:
        offs.append(fp.tell())
        fp.write(lumpdata)

    # entry table
    infotableofs = fp.tell()
    for offset, (lumpname, lumpdata) in zip(offs, lumps):
        fp.write(struct.pack("<i", offset))
        fp.write(struct.pack("<i", len(lumpdata)))
        fp.write(_wadifyString(lumpname))

    # header
    fp.seek(0)
    fp.write("PWAD")
    fp.write(struct.pack("<i", len(lumps)))
    fp.write(struct.pack("<i", infotableofs))

    fp.close()


class WadLump(object):
    """
    On disk, each entry is 16 bytes. 8 for the name, 4 for the filepos,
    4 for the size.
    """

    DISK_SIZE = 16

    def __init__(self, raw):
        self.filepos, = struct.unpack("<i", raw[0:4])
        self.size, = struct.unpack("<i", raw[4:8])
        self.name = _pythonifyString(raw[8:16])


class Wad(object):
    """
    Utility to read from wad files.
    """

    def __init__(self, path=""):
        self.lumps = []
        self.lump_name_to_num = {}
        self.lump_names = []

        self._handle = None

        if path:
            self.open(path)

    def open(self, path):
        handle = open(path, "rb")

        if handle.read(4) not in ("IWAD", "PWAD"):
            raise Exception("\"%s\" is not a valid wad file" % path)

        numlumps, = struct.unpack("<i", handle.read(4))
        infotableofs, = struct.unpack("<i", handle.read(4))

        handle.seek(infotableofs)
        raw = handle.read(numlumps * WadLump.DISK_SIZE)
        lumps = [WadLump(raw[idx * WadLump.DISK_SIZE:(idx + 1) * WadLump.DISK_SIZE]) for idx in xrange(numlumps)]

        self.close()
        self.lumps = lumps
        self.lump_name_to_num = { l.name: idx for idx, l in enumerate(self.lumps) }
        self.lump_names = [l.name for l in self.lumps]
        self._handle = handle

    def close(self):
        if self._handle:
            self.lumps = []
            self.lump_name_to_num = {}
            self._handle.close()
            self._handle = None

    def readLumpFromOffset(self, lumpname, offs):
        while offs < len(self.lumps):
            if self.lumps[offs].name == lumpname:
                return self.readLump(self.lumps[offs])
            offs += 1
        raise Exception("unable to find lump \"%s\"" % lumpname)

    def readLump(self, l):
        if type(l) == types.IntType:
            l = self.lumps[l]
        elif type(l) == types.StringType:
            l = self.lumps[self.lump_name_to_num[l]]
        elif type(l) == WadLump:
            pass
        else:
            raise Exception("invalid lump \"%s\"" % l)

        self._handle.seek(l.filepos)
        return self._handle.read(l.size)


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        pass
    elif len(sys.argv) == 2:
        w = Wad(sys.argv[1])
        print "offset size name"
        for l in w.lumps:
            print l.filepos, l.size, l.name
        print "%d lumps" % len(w.lumps)
    else:
        w = Wad(sys.argv[1])
        for lumpname in sys.argv[2:]:
            lumpname = lumpname.upper()
            dat = w.readLump(lumpname)
            fp = open(lumpname, "wb")
            fp.write(dat)
            fp.close()
            print "wrote %d bytes to \"%s\"" % (len(dat), lumpname)
