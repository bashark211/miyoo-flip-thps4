"""Pinned public-source downloads and content verification."""
from pathlib import Path
import hashlib, urllib.request, shutil, time
ROOT = Path(__file__).resolve().parents[1]
def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()
def download(spec, cache):
    cache = Path(cache); cache.mkdir(parents=True, exist_ok=True)
    dest = cache / spec['filename']
    if dest.is_file() and sha(dest) == spec['sha256']:
        return dest
    errors = []
    for url in spec['urls']:
        for attempt in range(2):
            tmp = dest.with_name(dest.name + '.partial')
            try:
                req = urllib.request.Request(url, headers={'User-Agent':'miyoo-flip-thps4-source-builder/1'})
                with urllib.request.urlopen(req, timeout=90) as src, tmp.open('wb') as out:
                    shutil.copyfileobj(src, out)
                if sha(tmp) != spec['sha256']:
                    raise ValueError('SHA256 mismatch for ' + spec['filename'])
                tmp.replace(dest); return dest
            except Exception as exc:
                errors.append(str(exc)); tmp.unlink(missing_ok=True); time.sleep(attempt + 1)
    raise RuntimeError('Download failed: ' + spec['filename'] + ': ' + '; '.join(errors))
def safe_destination(root, relative):
    p = Path(relative)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError('Unsafe output path: ' + relative)
    target = Path(root) / p
    if not target.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError('Output escapes target directory')
    return target
