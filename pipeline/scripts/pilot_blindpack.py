"""pilot_blindpack.py -- re-curate the sellability pilot into a TRULY BLIND judging bundle.

WHY this exists (a census of the raw pilot, 2026-07-15, found the forced-choice was not
measuring sellability, it was measuring artefacts the judge could not un-see):
  1. RESOLUTION GULF   our renders are ~1MP (1234x864); the delivered anchors are 4K-22MP.
                       A "which is sharper" reflex picks the anchor every time. -> every image
                       is re-encoded to a common long edge (DISPLAY_EDGE) so neither side wins
                       on pixels.
  2. WATERMARK LEAK    at least one anchor carries a studio logo + a room caption BURNED INTO
                       the pixels. No amount of path-hiding blinds that -- the image itself
                       announces "delivered work". -> such anchors are EXCLUDED (--exclude),
                       never shown.
  3. FRAMING MISMATCH  one anchor is a portrait detail vignette paired against our full-room
                       landscape heroes -- the judge would be grading shot-type. -> EXCLUDED.
  4. NO NEG CONTROL    the raw pilot shipped without the "a known-bad render MUST lose" tripwire
                       (its sitting anchor was never labelled). -> a clay/massing control of our
                       OWN bedroom rides in phase 2 (see the two-phase law below).
  5. HTML BLINDNESS    the judging surface embedded full file:// paths -- client name and the
                       ours-vs-delivered role both one hover away. -> images are copied to
                       OPAQUE names (imgs/imgNNN.jpg); the real mapping lives ONLY in the key.

Two-phase judging law (why the tripwires are gated, not inline):
  The negative control is a CLAY massing of our OWN bedroom -- it is self-identifying (white
  blocks) AND it shares the geometry of one of our finished renders. Shown alongside the blind
  pairs it would let the judge back out which finished render is ours. So phase 1 (the finished
  pairs that GATE anything) is judged and LOCKED first; only then does phase 2 (clay-must-lose +
  anchor-vs-itself) unlock. Phase 2 validates the judge/harness, never our work, so a reveal
  there cannot bias the gate.

What this script REFUSES (inherited from precut_pair.py; the pilot's whole point):
  * it never assigns a room type to an anchor -- rooms come only from the labelled worksheet
    already frozen in pilot-pairs.json; this script only FILTERS and RE-PRESENTS that.
  * it never judges. It builds the sheet; the DESIGNER grades it. No score is computed here.

Outputs (LOCAL-ONLY, under _private/benchmark/pilot-blind/, gitignored):
  imgs/imgNNN.jpg        opaque, resolution-normalised copies -- the ONLY images the html loads
  pilot-blind.html       the blind judging surface (phase-1 visible, phase-2 gated)
  pilot-blind-key.json   the answer/scoring key (row -> pair, which side ours, ref, expectations)
                         -- the DESIGNER opens this ONLY after judging
  pilot-blind.md         I-coded human fallback + how-to (refs only; no which-side-ours)

Exit codes: 0 = bundle written & blindness self-guard passed; 1 = error / refused / a forbidden
token reached the html (fail-loud, bundle left un-trusted).

Privacy: the html and the md are derived so that NO client string, NO R_PRJ name, NO real path,
NO 'ours' role marker reaches them. guard_html enforces this with three checks (denylist of role
words + path segments AND their -_. sub-parts re-derived from the real paths at RUNTIME so this
file carries no client name; every image src must be an opaque imgNNN.jpg; an ALLOWLIST proving the
injected P1/P2 data contains only opaque ids) and main() hard-exits (1) if any check trips.
NOTE on scope: this blinds the LAZY tells (resolution/watermark/path/filename). It does NOT make
phase-1 role-blind to an analyst -- the pairwise structure is a complete bipartite graph that
separates ours from anchors by co-occurrence; that residual is DISCLOSED in the key, not hidden.
See qa/benchmark-sellability.md for the standing LOCAL-ONLY owner decision.
"""
import argparse
import hashlib
import json
import os
import random
import re
import shutil
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DISPLAY_EDGE = 1280            # px: longest edge every judged image is normalised to
JPEG_QUALITY = 92
SEED = 20260715               # fixed -> byte-identical re-runs (never Date-derived)

