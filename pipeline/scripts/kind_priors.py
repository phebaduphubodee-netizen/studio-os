"""kind_priors.py -- deterministic per-kind size/aspect bands for the benchmark lane.

    python kind_priors.py --derive <out.json> <gt-dir> [<gt-dir> ...]

Bands are derived from TRAIN-split gt.json only (units=='mm' files), scored on the test
split -- legitimate train/test separation. suggest_kind emits a kind ONLY when the
footprint falls inside exactly ONE kind's band (unique membership); any ambiguity
(0 or >=2 candidates) returns None and the element stays kind-less. The benchmark
scores a kind-less matched pair as WRONG (norm_kind(None)->'' in benchmark_reader),
never skipped -- unreported is the honest failure mode, a guess is a false-accept.

BENCHMARK / SUGGESTION LANE ONLY: identity in owner projects is owner-signed semantic
truth. This module must never be imported by placement_gate, gen_floor2_v4_specs,
raster_overlay, or build_floor.

SCOPE (v1): bands are SIZE/ASPECT only. The item spec mentions curve-signature bands,
but gt.json elements carry no curve field (only id/x/y/w/d/layer/n_prims/kind) -- a
grounded curve prior needs a train-side reader run to pair pred curve flags with GT
kinds, a follow-up slice, not fabricated here. The pred-side curve/fill fields stay
unused by v1 suggestion.
"""
import glob
import json
import os
import sys
from datetime import date

from floorplancad_adapter import ADAPTER_VERSION

SCHEMA = "interior-ai/kind-priors@0.1"
Q_LO, Q_HI = 0.10, 0.90
PAD_MM = 50.0            # covers cluster-AABB dilation: pred dims are morphology bboxes
                        # rounded to int mm, +-2*res ~ +-12 mm typical
ASPECT_PAD = 1.15
MIN_SUPPORT = 50


def _quantile(sorted_vals, q):
    """Positional quantile of a PRE-SORTED ascending list (the sorted_vals name is the
    contract, not a hint -- quantiling an unsorted list yields garbage bands)."""
    return sorted_vals[int(round(q * (len(sorted_vals) - 1)))]


def derive(gt_dirs, min_support=MIN_SUPPORT):
    """Per-kind size/aspect bands from TRAIN gt.json (units=='mm' only). Openings are
    NEVER sampled (door widths ~999 mm would collide with furniture bands); svg-unit
    files are skipped AND counted (their raw dims are ~100x off)."""
    samples = {}                    # kind -> list of (lo, hi, aspect)
    n_files_total = n_files_mm = n_files_skipped_units = 0
    n_elements_sampled = n_elements_malformed = 0
    for d in gt_dirs:
        for fp in sorted(glob.glob(os.path.join(d, "*.gt.json"))):
            n_files_total += 1
            with open(fp, encoding="utf-8") as fh:
                doc = json.load(fh)
            if (doc.get("meta") or {}).get("units") != "mm":
                n_files_skipped_units += 1          # raw svg-unit dims poison bands ~100x
                continue
            n_files_mm += 1
            for e in doc.get("elements", []):       # elements ONLY, never openings
                try:
                    w, dd = float(e["w"]), float(e["d"])
                    kind = e["kind"]
                except (KeyError, TypeError, ValueError):
                    n_elements_malformed += 1
                    continue
                if w <= 0 or dd <= 0:
                    n_elements_malformed += 1
                    continue
                lo, hi = sorted((w, dd))
                samples.setdefault(kind, []).append((lo, hi, hi / lo))
                n_elements_sampled += 1

    date_str = str(date.today())
    kinds, excluded = {}, {}
    for kind in sorted(samples):
        rows = samples[kind]
        n = len(rows)
        if n < min_support:
            excluded[kind] = n
            continue
        # THREE separate lists, each sorted ascending BEFORE quantiling (_quantile indexes
        # positionally and assumes pre-sorted input)
        los = sorted(r[0] for r in rows)
        his = sorted(r[1] for r in rows)
        asp = sorted(r[2] for r in rows)
        lo_q10, lo_q90 = _quantile(los, Q_LO), _quantile(los, Q_HI)
        hi_q10, hi_q90 = _quantile(his, Q_LO), _quantile(his, Q_HI)
        as_q10, as_q90 = _quantile(asp, Q_LO), _quantile(asp, Q_HI)
        provenance = ("floorplancad "
                      + "+".join(os.path.basename(os.path.normpath(g)) for g in gt_dirs)
                      + f", units=mm gt.json, n={n} instances, "
                      + f"adapter {ADAPTER_VERSION}, derived {date_str}")
        kinds[kind] = {
            "n": n,
            "lo_mm": [lo_q10 - PAD_MM, lo_q90 + PAD_MM],
            "hi_mm": [hi_q10 - PAD_MM, hi_q90 + PAD_MM],
            "aspect": [max(1.0, as_q10 / ASPECT_PAD), as_q90 * ASPECT_PAD],
            "raw": {"lo_q10": lo_q10, "lo_q90": lo_q90, "hi_q10": hi_q10,
                    "hi_q90": hi_q90, "aspect_q10": as_q10, "aspect_q90": as_q90},
            "provenance": provenance,
        }
    return {
        "schema": SCHEMA,
        "meta": {
            "derived_from": [os.path.abspath(d) for d in gt_dirs],
            "date": date_str,
            "n_files_total": n_files_total,
            "n_files_mm": n_files_mm,
            "n_files_skipped_units": n_files_skipped_units,
            "n_elements_sampled": n_elements_sampled,
            "n_elements_malformed": n_elements_malformed,
            "params": {"q_lo": Q_LO, "q_hi": Q_HI, "pad_mm": PAD_MM,
                       "aspect_pad": ASPECT_PAD, "min_support": min_support},
        },
        "kinds": kinds,
        "excluded_low_support": excluded,
    }


