"""Extra ALFRED pulls for the research stage (DECISIONS 2026-10-16T18:20Z).

M18 (D-C): CPIAUCSL and PAYEMS, all vintages, observations from 2006-01, for factual calibration of
  numeric claims about inflation and payrolls.
M19 (D-A and pce_cum36): UNRATE, PCEPI and GDPC1, all vintages, observations from 1976-01. The original
  M01-M03 pulls start observations in 2008, which is too short for 36-month cumulative inflation in
  2010-2011 and for the 2000-09 and 1978 estimation windows.
Same request pattern as macro.py; files land in data/raw/M18|M19/<day>/. Run from the project root:
  python3 src/collect/alfred_extra.py
"""
from common import *
from macro import LICENSE

PULLS={'M18':(['CPIAUCSL','PAYEMS'],'2006-01-01'),'M19':(['UNRATE','PCEPI','GDPC1'],'1976-01-01')}

def collect(ds):
 sids,obs_start=PULLS[ds]
 for sid in sids:
  base={'series_id':sid,'file_type':'json'}
  fetch(ds,'https://api.stlouisfed.org/fred/series',sid+'_metadata.json',base,key='fred',license_note=LICENSE)
  for endpoint,field in [('observations','observations'),('vintagedates','vintage_dates')]:
   offset=0
   while True:
    p=dict(base,realtime_start='1776-07-04',realtime_end=CUTOFF,limit=100000 if endpoint=='observations' else 10000,offset=offset)
    if endpoint=='observations':p.update(observation_start=obs_start,observation_end=CUTOFF,output_type=1)
    path=fetch(ds,'https://api.stlouisfed.org/fred/series/'+endpoint,f'{sid}_{endpoint}_{offset:07}.json',p,key='fred',license_note=LICENSE)
    if not path:raise SystemExit(f'{ds} {sid} {endpoint}: request failed, see provenance/requests.jsonl')
    obj=json.loads(path.read_bytes())
    if field not in obj:raise SystemExit(f'{ds} {sid}: invalid response')
    offset+=len(obj[field])
    if offset>=int(obj['count']):break
    if not obj[field]:raise ValueError('Empty pagination page before count reached')
  print(ds,sid,'ok',flush=True)

if __name__=='__main__':
 for ds in PULLS:collect(ds)
 print('done')
