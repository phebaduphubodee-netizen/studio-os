# An archviz artist judging seven CG renders out loud — with numbers

**Source (REFERENCE tier).** YouTube `UmJaVnO3Sxw` —
<https://www.youtube.com/watch?v=UmJaVnO3Sxw> · Nuno Silva, *"Reviewing your 3d renders —
Archviz Art Critique Ep.2"* · 26 min 44 s. Watched 2026-08-28 (40 scene frames via
`pipeline/scripts/watch_local.py`; transcript via `youtube-transcript-api`). Seven
viewer-submitted renders opened one at a time and criticised in the order he notices
things. Timestamps verbatim.

**Why it was picked.** Three judge lanes chose it independently — the joint-highest
agreement in the whole 807-video harvest. It is the rung the first panel said did not
exist: **a professional naming CG-specific failure modes**, not a designer critiquing a
photographed room. Those are different failure sets: a photographed room cannot have
texture tiling, zero-thickness planes or a repeated asset.

**Caveat.** The submissions skew exterior; only two are interiors, and none is a bedroom
with built-in joinery. He sells a Lumion course and says so three times. The value is the
FAILURE TAXONOMY, which is software-independent.

---

## 1. HIS READ-ORDER — and it is not the builder's

For all seven renders he moves in the same sequence:
**lighting direction → composition/crop → camera → materials at 100% zoom → repeated
assets → the small physical impossibilities → colour grade.**

Note what is FIRST. Not the model, not the materials. **Where the light comes from and
whether the shot is framed.** Our lane spends its rounds on the last three.

---

## 2. THE NUMBERS — everything in this video that is a quantity

| Number | Timestamp | The rule |
|---|---|---|
| **≤ 120 cm camera height** | `[06:17]` | *"most of the interior photography is done with the camera at chest level, so it's probably maximum height about around 120"* — he drops a submission from an estimated 170-180 cm to 120-130 |
| **joints every 1.0-1.5 m** | `[23:20]` `[23:51]` | *"I think it's better if you really break the glass into one metre and a half… you would see little connection to it. It's all in these details that help to have a realistic render"* |
| **3000 K** | `[24:23]` | *"for living areas it's a more comfortable light, not so cold like this one"* — and it buys a warm/cool contrast against a blue exterior |
| **verticals at 0°** | `[04:44]` `[24:54]` | *"you should always have the vertical line straight"* — two-point perspective, or fixed in Camera Raw → Geometry → Vertical |
| **+300 px of room** | `[01:32]` | before cropping, ADD canvas: *"let the building breathe, everything doesn't look so cramped"*, then crop to 4:5 on the thirds |

Five quantities from one video, against the zero that the whole soft-goods harvest
produced. This is why the CG lane was worth a separate pass.

---

## 3. THE FAILURE TAXONOMY — CG tells, named

### 3.1 FLAT LIGHT IS THE FIRST THING HE CHECKS, AND IT IS OUR STANDING VERDICT
`[01:01]` *"this area here it's all in shadow and this area is being lit — this gives the
three dimension to your building… if you have the sun facing both this front and the side
you'll not see correctly the dimensions of the building, and I think it's best to have
this type of lighting instead of a very flat lighting with all the sun facing all the
faces."*

The defect is not "not bright enough". It is **every visible plane receiving the same
light**, so nothing separates. Our frame has been called flat by every critic; this is the
mechanism stated by someone who checks it first, every time.

Corollaries he applies elsewhere: `[16:03]` *"the interior is way too dark — add a little
bit of light inside… adjust the hyper light effect to create a little bit more bounces"*;
`[19:12]` praise for *"a very good balance with the dark areas and light areas… which
helps you to focus on the main purpose"*; `[13:31]` add light in windows *"to give a nice
contrast"*.

### 3.2 THE REPEATED ASSET — said twice, and it is our wood wall in another costume
`[13:01]` *"this asset it's repeating a lot of times… it's okay to use the same asset but
at least try to **rotate** the asset, maybe **change a little bit the colour** — one has a
little bit more greenish tones, another a little bit more yellow… **scale it, rotate it**,
all of these things will help you to not notice that it's exactly the same repeated all
over the scene."*
`[20:13]` again on a rock: *"you can see that it was repeated — it's best to rotate them,
so even though it's the same rock it doesn't look the same."*
`[18:08]` and on colour specifically: *"in nature you never have exactly the same green
tone throughout the whole forest… so you always have differences."*

