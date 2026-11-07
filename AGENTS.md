# For coding agents

You are helping someone make models for ps1core's cast. Read `SPEC.md` (the rules) and `WISHLIST.md` (what's wanted) first.
The person you work for decides what to make and approves how it looks; show them previews, not just check results.

## Steps

1. Agree on the model list with the person: ids with their collection prefix (`mycoll_...`), a one-line description each,
   and for characters the clips. Then copy `submission-template/` to a working folder and rename `progs/mycoll/`.
2. Choose the route per model:
   - **From the cast** (fastest for people and creatures): `python3 tools/fetch_cast.py` once (the 1942 soldiers and
     props, about 800 MB, cached), and `python3 tools/fetch_cast.py beyond` for the things from beyond (about 340 MB).
     Then `tools/derive.py SOURCE NEW_ID SUB --clips ... --desc "..."` (add `--cast beyond` for a beyond model).
     `reference/1942-cast.json` and `reference/beyond-cast.json` list every source model and its clips. Then repaint
     the PNGs, drop or reshape surfaces, add clips. The shoggoth and Cthulhu are sets of parts (`shoggoth_a`,
     `shoggoth_b`, `shoggoth_eyes`, ...) that a scene places together: derive each part you need.
   - **From code**: build meshes with numpy and write them with `tools/md3.py`, as `examples/buoy/build.py` does.
     Good for props: rocks, fences, lamps, doors, pipes, tanks.
   - **From a modelling tool**: the person exports MD3; you check and fix the catalog entry.
3. `tools/check.py SUB` until it reports 0 errors. Read the warnings too.
4. `tools/preview.py SUB MODEL_ID --out FILE.png`, then look at the image yourself: size next to the soldier bar, feet on
   the ground line, facing +X (left in the side view), no magenta (a missing texture), clips that loop, glow only where
   it should be (`--flat` turns the maps off to compare). Show it to the person. It is a software render, not the film
   look (README, "The preview is not the film look"): don't promise the person how it will look in a film from it.
5. Fill in `SOURCES.md` (author, what it's made from, license) and the `desc` of every model (no TODO left).
6. Zip the submission folder for the person to send.

## Working with the formats

- `tools/md3read.py` `read(path)` gives `frames` (names, bounds) and `surfaces`, each with `verts (F, V, 3)`,
  `normals (F, V, 3)`, `uv (V, 2)`, `tris (T, 3)` and its shader. `tools/md3.py` `write(path, surfaces, frame_names)`
  writes them back (dicts with `name`, `shader`, `verts`, `normals` or none to compute them, `uv`, `tris`). Read, change,
  write is the whole edit loop.
- Triangles read from an MD3 are already in the right winding; triangles you build counter-clockwise (Blender/glTF
  style) need `tris[:, ::-1]`.
- A new clip is new frames: append them to every surface's `verts` (and `normals`, or pass `normals=None`), name them
  `<clip>0..n`, and add `"clip": [first, last, fps]` to the catalog entry. Keep it in place and keep the feet at z −24.
- Removing a part (a helmet, a rifle) is removing its surface; the surface name and shader tell you which is which.
- There is no skeleton: frames are vertex positions (README, "Animation: what is quick and what is not"). Repaint,
  remove, reshape, re-time and combine are quick; new motion needs a rig in a modelling tool. Say so to the person
  before starting a new clip, and don't present stretched or warped existing frames as a new move.
- Textures: `tools/tex.py` has `save`, `normal_from_height` (writes the `_norm` map) and tileable `fbm` noise.
- Real materials: `tools/cc0_material.py` (optional) turns a CC0 ambientCG material into one surface's three maps.
  Use it on surfaces that are one material; on a painted atlas (faces, mixed gear) it shows seams and loses the paint.
  `--list` is ps1core's shortlist (50 vetted materials); any other of ambientCG's 2,931 assets (as of 2026-11-07) works with `--new`, and its printed SHA-256 goes
  in SOURCES.md.
- Use the `uv` scripts' pinned dependencies (numpy 2.3.1, Pillow 11.3.0); don't add packages without asking the person.

## Don't

- Don't make likenesses of existing characters or real people, even if a prompt names them; make an original that can
  play the same scene.
- Don't put the downloaded cast (`cast/`, 1942 and beyond) or derived models in a public repo: they are for ps1core films only.
- Don't change `reference/` or the tools to make a check pass; fix the model. If the person asks you to improve a
  tool, run `tests/run.sh` (and `--full` when it touches preview speed or big models) before handing it back.
