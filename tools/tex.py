"""Texture helpers: float arrays (H, W, C) in 0..1 -> PNG (DarkPlaces loads <name>.png replacements through libpng)."""
import numpy as np
from PIL import Image


def save(path, a, mode=None):
    a = np.clip(np.asarray(a, float), 0, 1)
    if a.ndim == 2: a = a[..., None]
    c = a.shape[2]
    img = (a * 255 + 0.5).astype(np.uint8)
    if c == 1: img = img[..., 0]
    path = path[:-4] + '.png' if path.endswith('.tga') else path
    Image.fromarray(img, mode or {1: 'L', 3: 'RGB', 4: 'RGBA'}[c]).save(path, compress_level=6)


def normal_from_height(h, strength=4.0, wrap=True):
    """Height (H, W) 0..1 -> DarkPlaces _norm texture (RGB normal, A height for offset mapping)."""
    if wrap:
        dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
        dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5
    else:
        dy, dx = np.gradient(h)
    n = np.stack([-dx * strength, dy * strength, np.ones_like(h)], -1)   # +y up in texture space: image rows go down
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return np.concatenate([n * 0.5 + 0.5, h[..., None]], -1)


def fbm(shape, octaves=5, seed=0, base=4, wrap=True):
    """Tileable fractal value noise in 0..1."""
    rng = np.random.default_rng(seed)
    H, W = shape
    out = np.zeros(shape); amp, tot = 1.0, 0.0
    for o in range(octaves):
        n = base * 2 ** o
        g = rng.random((n, n))
        ys = np.linspace(0, n, H, endpoint=False); xs = np.linspace(0, n, W, endpoint=False)
        y0 = np.floor(ys).astype(int); x0 = np.floor(xs).astype(int)
        fy = (ys - y0)[:, None]; fx = (xs - x0)[None, :]
        fy = fy * fy * (3 - 2 * fy); fx = fx * fx * (3 - 2 * fx)
        y1, x1 = (y0 + 1) % n, (x0 + 1) % n
        a = g[y0][:, x0]; b = g[y0][:, x1]; c = g[y1][:, x0]; d = g[y1][:, x1]
        out += amp * (a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy)
        tot += amp; amp *= 0.5
    return out / tot
