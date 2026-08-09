#!/usr/bin/env python3
"""edit_call.py — send ONE of our own renders to a Gemini IMAGE model and archive what
comes back, in a form `edge_drift.py` can judge.

    python pipeline/scripts/edit_call.py <render.png> <tag> --prompt-file <p.md>
                                         [--model pro|flash] [--aspect 4:3] [--size 2K]

Sibling of `critique_call.py`, which sends an image and receives TEXT. This one receives an
IMAGE, so the egress rules are the same and the RETURN is the thing that has to be
distrusted: a frame that came back is not evidence of anything until `edge_drift.py` has
said whether it is still our room.

EGRESS, ENFORCED HERE AND NOT BY REMEMBERING (R7b, narrowed by R10b to: the friend's
delivered work never goes to GIT, and never leaves this machine to a vendor):
  - exactly one image travels — the render named on the command line;
  - the prompt is scanned with `critique_call.FORBIDDEN`, the SAME pattern, imported
    rather than re-typed, so target/anchor/client references cannot ride along;
  - nothing about the file's location travels: only its pixels.

THE ASPECT CROP, and why it is done to OUR frame instead of to the return. The API emits
one of a fixed set of aspect ratios; this lane renders 1080x821 (1.316), whose nearest
offer is 4:3 (1.333) — 1.4 % away, which `edge_drift.ASPECT_TOL` correctly refuses as "a
different crop". Re-cropping what came BACK would be us deciding after the fact which part
of the model's picture matches ours, which is the reader inventing the alignment the
measurement is supposed to test. So the crop happens BEFORE anything is sent: the beauty
frame and its id mask are cut to the requested ratio TOGETHER, by the same slice, with no
resampling, and the cropped pair — not the originals — is what the probe compares. The
sidecar is copied unchanged beside them so the mask/beauty provenance check still bites.
"""
import argparse
import json
import os
import shutil
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from critique_call import FORBIDDEN, REPO      # ONE definition of what may not travel

MODELS = {"pro": "gemini-3-pro-image", "flash": "gemini-3.1-flash-image"}
# Published list price at the time of writing, for the spend line R6 asks for.
USD_PER_IMAGE = {"gemini-3-pro-image": 0.134, "gemini-3.1-flash-image": 0.039}


def crop_to_aspect(img, ratio):
    """Centre-crop a PIL image to `ratio` (w, h). Pure crop — no resampling, so a mask
    cropped this way still decodes to exactly the ids it carried."""
    w, h = img.size
    tw, th = ratio
    if w * th > h * tw:                      # too wide -> trim width
        new_w, new_h = int(round(h * tw / th)), h
    else:                                    # too tall -> trim height
        new_w, new_h = w, int(round(w * th / tw))
    x, y = (w - new_w) // 2, (h - new_h) // 2
    return img.crop((x, y, x + new_w, y + new_h))


def prepare(render, out_dir, ratio):
    """Write the cropped beauty + mask + sidecar into `out_dir`, keeping the STEM so
    edge_drift's provenance check (mask.source.blend == beauty stem) still applies."""
    from PIL import Image
    os.makedirs(out_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(render))[0]
    src_mask = os.path.splitext(render)[0] + ".idmask.png"
    src_json = os.path.splitext(render)[0] + ".idmask.json"
    for p in (render, src_mask, src_json):
        if not os.path.exists(p):
            sys.exit(f"missing {p} — run id_mask.py for this frame first; a drift check "
                     f"without a mask is an eyeball wearing arithmetic")
    beauty_p = os.path.join(out_dir, stem + ".png")
    mask_p = os.path.join(out_dir, stem + ".idmask.png")
    json_p = os.path.join(out_dir, stem + ".idmask.json")
    b = crop_to_aspect(Image.open(render).convert("RGB"), ratio)
    m = crop_to_aspect(Image.open(src_mask).convert("RGB"), ratio)
    if b.size != m.size:
        # RAISED, NOT ASSERTED: `python -O` strips asserts, and the one invariant that
        # makes every number downstream mean anything is that ONE slice cut both.
        raise ValueError(f"crop desynced: beauty {b.size} vs mask {m.size} — the mask "
                         f"would name other pixels than the ones we sent")
    b.save(beauty_p)
    m.save(mask_p)
    shutil.copyfile(src_json, json_p)
    return beauty_p, mask_p, json_p, b.size


