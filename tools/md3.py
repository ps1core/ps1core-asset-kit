"""MD3 writer for DarkPlaces: smooth per-vertex normals, several surfaces (one shader each), vertex-animated frames.

Positions are stored as int16 * 1/64 unit (range +-512). Normals use the Quake 3 lat/long byte encoding.
A surface: dict(name, shader, verts (F, V, 3) float, normals (F, V, 3) or None, uv (V, 2), tris (T, 3) int).
"""
import struct
import numpy as np


def vertex_normals(verts, tris):
    """Area-weighted smooth normals, (V, 3), for one frame."""
    v = np.asarray(verts, float)
    a, b, c = v[tris[:, 0]], v[tris[:, 1]], v[tris[:, 2]]
    fn = np.cross(b - a, c - a)
    n = np.zeros_like(v)
    for k in range(3): np.add.at(n, tris[:, k], fn)
    l = np.linalg.norm(n, axis=1, keepdims=True); l[l == 0] = 1
    return n / l


def encode_normals(n):
    n = np.asarray(n, float)
    n = n / np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-9)
    lat = np.round(np.arctan2(n[..., 1], n[..., 0]) * 256 / (2 * np.pi)).astype(int) & 255
    lng = np.round(np.arccos(np.clip(n[..., 2], -1, 1)) * 256 / (2 * np.pi)).astype(int) & 255
    return (lat << 8 | lng).astype(np.uint16)


def write(path, surfaces, frame_names=None, flags=0, name='model'):
    F = surfaces[0]['verts'].shape[0]
    frame_names = frame_names or [f'f{i}' for i in range(F)]
    allv = np.concatenate([s['verts'] for s in surfaces], axis=1)            # (F, Vtot, 3)
    assert np.abs(allv).max() < 511, f'{path}: model exceeds +-511 units'
    hdr_size, frame_size = 108, 56
    ofs_frames = hdr_size
    ofs_surfaces = ofs_frames + frame_size * F
    blobs = []
    for s in surfaces:
        V, T = s['verts'].shape[1], len(s['tris'])
        assert s['verts'].shape[0] == F
        normals = s.get('normals')
        if normals is None: normals = np.stack([vertex_normals(s['verts'][f], s['tris']) for f in range(F)])
        sh = 108
        ofs_shaders = sh; ofs_tris = ofs_shaders + 68; ofs_st = ofs_tris + 12 * T
        ofs_xyz = ofs_st + 8 * V; ofs_end = ofs_xyz + 8 * V * F
        b = bytearray(struct.pack('<4s64siiiiiiiiii', b'IDP3', s['name'].encode()[:63], 0, F, 1, V, T,
                                  ofs_tris, ofs_shaders, ofs_st, ofs_xyz, ofs_end))
        b += struct.pack('<64si', s['shader'].encode()[:63], 0)
        b += np.asarray(s['tris'], '<i4').tobytes()
        b += np.asarray(s['uv'], '<f4').tobytes()
        xyz = np.round(np.asarray(s['verts']) * 64).astype('<i2')            # (F, V, 3)
        enc = encode_normals(normals).astype('<u2')                          # (F, V)
        rec = np.zeros((F, V, 4), '<i2'); rec[..., :3] = xyz; rec[..., 3] = enc.view('<i2')
        b += rec.tobytes()
        assert len(b) == ofs_end
        blobs.append(bytes(b))
    ofs_eof = ofs_surfaces + sum(len(b) for b in blobs)
    out = bytearray(struct.pack('<4si64siiiiiiiii', b'IDP3', 15, name.encode()[:63], flags, F, 0, len(surfaces), 0,
                                ofs_frames, ofs_surfaces, ofs_surfaces, ofs_eof))
    for f in range(F):
        v = allv[f]; lo, hi = v.min(0), v.max(0)
        out += struct.pack('<3f3f3ff16s', *lo, *hi, 0, 0, 0, float(np.linalg.norm(v, axis=1).max()),
                           frame_names[f].encode()[:15])
    for b in blobs: out += b
    assert len(out) == ofs_eof
    open(path, 'wb').write(out)
    return dict(frames=F, verts=int(allv.shape[1]), tris=int(sum(len(s['tris']) for s in surfaces)), bytes=len(out))
