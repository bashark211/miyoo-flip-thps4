"""Make the tested G29 ARMhf ELF padding readable; no instruction patching."""
from pathlib import Path
import hashlib, struct, sys
ORIGINAL='6c7ac4257032ade760091164d4957b248ebcd64dd1ef4ac4b51a8985333f504c'
PATCHED='3cae0890b096fd667fb00ab4532379e9e56c45ad2ebdd2d02ba5d7a273f290d0'
def patch(source, output):
    data=bytearray(Path(source).read_bytes())
    if hashlib.sha256(data).hexdigest()!=ORIGINAL:
        raise ValueError('Expected the pinned, unmodified G52 G29 ARMhf driver')
    ph=struct.unpack_from('<I',data,28)[0]
    size,count=struct.unpack_from('<HH',data,42)
    changed=0
    for i in range(count):
        at=ph+i*size; p=struct.unpack_from('<8I',data,at)
        if p[0]==1 and p[1]==0 and p[6]==5:
            assert p[4]==p[5]==0x25b7384
            struct.pack_into('<II',data,at+16,0x25c7000,0x25c7000); changed+=1
    assert changed==1 and hashlib.sha256(data).hexdigest()==PATCHED
    Path(output).write_bytes(data)
if __name__=='__main__':
    if len(sys.argv)!=3: raise SystemExit('usage: patch-mali.py INPUT OUTPUT')
    patch(*sys.argv[1:])