def suggest_kind(w_mm, d_mm, priors):
    """Emit a kind ONLY when the footprint falls inside exactly ONE kind's band. Any
    ambiguity (0 or >=2 candidates) or a non-positive/non-numeric dim returns None; the
    element then stays kind-less (scored WRONG, never skipped -- the honest failure)."""
    try:
        w, dd = float(w_mm), float(d_mm)
    except (TypeError, ValueError):
        return None
    if w <= 0 or dd <= 0:
        return None
    lo, hi = sorted((w, dd))
    aspect = hi / lo
    cands = [k for k, b in sorted(priors["kinds"].items())
             if b["lo_mm"][0] <= lo <= b["lo_mm"][1]
             and b["hi_mm"][0] <= hi <= b["hi_mm"][1]
             and b["aspect"][0] <= aspect <= b["aspect"][1]]
    return cands[0] if len(cands) == 1 else None      # unique membership IS the confidence rule


def load(path):
    """Load a priors doc, failing LOUDLY at startup (never a per-sheet error row) if the
    file is not a kind-priors artifact."""
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    if doc.get("schema") != SCHEMA:
        raise SystemExit(f"not a kind-priors file: {path}")
    return doc


def main(argv):
    if len(argv) >= 4 and argv[1] == "--derive":
        out, gt_dirs = argv[2], argv[3:]
        doc = derive(gt_dirs)
        parent = os.path.dirname(out)
        if parent:
            os.makedirs(parent, exist_ok=True)
        tmp = out + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, out)
        m = doc["meta"]
        print(f"wrote {out}")
        print(f"schema {doc['schema']}  files mm {m['n_files_mm']}/{m['n_files_total']} "
              f"(skipped-units {m['n_files_skipped_units']})  "
              f"elements sampled {m['n_elements_sampled']} malformed {m['n_elements_malformed']}")
        print(f"{'kind':<16}{'n':>7}  {'lo_mm':>16}{'hi_mm':>18}{'aspect':>16}")
        for k in sorted(doc["kinds"], key=lambda z: -doc["kinds"][z]["n"]):
            b = doc["kinds"][k]
            lo = f"[{b['lo_mm'][0]:.0f},{b['lo_mm'][1]:.0f}]"
            hi = f"[{b['hi_mm'][0]:.0f},{b['hi_mm'][1]:.0f}]"
            asp = f"[{b['aspect'][0]:.2f},{b['aspect'][1]:.2f}]"
            print(f"{k:<16}{b['n']:>7}  {lo:>16}{hi:>18}{asp:>16}")
        print(f"excluded_low_support: {doc['excluded_low_support']}")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
