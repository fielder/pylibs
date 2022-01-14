#!/usr/bin/env python3

import string
import sys

import wad2
import png
import bytereader

MIPLEVELS = 4


def filtName(n):
    chars = string.ascii_letters + string.digits + "_"
    return "".join(filter(lambda c: c in chars, n))


def parseTex(raw):
    br = bytereader.ByteReader(raw)
    name = br.get("16s").decode()
    if "\x00" in name:
        name = name[:name.index("\x00")]
    w = br.getUInt()
    h = br.getUInt()
    offsets = [br.getUInt() for _ in range(MIPLEVELS)]

    mip0_off = offsets[0]
    pix = raw[mip0_off:mip0_off + w * h]
    return (name, w, h, pix)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        w = wad2.Wad2(p)

        if "PALETTE" in w.lump_names:
            pal = w.readLump("PALETTE")
        else:
            with open("PALETTE", "rb") as fp:
                pal = fp.read()

        def _rgb(i):
            return bytes((pal[i * 3 + 0], pal[i * 3 + 1], pal[i * 3 + 2]))
        index2rgb = [_rgb(i) for i in range(256)]

        for l in w.lumps:
            if l.type == wad2.TYP_MIPTEX:
                tname, tw, th, tpix = parseTex(w.readLump(l))
                outpath = "{}.png".format(filtName(tname))
                rgbpix = b"".join((index2rgb[p] for p in tpix))
                png.writePNG(outpath, rgbpix, tw, th, is_rgba=False)
