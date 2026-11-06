"""Assemble runtime files from pinned public sources, without any game data."""
from pathlib import Path
import json, subprocess, shutil, tarfile, zipfile, gzip, importlib.util, os
from common import ROOT, sha, download, safe_destination
WORK=ROOT/'work';CACHE=WORK/'downloads';OUT=ROOT/'dist/runtime';SRC=WORK/'sources'
for p in [WORK,CACHE,OUT,SRC]:p.mkdir(parents=True,exist_ok=True)
sources=json.loads((ROOT/'runtime/sources.json').read_text())
def run(args,**kw):subprocess.run([str(x) for x in args],check=True,**kw)
def checkout(name):
    url,commit=sources['git'][name];p=SRC/(name+'-'+commit[:12])
    if not p.exists():
        run(['git','clone','--no-checkout',url,p]);run(['git','-C',p,'checkout','--detach',commit]);(p/'.thps4-builder-owned').touch()
    if not (p/'.thps4-builder-owned').is_file():raise RuntimeError('Refusing to alter an unmarked source tree')
    if subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip()!=commit:raise RuntimeError('Source revision mismatch')
    return p

def apply(source,patch):
    test=subprocess.run(['git','-C',str(source),'apply','--reverse','--check',str(patch)],capture_output=True)
    if test.returncode:run(['git','-C',source,'apply',patch])

print('Fetching pinned runtime dependencies',flush=True)
deps=json.loads((ROOT/'runtime/dependencies.json').read_text());groups={}
for item in deps['files']:groups.setdefault(item['artifact'],[]).append(item)
for key,items in groups.items():
    artifact=download(deps['artifacts'][key],CACHE);needed={x['member'].removeprefix('./'):x for x in items};found=set()
    proc=subprocess.Popen(['dpkg-deb','--fsys-tarfile',str(artifact)],stdout=subprocess.PIPE)
    with tarfile.open(fileobj=proc.stdout,mode='r|') as tar:
        for member in tar:
            name=member.name.removeprefix('./')
            if name not in needed:continue
            data=tar.extractfile(member).read();specs=[x for x in items if x['member'].removeprefix('./')==name]
            import hashlib
            for item in specs:
                if hashlib.sha256(data).hexdigest()!=item['sha256']:raise RuntimeError('Dependency content mismatch')
                dest=safe_destination(OUT,item['destination']);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);dest.chmod(0o755);found.add(item['destination'])
    if proc.wait()!=0 or found!={x['destination'] for x in items}:raise RuntimeError('Missing dependency member')

print('Fetching Wine, Westonpack, driver and Direct3D runtime',flush=True)
files={key:download(sources[key],CACHE) for key in ['weston','wine','mali','dxvk']}
shutil.copy(files['weston'],OUT/'weston_pkg_0.2.squashfs')
wine=WORK/'wine-extract'
if not (wine/'wine-8.21-x86/bin/wine').exists():
    wine.mkdir(exist_ok=True)
    with tarfile.open(files['wine'],'r:xz') as archive:
        for member in archive.getmembers(): safe_destination(wine,member.name)
        archive.extractall(wine)
if not (wine/'wine-8.21-x86/bin/wine').is_file():raise RuntimeError('Unexpected Wine archive layout')
image=OUT/'wine-8.21-x86.squashfs'
if not image.exists():run(['mksquashfs',wine/'wine-8.21-x86',image,'-noappend','-comp','gzip','-no-xattrs','-all-root'])
r=OUT/'route-research';r.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('patch_mali',ROOT/'tools/patch-mali.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.patch(files['mali'],r/'libmali-g52-g29p1-armhf-readable-padding.so')
with zipfile.ZipFile(files['dxvk']) as z:
    for dll in ['d3d8.dll','d3d9.dll']:
        member=next(n for n in z.namelist() if n.endswith('/x32/'+dll));dest=r/'dxvk-candidates/pandxvk'/dll;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(member))

print('Preparing pinned Slang shader compiler',flush=True)
slang_archive=download(sources['slang'],CACHE);slang=WORK/'slang'
if not (slang/'bin/slangc').exists():
    slang.mkdir(exist_ok=True)
    with tarfile.open(slang_archive,'r:gz') as archive:
        for member in archive.getmembers(): safe_destination(slang,member.name)
        archive.extractall(slang)
