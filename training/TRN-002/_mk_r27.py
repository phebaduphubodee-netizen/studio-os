"""spec_r26 -> spec_r27.

ONE mechanism: the wardrobe run's FAR END. Its far end was typed at y=-2550
(body, band) and y=-1200 (bulkhead); nothing measured any of the three. The
target fits the cabinet's own far silhouette on its front plane x=-1290 at
u=730.21 in two independent v-bands (sd 0.05 / 0.06 over 250 rows) -> y=-2290.8.

What that one number removes from the frame:
  - the 23 px floor-to-ceiling SLOT at u 731..753 through which our camera saw
    the right wall's unlit inner face (the thing the owner read as a second
    door at the head of the bed), and
  - the 1,090 mm of `ward_bulkhead` that overhung past the cabinet into empty
    air, whose end face renders as a white soffit beam the target does not have.
"""
import io
import json
import os

Y_FAR = -2290.8
SRC = os.path.join(os.path.dirname(__file__), "spec_r26.json")
DST = os.path.join(os.path.dirname(__file__), "spec_r27.json")

FIT = ("M(far end: the cabinet's own far silhouette on its front plane "
       "x=-1290, fitted subpixel in the target at u=730.21, sd 0.05 over "
       "v 180..300 and sd 0.06 over v 300..430, 250/250 rows kept -> "
       "y=-2290.8)")

EDITS = {
    "ward_body": (Y_FAR, FIT + " -- was -2550, typed. The 259 mm this adds is "
                  "the whole of the slot: the right wall was visible ONLY in "
                  "u 730.64..754.33 and the corrected silhouette closes it."),
    "ward_bulkhead": (Y_FAR, FIT + " -- was -1200, i.e. 1,090 mm PAST the "
                      "cabinet it caps, standing on nothing. Its own `seen` "
                      "records the course measured at u 726..960 and u=726 is "
                      "this end; everything beyond it was assumed. R10: an "
                      "object invented to satisfy a structure is a declared "
                      "assumption, not a measurement."),
    "ward_band": (Y_FAR, "A(structural closure: the oak panel must run under "
                  "the carcass it faces. Its OWN silhouette fits y=-2540+-1.1 "
                  "on x=-1314, which would leave the cabinet's last 259 mm "
                  "overhanging - but that fit keeps 12 of 52 rows and every "
                  "one of them is behind the headboard. Occluded in this "
                  "frame either way; declared, not measured.)"),
}


def main():
    spec = json.load(io.open(SRC, encoding="utf-8"))
    spec["round"] = 27
    for m in spec["masses"]:
        if m["name"] not in EDITS:
            continue
        y_far, note = EDITS[m["name"]]
        c, s = m["c"], m["s"]
        y0 = c[1] - s[1] / 2.0          # near end, toward the camera: untouched
        y1_old = c[1] + s[1] / 2.0
        s[1] = y_far - y0
        c[1] = (y0 + y_far) / 2.0
        m["prov"] = m["prov"] + " / " + note
        print(f"  {m['name']:16s} far end {y1_old:9.1f} -> {y_far:9.1f}  "
              f"({y_far - y1_old:+7.1f} mm)  len {s[1]:.1f}")
    spec["STATUS"] = (
        "r27 = r26 with ONE geometry change: the wardrobe run's far end, "
        "derived from the target's own subpixel silhouette instead of typed. "
        "It closes the slot that showed the right wall (read as a second door "
        "at the headboard) and removes the bulkhead's 1,090 mm overhang."
    )
    with io.open(DST, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=1, ensure_ascii=False)
    print(f"wrote {DST}")


if __name__ == "__main__":
    main()
