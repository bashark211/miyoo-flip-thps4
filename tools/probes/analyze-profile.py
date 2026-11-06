#!/usr/bin/env python3
import json,re,bisect,collections,base64,sys
from pathlib import Path
p=Path(sys.argv[1]);before=json.loads((p/'before/box86-map.json').read_text());after=json.loads((p/'after/box86-map.json').read_text())
after_by={b['native_start']:b for b in after['blocks']}
blocks=sorted(before['blocks'],key=lambda x:x['native_start']);starts=[b['native_start'] for b in blocks]
def mapsparse(s):
 out=[]
 for l in s.splitlines():
  f=l.split(None,5);a,b=map(lambda t:int(t,16),f[0].split('-'));out.append((a,b,f[5] if len(f)>5 else '[anonymous]',int(f[2],16)))
 return sorted(out)
maps=mapsparse(before['maps']);mstarts=[x[0] for x in maps]
def module(addr):
 i=bisect.bisect_right(mstarts,addr)-1
 if i>=0 and addr<maps[i][1]:return maps[i][2]
 return '[unmapped]'
def instguest(b,ip):
 t=base64.b64decode(b['inst_sizes_b64']);i=0;g=b['guest_start'];n=b['native_start']
 while i<len(t):
  x=0;arm=0
  while i<len(t):
   v=t[i];i+=1;x+=v&15;arm+=(v>>4)*4
   if v&15!=15 and v>>4!=15:break
  if n<=ip<n+arm:return g
  n+=arm;g+=x
  if i==len(t) or t[i]==0:break
 return None
counts=collections.Counter();threads=collections.Counter();tm=collections.Counter();hot=collections.Counter();unstable=0;unresolved=0;n=0
file=p/'samples-weighted.txt';weighted=file.exists()
if not weighted:file=p/'samples.txt'
for line in file.read_text().splitlines():
 r=re.match(r'\s*(\d+)/(\d+)\s+([\d.]+):\s+(?:(\d+)\s+)?([0-9a-f]+)\s+(.*?)\s+\((.*)\)$',line)
 if not r:raise ValueError(line)
 pid,tid,t,period,ip,sym,dso=r.groups();ip=int(ip,16);w=int(period) if period else 1;n+=1
 i=bisect.bisect_right(starts,ip)-1;b=blocks[i] if i>=0 and ip<blocks[i]['native_end'] else None
 if b:
  aft=after_by.get(b['native_start'])
  stable=aft and (aft['native_end'],aft['guest_start'],aft['guest_end'],aft['inst_sizes_b64'])==(b['native_end'],b['guest_start'],b['guest_end'],b['inst_sizes_b64'])
  if stable:
   guest=instguest(b,ip)
   if guest is None:unresolved+=1
   name=module(guest if guest is not None else b['guest_start']);label='translated:'+Path(name).name
   if guest is not None:hot[(label,guest&~63)]+=w
   else:hot[(label+':block_only',b['guest_start'])]+=w
  else:label='translated:unstable_mapping';unstable+=1
 else:label='native:'+Path(module(ip)).name;hot[(label,ip&~63)]+=w
 counts[label]+=w;threads[tid]+=w;tm[(tid,label)]+=w
s=sum(counts.values())
rows=lambda c:[{'name':str(k),'percent':round(v/s*100,3),'weight':v} for k,v in c.most_common()]
report={'samples':n,'weight_unit':'task-clock period nanoseconds' if weighted else 'samples','total_weight':s,'unstable_samples':unstable,'unresolved_guest_samples':unresolved,'modules':rows(counts),'threads':rows(threads),'thread_modules':rows(tm),'hot_64byte_ranges':rows(hot)[:80]}
(p/'attribution.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['hot_64byte_ranges','thread_modules']},indent=2));print('TOP_RANGES',json.dumps(report['hot_64byte_ranges'][:15],indent=2))
