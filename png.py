#!/usr/bin/env python3

import collections
import struct
import zlib

_png_signature = bytes((137, 80, 78, 71, 13, 10, 26, 10))


def _iterChop(sequence, chunksz):
    for idx in range(0, len(sequence), chunksz):
        yield sequence[idx : idx + chunksz]


def _mkChunk(type_, bytes_):
    body = type_.encode() + bytes_
    return  struct.pack(">I", len(bytes_)) + \
            body + \
            struct.pack(">I", zlib.crc32(body))


def _buildPalettized(pixels, width, height, paldict):
    """
    paldict is in the form { b"\\xRR\\xGG\\xBB" : pal_idx }
    """

    # convert rgb -> pal_idx
    idxpix = bytes((paldict[p] for p in _iterChop(pixels, 3)))

    # the png spec recommends to just filter rows with type 0 for
    # palettized images (no filtering)

    filtered = b"".join((b"\x00" + row for row in _iterChop(idxpix, width)))

    ihdr_dat = struct.pack(">IIBBBBB", width, height, 8, 3, 0, 0, 0)
    plte_dat = b"".join(paldict.keys())
    idat_dat = zlib.compress(filtered)

    ihdr_chunk = _mkChunk("IHDR", ihdr_dat)
    plte_chunk = _mkChunk("PLTE", plte_dat)
    idat_chunk = _mkChunk("IDAT", idat_dat)
    iend_chunk = _mkChunk("IEND", b"")

    return _png_signature + ihdr_chunk + plte_chunk + idat_chunk + iend_chunk


def _sub(a, b):
    return (a - b) % 256


def _filterRow(pixels, width, bpp, y):
    row = pixels[y * width * bpp : (y + 1) * width * bpp]
    left = (b"\x00" * bpp) + row[:-bpp]
    if y == 0:
        up = b"\x00" * (width * bpp)
    else:
        up = pixels[(y - 1) * width * bpp : y * width * bpp]

    # one entry per filter type; 5 total
    # keyed by the quality of that filter method; lower is better
    # { sum_of_filtered: (filter_type, filtered_data) }
    sums = collections.OrderedDict()

    # (type 0) unfiltered
    enc = row
    sums[sum(enc)] = (0, enc)

    # (type 1) pix - left
    enc = bytes((_sub(row[i], left[i]) for i in range(len(row))))
    sums[sum(enc)] = (1, enc)

    # (type 2) pix - up
    enc = bytes((_sub(row[i], up[i]) for i in range(len(row))))
    sums[sum(enc)] = (2, enc)

    # (type 3) pix - floor((left + up) / 2)
    enc = bytes((_sub(row[i], int((left[i] + up[i]) / 2)) for i in range(len(row))))
    sums[sum(enc)] = (3, enc)

    # (type 3) paeth
#   enc = TODO
#   sums[sum(enc)] = (3, enc)

    type_, enc = sums[min(sums.keys())]
    return bytes([type_]) + enc


def _buildTrueColor(pixels, width, height, is_rgba):
    bpp = { False: 3, True: 4 }[is_rgba]
    imgtyp = { False: 2, True: 6 }[is_rgba]

    filtered = b"".join((_filterRow(pixels, width, bpp, y) for y in range(height)))

    ihdr_dat = struct.pack(">IIBBBBB", width, height, 8, imgtyp, 0, 0, 0)
    idat_dat = zlib.compress(filtered)

    ihdr_chunk = _mkChunk("IHDR", ihdr_dat)
    idat_chunk = _mkChunk("IDAT", idat_dat)
    iend_chunk = _mkChunk("IEND", b"")

    return _png_signature + ihdr_chunk + idat_chunk + iend_chunk


def buildPNG(pixels, width, height, is_rgba=False):
    """
    Build a fully constructed PNG image as a byte string that can be
    written directly out to a file.

    pixels should be a byte string of RGB or RGBA values, depending on
    the is_rgba flag.
    """

    if not True: # rgb debug
        return _buildTrueColor(pixels, width, height, is_rgba)

    if not is_rgba:
        # no alpha; check if it can be written out as a
        # palettized image

        if (len(pixels) % 3) != 0:
            raise Exception("invalid RGB pixels")

        # build up the palette; { rgb: index_in_palette, ... }
        pal = collections.OrderedDict()

        for p in _iterChop(pixels, 3):
            pal.setdefault(p, len(pal))
            if len(pal) > 256:
                # too many different colors for a palettized image
                return _buildTrueColor(pixels, width, height, False)

        # <= 256 colors
        return _buildPalettized(pixels, width, height, pal)
    else:
        if (len(pixels) % 4) != 0:
            raise Exception("invalid RGBA pixels")
        return _buildTrueColor(pixels, width, height, True)


def writePNG(path, pixels, width, height, is_rgba=False):
    """
    Build a PNG image and write it out to a file.

    pixels should be a byte string of RGB or RGBA values, depending on
    the is_rgba flag.
    """

    with open(path, "wb") as fp:
        fp.write(buildPNG(pixels, width, height, is_rgba=is_rgba))


if __name__ == "__main__":
    #_test1sz = 2
    _test1sz = 31
    _test1 = ( \
        (b"\xff\xff\xff" * _test1sz) + \
        (b"\xff\x00\x00" * _test1sz) + \
        (b"\x00\xff\x00" * _test1sz) + \
        (b"\x00\x00\xff" * _test1sz) + \
        (b"\x00\x00\x00" * _test1sz) \
        ) * _test1sz
    writePNG("test1.png",_test1,_test1sz*5,_test1sz)

    _test2sz = 2
    #_test2sz = 7
    _test2 = ( \
        (b"\xff\xff\xff\xff" * _test2sz) + \
        (b"\xff\x00\x00\xff" * _test2sz) + \
        (b"\x00\xff\x00\xff" * _test2sz) + \
        (b"\x00\x00\xff\xff" * _test2sz) + \
        (b"\x00\x00\x00\xff" * _test2sz) \
        ) * _test2sz
    writePNG("test2.png",_test2,_test2sz*5,_test2sz,True)
