"""Install onto an offline Spruce SD card, preserving saves and Wine state."""
from pathlib import Path
import argparse, json, gzip, shutil, tempfile, os, struct
from common import ROOT, sha, safe_destination
PROJECT='bashark211/miyoo-flip-thps4'

def validate_runtime(folder):
    folder=Path(folder).resolve();m=json.loads((folder/'manifest.json').read_text())
    if m.get('project')!=PROJECT or m.get('schema')!=1:raise ValueError('Unrecognized runtime manifest')
    for name,want in m['files'].items():
        p=safe_destination(folder,name)
        if not p.is_file() or sha(p)!=want:raise ValueError('Runtime file failed verification: '+name)
    for name in ['THPS4.sh','config.cfg','empty-prefix.img.gz','weston_pkg_0.2.squashfs','wine-8.21-x86.squashfs']:
        if name not in m['files']:raise ValueError('Missing required runtime file: '+name)
    return folder,m

def validate_image(image):
    image=Path(image).resolve()
    with image.open('rb') as f:header=f.read(96)
    if len(header)!=96 or header[:4]!=b'hsqs' or struct.unpack_from('<H',header,20)[0] not in (1,4):raise ValueError('Expected a gzip/XZ SquashFS game image from pack-game.py')
    return image

def atomic_copy(source,destination):
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.thps4-install-',dir=destination.parent);os.close(fd)
    try:shutil.copy(source,name);os.replace(name,destination)
    finally:Path(name).unlink(missing_ok=True)

def install(sd,runtime,game):
    sd=Path(sd).resolve();runtime,m=validate_runtime(runtime);game=validate_image(game)
    if not (sd/'spruce/flip').is_dir() or not (sd/'Roms/ports').is_dir():raise ValueError('Choose the mounted Spruce SD root, not a laptop system directory')
    lab=safe_destination(sd,'Persistent/thps4-lab');marker=lab/'runtime-manifest.json';image=lab/'thps4-complete-xz.squashfs'
    if lab.exists() and any(lab.iterdir()) and not marker.exists():raise ValueError('Existing experiment runtime found. Back it up and move it aside before a fresh install')
    if image.exists() and sha(image)!=sha(game):raise ValueError('A different game image already exists. Move it aside before installing another game build')
    lab.mkdir(parents=True,exist_ok=True)
    for name in m['files']:
        if name in ['THPS4.sh','config.cfg','empty-prefix.img.gz']:continue
        dest=safe_destination(lab,name)
        if not dest.is_file() or sha(dest)!=m['files'][name]:atomic_copy(runtime/name,dest)
    prefix=lab/'wine-prefix-opt.img'
    if not prefix.exists():
        fd,temp=tempfile.mkstemp(prefix='.prefix-install-',dir=lab);os.close(fd)
        try:
            total=0
            with gzip.open(runtime/'empty-prefix.img.gz','rb') as src,open(temp,'wb') as out:
                while chunk:=src.read(1048576):
                    total+=len(chunk)
                    if total>536870912:raise ValueError('Prefix template exceeds 512MiB')
                    out.write(chunk)
            if total!=536870912:raise ValueError('Invalid empty prefix template')
            os.replace(temp,prefix)
        finally:Path(temp).unlink(missing_ok=True)
    port=safe_destination(sd,'Roms/ports/thps4');(port/'saves').mkdir(parents=True,exist_ok=True)
    if not (port/'config.cfg').exists():atomic_copy(runtime/'config.cfg',port/'config.cfg')
    if not image.exists():atomic_copy(game,image)
    atomic_copy(runtime/'THPS4.sh',sd/'Roms/ports/THPS4.sh');(sd/'Roms/ports/THPS4.sh').chmod(0o755)
    atomic_copy(runtime/'manifest.json',marker)
    print('Installed one THPS4 entry. Existing saves, config and prefix were preserved.')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--sd-root',required=True);p.add_argument('--runtime',default=str(ROOT/'dist/runtime'));p.add_argument('--game-image',required=True);a=p.parse_args();install(a.sd_root,a.runtime,a.game_image)
if __name__=='__main__':main()
