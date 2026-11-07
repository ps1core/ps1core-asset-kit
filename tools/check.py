#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy==2.3.1", "pillow==11.3.0"]
# ///
"""Check a submission folder against SPEC.md. Exit status 1 if anything must be fixed.

  tools/check.py SUBMISSION_DIR [--model ID]

SUBMISSION_DIR holds models.json, SOURCES.md and progs/<collection>/ (see submission-template/).
Errors must be fixed before we can take the model; warnings are worth a look; notes are information.
"""
import argparse, json, re, sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import md3read

REQUIRED = ('path', 'desc', 'idle', 'clips', 'height', 'lift')
OPTIONAL = ('light', 'internal', 'kind', 'based_on')
# Any character needs idle and walk (the beyond creatures have little more). The recommended ones are the 1942 soldiers'
# clips (reference/1942-cast.json): a person who has them can stand in for a soldier in any scene written for one.
CHAR_REQUIRED = ('idle', 'walk')
CHAR_RECOMMENDED = ('run', 'crouch', 'die', 'stand', 'crouch_run', 'lie', 'crawl', 'swim', 'flinch', 'die_back', 'run_low', 'crawl_up', 'tend', 'drag', 'breathe')
ID = re.compile(r'^[a-z][a-z0-9_]{1,31}$')


class Report:
    def __init__(self): self.errors = self.warnings = 0
    def err(self, m, s): self.errors += 1; print(f'  ERROR  {m}: {s}')
    def warn(self, m, s): self.warnings += 1; print(f'  warn   {m}: {s}')
    def note(self, m, s): print(f'  note   {m}: {s}')


def check_texture(r, mid, png, required=True, rgba=False):
    if not png.is_file():
        (r.err if required else r.warn)(mid, f'missing texture {png.name}')
        return
    im = Image.open(png)
    w, h = im.size
    if w & (w - 1) or h & (h - 1): r.warn(mid, f'{png.name} is {w}x{h}: use power-of-two sizes')
    if max(w, h) > 2048: r.err(mid, f'{png.name} is {w}x{h}: 2048 px at most (1024 is the default)')
    if rgba and im.mode != 'RGBA': r.warn(mid, f'{png.name} is {im.mode}: a _norm map is RGBA (alpha = height); RGB works but loses offset mapping')


