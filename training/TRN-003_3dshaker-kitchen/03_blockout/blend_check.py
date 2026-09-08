#!/usr/bin/env python3
"""blend_check.py - lay the render ON the plate at 50 percent and look.

The overlay of the SPEC boxes (fit_and_overlay.py) answers "does the declared geometry
project onto the photo". It cannot answer "does the scene Blender actually rendered land
on the photo", and for one full day those two were different files. This one takes the
render itself, scales it to the plate, and blends. Nothing is fitted, so nothing can be
flattered: a mass in the wrong place shows as a doubled edge.

    python 03_blockout/blend_check.py 05_build/out/p1_blockout.png [out.png] [--alpha .5]
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PLATE = os.path.join(HERE, "..", "01_reference", "plates", "REF-HERO.png")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    alpha = 0.5
    for a in sys.argv[1:]:
        if a.startswith("--alpha"):
            alpha = float(a.split("=")[1] if "=" in a else a[7:])
    ren = args[0]
    out = args[1] if len(args) > 1 else os.path.splitext(ren)[0] + ".BLEND.png"
    p = Image.open(PLATE).convert("RGB")
    r = Image.open(ren).convert("RGB").resize(p.size, Image.LANCZOS)
    Image.blend(p, r, alpha).save(out)
    sbs = Image.new("RGB", (p.size[0] * 2 + 12, p.size[1]), (18, 18, 18))
    sbs.paste(p, (0, 0))
    sbs.paste(r, (p.size[0] + 12, 0))
    sbs2 = os.path.splitext(out)[0] + ".SBS.png"
    sbs.save(sbs2)
    print(out)
    print(sbs2)


main()