# anchors the census proved un-judgeable, excluded by REF (see module docstring 2+3):
#   I-25-005/033/1281a148.jpg  = a portrait vanity DETAIL vignette (shot-type mismatch)
#   I-23-023/002/8c37e822.png  = a presentation board with a studio watermark burned in
DEFAULT_EXCLUDE = ["I-25-005/033/1281a148.jpg", "I-23-023/002/8c37e822.png"]

# role words that must never appear in the blind html (static half of the guard):
FORBIDDEN_STATIC = ["ours", "R_PRJ", "MasterSuite", "LivingRoom", "SittingRoom",
                    "control-clay", "clay", "dewood", "renders", "assets", "discord",
                    "PlingPeat", "OneDrive", "Users", "teza"]


def _log(msg):
    print(msg, file=sys.stderr)


def load_pilot(pairs_json):
    with open(pairs_json, encoding="utf-8") as fh:
        return json.load(fh)


def resolve(path):
    """A pilot path may be absolute (our renders) or REPO-relative (anchors)."""
    return path if os.path.isabs(path) else os.path.join(REPO, path)


def kept_pairs(pilot, exclude):
    """The real, finished pairs that survive exclusion, plus a per-room clean-anchor census."""
    ex = set(exclude)
    kept = [p for p in pilot["pairs"] if p["anchor"]["ref"] not in ex]
    anchors_by_room = {}
    for p in kept:
        anchors_by_room.setdefault(p["room_type"], set()).add(p["anchor"]["ref"])
    parity = pilot.get("parity_minimum", 2)
    for p in kept:
        p["_advisory"] = len(anchors_by_room[p["room_type"]]) < parity
    return kept, {r: sorted(a) for r, a in anchors_by_room.items()}, parity


def pick_bedroom_anchor(kept, prefer_ref=None):
    """A deterministic bedroom anchor pair (for the tripwire rows). prefer_ref lets the
    self-tie and the neg-control choose DIFFERENT anchors so one image does not dominate."""
    beds = sorted([p for p in kept if p["room_type"] == "bedroom"],
                  key=lambda p: p["anchor"]["ref"])
    if not beds:
        return None
    if prefer_ref:
        for p in beds:
            if p["anchor"]["ref"] == prefer_ref:
                return p
    return beds[0]


def build_slots(kept, clay_path):
    """A slot = one concrete image that will get an opaque id. Returns (slots, phase1, phase2).

    phase1/phase2 rows reference slots by their real key; opaque ids + shuffling happen later.
    A slot key is the real absolute path (identical images share one slot -> one opaque id)."""
    slots = {}   # realpath -> {"role": ..., "ref"/"name": ...}

    def slot_for(realpath, role, **meta):
        rp = os.path.abspath(realpath)
        if rp not in slots:
            slots[rp] = {"role": role, **meta}
        return rp

    phase1 = []
    for p in kept:
        ours = slot_for(resolve(p["ours"]["path"]), "ours", name=p["ours"]["name"])
        anch = slot_for(resolve(p["anchor"]["path"]), "anchor", ref=p["anchor"]["ref"],
                        icode=p["anchor"].get("icode"))
        for order in ("ours-left", "ours-right"):
            left, right = (ours, anch) if order == "ours-left" else (anch, ours)
            phase1.append({"pair_id": p["pair_id"], "room_type": p["room_type"],
                           "advisory": p["_advisory"], "order": order,
                           "left": left, "right": right, "ours_side": order})

    phase2 = []
    # neg control: clay massing of OUR bedroom must LOSE to a delivered bedroom anchor
    neg_anchor_pair = pick_bedroom_anchor(kept)
    if clay_path and os.path.exists(resolve(clay_path)) and neg_anchor_pair:
        clay = slot_for(resolve(clay_path), "neg_control", name=os.path.basename(clay_path))
        anch = slot_for(resolve(neg_anchor_pair["anchor"]["path"]), "anchor",
                        ref=neg_anchor_pair["anchor"]["ref"])
        for order in ("bad-left", "bad-right"):
            left, right = (clay, anch) if order == "bad-left" else (anch, clay)
            phase2.append({"pair_id": "NEG", "kind": "known-bad-must-lose", "order": order,
                           "left": left, "right": right, "bad_side": order, "anchor_slot": anch,
                           "expectation": "the clay/massing side MUST lose; a win indicts the harness. "
                           "NOTE: clay (untextured massing) is a FLOOR-ONLY proxy -- it catches only a "
                           "catastrophically broken/inverted judge. It is NOT the protocol's tripwire #1 "
                           "(a FINISHED-but-REWORK render must lose, the near-boundary test); that one is "
                           "OUTSTANDING (no leg-C/sitting anchor labelled). Passing this does not validate "
                           "near-boundary discrimination -- do not read a clay loss as 'the judge is calibrated'."})
    # self-tie: a DIFFERENT clean bedroom anchor vs itself must TIE (position-bias probe)
    other_ref = None
    beds = sorted({p["anchor"]["ref"] for p in kept if p["room_type"] == "bedroom"})
    if neg_anchor_pair:
        for r in beds:
            if r != neg_anchor_pair["anchor"]["ref"]:
                other_ref = r
                break
    tie_pair = pick_bedroom_anchor(kept, prefer_ref=other_ref)
    if tie_pair:
        a = slot_for(resolve(tie_pair["anchor"]["path"]), "anchor", ref=tie_pair["anchor"]["ref"])
        tie_shares_neg = bool(neg_anchor_pair) and tie_pair["anchor"]["ref"] == neg_anchor_pair["anchor"]["ref"]
        for tag in ("AA", "AA2"):
            phase2.append({"pair_id": "TIE", "kind": "anchor-vs-itself", "order": tag,
                           "left": a, "right": a, "anchor_slot": a, "shares_neg_anchor": tie_shares_neg,
                           "expectation": "SELF-IDENTIFYING: same image both sides -- the judge WILL see it is "
                           "a tie. This row ONLY probes position bias (does the judge always pick a side?); the "
                           "two rows are identical presentations, not swapped orders, so expect TIE both times. "
                           "A consistent L-or-R pick is a position-bias defect."})
    return slots, phase1, phase2


