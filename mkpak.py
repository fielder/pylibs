#!/usr/bin/env python3

import sys
import os
import struct


class PakEntry(object):
    def __init__(self, name, pos, length):
        if len(name) >= 56:
            raise ValueError("pak entry name too long: \"{}\"".format(name))
        self.name = name
        self.filepos = pos
        self.filelen = length

    def rawInfo(self):
        return struct.pack("56s", self.name.encode()) + \
               struct.pack("<I", self.filepos) + \
               struct.pack("<I", self.filelen)


def packFiles(path, filenames):
    entries = []

    with open(path, "wb") as fp:
        fp.write(b"\x00" * 12) # header will get overwritten later with correct info

        for fn in filenames:
            name = "/".join(fn.split(os.path.sep))
            with open(fn, "rb") as infp:
                dat = infp.read()
            entries.append(PakEntry(name, fp.tell(), len(dat)))
            fp.write(dat)
            print("added \"{}\"".format(name))

        dirofs = fp.tell()

        for e in entries:
            fp.write(e.rawInfo())

        dirlen = fp.tell() - dirofs

        fp.seek(0)
        fp.write(b"PACK")
        fp.write(struct.pack("<I", dirofs))
        fp.write(struct.pack("<I", dirlen))

        print("wrote {} files".format(len(entries)))


def main(argv):
    if len(sys.argv) != 3:
        print("usage: {} <output_pak> <file_list>".format(sys.argv[0]))
        print("")
        print("Collect files into a single .pak file. The input files are\ngiven as a simple list of files in the input file. If '-' is\ngiven as the file list, read the list from stdin.")
        print("")
        sys.exit(0)

    out_path = sys.argv[1]
    in_path = sys.argv[2]

    if in_path == "-":
        lines = [l.strip() for l in sys.stdin.readlines()]
    else:
        with open(in_path, "rt") as fp:
            lines = [l.strip() for l in fp.readlines()]

    filenames = [os.path.normpath(p) for p in filter(None, lines)]

    # disallow any path referring up the tree
    for fn in filenames:
        if fn.startswith(os.path.pardir) or fn.startswith(os.path.sep):
            print("error: non-relative path \"{}\"".format(fn))
            sys.exit(0)

    packFiles(out_path, filenames)


if __name__ == "__main__":
    main(sys.argv)
