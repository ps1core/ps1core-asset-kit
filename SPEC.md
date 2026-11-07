# Asset spec

What a model must be to work in the 1942 and 1942-WEIRD sets, and in every other set rendered the same way:
anything in the cast can be cast in any set. Run `tools/check.py` on your submission; it tests everything marked
**must** below.

## Format

- **must** Quake 3 **MD3**, vertex-animated, one or more surfaces, **one shader per surface**.
- **must** Under about **65,000 vertices** per model (the engine crashes above it). The soldiers are about 4,700 and the bunker about 1,600.
  Something huge (a sea monster, a building) is built in parts that a scene places together.
- Smooth per-vertex normals. `tools/md3.py` computes them if you build from code.
- Triangle winding: Quake order, which is the **reverse** of Blender/glTF (counter-clockwise from outside). Reverse
  each triangle (`tris[:, ::-1]`) when you convert. If your model looks inside-out in our review render, this is why.

## Units, origin, facing

- **must** Quake units: **1 unit ≈ 2.5 cm**; the soldiers are **72.7 units** tall, a crate 53, the bunker 158.
- **must** Everything within **±511 units** of the origin in every frame (MD3 stores positions as int16 at 1/64 unit).
- **must** The origin is **24 units above the feet** (`lift: 24`): the feet or the base sit at **z = −24**.
- Z is up. The model **faces +X**; its right hand is at −Y.
- **must** Animation plays **in place**: walk, run, swim and crawl cycles do not travel. The scene moves the actor.

## Clips (animation)

- A clip is a contiguous range of frames with its own speed: `"walk": [first, last, fps]` in the catalog.
- Frames are named after their clip, cut to 11 characters, plus the index from 0: `walk0 … walk23`, `steady_ches0`.
- **must** Every model has an `idle` clip. A prop can be a single `idle` frame.
- **must** A character (anything with a `walk`) has `idle` and `walk`.
- Recommended for people, because scenes written for the soldiers use them: `run`, `crouch`, `die`, `stand`, `crouch_run`, `lie`, `crawl`,
  `swim`, `flinch`, `die_back`, `run_low`, `crawl_up`, `tend`, `drag`, `breathe`. The full soldier set, with frame
  counts and speeds, is in `reference/1942-cast.json`; the beyond creatures' clips are in `reference/beyond-cast.json`. Reusing a range at another speed (`run_slow`) is fine.
- New clips are welcome (see WISHLIST.md); name them in lowercase, `_` between words, 15 characters at most.

What the soldiers' clips look like (feet at z −24, measured):

| clip | frames @ fps | top of the body (z) | pose |
|---|---|---|---|
| idle, stand | 18 @ 10 | 49 | standing, rifle up |
| walk / run | 24 @ 18 / 13 @ 34 | 49 / 44 | in place |
| crouch | 18 @ 10 | 27 | on one knee |
| lie, crawl | 17 @ 8, 18 @ 16 | −1 / 5 | prone |
| swim | 22 @ 18 | 16 | a head-up stroke; scenes also play it below the surface (the depth is the scene's choice) |
| die | 24 @ 22 | 46 | falls backward along −X |

## Textures

- **must** One PNG per surface, named after the surface's shader. The shader is `progs/<collection>/<model>_<material>`
  and the file is `progs/<collection>/<model>_<material>.png`.
- **must** Power-of-two sizes, 2048 px at most; **1024 is the default** atlas, 256–512 for small props.
- Beside each one, optional but expected for the HD look:
  - `<name>_norm.png`: RGBA, RGB = tangent-space normal, **A = height** (used for offset mapping).
  - `<name>_gloss.png`: greyscale specular.
  - `<name>_glow.png`: emissive (eyes, lamps, screens, fire). Black elsewhere.
- Paint for the delivery size: films are 1920×800 (cinematic) and 1080×1920 (reel), and most shots are wide or medium,
  so a character is often a few hundred pixels tall or less. Silhouette and value contrast read; fine detail does not.
- No baked lighting in the albedo beyond light ambient occlusion: the scenes light the model in real time
  (night, fog, lamps).

## Catalog entry (`models.json`)

```json
{
  "mycoll_infiltrator": {
    "path": "progs/mycoll/mycoll_infiltrator.md3",
    "desc": "a lean infiltrator in a dark grey wetsuit and harness, a radio at the collar, unarmed",
    "kind": "character",
    "idle": "idle",
    "clips": {"idle": [0, 17, 10], "walk": [18, 41, 18]},
    "height": 72.0,
    "lift": 24
  }
}
```

- **must** `path`, `desc`, `idle`, `clips`, `height` (units, feet to top in the idle pose), `lift` (24).
- `desc` is what the scene director reads when it chooses a cast: one plain sentence saying who or what it is and what it
  looks like. No names of real people, brands or characters from other works.
- `kind`: `character` or `prop` (for the checker; we drop it when we merge).
- `light`: a light the model carries, e.g. a lamp: `{"radius": 90, "intensity": 1.2, "offset": [0, 0, 40], "tint": [1, 0.75, 0.4]}`.
- Model ids: lowercase, start with your collection prefix (`mycoll_`), 32 characters at most. `bf_`, `er_`, `kit_`
  and existing ids are taken.

## Rights (must)

Two kinds of model, and `SOURCES.md` says which each one is:

- **Original**: your own work, or under a license that lets us use and redistribute it (CC0, CC-BY with the credit
  written in SOURCES.md). CC0 materials from ambientCG count: `tools/cc0_material.py` fetches them; name the
  material id in SOURCES.md (and the SHA-256 the tool prints for one that is not in `reference/cc0.lock.json`).
- **Based on the cast** (`tools/fetch_cast.py [beyond]`, then `tools/derive.py`): a 1942 soldier or prop, or a beyond
  creature (ghouls, vampires, the tall ones, the shoggoth, Cthulhu), reshaped, repainted or given new clips. Welcome: it is often the quickest way to a new character. It carries the site's 1942 terms (free films
  only, like the 1942 sets) and its catalog entry keeps `"based_on"`.

Either way: nothing ripped or converted from another game, film or commercial model pack, and no likeness of an
existing character or real person, even when a prompt asks for one by name (see WISHLIST.md). Every model is listed in
`SOURCES.md`. Everything is subject to the site's terms (ps1core.com/terms).
