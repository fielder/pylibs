#!/usr/bin/env python

import os
import sys
import struct

import pcx


for path in sys.argv[1:]:
    w, h, pal, pix = pcx.loadPCX(path)

    pix_to_rgb = { chr(i): pal[i * 3: i * 3 + 3] for i in xrange(256) }

    with open(path + os.path.extsep + "rgb", "wb") as fp:
        fp.write(struct.pack("<ii", w, h))
        for p in pix:
            fp.write(pix_to_rgb[p])
