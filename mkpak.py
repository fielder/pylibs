#!/usr/bin/env python

import sys
import os
import struct


def _cString(s, totlen):
    if len(s) < totlen:
        s += "\x00" * (totlen - len(s))
    if s[-1] != "\x00":
        s = s[:-1] + "\x00"
    return s


class PFile(object):
    def __init__(self, n, p, l):
        self.name = n
        self.filepos = p
        self.filelen = l

    def asRaw(self):
        return struct.pack("56s", _cString(self.name, 56)) + \
               struct.pack("<I", self.filepos) + \
               struct.pack("<I", self.filelen)


def _pakFiles(path, files):
    fileinfos = []

    fp = open(path, "wb")
    fp.write("\x00" * 12) # header will get overwritten later with correct info

    for f in files:
        name = "/".join(f.split(os.path.sep))
        dat = open(f, "rb").read()
        fileinfos.append(PFile(name, fp.tell(), len(dat)))
        fp.write(dat)
        print "added \"%s\"" % name

    dirofs = fp.tell()

    for fi in fileinfos:
        fp.write(fi.asRaw())

    dirlen = fp.tell() - dirofs

    fp.seek(0)
    fp.write("PACK")
    fp.write(struct.pack("<I", dirofs))
    fp.write(struct.pack("<I", dirlen))

    print "wrote %d files" % len(fileinfos)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "usage: %s <output_file> <input_file>" % sys.argv[0]
        sys.exit(0)

    out_path = sys.argv[1]
    in_path = sys.argv[2]

    if in_path == "-":
        in_handle = sys.stdin
    else:
        in_handle = open(in_path, "rt")

    lines = [f.strip() for f in in_handle.readlines()]
    files = [os.path.normpath(p) for p in filter(None, lines)]

    # disallow any path referring up the tree
    for f in files:
        if f.startswith(os.path.pardir) or f.startswith(os.path.sep):
            print "error: non-relative path \"%s\"" % f
            sys.exit(0)

    _pakFiles(out_path, files)
