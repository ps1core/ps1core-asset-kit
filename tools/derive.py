#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy==2.3.1", "pillow==11.3.0"]
# ///
"""Start a new model from one in the cast (1942, or beyond with --cast beyond): copy its mesh, the clips you choose and
its textures into your submission under a new id, ready to repaint, reshape or extend with new clips. Run
tools/fetch_cast.py (and tools/fetch_cast.py beyond) first.

  tools/derive.py SOURCE_ID NEW_ID SUBMISSION_DIR [--cast 1942|beyond] [--clips idle,walk,swim] [--desc "one sentence"] [--collection mycoll]

  tools/derive.py bf_ger_rifleman mycoll_diver sub/ --clips idle,walk,run,crouch,die,swim,crawl,crawl_up \\
      --desc "a diver in a dark wetsuit and harness, a small radio at the collar"

What it writes: progs/<collection>/<NEW_ID>.md3 and its PNGs (shaders renamed to <NEW_ID>_<material>), a catalog
entry in models.json with "based_on", and a row in SOURCES.md. The result carries the site's 1942 terms (free films
only; SPEC.md, Rights), whichever cast it comes from. Decal anchor surfaces (shader nodraw) are dropped. Next: repaint the PNGs, edit the vertices
(tools/md3read.py reads, tools/md3.py writes), add clips, then tools/check.py.
"""
import argparse, json, re, shutil, sys
from pathlib import Path

import numpy as np

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT / 'tools'))
import md3, md3read



def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('source'); ap.add_argument('new_id'); ap.add_argument('dir')
    ap.add_argument('--cast', default='1942', choices=('1942', 'beyond'))
    ap.add_argument('--clips'); ap.add_argument('--desc'); ap.add_argument('--collection')
    a = ap.parse_args()
    cast = json.loads((KIT / f'reference/{a.cast}-cast.json').read_text())
    if a.source not in cast: sys.exit(f'{a.source}: not in reference/{a.cast}-cast.json' + ('' if a.cast == 'beyond' else ' (a beyond model? add --cast beyond)'))
    CAST = KIT / 'cast' / a.cast
    src_md3 = CAST / f'{a.source}.md3'
    if not src_md3.is_file(): sys.exit(f'{src_md3}: missing; run tools/fetch_cast.py' + (' beyond' if a.cast == 'beyond' else ''))
    root = Path(a.dir); root.mkdir(parents=True, exist_ok=True)
    coll = a.collection
    if not coll:
        have = [p.name for p in (root / 'progs').iterdir() if p.is_dir()] if (root / 'progs').is_dir() else []
        if len(have) != 1: sys.exit('give --collection (the submission has no single progs/<collection>/ yet)')
        coll = have[0]
    if not a.new_id.startswith(coll + '_'): sys.exit(f'{a.new_id}: ids start with the collection prefix, {coll}_')
    out = root / 'progs' / coll; out.mkdir(parents=True, exist_ok=True)

    entry = cast[a.source]
    clips = entry['clips']
    pick = a.clips.split(',') if a.clips else list(clips)
    miss = [c for c in pick if c not in clips]
    if miss: sys.exit(f'{a.source} has no clips {miss}; it has {", ".join(clips)}')
    if 'idle' not in pick: pick.insert(0, 'idle')

    # new frame order: each distinct source range once, in clip order; clips sharing a range share frames
    order, names, ranges, new_clips = [], [], {}, {}
    for c in pick:
        f0, f1, fps = clips[c]
        if (f0, f1) not in ranges:
            ranges[(f0, f1)] = len(order)
            order += list(range(f0, f1 + 1)); names += [f'{c[:11]}{i}' for i in range(f1 - f0 + 1)]
        s = ranges[(f0, f1)]
        new_clips[c] = [s, s + f1 - f0, fps]

    m = md3read.read(src_md3)
    surfs, copied = [], set()
    for s in m['surfaces']:
        sh = s['shaders'][0]
        if sh.endswith('nodraw'): continue
        base = sh.split('/')[-1]
        mat = base[len(a.source) + 1:] if base.startswith(a.source + '_') else base
        mat = re.sub(r'[^A-Za-z0-9_]', '_', mat)
        new_sh = f'progs/{coll}/{a.new_id}_{mat}'
        surfs.append(dict(name=s['name'], shader=new_sh, verts=s['verts'][order], normals=s['normals'][order],
                          uv=np.array(s['uv']), tris=np.array(s['tris'])))
        for suf in ('', '_norm', '_gloss', '_glow'):
            f = CAST / f'{base}{suf}.png'
            if f.is_file() and (base, suf) not in copied:
                shutil.copyfile(f, out / f'{a.new_id}_{mat}{suf}.png'); copied.add((base, suf))
    info = md3.write(str(out / f'{a.new_id}.md3'), surfs, frame_names=names, name=a.new_id)

    cat_path = root / 'models.json'
    cat = json.loads(cat_path.read_text()) if cat_path.is_file() else {}
    cat[a.new_id] = dict(path=f'progs/{coll}/{a.new_id}.md3', desc=a.desc or f'TODO: describe it ({entry["desc"]})',
                         kind='character' if 'walk' in new_clips else 'prop', based_on=a.source,
                         idle='idle', clips=new_clips, height=entry['height'], lift=entry.get('lift', 24))
    cat_path.write_text(json.dumps(cat, indent=1) + '\n')
    src_md = root / 'SOURCES.md'
    if not src_md.is_file():
        src_md.write_text('# Sources\n\n| Model | Author | Made from | License |\n|---|---|---|---|\n')
    if f'`{a.new_id}`' not in src_md.read_text():
        with open(src_md, 'a') as f:
            f.write(f'| `{a.new_id}` | TODO: your name | based on `{a.source}` from the {a.cast} cast | 1942 terms: free films only |\n')
    print(f'{a.new_id}: {info["frames"]} frames, {info["verts"]} vertices, {len(surfs)} surfaces, '
          f'{len(copied)} textures, clips {", ".join(new_clips)} -> {out}')


if __name__ == '__main__':
    main()
