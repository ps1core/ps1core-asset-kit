#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy==2.3.1", "pillow==11.3.0"]
# ///
"""Contact sheet of one model, without the engine: four views of the idle pose and a strip per clip, next to a
72.7-unit soldier-height bar, with the ground at the feet. Orthographic, one sun, with the model's maps: albedo,
_norm (tangent-space normal), _gloss (specular) and _glow (emissive, added on top). Software only (numpy), no GPU.

  tools/preview.py SUBMISSION_DIR MODEL_ID [--out FILE.png] [--size 320] [--clips idle,walk] [--flat]

--flat: albedo and simple shading only, no maps (to tell a map problem from a mesh or UV problem).

What it is good for: scale, facing, UVs, clips, missing textures (magenta), a broken or inverted _norm map, glow in the
wrong place. What it is not: the look in a film. ps1core's renderer adds its own shading, realtime lights and shadows,
offset mapping from the _norm alpha, bloom on glow, fog, water, night and the set's light; this sheet has none of that.
Today we send an in-engine review render back with every submission; an in-engine preview through the ps1core API is
planned but not available yet.
"""
import argparse, json, sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import md3read

SOLDIER = 72.7   # the 1942 soldiers' height in units
MISSING = np.full((2, 2, 3), (1.0, 0.0, 1.0))     # magenta: missing texture


def _img(p, mode):
    return np.asarray(Image.open(p).convert(mode), float) / 255 if p.is_file() else None


def load_maps(root, shader, flat=False):
    """{'alb', 'norm', 'gloss', 'glow'} for a surface (None where absent), or None for an invisible surface."""
    if shader.endswith('nodraw'): return None
    base = root / shader
    alb = _img(base.with_name(base.name + '.png'), 'RGB')
    maps = dict(alb=MISSING if alb is None else alb, norm=None, gloss=None, glow=None)
    if not flat and alb is not None:
        maps['norm'] = _img(base.with_name(base.name + '_norm.png'), 'RGB')
        g = _img(base.with_name(base.name + '_gloss.png'), 'L')
        maps['gloss'] = g
        maps['glow'] = _img(base.with_name(base.name + '_glow.png'), 'RGB')
    return maps


def sample(tex, u, v):
    th, tw = tex.shape[:2]
    return tex[np.floor(v * th).astype(int) % th, np.floor(u * tw).astype(int) % tw]


