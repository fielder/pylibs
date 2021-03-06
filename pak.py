"""
Utility to load Quake1 or Quake2 data pak files.
"""

import types
import struct


def _pythonifyString(s):
    """
    Get rid of c-style string terminators.
    """

    if b"\x00" in s:
        s = s[:s.index(b"\x00")]
    return s.decode()


class PackFile(object):
    """
    On disk, each entry is 64 bytes. 56 for the name, 4 for the filepos,
    4 for the filelen.
    """

    DISK_SIZE = 64

    def __init__(self, raw):
        self.name = _pythonifyString(raw[:56])
        self.filepos, = struct.unpack("<I", raw[56:60])
        self.filelen, = struct.unpack("<I", raw[60:64])


class Pack(object):
    """
    Pak file starts off with a 4-byte identifier, then 2 little-endian
    ints telling the directory offset and length. The directory is
    composed of a bunch of entries, one for each file represented inside
    the pak file. Each directory entry is 64 bytes, telling the name of
    the data and where it is located within the file.
    """

    def __init__(self, path=""):
        self.files = []

        self._handle = None
        self._filename_to_file = {}

        if path:
            self.open(path)

    def open(self, path):
        handle = open(path, "rb")

        if handle.read(4) != b"PACK":
            raise Exception("\"{}\" is not a valid pak file".format(path))

        dirofs, = struct.unpack("<I", handle.read(4))
        dirlen, = struct.unpack("<I", handle.read(4))

        handle.seek(dirofs)
        raw = handle.read(dirlen)
        files = [PackFile(raw[idx * PackFile.DISK_SIZE:(idx + 1) * PackFile.DISK_SIZE]) for idx in range(dirlen // PackFile.DISK_SIZE)]

        self.close()
        self.files = files
        self._handle = handle
        self._filename_to_file = { f.name: f for f in self.files }

    def close(self):
        if self._handle:
            self.files = []
            self._handle.close()
            self._handle = None
            self._filename_to_file = {}

    def readFile(self, f):
        if isinstance(f, int):
            f = self.files[f]
        elif isinstance(f, str):
            f = self._filename_to_file[f]
        elif isinstance(f, PackFile):
            pass
        else:
            raise Exception("invalid pakfile entry \"{}\"".format(f))

        self._handle.seek(f.filepos)
        return self._handle.read(f.filelen)

    def hasFile(self, path):
        return path in self._filename_to_file.keys()


if __name__ == "__main__":
    import os
    import sys

    if len(sys.argv) == 1:
        pass
    elif len(sys.argv) == 2:
        p = Pack(sys.argv[1])
        print("offset size name")
        for f in p.files:
            print("{} {} {}".format(f.filepos, f.filelen, f.name))
        print("{} files".format(len(p.files)))
    else:
        p = Pack(sys.argv[1])

        if len(sys.argv) >= 3:
            if sys.argv[2] == "*":
                names = (f.name for f in p.files)
            else:
                names = sys.argv[2:]
        else:
            names = []

        for name in names:
            dirs = os.path.dirname(name)
            if dirs and not os.path.isdir(dirs):
                os.makedirs(dirs)
            dat = p.readFile(name)
            fp = open(name, "wb")
            fp.write(dat)
            fp.close()
            print("wrote {} bytes to \"{}\"".format(len(dat), name))
