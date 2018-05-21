import struct


def _decompress(raw, idx, w):
    row = b""
    while len(row) < w:
        b = raw[idx]
        idx += 1
        if b > 128:
            c = raw[idx:idx+1]
            idx += 1
            row += c * (257 - b)
        elif b < 128:
            cnt = b + 1
            row += raw[idx:idx+cnt]
            idx += cnt
        else:
            # no-op
            pass
    return (row, idx)


def loadLBM(fdat):
    if fdat[0:4] != b"FORM":
        raise ValueError("image did not start with FORM chunk")
    formsz, = struct.unpack(">I", fdat[4:8])

    typeid = fdat[8:12]
    if typeid not in (b"PBM ",):
        raise ValueError("unsupported type id \"{}\"".format(typeid))

    pixels = b""
    compressed = False
    pal = None
    w = None
    h = None

    idx = 12
    while idx < len(fdat):
        if idx % 2:
            # chunks always begin on even byte
            idx += 1
            continue

        chunktype = fdat[idx:idx+4]
        idx += 4
        chunksz, = struct.unpack(">I", fdat[idx:idx+4])
        idx += 4
        raw = fdat[idx:idx+chunksz]
        idx += chunksz

        if chunktype == b"BMHD":
            w, = struct.unpack(">H", raw[0:2])
            h, = struct.unpack(">H", raw[2:4])
            compressed = bool(raw[10])

        elif chunktype == b"CMAP":
            pal = [raw[i*3:i*3+3] for i in range(len(raw)//3)]

        elif chunktype == b"BODY":
            if None in (w, h):
                raise ValueError("body without header")
            i = 0
            for y in range(h):
                if compressed:
                    row, i = _decompress(raw, i, w)
                else:
                    row = raw[i:i+w]
                    #TODO: quake src indicates input rows are 2-aligned
                    # but I've seen it said that the chunk data is used
                    # *directly*
                    if w % 2:
                        i += w + 1
                    else:
                        i += w
                pixels += row

        else:
            # unknown sub-chunk; ignore
            pass

    return (pixels, pal, w, h)


if __name__ == "__main__":
    import sys
    import os
    import png

    for path in sys.argv[1:]:
        fdat = open(path, "rb").read()

        pixels, pal, w, h = loadLBM(fdat)
        if not pal:
            raise ValueError("file contains no colormap")

        rgb = b"".join((pal[p] for p in pixels))

        base, ext = os.path.splitext(path)
        outpath = os.path.extsep.join((base, "png"))
        png.writePNG(outpath, rgb, w, h)