def _post_rest(model, key, png_bytes, prompt, aspect, size, timeout=300):
    """One generateContent call over urllib. Returns the parsed JSON body."""
    import base64
    import urllib.error
    import urllib.request
    body = {
        "contents": [{"parts": [
            {"inline_data": {"mime_type": "image/png",
                             "data": base64.b64encode(png_bytes).decode()}},
            {"text": prompt}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"],
                             "imageConfig": {"aspectRatio": aspect, "imageSize": size}},
    }
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": key})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} from {model}: {e.read()[:500].decode('utf-8', 'replace')}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("render", help="our own render — the ONLY image that leaves")
    ap.add_argument("tag", help="short name for this attempt, e.g. 'A_surface'")
    ap.add_argument("--prompt-file", required=True)
    ap.add_argument("--model", default="pro", choices=list(MODELS))
    ap.add_argument("--aspect", default="4:3")
    ap.add_argument("--size", default="2K", choices=["1K", "2K", "4K"])
    a = ap.parse_args(argv)

    prompt = open(a.prompt_file, encoding="utf-8").read()
    hit = FORBIDDEN.search(prompt)
    if hit:
        sys.exit(f"prompt references '{hit.group(0)}' — refusing to send")
    if FORBIDDEN.search(a.tag):
        sys.exit("tag references forbidden material — refusing to send")

    ratio = tuple(int(v) for v in a.aspect.split(":"))
    out_dir = os.path.join(os.path.dirname(os.path.abspath(a.render)),
                           "editprobe-" + a.tag)
    beauty_p, mask_p, json_p, size = prepare(a.render, out_dir, ratio)
    print(f"prepared {size[0]}x{size[1]} ({a.aspect}) in {out_dir}")

    from dotenv import load_dotenv
    load_dotenv(REPO / ".env")
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        sys.exit("GEMINI_API_KEY not in repo .env")
    model = MODELS[a.model]

    # WHY REST AND NOT THE google-genai SDK, WHICH critique_call.py USES HAPPILY. On this
    # machine every image-model call through the SDK dies with httpx
    # `RemoteProtocolError: Server disconnected without sending a response` — a bare 64x48
    # test image does it too, while a text call on the same key in the same process
    # succeeds. The identical request over urllib returns HTTP 200 with an image. Same
    # family as the schannel revocation trap already in the machine notes: the transport
    # is the fault, not the network and not the key. urllib carries its own TLS stack, so
    # it is used here and `critique_call.py` is left alone.
    resp = _post_rest(model, key, open(beauty_p, "rb").read(), prompt, a.aspect, a.size)

    # A REFUSAL IS NOT AN IMAGE, AND MUST NOT READ AS ONE. Image models answer some asks in
    # words; if we only looked for image parts we would report "no output" for a model that
    # explained exactly why it declined.
    img_bytes, said = None, []
    for cand in (resp.get("candidates") or []):
        for part in ((cand.get("content") or {}).get("parts") or []):
            blob = part.get("inlineData") or part.get("inline_data")
            if blob and blob.get("data") and img_bytes is None:
                import base64
                img_bytes = base64.b64decode(blob["data"])
            if part.get("text"):
                said.append(part["text"])
    after_p = os.path.join(out_dir, f"after_{a.tag}.png")
    meta = {"model": model, "tag": a.tag, "aspect": a.aspect, "size": a.size,
            "prompt_file": os.path.basename(a.prompt_file), "prompt": prompt,
            "sent": os.path.basename(beauty_p), "sent_px": list(size),
            "text": "\n".join(said),
            "usd_list": USD_PER_IMAGE.get(model), "date": date.today().isoformat()}
    if img_bytes:
        open(after_p, "wb").write(img_bytes)
        meta["after"] = os.path.basename(after_p)
    with open(os.path.join(out_dir, f"call_{a.tag}.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=1)

    usage = REPO / ".gemini_usage.json"
    try:
        data = json.loads(usage.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    if data.get("date") != date.today().isoformat():
        data = {"date": date.today().isoformat()}
    data["image"] = data.get("image", 0) + 1
    usage.write_text(json.dumps(data, indent=2), encoding="utf-8")

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if said:
        print("model said:", "\n".join(said)[:800])
    if not img_bytes:
        print("NO IMAGE RETURNED — see the text above; nothing to measure")
        return 1
    print(f"after -> {after_p}\n")

    # THE GUARD RUNS HERE, NOT IN A PRINTED SUGGESTION. The first cut of this file ended
    # by printing the edge_drift command for a human to copy, which makes the guard a
    # recommendation — and this repo has already paid for that shape once (`an instrument
    # nothing calls is a defect`). D-011 says no generative frame enters a lane unmeasured;
    # the only way that is true is if the thing that PRODUCES the frame refuses to hand it
    # over clean. So: exit 0 only when the geometry held.
    import edge_drift
    try:
        rc = edge_drift._main(["edge_drift", beauty_p, after_p, mask_p, json_p])
    except edge_drift.DriftError as e:
        print(f"EDGE DRIFT REFUSED: {e}")
        return 2
    if rc:
        print("\nNOT ADMISSIBLE (D-011): this frame moved geometry we measured. It may be "
              "looked at; it may not enter a lane.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