def assign_opaque(slots):
    """realpath -> imgNNN.jpg, ordered by a salted hash so the numbering leaks no role.
    The hash keys on a MACHINE-INDEPENDENT identity (anchor ref / render basename), not the
    absolute path, so the numbering is byte-identical across checkouts, not just run-to-run."""
    def ident(rp):
        m = slots[rp]
        return m.get("ref") or m.get("name") or os.path.basename(rp)
    ordered = sorted(slots, key=lambda rp: hashlib.sha1(("blind:" + ident(rp)).encode()).hexdigest())
    return {rp: "img%03d.jpg" % (i + 1) for i, rp in enumerate(ordered)}


def normalise_image(src, dst):
    """Copy src -> dst as JPEG, longest edge <= DISPLAY_EDGE, metadata stripped. Returns (w,h)."""
    from PIL import Image
    im = Image.open(src).convert("RGB")    # convert drops the source's mode-specific metadata
    if max(im.size) > DISPLAY_EDGE:
        im.thumbnail((DISPLAY_EDGE, DISPLAY_EDGE), Image.LANCZOS)
    im.info.pop("icc_profile", None)       # do not carry a colour profile into the blind copy
    im.info.pop("exif", None)
    im.save(dst, "JPEG", quality=JPEG_QUALITY)   # PIL writes no EXIF unless asked
    return im.size


