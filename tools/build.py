from pathlib import Path
import shutil, subprocess, platform
from common import ROOT
if platform.machine().lower() not in ('x86_64','amd64'):
    raise SystemExit('This pinned build uses an x86_64 Linux Slang compiler; use an x86_64 Linux build host')
engine=shutil.which('podman') or shutil.which('docker')
if not engine: raise SystemExit('Install Podman or Docker first')
subprocess.run([engine,'build','-t','miyoo-flip-thps4-builder','-f',str(ROOT/'tools/Containerfile'),str(ROOT)],check=True)
subprocess.run([engine,'run','--rm','-v',str(ROOT)+':/project:Z','miyoo-flip-thps4-builder'],check=True)
