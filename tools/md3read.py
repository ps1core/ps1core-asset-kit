"""Read an MD3 back into numpy arrays (for check.py and preview.py). The inverse of md3.write."""
import struct
import numpy as np


def read(path):
    b = open(path, 'rb').read()
    ident, ver, name, flags, F, ntags, S, nskins, ofs_frames, ofs_tags, ofs_surf, ofs_eof = struct.unpack_from('<4si64siiiiiiiii', b)
    if ident != b'IDP3' or ver != 15:
        raise ValueError(f'{path}: not an MD3 (ident {ident!r}, version {ver})')
    frames = []
    for f in range(F):
        v = struct.unpack_from('<3f3f3ff16s', b, ofs_frames + 56 * f)
        frames.append(dict(lo=v[0:3], hi=v[3:6], radius=v[9], name=v[10].split(b'\0')[0].decode('latin-1')))
    surfaces, o = [], ofs_surf
    for _ in range(S):
        (sid, sname, sflags, sF, nsh, V, T, ofs_tris, ofs_sh, ofs_st, ofs_xyz, ofs_end) = struct.unpack_from('<4s64siiiiiiiiii', b, o)
        shaders = [struct.unpack_from('<64si', b, o + ofs_sh + 68 * i)[0].split(b'\0')[0].decode('latin-1') for i in range(nsh)]
        tris = np.frombuffer(b, '<i4', T * 3, o + ofs_tris).reshape(T, 3)
        uv = np.frombuffer(b, '<f4', V * 2, o + ofs_st).reshape(V, 2)
        rec = np.frombuffer(b, '<i2', sF * V * 4, o + ofs_xyz).reshape(sF, V, 4)
        enc = rec[..., 3].view('<u2').astype(int)
        lat, lng = (enc >> 8 & 255) * 2 * np.pi / 256, (enc & 255) * 2 * np.pi / 256
        normals = np.stack([np.cos(lat) * np.sin(lng), np.sin(lat) * np.sin(lng), np.cos(lng)], -1)
        surfaces.append(dict(name=sname.split(b'\0')[0].decode('latin-1'), shaders=shaders, frames=sF,
                             verts=rec[..., :3].astype(float) / 64.0, normals=normals, tris=tris, uv=uv))
        o += ofs_end
    return dict(name=name.split(b'\0')[0].decode('latin-1'), frames=frames, surfaces=surfaces, bytes=len(b), eof_ok=ofs_eof == len(b))
