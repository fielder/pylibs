"""
Utility to load/save palettized pcx files. This doesn't conform to the
full PCX spec, just enough to allow loading common 8-bit palettized
images.
"""

import struct


class _PCXHeader(object):
    MEMBERS = [ ("manufacturer",   "B"),
                ("version",        "B"),
                ("encoding",       "B"),
                ("bpp",            "B"),
                ("minx",           "<H"),
                ("miny",           "<H"),
                ("maxx",           "<H"),
                ("maxy",           "<H"),
                ("hres",           "<H"),
                ("vres",           "<H"),
                ("ega_palette",    "48s"),
                ("reserved",       "B"),
                ("num_planes",     "B"),
                ("bytes_per_line", "<H"),
                ("pal_type",       "<H"),
                ("unused",         "58s") ]

    DISK_SIZE = sum([struct.calcsize(m[1]) for m in MEMBERS])

    def __init__(self, raw=None):
        if raw is None:
            raw = "\x00" * self.DISK_SIZE

        idx = 0
        for obj, fmt in self.MEMBERS:
            sz = struct.calcsize(fmt)
            dat = raw[idx:idx + sz]
            idx += sz
            setattr(self, obj, struct.unpack(fmt, dat)[0])

    def __repr__(self):
        return "".join([struct.pack(fmt, getattr(self, obj)) for obj, fmt in self.MEMBERS])


def loadPCX(path):
    return loadPCXFromRaw(open(path, "rb").read())


def loadPCXFromRaw(raw):
    header = _PCXHeader(raw)

    width = header.maxx - header.minx + 1
    height = header.maxy - header.miny + 1

    if  header.manufacturer != 0x0a or \
        header.version != 5         or \
        header.encoding != 1        or \
        header.bpp != 8             or \
        header.num_planes != 1      or \
        header.pal_type != 1        or \
        width <= 0                  or \
        height <= 0:
            raise Exception("invalid file")

    pixels = ""
    idx = header.DISK_SIZE
    for y in xrange(height):
        x = 0
        while x < header.bytes_per_line:
            p = raw[idx]
            idx += 1
            if (ord(p) & 0xc0) == 0xc0:
                c = ord(p) & 0x3f
                p = raw[idx]
                idx += 1
            else:
                c = 1
            while c > 0:
                if x < width:
                    # bytes_per_line must always be even, although the
                    # image width might be odd. So ignore extra bytes
                    # that don't contribute to the image's pixels.
                    pixels += p
                x += 1
                c -= 1

    if raw[idx] != "\x0c":
        raise Exception("missing palette identifier byte")

    palette = raw[-768:]

    return (width, height, palette, pixels)


def writePCX(path, width, height, palette, pixels):

    def _encodeRow(row):
        idx = 0
        ret = ""
        while idx < len(row):
            c = 0
            p = row[idx]
            while idx < len(row) and row[idx] == p and c < 0x3f:
                idx += 1
                c += 1
            if c > 1 or (ord(p) & 0xc0) == 0xc0:
                ret += chr(0xc0 + c)
            ret += p

        if len(row) & 1:
            # PCX spec says each row must have an even byte count
            ret += "\x00"

        return ret

    if width * height != len(pixels):
        raise Exception("pixel count does not match given dimensions")
    if len(palette) != 768:
        raise Exception("invalid palette")

    header = _PCXHeader()
    header.manufacturer = 0x0a
    header.version = 5
    header.encoding = 1
    header.bpp = 8
    header.minx = 0
    header.miny = 0
    header.maxx = width - 1
    header.maxy = height - 1
    header.hres = width
    header.vres = height
    header.num_planes = 1
    header.bytes_per_line = (width + 1) & ~1
    header.pal_type = 1

    rle = "".join([_encodeRow(pixels[y * width:(y + 1) * width]) for y in xrange(height)])

    fp = open(path, "wb")
    fp.write(repr(header))
    fp.write(rle)
    fp.write("\x0c")
    fp.write(palette)
    fp.close()
