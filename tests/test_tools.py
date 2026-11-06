"""Host checks for packaging isolation and safe, repeatable SD installation."""
import importlib.util, sys, tempfile, unittest, json, struct, gzip, subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from common import sha, safe_destination
ROOT=Path(__file__).resolve().parents[1]
def module(name):
    s=importlib.util.spec_from_file_location(name,ROOT/'tools'/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
installer=module('install');packer=module('pack-game')
class Tools(unittest.TestCase):
    def test_pack_preserves_source_and_omits_personal_data(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);game=p/'Game';(game/'Data').mkdir(parents=True);(game/'Data/level.dat').write_bytes(b'asset')
            exe=bytearray(128);exe[:2]=b'MZ';struct.pack_into('<I',exe,60,64);exe[64:68]=b'PE\0\0';struct.pack_into('<H',exe,68,0x14c);(game/'skate4.exe').write_bytes(exe)
            (game/'Save').mkdir();(game/'Save/private').write_text('personal');(game/'config.cfg').write_text('personal config');(game/'d3d9.dll').write_text('old override')
            image=p/'game.squashfs';subprocess.run([sys.executable,str(ROOT/'tools/pack-game.py'),str(game),'--output',str(image)],check=True,stdout=subprocess.DEVNULL)
            extracted=p/'extracted';subprocess.run(['unsquashfs','-d',str(extracted),str(image)],check=True,stdout=subprocess.DEVNULL)
            self.assertEqual((game/'Save/private').read_text(),'personal');self.assertTrue((extracted/'Skate4.exe').is_file());self.assertFalse((extracted/'Save/private').exists());self.assertEqual((extracted/'config.cfg').stat().st_size,0);self.assertFalse((extracted/'d3d9.dll').exists());self.assertEqual((extracted/'Data/level.dat').read_bytes(),b'asset')
            (game/'escape').symlink_to('/etc/passwd')
            with self.assertRaises(ValueError):packer.validate_game(game)
    def test_install_preserves_state_and_rejects_corruption(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);sd=p/'sd';(sd/'spruce/flip').mkdir(parents=True);(sd/'Roms/ports').mkdir(parents=True);runtime=p/'runtime';runtime.mkdir()
            for name in ['THPS4.sh','config.cfg','weston_pkg_0.2.squashfs','wine-8.21-x86.squashfs']:(runtime/name).write_bytes(b'runtime')
            with gzip.open(runtime/'empty-prefix.img.gz','wb',compresslevel=1) as f:
                for _ in range(512):f.write(bytes(1048576))
            manifest={'schema':1,'project':installer.PROJECT,'files':{x.name:sha(x) for x in runtime.iterdir()}};(runtime/'manifest.json').write_text(json.dumps(manifest))
            image=p/'game';header=bytearray(96);header[:4]=b'hsqs';struct.pack_into('<H',header,20,4);image.write_bytes(header)
            installer.install(sd,runtime,image);prefix=sd/'Persistent/thps4-lab/wine-prefix-opt.img'
            with prefix.open('r+b') as f:f.write(b'personal prefix')
            save=sd/'Roms/ports/thps4/saves/career';save.write_bytes(b'career');config=sd/'Roms/ports/thps4/config.cfg';config.write_bytes(b'custom')
            installer.install(sd,runtime,image)
            with prefix.open('rb') as f:self.assertEqual(f.read(15),b'personal prefix')
            self.assertEqual(save.read_bytes(),b'career');self.assertEqual(config.read_bytes(),b'custom')
            (runtime/'THPS4.sh').write_bytes(b'corrupted')
            with self.assertRaises(ValueError):installer.install(sd,runtime,image)
    def test_path_escape(self):
        for path in ['/tmp/out','../out','a/../../out']:
            with self.assertRaises(ValueError):safe_destination('/tmp/runtime',path)
if __name__=='__main__':unittest.main()