HTML_TEMPLATE = r"""<!doctype html><html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sellability pilot -- blind judging</title>
<style>
 body{font-family:-apple-system,Segoe UI,Tahoma,sans-serif;margin:0;background:#111;color:#eee}
 header{padding:18px 22px;background:#1b1b1b;border-bottom:1px solid #333;position:sticky;top:0;z-index:5}
 header h1{font-size:17px;margin:0 0 6px} header p{margin:4px 0;font-size:13px;color:#bbb;line-height:1.5}
 .wrap{max-width:1180px;margin:0 auto;padding:18px}
 .row{background:#191919;border:1px solid #2c2c2c;border-radius:10px;padding:14px;margin:18px 0}
 .rid{font-size:12px;color:#888;margin-bottom:8px;letter-spacing:.5px}
 .pair{display:flex;gap:14px}
 .side{flex:1 1 0;min-width:0;display:flex;flex-direction:column;align-items:center}
 .side .tag{font-size:12px;color:#9ab;margin-bottom:6px}
 .side img{width:100%;height:auto;border-radius:6px;cursor:zoom-in;background:#000;display:block}
 .ans{display:flex;gap:8px;justify-content:center;margin-top:12px;flex-wrap:wrap}
 .ans label{padding:7px 16px;border:1px solid #3a3a3a;border-radius:20px;cursor:pointer;font-size:14px;user-select:none}
 .ans input{display:none}
 .ans input:checked+span{font-weight:700}
 .ans label:has(input:checked){background:#2d4a63;border-color:#4a7ba0}
 .note{width:100%;margin-top:8px;background:#111;border:1px solid #333;color:#ddd;border-radius:6px;padding:6px 8px;font-size:13px}
 .gate{margin:26px 0;padding:16px;border:1px dashed #665;border-radius:10px;background:#1d1c15}
 button{background:#2d4a63;color:#fff;border:0;border-radius:8px;padding:10px 18px;font-size:14px;cursor:pointer}
 button:disabled{opacity:.4;cursor:not-allowed}
 #p2{display:none} #out{width:100%;height:120px;margin-top:10px;background:#0c0c0c;color:#8f8;border:1px solid #333;font-family:monospace;font-size:12px}
 #zoom{position:fixed;inset:0;background:rgba(0,0,0,.95);display:none;align-items:center;justify-content:center;z-index:20;cursor:zoom-out}
 #zoom img{max-width:98vw;max-height:98vh}
 .locked{opacity:.55;pointer-events:none}
 .adv{font-size:11px;color:#666}
</style></head><body>
<header>
 <h1>Sellability pilot &mdash; ตัดสินแบบปิดตา (blind)</h1>
 <p>แต่ละแถวมีภาพ <b>ซ้าย</b> กับ <b>ขวา</b> คลิกเพื่อซูมเต็มจอ สลับดูไปมา แล้วเลือกว่า
    <b>ถ้าลูกค้าจ่ายเงิน ภาพไหน "ขายได้" มากกว่า</b> &mdash; L / R / T (เสมอ)</p>
 <p>ตัดสินที่ <b>ความเนี้ยบ / ความเสร็จสมบูรณ์ / ความน่าเชื่อว่าเป็นงานจริง</b>
    &mdash; <u>ไม่ใช่</u>ว่าคุณชอบสไตล์ไหนมากกว่า (มินิมอล vs หรูคลาสสิก ไม่ใช่ตัววัด)</p>
 <p>ทุกภาพถูกปรับให้ <b>แสดงผลขนาดเท่ากัน</b> (ไม่ได้การันตีความคมเท่ากัน 100% &mdash;
    งานส่งจริงมาจากไฟล์ 4K จึงอาจยังคมกว่าเล็กน้อย ระวังอย่าให้ "ความคม" ตัดสินแทนดีไซน์)
    ทำ <b>เฟส 1 ให้ครบทุกแถวก่อน</b> แล้วค่อยกดล็อกเพื่อเปิดเฟส 2</p>
</header>
<div class="wrap">
 <div id="p1"></div>
 <div class="gate">
   <div id="p1status" style="margin-bottom:10px;font-size:13px;color:#cc9">เฟส 1: ยังตอบไม่ครบ</div>
   <button id="lockbtn" disabled>ล็อกเฟส 1 แล้วเปิด tripwire (เฟส 2)</button>
 </div>
 <div id="p2">
   <h3 style="color:#cc9">เฟส 2 &mdash; tripwire (ตรวจตัวผู้ตัดสิน/เครื่องมือ ไม่ใช่งานเรา)</h3>
   <div id="p2rows"></div>
 </div>
 <div class="gate">
   <button id="exportbtn">สร้าง JSON ผลตัดสิน</button>
   <p style="font-size:12px;color:#999">คัดลอกข้อความด้านล่างส่งกลับ (หรือเซฟเป็น pilot-blind-results.json)</p>
   <textarea id="out" readonly></textarea>
 </div>
</div>
<div id="zoom"><img id="zimg" alt=""></div>
<script>
const P1 = __P1__, P2 = __P2__;
const zoom=document.getElementById('zoom'), zimg=document.getElementById('zimg');
function imgEl(src){const i=new Image();i.src='imgs/'+src;i.loading='lazy';
  i.onclick=e=>{e.stopPropagation();zimg.src='imgs/'+src;zoom.style.display='flex';};return i;}
zoom.onclick=()=>zoom.style.display='none';
function rowEl(r,phase){
  const d=document.createElement('div');d.className='row';d.dataset.rid=r.rid;
  const rid=document.createElement('div');rid.className='rid';rid.textContent=r.rid;d.appendChild(rid);
  const pair=document.createElement('div');pair.className='pair';
  for(const [side,src] of [['ซ้าย',r.left],['ขวา',r.right]]){
    const s=document.createElement('div');s.className='side';
    const t=document.createElement('div');t.className='tag';t.textContent=side;
    s.appendChild(t);s.appendChild(imgEl(src));pair.appendChild(s);}
  d.appendChild(pair);
  const ans=document.createElement('div');ans.className='ans';
  for(const [v,lbl] of [['L','ซ้ายชนะ'],['R','ขวาชนะ'],['T','เสมอ']]){
    const l=document.createElement('label');const inp=document.createElement('input');
    inp.type='radio';inp.name=r.rid;inp.value=v;inp.dataset.phase=phase;
    const sp=document.createElement('span');sp.textContent=lbl;
    l.appendChild(inp);l.appendChild(sp);ans.appendChild(l);
    inp.onchange=updateStatus;}
  d.appendChild(ans);
  const note=document.createElement('input');note.className='note';note.placeholder='เหตุผลสั้น ๆ (ถ้ามี)';
  note.dataset.note=r.rid;d.appendChild(note);
  return d;
}
const p1box=document.getElementById('p1');P1.forEach(r=>p1box.appendChild(rowEl(r,'1')));
const p2box=document.getElementById('p2rows');P2.forEach(r=>p2box.appendChild(rowEl(r,'2')));
function answered(phase){return [...document.querySelectorAll(`input[data-phase="${phase}"]:checked`)]
  .reduce((s,i)=>{s.add(i.name);return s;},new Set()).size;}
function updateStatus(){
  const n=answered('1'),tot=P1.length;
  document.getElementById('p1status').textContent=`เฟส 1: ตอบแล้ว ${n}/${tot}`;
  document.getElementById('lockbtn').disabled=(n<tot);
}
document.getElementById('lockbtn').onclick=function(){
  document.getElementById('p1').classList.add('locked');
  this.disabled=true;this.textContent='เฟส 1 ล็อกแล้ว';
  document.getElementById('p2').style.display='block';
  document.getElementById('p2').scrollIntoView({behavior:'smooth'});
};
document.getElementById('exportbtn').onclick=function(){
  const res={phase1:{},phase2:{}};
  document.querySelectorAll('.row').forEach(row=>{
    const rid=row.dataset.rid;const sel=row.querySelector('input[type=radio]:checked');
    const note=row.querySelector('input[data-note]').value.trim();
    const phase=row.querySelector('input[type=radio]').dataset.phase;
    (phase==='1'?res.phase1:res.phase2)[rid]={verdict:sel?sel.value:null,note:note||undefined};
  });
  document.getElementById('out').value=JSON.stringify(res,null,1);
};
updateStatus();
</script></body></html>
"""


