#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy==2.3.1", "pillow==11.3.0"]
# ///
"""Turn a CC0 material from ambientCG (CC0 1.0: free to use, change and redistribute) into one surface's maps:
<prefix>.png (albedo), <prefix>_norm.png (normal + height in alpha), <prefix>_gloss.png. For repainting a surface that
is one material: a wetsuit tunic, concrete, rust, rock.

  tools/cc0_material.py MATERIAL_ID --out SUB/progs/mycoll/mycoll_diver_GerBody_tunic [--size 512] [--tile 2] [--new]
  tools/cc0_material.py --list

- reference/cc0.lock.json is a shortlist: ps1core's library of vetted materials (50 as of 2026-11-07), pinned by
  SHA-256 (the download must match). ambientCG has many more (2,931 assets as of 2026-11-07: https://ambientcg.com); any of them
  works with --new.
- Any other ambientCG id needs --new: it is downloaded and its SHA-256 printed; write the id and the hash in SOURCES.md.
- --tile N repeats the swatch N x N across the texture (the material looks N times smaller on the model).
- Downloads the 1K JPG set once (a few MB), cached in ~/.cache/ps1core-assets/cc0/. Only the JPG maps are read.

Mapping: Color -> albedo; NormalGL -> _norm RGB (green up, as tools/tex.py writes; not yet compared in the engine);
Displacement -> _norm alpha; 1 - Roughness -> _gloss; Opacity, when the set has one, -> albedo alpha.
A tileable swatch suits a surface that is one material. On a painted atlas (a face, mixed gear) it shows seams and
loses the painted detail: blend it in with numpy instead, or keep the original paint.
"""
import argparse, hashlib, io, json, os, sys, urllib.request, zipfile
from pathlib import Path

import numpy as np
from PIL import Image

KIT = Path(__file__).resolve().parents[1]
LOCK = KIT / 'reference/cc0.lock.json'
CACHE = Path(os.environ.get('PS1_ASSET_CACHE', Path.home() / '.cache/ps1core-assets')) / 'cc0'
URL = 'https://ambientcg.com/get?file={id}_1K-JPG.zip'


def fetch(mid, new):
    lock = json.loads(LOCK.read_text())['materials']
    if mid not in lock and not new:
        sys.exit(f'{mid} is not in reference/cc0.lock.json (vetted: {", ".join(lock)}). For another ambientCG id add --new.')
    CACHE.mkdir(parents=True, exist_ok=True)
    z = CACHE / f'{mid}_1K-JPG.zip'
    if not z.exists():
        req = urllib.request.Request(URL.format(id=mid), headers={'User-Agent': 'ps1core-asset-kit/1'})
        with urllib.request.urlopen(req, timeout=120) as r: data = r.read()
        tmp = z.with_suffix(f'.{os.getpid()}.tmp'); tmp.write_bytes(data); os.replace(tmp, z)
    data = z.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    if mid in lock and lock[mid]['sha256'] != sha:
        z.unlink()
        sys.exit(f'{mid}: download does not match the pinned SHA-256 (ambientCG changed the file?): not used')
    if mid not in lock:
        print(f'{mid}: not vetted. Record it in SOURCES.md: "ambientCG {mid}, CC0 1.0, sha256 {sha}"')
    return zipfile.ZipFile(io.BytesIO(data))


def read(zf, mid, kind, mode):
    name = f'{mid}_1K-JPG_{kind}.jpg'
    if name not in zf.namelist(): return None
    return Image.open(io.BytesIO(zf.read(name))).convert(mode)


def fit(im, size, tile, resample=Image.LANCZOS):
    if tile > 1:
        w, h = im.size; big = Image.new(im.mode, (w * tile, h * tile))
        for i in range(tile):
            for j in range(tile): big.paste(im, (i * w, j * h))
        im = big
    return im.resize((size, size), resample)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('material', nargs='?'); ap.add_argument('--out'); ap.add_argument('--size', type=int, default=512)
    ap.add_argument('--tile', type=int, default=1); ap.add_argument('--new', action='store_true'); ap.add_argument('--list', action='store_true')
    a = ap.parse_args()
    if a.list:
        for k, v in json.loads(LOCK.read_text())['materials'].items(): print(f'{k:22s} {v["use"]}')
        print('A shortlist (ps1core\'s vetted library). ambientCG has 2,931 assets (as of 2026-11-07); any other works with --new: https://ambientcg.com')
        return
    if not a.material or not a.out: ap.error('give MATERIAL_ID and --out PREFIX (or --list)')
    if a.size & (a.size - 1) or not 16 <= a.size <= 2048: sys.exit('--size must be a power of two, 16 to 2048')
    zf = fetch(a.material, a.new)
    color = read(zf, a.material, 'Color', 'RGB')
    if color is None: sys.exit(f'{a.material}: no Color map in the set')
    nrm = read(zf, a.material, 'NormalGL', 'RGB')
    disp = read(zf, a.material, 'Displacement', 'L')
    rough = read(zf, a.material, 'Roughness', 'L')
    opac = read(zf, a.material, 'Opacity', 'L')
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    S, T = a.size, a.tile
    alb = fit(color, S, T)
    if opac is not None: alb = alb.convert('RGBA'); alb.putalpha(fit(opac, S, T))
    alb.save(f'{out}.png')
    if nrm is not None:
        n = fit(nrm, S, T, Image.BILINEAR).convert('RGBA')
        n.putalpha(fit(disp, S, T) if disp is not None else Image.new('L', (S, S), 128))
        n.save(f'{out}_norm.png')
    if rough is not None:
        g = 1 - np.asarray(fit(rough, S, T), float) / 255
        Image.fromarray((g * 255 + 0.5).astype(np.uint8)).save(f'{out}_gloss.png')
    made = [f'{out.name}{s}.png' for s, ok in (('', True), ('_norm', nrm is not None), ('_gloss', rough is not None)) if ok]
    print(f'{a.material} -> {", ".join(made)} ({S} px, tile {T})')


if __name__ == '__main__':
    main()
