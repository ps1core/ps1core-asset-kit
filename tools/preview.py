#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy==2.3.1", "pillow==11.3.0"]
# ///
"""Contact sheet of one model, without the engine: four views of the idle pose and a strip per clip, next to a
72.7-unit soldier-height bar, with the ground at the feet. Textured, simple sun light, orthographic.

  tools/preview.py SUBMISSION_DIR MODEL_ID [--out FILE.png] [--size 320] [--clips idle,walk]

This is a sanity check for scale, facing, UVs and clips. It is not the look in a film: the engine adds normal,
gloss and glow maps, realtime light and fog. We send a real in-engine review render back with every submission.
"""
import argparse, json, sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import md3read

SOLDIER = 72.7   # the 1942 soldiers' height in units


def load_tex(root, shader):
    if shader.endswith('nodraw'): return None
    p = root / (shader + '.png')
    if p.is_file(): return np.asarray(Image.open(p).convert('RGB'), float) / 255
    return np.full((2, 2, 3), (1.0, 0.0, 1.0))     # magenta: missing texture


def render(m, texs, frame, yaw, size, scale, z0):
    """Orthographic view from direction yaw (0 = in front of the model, which faces +x). Returns an RGB image."""
    img = np.full((size, size, 3), 0.16); zbuf = np.full((size, size), -1e9)
    d = np.array([np.cos(yaw), np.sin(yaw), 0.0]); right = np.array([-np.sin(yaw), np.cos(yaw), 0.0])
    sun = np.array([0.5, -0.4, 0.75]); sun /= np.linalg.norm(sun)
    gy = int(size * 0.88)                                       # ground line in pixels (feet, z = -24)
    for s, tex in zip(m['surfaces'], texs):
        if tex is None: continue
        v = s['verts'][frame]
        sx = size / 2 + (v @ right) * scale
        sy = gy - (v[:, 2] - z0) * scale
        dep = v @ d
        th, tw = tex.shape[:2]
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
            n = np.cross(v[b] - v[a], v[c] - v[a]); ln = np.linalg.norm(n)
            n = n / ln if ln else n
            shade = 0.35 + 0.65 * abs(n @ sun)                 # two-sided: winding problems show up in the engine, not here
            uv = s['uv']
            u = w0 * uv[a, 0] + w1 * uv[b, 0] + w2 * uv[c, 0]
            vv = w0 * uv[a, 1] + w1 * uv[b, 1] + w2 * uv[c, 1]
            col = tex[(np.floor(vv * th).astype(int)) % th, (np.floor(u * tw).astype(int)) % tw] * shade
            sub[hit] = z[hit]
            img[y0:y1, x0:x1][hit] = col[hit]
    return img


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('dir'); ap.add_argument('model'); ap.add_argument('--out'); ap.add_argument('--size', type=int, default=320)
    ap.add_argument('--clips', help='comma-separated clips to show (default: all)')
    a = ap.parse_args()
    root = Path(a.dir)
    e = json.loads((root / 'models.json').read_text())[a.model]
    m = md3read.read(root / e['path'])
    texs = [load_tex(root, s['shaders'][0]) for s in m['surfaces']]
    clips = e['clips'] if not a.clips else {c: e['clips'][c] for c in a.clips.split(',')}
    used = sorted({clips.get('idle', e['clips']['idle'])[0]} | {f for f0, f1, _ in clips.values() for f in range(f0, f1 + 1)})
    allv = np.concatenate([s['verts'][used] for s in m['surfaces']], axis=1)
    ext = max(np.abs(allv[..., :2]).max() * 2, allv[..., 2].max() + e['lift'], SOLDIER * 1.2)
    S = a.size; scale = S * 0.8 / ext; z0 = -e['lift']
    rows = [('idle: front, side (its left), back, three-quarter', [(clips.get('idle', e['clips']['idle'])[0], y) for y in (0, np.pi / 2, np.pi, np.pi / 4)])]
    for c, (f0, f1, fps) in clips.items():
        picks = sorted(set(np.linspace(f0, f1, 4).round().astype(int)))
        rows.append((f'{c}: frames {f0}-{f1} at {fps} fps (side view)', [(f, np.pi / 2) for f in picks]))
    W = S * 4 + 60; H = len(rows) * (S + 24)
    sheet = Image.new('RGB', (W, H), (24, 24, 24)); dr = ImageDraw.Draw(sheet)
    for i, (label, cells) in enumerate(rows):
        oy = i * (S + 24)
        dr.text((6, oy + 5), label, fill=(220, 220, 220))
        for j, (f, yaw) in enumerate(cells):
            im = render(m, texs, f, yaw, S, scale, z0)
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