def check_model(r, root, coll, mid, e, sources):
    if not ID.match(mid): r.err(mid, 'model id must be lowercase letters, digits and _, 2 to 32 characters, starting with a letter')
    for k in REQUIRED:
        if k not in e: r.err(mid, f'catalog entry has no "{k}"')
    for k in e:
        if k not in REQUIRED + OPTIONAL: r.warn(mid, f'unknown catalog field "{k}" (ignored)')
    if not all(k in e for k in REQUIRED): return
    want = f'progs/{coll}/{mid}.md3'
    if e['path'] != want: r.err(mid, f'path is {e["path"]!r}, expected {want!r}')
    if not (20 <= len(e['desc']) <= 300): r.warn(mid, f'desc is {len(e["desc"])} characters: one plain sentence, 20 to 300')
    if mid not in sources: r.err(mid, 'not listed in SOURCES.md (who made it, from what, under which licence)')
    if e.get('based_on'): r.note(mid, f'based on {e["based_on"]} from the cast: carries the 1942 terms (free films only)')
    if e['desc'].startswith('TODO'): r.err(mid, 'desc still says TODO')
    f = root / e['path']
    if not f.is_file(): r.err(mid, f'no file {e["path"]}'); return
    try: m = md3read.read(f)
    except Exception as x: r.err(mid, f'cannot read the MD3: {x}'); return
    if not m['eof_ok']: r.err(mid, 'MD3 header size does not match the file')
    F = len(m['frames'])
    for s in m['surfaces']:
        if s['frames'] != F: r.err(mid, f'surface {s["name"]} has {s["frames"]} frames, the model {F}')
        if len(s['shaders']) != 1: r.err(mid, f'surface {s["name"]} has {len(s["shaders"])} shaders, needs exactly 1')
        if s['tris'].size and (s['tris'].min() < 0 or s['tris'].max() >= s['verts'].shape[1]): r.err(mid, f'surface {s["name"]}: triangle index out of range')
        if not np.isfinite(s['uv']).all(): r.err(mid, f'surface {s["name"]}: non-finite UVs')
    # clips
    clips = e['clips']
    if e['idle'] not in clips: r.err(mid, f'idle clip {e["idle"]!r} is not in clips')
    if 'idle' not in clips: r.err(mid, 'every model needs an "idle" clip')
    seen = set()
    for c, v in clips.items():
        if not (isinstance(v, list) and len(v) == 3 and all(isinstance(x, (int, float)) for x in v)):
            r.err(mid, f'clip {c}: expected [first, last, fps]'); continue
        a, b, fps = v
        if not (0 <= a <= b < F): r.err(mid, f'clip {c}: frames {a}..{b} outside the model\'s 0..{F - 1}'); continue
        if not (1 <= fps <= 60): r.warn(mid, f'clip {c}: {fps} fps')
        if len(c) > 15: r.err(mid, f'clip name {c!r} is over 15 characters')
        if (a, b) not in seen:   # first clip on this range: its frames should carry its name (later clips may reuse a range at another speed)
            nm = m['frames'][a]['name']
            if not nm.startswith(c[:11]): r.warn(mid, f'clip {c}: first frame is named {nm!r}, expected {c[:11]}0')
        seen.add((a, b))
    is_char = e.get('kind') == 'character' or 'walk' in clips
    if is_char:
        miss = [c for c in CHAR_REQUIRED if c not in clips]
        if miss: r.err(mid, f'a character needs the clips {", ".join(miss)}')
        rec = [c for c in CHAR_RECOMMENDED if c not in clips]
        if rec: r.note(mid, f'recommended clips not present (scenes written for the soldiers use them): {", ".join(rec)}')
    # size, units, feet
    allv = np.concatenate([s['verts'] for s in m['surfaces']], axis=1)
    V = allv.shape[1]
    if V > 65000: r.err(mid, f'{V} vertices: the engine crashes above about 65,000 per model (split it into parts)')
    elif V > 30000: r.warn(mid, f'{V} vertices: heavy; the soldiers are about 3,000 to 6,000')
    if np.abs(allv).max() >= 511: r.err(mid, f'reaches {np.abs(allv).max():.0f} units from the origin: everything must stay within 511')
    if 'idle' in clips and isinstance(clips['idle'], list):
        f0 = clips['idle'][0]; v0 = allv[f0] if f0 < F else allv[0]
        feet, top = v0[:, 2].min(), v0[:, 2].max()
        if abs(feet + e['lift']) > 2: r.warn(mid, f'lowest point of idle is z {feet:.1f}; with lift {e["lift"]} the feet should be at z {-e["lift"]}')
        meas = top + e['lift']
        if abs(meas - e['height']) > max(2, 0.1 * meas): r.warn(mid, f'height is {e["height"]} but the idle pose measures {meas:.1f}')
        r.note(mid, f'{F} frames, {V} vertices, {sum(len(s["tris"]) for s in m["surfaces"])} triangles, {len(m["surfaces"])} surfaces, idle height {meas:.1f} units')
    if e['lift'] != 24: r.warn(mid, f'lift is {e["lift"]}: 24 is the convention for everything in the cast')
    # textures
    pre = f'progs/{coll}/{mid}_'
    for s in m['surfaces']:
        sh = s['shaders'][0] if s['shaders'] else ''
        if not sh.startswith(pre): r.err(mid, f'surface {s["name"]}: shader {sh!r} should start with {pre!r}'); continue
        base = root / sh
        check_texture(r, mid, base.with_name(base.name + '.png'))
        check_texture(r, mid, base.with_name(base.name + '_norm.png'), required=False, rgba=True)
        check_texture(r, mid, base.with_name(base.name + '_gloss.png'), required=False)
        if base.with_name(base.name + '_glow.png').is_file(): check_texture(r, mid, base.with_name(base.name + '_glow.png'))
    if 'light' in e:
        lt = e['light']
        if not isinstance(lt, dict) or 'radius' not in lt: r.err(mid, 'light needs at least "radius" (and usually "intensity", "offset" [x, y, z])')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('dir'); ap.add_argument('--model')
    a = ap.parse_args()
    root = Path(a.dir)
    cat = root / 'models.json'
    if not cat.is_file(): sys.exit(f'{cat}: not found')
    models = json.loads(cat.read_text())
    progs = [p.name for p in (root / 'progs').iterdir() if p.is_dir()] if (root / 'progs').is_dir() else []
    if len(progs) != 1: sys.exit(f'{root}/progs/ must hold exactly one collection folder, found {progs}')
    coll = progs[0]
    src = (root / 'SOURCES.md').read_text() if (root / 'SOURCES.md').is_file() else ''
    sources = set(re.findall(r'`([a-z][a-z0-9_]+)`', src))
    r = Report()
    print(f'collection {coll}: {len(models)} models')
    for mid, e in models.items():
        if a.model and mid != a.model: continue
        print(mid)
        check_model(r, root, coll, mid, e, sources)
    on_disk = {p.stem for p in (root / 'progs' / coll).glob('*.md3')}
    for extra in sorted(on_disk - set(models)): r.warn(extra, 'an MD3 with no catalog entry in models.json')
    print(f'\n{r.errors} errors, {r.warnings} warnings')
    sys.exit(1 if r.errors else 0)


if __name__ == '__main__':
    main()
