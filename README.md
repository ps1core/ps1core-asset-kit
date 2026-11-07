# ps1core asset kit

Everything you need to make characters and props for ps1core's **1942** and **1942-WEIRD** sets. ps1core turns a
prompt or a scene into a short film rendered by a real 3D engine. Anything in the cast can appear in any set, so what you
make here can be used in every film, whatever the set.

What's in the kit:

| | |
|---|---|
| `SPEC.md` | what a model must be: format, units, origin, clips, textures, catalog entry, rights |
| `WISHLIST.md` | what people ask for that the cast cannot play yet |
| `reference/1942-cast.json` | the 1942 cast: ids, descriptions, heights, clips (no art) |
| `reference/beyond-cast.json` | the things from beyond, part of 1942-WEIRD: ghouls, vampires, the tall ones, the shoggoth, Cthulhu |
| `reference/sets.json` | the two sets: description, bounds, landmarks, in Quake units |
| `AGENTS.md` | the workflow in steps, for a coding agent (Claude Code, Codex, ...) doing the work |
| `tools/fetch_cast.py` | downloads the cast's models (pinned, SHA-256 checked) into `cast/1942/`, or `cast/beyond/` with `beyond` |
| `tools/derive.py` | starts a new model from a cast model (1942 by default, `--cast beyond`): mesh, chosen clips, textures, catalog entry |
| `tools/cc0_material.py` | optional: turns a CC0 material from ambientCG (leather, fabric, concrete, rusty metal...) into a surface's albedo, `_norm` and `_gloss` maps, pinned by SHA-256 |
| `tools/check.py` | checks a submission against the spec |
| `tools/preview.py` | a contact sheet of one model (four views, every clip, a soldier-height bar) with its normal, gloss and glow maps; software only, no engine or GPU (see below) |
| `tools/md3.py`, `tools/tex.py` | an MD3 writer and texture helpers (normal-from-height, tileable noise), for building from code |
| `examples/buoy/` | a complete, valid submission built from code |
| `tests/run.sh` | end-to-end test of the tools (see below) |
| `submission-template/` | the folder you send back |

## Setup

