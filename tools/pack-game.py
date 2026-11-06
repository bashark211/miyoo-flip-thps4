"""Package a user's installed PC Game directory without changing its contents."""
from pathlib import Path
import argparse, shutil, subprocess, tempfile, struct, json, hashlib
from common import sha

def validate_game(folder):
    folder=Path(folder).resolve()
    if any(p.is_symlink() for p in folder.rglob('*')):
        raise ValueError('Resolve symbolic links into a self-contained game directory first')
    entries={p.name.casefold():p for p in folder.iterdir()}
    exe=entries.get('skate4.exe')
    if not exe or not exe.is_file(): raise ValueError('Choose the installed PC Game directory containing Skate4.exe')
    data=exe.read_bytes()
    if len(data)<64 or data[:2]!=b'MZ': raise ValueError('Skate4.exe is not a Windows executable')
    pe=struct.unpack_from('<I',data,60)[0]
    if pe+6>len(data) or data[pe:pe+4]!=b'PE\0\0' or struct.unpack_from('<H',data,pe+4)[0]!=0x14c:
        raise ValueError('Expected the x86/PE32 PC edition')
    if 'data' not in entries or not entries['data'].is_dir(): raise ValueError('The Data directory is missing; an executable alone is not enough')
    return folder, exe

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('game');p.add_argument('--output',required=True);p.add_argument('--include-movies',action='store_true');a=p.parse_args()
    folder,exe=validate_game(a.game);out=Path(a.output).resolve()
    if out.exists(): raise SystemExit('Output already exists; choose a new file')
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='thps4-own-game-') as temp:
        stage=Path(temp)/'Game';subprocess.run(['cp','-a','--reflink=auto','--',str(folder),str(stage)],check=True)
        for child in list(stage.iterdir()):
            name=child.name.casefold()
            omit=name in ['save','config.cfg','d3d8.dll','d3d9.dll'] or (not a.include_movies and name in ['movies','movie'])
            if omit:
                if child.is_dir() and not child.is_symlink(): shutil.rmtree(child)
                else: child.unlink()
        if exe.name!='Skate4.exe': (stage/exe.name).rename(stage/'Skate4.exe')
        (stage/'Save').mkdir(exist_ok=True);(stage/'config.cfg').touch();(stage/'d3d8.dll').touch()
        subprocess.run(['mksquashfs',str(stage),str(out),'-noappend','-comp','xz','-no-xattrs','-all-root'],check=True)
    out.with_suffix(out.suffix+'.manifest.json').write_text(json.dumps({'executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'image_sha256':sha(out),'movies_included':a.include_movies},indent=2)+'\n')
    print('Created',out,'from your local game files; nothing was uploaded')
if __name__=='__main__': main()
