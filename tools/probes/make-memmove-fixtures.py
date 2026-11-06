"""Regenerate Wine-derived test fixtures from the reviewable bridge patch."""
from pathlib import Path
import re,hashlib
root=Path(__file__).resolve().parents[2]
text=(root/'patches/box86-native-memmove.patch').read_text()
body=re.search(r'signature\[\] = \{(.*?)\};',text,re.S).group(1)
data=bytes(int(x,16) for x in re.findall(r'0x([0-9a-f]{2})',body))
assert hashlib.sha256(data).hexdigest()=='4e5ab519a3b8e7246513fbec4a72a0f719a75526ab502c7a626cce0e9259028d'
output=root/'work/memmove-probes';output.mkdir(parents=True,exist_ok=True)
(output/'wine821-sse2-memmove.bin').write_bytes(data)
negative=bytearray(data)
for a,b in [(0,1),(218,219),(492,493)]:negative[a],negative[b]=negative[b],negative[a]
(output/'wine821-sse2-memmove-negative.bin').write_bytes(negative)
print(output)
