# ps1core asset kit

Everything you need to make characters and props for ps1core's **1942** and **1942-WEIRD** sets. ps1core turns a
prompt or a scene into a short film rendered by a real 3D engine. Anything in the cast can appear in any set, so what you
make here can be used in every film, whatever the set.

What's in the kit:

| | |
|---|---|
| `SPEC.md` | what a model must be: format, units, origin, clips, textures, catalog entry, rights |
| `WISHLIST.md` | what people ask for that the cast cannot play yet |
| `reference/1942-cast.json` | the existing cast: ids, descriptions, heights, clips with frame counts and speeds (no art) |
| `reference/sets.json` | the two sets: description, bounds, landmarks, in Quake units |
| `AGENTS.md` | the workflow in steps, for a coding agent (Claude Code, Codex, ...) doing the work |
| `tools/fetch_cast.py` | downloads the 1942 cast's models (pinned, SHA-256 checked) into `cast/1942/` |
| `tools/derive.py` | starts a new model from a 1942 soldier or prop: mesh, chosen clips, textures, catalog entry |
| `tools/check.py` | checks a submission against the spec |
| `tools/preview.py` | a contact sheet of one model (four views, every clip, a soldier-height bar), no engine needed |
| `tools/md3.py`, `tools/tex.py` | an MD3 writer and texture helpers (normal-from-height, tileable noise), for building from code |
| `examples/buoy/` | a complete, valid submission built from code |
| `submission-template/` | the folder you send back |

## Setup

[uv](https://docs.astral.sh/uv/) runs the tools; each one declares its pinned dependencies (numpy, Pillow).

```sh
examples/buoy/build.py /tmp/buoy            # build the example submission
tools/check.py /tmp/buoy                    # 0 errors
tools/preview.py /tmp/buoy kit_buoy --out buoy.png
```

## Making a model

1. Pick something from `WISHLIST.md` (or propose your own) and tell us, so nobody else makes it too.
2. Choose a short collection prefix, e.g. your handle: `mycoll`. Every id and file starts with it.
3. Start from the 1942 cast (`tools/fetch_cast.py`, then `tools/derive.py bf_ger_rifleman mycoll_diver SUB --clips ...`)
   and repaint, reshape or add clips; or model it in any tool and export to MD3 (Blender has community MD3 exporters);
   or build it from code with `tools/md3.py` as `examples/buoy/build.py` does. Follow `SPEC.md`: 72.7 units for a soldier-sized person,
   feet at z −24, facing +X, in-place clips, one PNG per surface plus `_norm` / `_gloss` / `_glow`.
4. Copy `submission-template/` and rename `progs/mycoll/` to your prefix. Put your MD3s and PNGs there, add a catalog
   entry per model to `models.json`, and a line per model to `SOURCES.md`.
5. `tools/check.py SUBMISSION` until there are no errors, then `tools/preview.py SUBMISSION MODEL` and look at it:
   is it the right size next to the soldier bar, facing the right way, and do the clips loop?
6. Send the folder (zipped) to whoever gave you this kit.

## What happens next

Your models become a collection of their own, named after your prefix, hidden while we review it. We render every
model in the engine, in the sets, in real lighting, and send you the review videos. It may take a round or two of
changes. When a model is approved we publish your collection and it joins the cast: anyone can then cast it in a film.
If any of your models is based on the 1942 cast, your collection is for free films only, like the 1942 sets. Your
credit goes where `SOURCES.md` says.

## Licence

The kit's code and docs are MIT (`LICENSE`). The 1942 cast you download with `fetch_cast.py` is not part of the kit
and is not MIT: it and anything based on it are for free films on ps1core, under the site's terms. Your original models
stay yours; how you license them to ps1core is written in `SOURCES.md` for each one (see `SPEC.md`, Rights).
