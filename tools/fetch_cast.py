#!/usr/bin/env python3
"""Download the 1942 cast's models (the package the site renders with), check its SHA-256, and unpack the models into
cast/1942/ (ignored by git). Standard library only. About 800 MB, cached in ~/.cache/ps1core-assets.

  tools/fetch_cast.py

These models carry the site's 1942 terms (free films only): read SPEC.md, Rights, before you base anything on them.
"""
import hashlib, json, os, shutil, sys, tarfile, urllib.request
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
LOCK = KIT / 'reference/1942-package.lock.json'
OUT = KIT / 'cast/1942'
CACHE = Path(os.environ.get('PS1_ASSET_CACHE', Path.home() / '.cache/ps1core-assets'))


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def main():
    lock = json.loads(LOCK.read_text())
    CACHE.mkdir(parents=True, exist_ok=True)
    pkg = CACHE / lock['name']
    if not pkg.exists() or sha256(pkg) != lock['sha256']:
        print(f'downloading {lock["url"]} ({lock["bytes"] / 1e6:.0f} MB)')
        tmp = pkg.with_suffix(f'.{os.getpid()}.tmp')
        with urllib.request.urlopen(lock['url'], timeout=300) as r, open(tmp, 'wb') as f: shutil.copyfileobj(r, f, 1 << 20)
        if sha256(tmp) != lock['sha256']:
            tmp.unlink(); sys.exit('checksum mismatch: not unpacked')
        os.replace(tmp, pkg)
    OUT.mkdir(parents=True, exist_ok=True)
    n = 0
    with tarfile.open(pkg) as t:
        for m in t.getmembers():
            p = Path(m.name)
            if m.name.startswith('/') or '..' in p.parts or not (m.isfile() or m.isdir()): sys.exit(f'bad path in package: {m.name}')
            if m.isfile() and p.parts[:2] == ('progs', '1942'):
                dst = OUT / p.name
                with t.extractfile(m) as src, open(dst, 'wb') as f: shutil.copyfileobj(src, f)
                n += 1
    print(f'{n} files in {OUT}')


if __name__ == '__main__':
    main()
