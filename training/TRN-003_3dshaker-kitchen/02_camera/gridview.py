#!/usr/bin/env python3
"""gridview.py - draw a labelled pixel grid over an image (or a crop of it).

This is the "open the picture" tool for picking vanishing-point lines by eye the way
fSpy asks you to: you cannot type a pixel coordinate you have not read off the image.

    python gridview.py <img> <out> [x0 y0 x1 y1] [--step N]
"""
import sys
from PIL import Image, ImageDraw


def grid(img, box=None, step=None, out="grid.png", upscale=1):
    im = Image.open(img).convert("RGB")
    W, H = im.size
    if box:
        x0, y0, x1, y1 = box
        im = im.crop((x0, y0, x1, y1))
    else:
        x0, y0 = 0, 0
    w, h = im.size
    if upscale != 1:
        im = im.resize((w * upscale, h * upscale), Image.LANCZOS)
    if step is None:
        step = 100 if max(w, h) > 600 else 25
    d = ImageDraw.Draw(im)
    sw, sh = im.size
    gx = x0 - (x0 % step) + step
    while (gx - x0) * upscale < sw:
        px = (gx - x0) * upscale
        d.line([(px, 0), (px, sh)], fill=(255, 0, 128), width=1)
        d.text((px + 2, 2), str(gx), fill=(255, 0, 128))
        gx += step
    gy = y0 - (y0 % step) + step
    while (gy - y0) * upscale < sh:
        py = (gy - y0) * upscale
        d.line([(0, py), (sw, py)], fill=(0, 200, 255), width=1)
        d.text((2, py + 2), str(gy), fill=(0, 200, 255))
        gy += step
    im.save(out)
    return out, (W, H)


if __name__ == "__main__":
    a = sys.argv[1:]
    img, out = a[0], a[1]
    rest = a[2:]
    step = None
    up = 1
    if "--step" in rest:
        i = rest.index("--step"); step = int(rest[i + 1]); rest = rest[:i] + rest[i + 2:]
    if "--up" in rest:
        i = rest.index("--up"); up = int(rest[i + 1]); rest = rest[:i] + rest[i + 2:]
    box = [int(v) for v in rest] if len(rest) == 4 else None
    print(grid(img, box, step, out, up))