[uv](https://docs.astral.sh/uv/) runs the tools; each one declares its pinned dependencies (numpy, Pillow).

```sh
examples/buoy/build.py /tmp/buoy            # build the example submission
tools/check.py /tmp/buoy                    # 0 errors
tools/preview.py /tmp/buoy kit_buoy --out buoy.png
```

## The cast download

`tools/fetch_cast.py` downloads the packages ps1core renders with, so you can base models on the existing cast. Each is
pinned in `reference/<package>-package.lock.json` (file name, SHA-256, size, URL in ps1core's public asset bucket):

| Command | What | Size (as of 2026-11-07) |
|---|---|---|
| `tools/fetch_cast.py` | **1942** (the default): the soldiers and props, package `1942-db6471b847b2` | about 800 MB, about 3,500 files |
| `tools/fetch_cast.py beyond` | **beyond**, the things from beyond of 1942-WEIRD, package `beyond-31e271c610d8` | about 340 MB, about 770 files |

- Downloaded once and cached in `~/.cache/ps1core-assets/` (`PS1_ASSET_CACHE` moves it).
- The download is refused if its SHA-256 does not match the lock.
- Only the models and their textures are unpacked, into `cast/1942/` or `cast/beyond/` (ignored by git).
- The pin is a snapshot: when ps1core updates a cast, this kit keeps this version until its lock is updated.

Not needed for models you make from scratch.

## Making a model

1. Pick something from `WISHLIST.md` (or propose your own) and tell us on the [ps1core Discord](https://discord.gg/4e45kQyeN9), so nobody else makes it too.
2. Choose a short collection prefix, e.g. your handle: `mycoll`. Every id and file starts with it.
3. Start from the 1942 cast (`tools/fetch_cast.py`, then `tools/derive.py bf_ger_rifleman mycoll_diver SUB --clips ...`)
   and repaint, reshape or add clips; or model it in any tool and export to MD3 (Blender has community MD3 exporters);
   or build it from code with `tools/md3.py` as `examples/buoy/build.py` does. To repaint a surface that is one material
   (a tunic as a wetsuit, a wall as concrete), `tools/cc0_material.py --list` shows ps1core's shortlist of 50 vetted CC0 materials (any other of
   [ambientCG](https://ambientcg.com)'s 2,931 assets, as of 2026-11-07, works with `--new`); it writes all
   three maps for one surface (`tools/cc0_material.py Leather030 --out SUB/progs/mycoll/mycoll_diver_GerBody_tunic --tile 3`). Follow `SPEC.md`: 72.7 units for a soldier-sized person,
   feet at z −24, facing +X, in-place clips, one PNG per surface plus `_norm` / `_gloss` / `_glow`.
4. Copy `submission-template/` and rename `progs/mycoll/` to your prefix. Put your MD3s and PNGs there, add a catalog
   entry per model to `models.json`, and a line per model to `SOURCES.md`.
5. `tools/check.py SUBMISSION` until there are no errors, then `tools/preview.py SUBMISSION MODEL` and look at it:
   is it the right size next to the soldier bar, facing the right way, and do the clips loop?
6. Zip the folder and send it to us on the [ps1core Discord](https://discord.gg/4e45kQyeN9).

## Animation: what is quick and what is not

Models are vertex-animated: each frame stores every vertex, and there is no skeleton or rig anywhere in the kit or in
the cast you download. So:

- **Quick:** repaint, remove or reshape parts (a helmet, a rifle), change the size; reuse, re-time or combine clips the
  source model already has. `derive.py` and a few lines of numpy do it, and a coding agent can do it for you.
- **Real work:** new motion, such as a diver's underwater stroke, climbing out of the water or talking on a radio. That
  needs a rigged character animated in Blender (or similar) and exported to MD3, or a body built and animated from code
  (fine for simple things like the buoy's bob, hard for a convincing person). Stretching or warping existing frames does
  not make a believable new move.

If the clip you need is the hard kind, tell us on the Discord before you start.

## The preview is not the film look

`tools/preview.py` is a quick software render (numpy, one sun, orthographic) for checking scale, facing, UVs, clips,
missing textures (magenta), and normal, gloss and glow maps (`--flat` turns the maps off to compare). ps1core's
renderer looks different: its own shading, realtime lights and shadows, offset mapping from the `_norm` alpha (most of
the soldiers' relief is there, so their normal maps look nearly flat in the preview), bloom on glow, fog, water, night
and each set's light. Today the real look comes from the in-engine review render we send back with every submission. An
in-engine preview through the ps1core API, which you or your agent could call yourselves, is planned but not available yet.

Big models are slow: a soldier's sheet takes a few seconds, a 58,000-vertex shoggoth part a minute or two. Use
`--clips idle` while you iterate.

## What happens next

Your models become a collection of their own, named after your prefix, hidden while we review it. We render every
model in the engine, in the sets, in real lighting, and send you the review videos. It may take a round or two of
changes. When a model is approved we publish your collection and it joins the cast: anyone can then cast it in a film.
If any of your models is based on the cast (1942 or beyond), your collection is for free films only, like the 1942 sets. Your
credit goes where `SOURCES.md` says.

## Testing the kit

```sh
tests/run.sh              # about 30 s once the cast is cached (first run downloads it: about 1.1 GB)
tests/run.sh --full       # also the shoggoth part, a big model: about 2 minutes more
tests/run.sh --out DIR    # keep the test submission and the preview sheets to look at
```

It builds the buoy, derives a 1942 soldier (repainting its tunic with a CC0 material) and a beyond ghoul, checks them, draws their previews with and without
maps, and makes sure `check.py` rejects a broken entry. Run it after changing anything in `tools/`.

## License

The kit's code and docs are MIT (`LICENSE`). The cast you download with `fetch_cast.py` (1942 and beyond) is not part
of the kit and is not MIT: it and anything based on it are for free films on ps1core, under the site's terms. Your original models
stay yours; how you license them to ps1core is written in `SOURCES.md` for each one (see `SPEC.md`, Rights).