def render(m, maps, frame, yaw, size, scale, z0):
    """Orthographic view from direction yaw (0 = in front of the model, which faces +x). Returns an RGB image."""
    img = np.full((size, size, 3), 0.16); zbuf = np.full((size, size), -1e9)
    d = np.array([np.cos(yaw), np.sin(yaw), 0.0]); right = np.array([-np.sin(yaw), np.cos(yaw), 0.0])
    sun = np.array([0.5, -0.4, 0.75]); sun /= np.linalg.norm(sun)
    half = sun + d; half /= np.linalg.norm(half)
    gy = int(size * 0.88)                                       # ground line in pixels (feet, z = -24)
    for s, mp in zip(m['surfaces'], maps):
        if mp is None: continue
        v = s['verts'][frame]; vn = s['normals'][frame]; uv = s['uv']
        sx = size / 2 + (v @ right) * scale
        sy = gy - (v[:, 2] - z0) * scale
        dep = v @ d
        for t in s['tris']:
            a, b, c = t
            x = sx[[a, b, c]]; y = sy[[a, b, c]]
            area = (x[1] - x[0]) * (y[2] - y[0]) - (x[2] - x[0]) * (y[1] - y[0])
            if abs(area) < 1e-9: continue
            x0, x1 = max(int(x.min()), 0), min(int(x.max()) + 1, size)
            y0, y1 = max(int(y.min()), 0), min(int(y.max()) + 1, size)
            if x0 >= x1 or y0 >= y1: continue
            px, py = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
            w0 = ((x[1] - px) * (y[2] - py) - (x[2] - px) * (y[1] - py)) / area
            w1 = ((x[2] - px) * (y[0] - py) - (x[0] - px) * (y[2] - py)) / area
            w2 = 1 - w0 - w1
            inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
            if not inside.any(): continue
            z = w0 * dep[a] + w1 * dep[b] + w2 * dep[c]
            sub = zbuf[y0:y1, x0:x1]
            hit = inside & (z > sub)
            if not hit.any(): continue
            W = np.stack([w0[hit], w1[hit], w2[hit]], -1)                     # (P, 3) barycentrics of the visible pixels
            u, vv = (W @ uv[[a, b, c]]).T
            n = W @ vn[[a, b, c]]
            n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
            if mp['norm'] is not None:                                          # tangent frame from the triangle's UVs
                e1, e2 = v[b] - v[a], v[c] - v[a]
                du1, dv1 = uv[b] - uv[a]; du2, dv2 = uv[c] - uv[a]
                det = du1 * dv2 - du2 * dv1
                if abs(det) > 1e-12:
                    T = (e1 * dv2 - e2 * dv1) / det; B = (e2 * du1 - e1 * du2) / det    # d(position)/du, d(position)/dv
                    T = T - n * (n @ T)[:, None]; T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
                    Bu = -B / max(np.linalg.norm(B), 1e-9)                            # texture "up" is -v (image rows go down)
                    tn = sample(mp['norm'], u, vv) * 2 - 1
                    n = T * tn[:, :1] + Bu[None] * tn[:, 1:2] + n * tn[:, 2:3]
                    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
            col = sample(mp['alb'], u, vv) * (0.3 + 0.7 * np.clip(n @ sun, 0, 1))[:, None]
            if mp['gloss'] is not None:
                col = col + (sample(mp['gloss'], u, vv) * np.clip(n @ half, 0, 1) ** 32 * 0.8)[:, None]
            if mp['glow'] is not None:
                col = col + sample(mp['glow'], u, vv)
            sub[hit] = z[hit]
            img[y0:y1, x0:x1][hit] = col
    return img


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('dir'); ap.add_argument('model'); ap.add_argument('--out'); ap.add_argument('--size', type=int, default=320)
    ap.add_argument('--clips', help='comma-separated clips to show (default: all)')
    ap.add_argument('--flat', action='store_true', help='albedo and simple shading only, no maps')
    a = ap.parse_args()
    root = Path(a.dir)
    e = json.loads((root / 'models.json').read_text())[a.model]
    m = md3read.read(root / e['path'])
    maps = [load_maps(root, s['shaders'][0], a.flat) for s in m['surfaces']]
    clips = e['clips'] if not a.clips else {c: e['clips'][c] for c in a.clips.split(',')}
    used = sorted({clips.get('idle', e['clips']['idle'])[0]} | {f for f0, f1, _ in clips.values() for f in range(f0, f1 + 1)})
    allv = np.concatenate([s['verts'][used] for s in m['surfaces']], axis=1)
    ext = max(np.abs(allv[..., :2]).max() * 2, allv[..., 2].max() + e['lift'], SOLDIER * 1.2)
    S = a.size; scale = S * 0.8 / ext; z0 = -e['lift']
    rows = [('idle: front, side (its left), back, three-quarter.  Software preview with maps' + (' off' if a.flat else '') + ': not the in-engine look', [(clips.get('idle', e['clips']['idle'])[0], y) for y in (0, np.pi / 2, np.pi, np.pi / 4)])]
    for c, (f0, f1, fps) in clips.items():
        picks = sorted(set(np.linspace(f0, f1, 4).round().astype(int)))
        rows.append((f'{c}: frames {f0}-{f1} at {fps} fps (side view)', [(f, np.pi / 2) for f in picks]))
    W = S * 4 + 60; H = len(rows) * (S + 24)
    sheet = Image.new('RGB', (W, H), (24, 24, 24)); dr = ImageDraw.Draw(sheet)
    for i, (label, cells) in enumerate(rows):
        oy = i * (S + 24)
        dr.text((6, oy + 5), label, fill=(220, 220, 220))
        for j, (f, yaw) in enumerate(cells):
            im = render(m, maps, f, yaw, S, scale, z0)
            sheet.paste(Image.fromarray((np.clip(im, 0, 1) * 255).astype(np.uint8)), (j * S, oy + 22))
            dr.text((j * S + 4, oy + 26), m['frames'][f]['name'], fill=(160, 160, 160))
        gy = oy + 22 + int(S * 0.88)
        bx = S * 4 + 25; top = gy - SOLDIER * scale
        dr.rectangle([bx, top, bx + 10, gy], fill=(90, 140, 90))
        dr.line([0, gy, S * 4, gy], fill=(80, 80, 80))
        if i == 0: dr.text((S * 4 + 4, top - 14), 'soldier', fill=(140, 190, 140))
    out = a.out or f'{a.model}-preview.png'
    sheet.save(out)
    print(out)


if __name__ == '__main__':
    main()
