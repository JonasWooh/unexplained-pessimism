from common import *

SERIES={'M01':['UNRATE'],'M02':['PCEPI'],'M03':['GDPC1'],'M04':['A191RL1Q225SBEA'],'M05':['PCEPILFE'],'M06':['U6RATE'],'M07':['DSPIC96','A229RX0'],'M08':['GASREGW'],'M09':['CPIUFDSL','CUSR0000SAF11'],'M10':['MORTGAGE30US'],'M11':['TDSP'],'M12':['USEPUINDXM'],'M14':['PCEC96'],'M15':['CSUSHPISA'],'M16':['SP500']}
LICENSE='FRED API terms; source-specific third-party restrictions apply; retain attribution, no redistribution pending license review.'

def collect(ds):
 for sid in SERIES[ds]:
  base={'series_id':sid,'file_type':'json'}
  fetch(ds,'https://api.stlouisfed.org/fred/series',sid+'_metadata.json',base,key='fred',license_note=LICENSE)
  for endpoint,field in [('observations','observations'),('vintagedates','vintage_dates')]:
   offset=0
   while True:
    p=dict(base,realtime_start='1776-07-04',realtime_end=CUTOFF,limit=100000 if endpoint=='observations' else 10000,offset=offset)
    if endpoint=='observations':p.update(observation_start='2008-01-01',observation_end=CUTOFF,output_type=1)
    path=fetch(ds,'https://api.stlouisfed.org/fred/series/'+endpoint,f'{sid}_{endpoint}_{offset:07}.json',p,key='fred',license_note=LICENSE)
    if not path:break
    obj=json.loads(path.read_bytes())
    if field not in obj:print(ds,sid,'INVALID RESPONSE',flush=True);break
    offset+=len(obj[field])
    if offset>=int(obj['count']):break
    if not obj[field]:raise ValueError('Empty pagination page before count reached')
  fetch(ds,'https://fred.stlouisfed.org/graph/fredgraph.csv',sid+'_latest.csv',{'id':sid},license_note=LICENSE)

if __name__=='__main__':
 import sys
 for ds in (sys.argv[1:] or SERIES):collect(ds)