def build_html(phase1_rows, phase2_rows):
    def slim(r):
        return {"rid": r["rid"], "left": r["left_img"], "right": r["right_img"]}
    p1 = json.dumps([slim(r) for r in phase1_rows], ensure_ascii=False)
    p2 = json.dumps([slim(r) for r in phase2_rows], ensure_ascii=False)
    return HTML_TEMPLATE.replace("__P1__", p1).replace("__P2__", p2)


def guard_html(html, slots):
    """Fail-loud: no client string / real path / role marker may reach the blind html.

    Three checks, defence in depth:
      (1) DENYLIST -- role words (FORBIDDEN_STATIC) + every real path SEGMENT and its name-like
          SUB-parts (split on separators AND on -_. so a client name buried in a folder like
          '033_I-25-005-Firstname-Lastname' is forbidden as 'Firstname'/'Lastname', not only whole);
      (2) OPAQUE SRC -- every image reference in the html is an imgNNN.jpg;
      (3) ALLOWLIST -- the injected P1/P2 data (the only dynamic content) contains ONLY opaque
          tokens (imgNNN.jpg / RNN / TNN); anything else there is a leak by construction.
    Returns (hits, bad_src): non-empty => the caller must REFUSE (exit 1)."""
    forbidden = set(FORBIDDEN_STATIC)
    GENERIC = {"img", "jpg", "png", "files"}

    def identifying(tok):
        # a client-identifying token: >=3 chars, not a generic word, and CONTAINS A LETTER
        # (Latin or Thai). Purely-numeric fragments like '002'/'033' are dropped -- they identify
        # no person AND would substring-collide with the opaque 'img002.jpg' counter.
        tok = tok.strip()
        return len(tok) >= 3 and tok.lower() not in GENERIC and bool(re.search(r"[^\W\d_]", tok))

    def add_subwords(text, seps):
        if identifying(text):
            forbidden.add(text)
        for sub in re.split(seps, text):
            if identifying(sub):
                forbidden.add(sub)
    for rp, meta in slots.items():
        # basename + ref are pure client identifiers -> forbid their letter-bearing sub-words
        # (e.g. 'Maneerin'); path SEGMENTS are forbidden WHOLE only, never sub-split -- the
        # absolute-path prefix is environment noise (Users/Desktop/AppData/Temp/<pytest-dir>...)
        # whose sub-words ('html','rows') legitimately appear in the template.
        add_subwords(os.path.basename(rp), r"[-_.\s]+")
        if isinstance(meta, dict) and meta.get("ref"):
            add_subwords(meta["ref"], r"[/\\\-_.\s]+")
        for part in re.split(r"[\\/]+", rp):
            if identifying(part):
                forbidden.add(part)
    hits = sorted({t for t in forbidden if t and t in html})
    # (2) every image reference must be an opaque imgNNN.jpg
    bad_src = [s for s in re.findall(r"img[^'\"]*\.(?:png|jpe?g)", html)
               if not re.fullmatch(r"img\d{3}\.jpg", s)]
    # (3) allowlist the injected data arrays: strings must be opaque ids only
    for m in re.finditer(r"const P1 = (\[.*?\]), P2 = (\[.*?\]);", html, re.S):
        for arr in (m.group(1), m.group(2)):
            try:
                for row in json.loads(arr):
                    for v in row.values():
                        if isinstance(v, str) and not re.fullmatch(r"(img\d{3}\.jpg|R\d{2}|T\d{2})", v):
                            bad_src.append("injected:" + v)
            except (ValueError, AttributeError):
                bad_src.append("injected:UNPARSEABLE")
    return hits, bad_src