os.environ['PATH']=str(slang/'bin')+os.pathsep+os.environ['PATH']
print('Building ARM components',flush=True)
headers=checkout('headers');box=checkout('box86');wsi=checkout('wsi');bcn=checkout('bcn')
apply(box,ROOT/'patches/box86-native-memmove.patch');apply(wsi,ROOT/'patches/wsi-cached-readback.patch');apply(bcn,ROOT/'patches/bcn-optional-device-fault.patch')
boxbuild=WORK/'build-box86';run(['cmake','-S',box,'-B',boxbuild,'-DCMAKE_SYSTEM_NAME=Linux','-DCMAKE_SYSTEM_PROCESSOR=armhf','-DCMAKE_C_COMPILER=arm-linux-gnueabihf-gcc','-DCMAKE_CXX_COMPILER=arm-linux-gnueabihf-g++','-DARM_DYNAREC=ON','-DARM64=ON','-DCMAKE_BUILD_TYPE=Release']);run(['cmake','--build',boxbuild,'-j4'])
shutil.copy(boxbuild/'box86',r/'box86-native-memmove-private-glibc');run(['patchelf','--set-interpreter','/mnt/SDCARD/Persistent/thps4-lab/route-research/armhf-glibc/usr/lib/arm-linux-gnueabihf/ld-linux-armhf.so.3',r/'box86-native-memmove-private-glibc'])
wbuild=WORK/'build-wsi';common=['-DCMAKE_TOOLCHAIN_FILE='+str(ROOT/'tools/armhf-toolchain.cmake'),'-DCMAKE_BUILD_TYPE=Release']
run(['cmake','-S',wsi,'-B',wbuild,*common,'-DCMAKE_C_FLAGS=-march=armv7-a -mfpu=neon -mfloat-abi=hard -Wno-error=conversion','-DCMAKE_CXX_FLAGS=-march=armv7-a -mfpu=neon -mfloat-abi=hard -Wno-error=conversion','-DVULKAN_CXX_INCLUDE='+str(headers/'include'),'-DBUILD_WSI_DISPLAY=OFF','-DBUILD_WSI_HEADLESS=ON','-DBUILD_WSI_WAYLAND=ON','-DBUILD_WSI_X11=ON','-DENABLE_ARM_NEON=OFF','-DSELECT_EXTERNAL_ALLOCATOR=dma_buf_heaps']);run(['cmake','--build',wbuild,'-j4']);(r/'wsi-armhf-cached-runtime').mkdir(exist_ok=True);shutil.copy(wbuild/'libVkLayer_window_system_integration.so',r/'wsi-armhf-cached-runtime/libVkLayer_window_system_integration.so')
bbuild=WORK/'build-bcn';run(['cmake','-S',bcn,'-B',bbuild,*common,'-DFORCE_GLSL=OFF','-DCMAKE_CXX_FLAGS=-march=armv7-a -mfpu=neon -mfloat-abi=hard -I'+str(headers/'include')]);run(['cmake','--build',bbuild,'-j4']);(r/'bcn-armhf').mkdir(exist_ok=True);shutil.copy(bbuild/'libbcn_layer.so',r/'bcn-armhf/libbcn_layer.so')
run(['aarch64-linux-gnu-gcc','-O2','-Wall','-Wextra','-Werror',ROOT/'tools/display-helper.c','-lX11','-o',r/'display-helper-aarch64'])
for n in ['wine-box86-vulkan-memmove.sh','wineserver-box86-vulkan-memmove.sh']:shutil.copy(ROOT/'runtime'/n,r/n);(r/n).chmod(0o755)
for n in ['fonts.conf','thps4.gptk']:shutil.copy(ROOT/'runtime'/n,OUT/n)
root='/mnt/SDCARD/Persistent/thps4-lab/route-research'
(r/'vendor-g29-armhf-readable-padding-icd.json').write_text(json.dumps({'file_format_version':'1.0.0','ICD':{'library_path':root+'/libmali-g52-g29p1-armhf-readable-padding.so','api_version':'1.3.303'}}))
layers=r/'vulkan-armhf-cached-home/vulkan/implicit_layer.d';layers.mkdir(parents=True,exist_ok=True)
wsi_manifest=json.loads((wbuild/'VkLayer_window_system_integration.json').read_text());wsi_manifest['layer']['library_path']=root+'/wsi-armhf-cached-runtime/libVkLayer_window_system_integration.so';(layers/'VkLayer_window_system_integration.json').write_text(json.dumps(wsi_manifest,indent=2))
bcn_manifest=json.loads((bbuild/'libbcn_layer.json').read_text());bcn_manifest['layer']['library_path']=root+'/bcn-armhf/libbcn_layer.so';(layers/'libbcn_layer.json').write_text(json.dumps(bcn_manifest,indent=2))
empty=WORK/'empty-prefix.img';run(['truncate','-s','512M',empty]);run(['mkfs.ext4','-q','-F','-O','^orphan_file,^metadata_csum_seed',empty])
with empty.open('rb') as src,gzip.open(OUT/'empty-prefix.img.gz','wb',compresslevel=1) as dest:shutil.copyfileobj(src,dest)
shutil.copy(ROOT/'runtime/THPS4.sh',OUT/'THPS4.sh');shutil.copy(ROOT/'runtime/config.cfg',OUT/'config.cfg')
manifest={str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='manifest.json'}
(OUT/'manifest.json').write_text(json.dumps({'schema':1,'project':'bashark211/miyoo-flip-thps4','files':manifest},indent=2)+'\n')
print('Runtime built in dist/runtime. No game, personal prefix or saves included.')