**Bearing on P2r-2.** Our wood wall repeats and MIRRORS across a visible axis — C2 filed
it by eye at p2r64 (*"the same block repeated left and right"*). The fix this artist
applies is not a better texture: it is **per-instance rotation, scale and hue jitter**.
That is a Blender-side, deterministic, testable change, and it is the same law the
`assets`/`styling` code already needs for props.

### 3.3 ZERO THICKNESS AND MISSING JOINTS — the CG version of cannot-be-built
`[23:20]` *"model this not only as the plane but also as a **box** so you can see some
thickness to it."*
`[17:37]` *"it's better to get a model for these roof tiles, because right now it looks
everything is flat basically — you have a flat plane here with the texture applied to it,
so you'll not get super realistic. Here on this area you can get away with it, **but here
not so much.**"*

The qualifier is the useful half: a textured plane is legitimate **far from camera** and
illegitimate **near it**. That is a distance rule our lane could actually apply, because
`frame_geometry.py` already knows the scene-to-pixel scale.

### 3.4 THE MATERIAL THAT ONLY FAILS AT 100 %
`[08:21]` *"this material here… you are seeing all of these lines. **From far it's okay,
because you cannot notice this, but if you look a little bit closer you can see all of
this.**"* He zooms to 100 % on every submission. `[16:34]` the same for a normals error:
shadows on the wrong side of a surface, diagnosed by tracing the sun direction by hand.

### 3.5 UNIFORMITY OF KIND
`[09:23]` *"you wouldn't have just one type of vegetation… try to get a little bit more
variation."*

This is the same defect Caroline Winkler names for interiors as *"all flat things on the
wall — that falls flat"* (see `Sz4TC-VJ2PQ`). **Two critics, two disciplines, one law:
one KIND of object repeated across a field reads as a fake field**, and adding more of the
same at higher quality does not fix it.

### 3.6 THE 3D-PEOPLE TELL
`[15:33]` praise for cutout people *not* facing the camera: *"if they are facing the camera
you can easily tell immediately that they are 3D people and it kind of breaks a little bit
the realism."*

---

## 4. COMPOSITION, stated as a procedure rather than a taste

1. `[01:32]` **Add canvas before you crop.** Extend the image ~300 px, fill, then crop —
   so the crop is not limited by what the camera happened to capture.
2. `[02:37]` Crop to a stated ratio (4:5, or 21:9 for a cinematic scene `[21:15]`) and put
   the subject's lines **on the thirds**.
3. `[02:37]` The goal in his words: *"a little bit more room to let the building breathe;
   everything doesn't look so cramped."*
4. `[07:49]` Put an element in the **foreground** to close the edges and push the eye to
   the subject; add vignetting to reinforce it.
5. `[13:31]` *"not only work on your model itself but always work on the **environment**,
   on the **background** and also on the **foreground** — never forget about those."*

---

## 5. WHAT IS OWED FROM THIS UNIT

1. **Per-instance jitter (rotation / scale / hue) wherever an asset or a board repeats** —
   row it against P2r-2 (wood wall mirror) and against the prop set. This is the first
   fix for that defect that came from outside this repo.
2. **Test the frame for flat light the way he does**: is there any large plane pair in
   the frame with a real luminance separation? Our D-rows measure amounts; this asks
   whether the *arrangement* separates at all.
3. **Camera height ≤ 120 cm** and **verticals at 0°** are two checks `frame_geometry.py`
   can answer today, before any render.
4. **Joint module 1.0-1.5 m** as a sanity rule for any long continuous element — the hang
   rail, the wood wall, the glazing.
5. **A near/far rule for textured planes** (§3.3): a plane with no thickness is allowed
   only beyond a distance the scene-to-pixel scale can state. Our rug and curtains are the
   first candidates.
6. **3000 K for the room's own fixtures** as the starting value in the lighting solve.
