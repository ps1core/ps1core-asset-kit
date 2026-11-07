#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy==2.3.1", "pillow==11.3.0"]
# ///
"""A complete, valid submission built from code: a marker buoy with a lamp, bobbing (one animated clip, a glow map).

  examples/buoy/build.py OUTDIR      then: tools/check.py OUTDIR ; tools/preview.py OUTDIR kit_buoy

Read it as a template for the conventions in SPEC.md (units, lift, facing, winding, shader names, maps, catalog),
not as an art reference. If you model in Blender or similar, you only need the MD3 + PNGs + catalog entry it writes.
"""
import json, sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import md3, tex

COLL, MID = 'kit_example', 'kit_buoy'
LIFT = 24


def lathe(profile, n=24, u0=0.0, u1=1.0):
    """Surface of revolution around z. profile: [(radius, z, v)] bottom to top. CCW seen from outside."""
    P = len(profile); verts, uv = [], []
    for i in range(n + 1):
        a = 2 * np.pi * i / n
        for r, z, v in profile:
            verts.append((r * np.cos(a), r * np.sin(a), z)); uv.append((u0 + (u1 - u0) * i / n, v))
    tris = []
    for i in range(n):
        for j in range(P - 1):
            p, q = i * P + j, (i + 1) * P + j
            tris += [(p, q, q + 1), (p, q + 1, p + 1)]
    return np.array(verts, float), np.array(uv, float), np.array(tris)


def bob(verts, t):
    """Frame t in 0..1: rise and fall 2 units, tilt 6 degrees around a slowly turning axis. In place (no travel)."""
    ang = np.radians(6) * np.sin(2 * np.pi * t); ax = 2 * np.pi * t * 0.5
    k = np.array([np.cos(ax), np.sin(ax), 0.0])
    v = verts * np.cos(ang) + np.cross(k, verts) * np.sin(ang) + np.outer(verts @ k, k) * (1 - np.cos(ang))
    return v + (0, 0, 2 * np.sin(2 * np.pi * t + 0.6))


def main():
    out = Path(sys.argv[1]); progs = out / 'progs' / COLL; progs.mkdir(parents=True, exist_ok=True)
    z = lambda h: h - LIFT                           # model z from height above the feet
    # hull: a squat drum with a conical top, red and white bands (texture v runs down the image: v 0 = top row)
    hull_v, hull_uv, hull_t = lathe([(0.1, z(0), 1.0), (16, z(0), 0.97), (18, z(6), 0.8), (18, z(26), 0.35), (9, z(38), 0.1), (2, z(40), 0.0)])
    # lamp: a small sphere on a mast
    mast_v, mast_uv, mast_t = lathe([(1.2, z(39), 1.0), (1.2, z(60), 0.6), (3.5, z(61), 0.55), (4.5, z(64), 0.4), (3.5, z(67), 0.2), (0.1, z(68), 0.0)], n=12)
    F = 16
    surfs = []
    for name, v, uv, t in (('hull', hull_v, hull_uv, hull_t), ('lamp', mast_v, mast_uv, mast_t)):
        frames = np.stack([bob(v, f / F) for f in range(F)])
        # md3.write takes Quake winding: reverse a CCW-outward mesh (Blender, glTF) with tris[:, ::-1]
        surfs.append(dict(name=name, shader=f'progs/{COLL}/{MID}_{name}', verts=frames, uv=uv, tris=t[:, ::-1].copy()))
    md3.write(str(progs / f'{MID}.md3'), surfs, frame_names=[f'idle{i}' for i in range(F)], name=MID)

    # textures: albedo, _norm (RGB normal + A height), _gloss, and _glow for the lamp
    S = 256
    yy = np.linspace(0, 1, S)[:, None] * np.ones((1, S))
    rust = tex.fbm((S, S), seed=3)
    band = (np.floor(yy * 6) % 2 == 0)
    alb = np.where(band[..., None], (0.62, 0.10, 0.07), (0.82, 0.80, 0.74)) * (0.75 + 0.25 * rust[..., None])
    alb = alb * (1 - 0.35 * (rust[..., None] > 0.62))                           # rust patches
    tex.save(str(progs / f'{MID}_hull.png'), alb)
    tex.save(str(progs / f'{MID}_hull_norm.png'), tex.normal_from_height(rust * 0.5, strength=3))
    tex.save(str(progs / f'{MID}_hull_gloss.png'), 0.15 + 0.4 * (1 - rust))
    lamp = np.where((yy < 0.6)[..., None], (1.0, 0.85, 0.45), (0.12, 0.12, 0.12)) * np.ones((S, S, 3))
    tex.save(str(progs / f'{MID}_lamp.png'), lamp)
    tex.save(str(progs / f'{MID}_lamp_norm.png'), tex.normal_from_height(np.zeros((S, S))))
    tex.save(str(progs / f'{MID}_lamp_gloss.png'), np.full((S, S), 0.6))
    tex.save(str(progs / f'{MID}_lamp_glow.png'), np.where((yy < 0.6)[..., None], (1.0, 0.8, 0.4), 0.0) * np.ones((S, S, 3)))

    catalog = {MID: dict(path=f'progs/{COLL}/{MID}.md3', kind='prop',
                         desc='a red and white steel marker buoy with a small amber lamp on its mast, bobbing gently in the water',
                         idle='idle', clips=dict(idle=[0, F - 1, 8]), height=68, lift=LIFT,
                         light=dict(radius=90, intensity=1.2, offset=[0, 0, 40], tint=[1.0, 0.75, 0.4]))}
    (out / 'models.json').write_text(json.dumps(catalog, indent=1) + '\n')
    (out / 'SOURCES.md').write_text('# Sources\n\n| Model | Author | Made from | License |\n|---|---|---|---|\n'
                                    '| `kit_buoy` | ps1core | procedural, examples/buoy/build.py; no outside data | same as this kit |\n')
    print(out)


if __name__ == '__main__':
    main()