def emit_md(kept, phase1_rows, phase2_rows, room_census, parity):
    """A pure how-to. It deliberately carries NO ref->image map: because every phase-1 row is
    one-ours-one-anchor, revealing WHICH opaque ids are anchors would de-blind the ours side by
    elimination. That map is a SPOILER and lives ONLY in pilot-blind-key.json."""
    return "\n".join([
        "# Sellability pilot -- blind bundle (how-to)", "",
        "1. เปิด `pilot-blind.html` ในเบราว์เซอร์",
        f"2. เฟส 1 ({len(phase1_rows)} แถว): เทียบ ซ้าย/ขวา ทีละแถว เลือก L / R / T",
        "   ตัดสินที่ความเนี้ยบ/ความเสร็จ/ความน่าเชื่อ -- ไม่ใช่รสนิยมสไตล์",
        "3. ตอบครบแล้วกด 'ล็อกเฟส 1' -> เฟส 2 (tripwire) จะเปิด ทำต่อให้ครบ",
        "4. กด 'สร้าง JSON ผลตัดสิน' คัดลอกส่งกลับ (หรือเซฟเป็น pilot-blind-results.json)",
        "5. เปิด `pilot-blind-key.json` ได้ **หลัง** ตัดสินครบเท่านั้น (มันคือเฉลย)", "",
        "หมายเหตุ: md นี้ไม่มี map ref->ภาพ โดยตั้งใจ -- เพราะทุกคู่เป็น 'งานเรา 1 : anchor 1'",
        "การบอกว่าภาพไหนคือ anchor จะเฉลยว่าอีกฝั่งคืองานเราโดยปริยาย เฉลยอยู่ใน key เท่านั้น", "",
        "census (anchor สะอาดต่อห้อง): " +
        ", ".join(f"{r}={len(a)}" + ("<parity=advisory" if len(a) < parity else "")
                  for r, a in sorted(room_census.items())),
    ]) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Re-curate the sellability pilot into a blind bundle.")
    ap.add_argument("--pairs", default="_private/benchmark/pilot-pairs.json")
    ap.add_argument("--out", default="_private/benchmark/pilot-blind")
    ap.add_argument("--clay",
                    default="assets/projects/PRJ-2026-002/maps/R_PRJ002_MasterSuite_Cam01_v01_control-clay.png")
    ap.add_argument("--exclude", nargs="*", default=DEFAULT_EXCLUDE,
                    help="anchor refs to drop (watermarked / wrong-framing)")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--no-images", action="store_true",
                    help="skip image copy/resize (structure-only; for tests)")
    args = ap.parse_args(argv)

    pairs_json = resolve(args.pairs)
    if not os.path.exists(pairs_json):
        _log(f"ERROR: no pilot-pairs.json at {pairs_json}"); return 1
    pilot = load_pilot(pairs_json)

    # no-silent-drop law: an --exclude ref that matches nothing is a typo/format-drift that would
    # let an un-blindable anchor through with no error. Refuse before building anything.
    orig_refs = {p["anchor"]["ref"] for p in pilot["pairs"]}
    unmatched = [e for e in args.exclude if e not in orig_refs]
    if unmatched:
        _log(f"REFUSED: --exclude refs matched NO pair (typo/format drift): {unmatched}. "
             f"An unmatched exclusion silently admits the anchor it was meant to drop."); return 1

    # census BEFORE exclusion (per room), for an explicit before/after in the key
    before = {}
    for p in pilot["pairs"]:
        before.setdefault(p["room_type"], set()).add(p["anchor"]["ref"])
    before = {r: sorted(a) for r, a in before.items()}
    delivery_by_ref = {p["anchor"]["ref"]: p["anchor"].get("delivery_signal", "unknown")
                       for p in pilot["pairs"]}
    rework_waiting = next((t.get("unavailable") for t in pilot.get("tripwires", [])
                           if t.get("tripwire", {}).get("kind") == "known-rework-must-lose"
                           and t.get("unavailable")), None)

    kept, room_census, parity = kept_pairs(pilot, args.exclude)
    beds = [p for p in kept if p["room_type"] == "bedroom"]
    if not beds:
        _log("ERROR: no bedroom pairs survive exclusion -- nothing to judge honestly."); return 1

    slots, phase1, phase2 = build_slots(kept, args.clay)
    opaque = assign_opaque(slots)

    # attach opaque ids + shuffle phase-1 row order (seeded, deterministic)
    for r in phase1 + phase2:
        r["left_img"] = opaque[r["left"]]
        r["right_img"] = opaque[r["right"]]
    rng = random.Random(args.seed)
    rng.shuffle(phase1)
    for i, r in enumerate(phase1):
        r["rid"] = "R%02d" % (i + 1)
    for i, r in enumerate(phase2):
        r["rid"] = "T%02d" % (i + 1)

    html = build_html(phase1, phase2)
    hits, bad_src = guard_html(html, slots)
    if hits or bad_src:
        _log(f"REFUSED: blindness guard tripped. leaked tokens={hits} non-opaque srcs={bad_src}")
        return 1

    out = resolve(args.out)
    imgs = os.path.join(out, "imgs")
    os.makedirs(imgs, exist_ok=True)
    if not args.no_images:
        for rp, name in opaque.items():
            normalise_image(rp, os.path.join(imgs, name))

    with open(os.path.join(out, "pilot-blind.html"), "w", encoding="utf-8") as fh:
        fh.write(html)

    # single-anchor guard: the neg-control and self-tie should lean on DIFFERENT anchors.
    neg_shares_tie = any(r.get("shares_neg_anchor") for r in phase2 if r["pair_id"] == "TIE")
    if neg_shares_tie:
        _log("WARNING: only one distinct bedroom anchor -- neg-control and self-tie reuse it "
             "(recorded in key.tripwire_anchor_overlap).")

    # the KEY -- everything the html deliberately withholds; opened only after judging
    key = {
        "note": "SPOILER. Open only AFTER judging pilot-blind.html. Maps opaque rows to the truth.",
        "seed": args.seed, "display_edge": DISPLAY_EDGE,
        "excluded_refs": args.exclude,
        "exclusion_reason": {
            "I-25-005/033/1281a148.jpg": "portrait vanity DETAIL vignette -- shot-type/orientation mismatch",
            "I-23-023/002/8c37e822.png": "studio watermark + room caption burned into pixels -- unblindable",
        },
        "parity_census_before_exclusion": before,
        "parity_census_after_exclusion": room_census, "parity_minimum": parity,
        "exclusion_effect": "excluding the watermarked living anchor dropped living from "
            f"{len(before.get('living', []))} to {len(room_census.get('living', []))} clean anchor(s); "
            "with parity_minimum=2, BEDROOM is the only gate-eligible room type -- living is advisory.",
        "delivery_status_caveat": "every anchor's delivery_signal is 'project-thread (proposed, "
            "unconfirmed)' in pilot-pairs.json -- is_delivered was NEVER confirmed. So 'meets_anchor_parity' "
            "means enough anchors EXIST, NOT that they are confirmed DELIVERED/PAID work. Per protocol the "
            "beauty-parity gate stays advisory REVIEW until delivery is confirmed AND kappa is re-measured.",
        "known_rework_tripwire_status": (rework_waiting or "not flagged in input") +
            " -- the clay neg-control is only a FLOOR proxy; protocol tripwire #1 remains OUTSTANDING.",
        "tripwire_anchor_overlap": neg_shares_tie,
        "residual_leaks_disclosed": [
            "PHASE-1 IS NOT ROLE-BLIND TO AN ANALYST: every phase-1 row is exactly one ours + one anchor, "
            "so the rows form a complete bipartite graph. Tallying co-occurrence deterministically splits the "
            "images into the ours-set and the anchor-set (ours never face ours, anchors never face anchors). "
            "The ours-set is then obvious: the two MasterSuite shots are the SAME bedroom from two angles, "
            "share a warm-minimalist-wood look, and appear more often (6x) than each anchor (4x). Blindness "
            "here neutralises the LAZY tells (resolution/watermark/path/filename), NOT active role inference.",
            "IF THE JUDGE IS THE AUTHOR (owner graded own renders): phase-1 is not blind at all -- the author "
            "recognises their own work. Value then = artifact-neutralisation + forced-choice format, not blindness.",
            "residual sharpness: our renders are native ~1MP (below the 1280 cap, so untouched); anchors are "
            "4K downscaled to 1280 and retain more true high-frequency detail -- display SIZE is equalised, "
            "perceived sharpness is not fully. A crisper anchor can still win on crispness, not design.",
            "aspect ratio: our renders ~1.43; anchors 1.50-1.78 -- another cue an analyst could cluster on.",
            "style register: warm-minimalist wood (ours) vs luxe-classic (anchors) -- inherent; mitigated by the "
            "'judge execution not style' instruction, not removable without altering the work.",
        ],
        "phase1": [], "phase2": [],
    }
    for r in phase1:
        ours_img = r["left_img"] if r["order"] == "ours-left" else r["right_img"]
        anchor_img = r["right_img"] if r["order"] == "ours-left" else r["left_img"]
        anchor_ref = slots[r["right"] if r["order"] == "ours-left" else r["left"]].get("ref")
        key["phase1"].append({
            "rid": r["rid"], "pair_id": r["pair_id"], "room_type": r["room_type"],
            "advisory_below_parity": r["advisory"], "order": r["order"],
            "ours_side": "left" if r["order"] == "ours-left" else "right",
            "ours": slots[r["left"] if r["order"] == "ours-left" else r["right"]].get("name"),
            "anchor_ref": anchor_ref,
            "anchor_delivery_signal": delivery_by_ref.get(anchor_ref, "unknown"),
            "ours_img": ours_img, "anchor_img": anchor_img,
            "meets_anchor_parity": (not r["advisory"]),
        })
    for r in phase2:
        entry = {"rid": r["rid"], "pair_id": r["pair_id"], "kind": r["kind"],
                 "order": r["order"], "expectation": r["expectation"],
                 "anchor_ref": slots[r["anchor_slot"]].get("ref") if r.get("anchor_slot") else None}
        if r["pair_id"] == "NEG":
            entry["bad_side"] = "left" if r["order"] == "bad-left" else "right"
        key["phase2"].append(entry)
    with open(os.path.join(out, "pilot-blind-key.json"), "w", encoding="utf-8") as fh:
        json.dump(key, fh, ensure_ascii=False, indent=1)

    with open(os.path.join(out, "pilot-blind.md"), "w", encoding="utf-8") as fh:
        fh.write(emit_md(kept, phase1, phase2, room_census, parity))

    n_gate = sum(1 for r in phase1 if not r["advisory"])
    _log(f"OK: {len(phase1)} phase-1 rows ({n_gate} meet-parity, {len(phase1) - n_gate} advisory), "
         f"{len(phase2)} tripwire rows, {len(slots)} distinct images -> {out}")
    _log(f"    excluded refs: {args.exclude}  (living now advisory: {len(room_census.get('living', []))} clean anchor)")
    _log(f"    blindness guard: PASS (lazy tells neutralised; phase-1 role-inference disclosed in key, NOT hidden)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
