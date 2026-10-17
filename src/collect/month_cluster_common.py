"""Fixed-seed calendar-day cluster designs and exact interval reuse."""
from common import *
from audit_runtime import checkpoint
import calendar,random,bisect
SEED=20261015
PLAN=PROV/'monthly_cluster_plan.json'

def months(lo,hi):
 y,m=map(int,lo.split('-'))
 while f'{y:04}-{m:02}'<=hi:
  yield f'{y:04}-{m:02}';y,m=(y+1,1) if m==12 else (y,m+1)

def day_bounds(date):
 lo=int(dt.datetime.fromisoformat(date).replace(tzinfo=dt.timezone.utc).timestamp());return lo,lo+86400

def build_plan():
 if PLAN.exists():return json.loads(PLAN.read_text())
 plan=dict(seed=SEED,cutoff=CUTOFF,design='calendar-day cluster sampling; complete selected days; not article/post-level simple random sampling',rng='Independent Python random.Random(20261015) per source; months ascending; sample days without replacement then sort',mediacloud=[],reddit=[])
 for cid,start in [('34412234','2025-09'),('38379429','2025-03')]:
  rng=random.Random(SEED)
  for month in months(start,'2026-09'):
   y,m=map(int,month.split('-'));chosen=sorted(rng.sample(range(1,calendar.monthrange(y,m)[1]+1),2))
   for day in chosen:plan['mediacloud'].append(dict(source=cid,month=month,date=f'{month}-{day:02}'))
 for sub,start,end in [('economy','2015-01','2024-12'),('Economics','2015-01','2024-12'),('personalfinance','2010-01',CUTOFF[:7])]:
  rng=random.Random(SEED)
  for month in months(start,end):
   y,m=map(int,month.split('-'));last=min(calendar.monthrange(y,m)[1],int(CUTOFF[8:])) if month==CUTOFF[:7] else calendar.monthrange(y,m)[1]
   for day in sorted(rng.sample(range(1,last+1),3)):plan['reddit'].append(dict(source=sub,month=month,date=f'{month}-{day:02}'))
 plan['retained_mc_complete_months']={'34412234':list(months('2025-01','2025-08')),'38379429':['2025-01','2025-02']}
 plan['retained_mc_partial_month']='2026-10 through 2026-10-14'
 with PLAN.open('x') as f:json.dump(plan,f,indent=2)
 return plan

def file_interval(rel):
 m=re.search(r'_(\d+)_(\d+)\.json$',Path(rel).name)
 if not m:raise ValueError('Missing interval in registered leaf filename')
 return int(m[1]),int(m[2])

def baseline_reddit():
 sources={s:[] for s in ['economy','Economics','personalfinance','inflation']}
 for name in ['reddit_collection_state.json','reddit_sampling_state.json']:
  state=json.loads((PROV/name).read_text())
  for sub,v in state['subreddits'].items():sources[sub].extend(v.get('leaf_files',[]))
 result={}
 for sub,files in sources.items():
  records=sorted((*file_interval(rel),rel) for rel in set(files));merged=[]
  for lo,hi,_ in records:
   if merged and lo<=merged[-1][1]:merged[-1][1]=max(merged[-1][1],hi)
   else:merged.append([lo,hi])
  result[sub]=dict(records=records,merged=merged,starts=[x[0] for x in merged])
 return result

def missing_parts(lo,hi,index):
 cursor=lo;parts=[]
 i=max(0,bisect.bisect_right(index['starts'],lo)-1)
 for a,b in index['merged'][i:]:
  if a>=hi:break
  if b<=cursor:continue
  if a>cursor:parts.append([cursor,min(a,hi)])
  cursor=max(cursor,b)
  if cursor>=hi:break
 if cursor<hi:parts.append([cursor,hi])
 return parts

def overlapping_files(lo,hi,index):return [rel for a,b,rel in index['records'] if a<hi and b>lo]

def save_day_selection(source,date,files,kind):
 lo,hi=day_bounds(date);items={}
 for rel in dict.fromkeys(files):
  o=json.loads((ROOT/rel).read_bytes());data=o.get('stories',o.get('data',[]))
  for item in data:
   inside=item.get('publish_date','')[:10]==date if kind=='mediacloud' else lo<=item['created_utc']<hi
   if inside:items[str(item['id'])]=item
 path=PROV/'monthly_cluster_selections'/f'{kind}_{source}_{date}.json';path.parent.mkdir(exist_ok=True)
 value=dict(source=source,date=date,design='complete selected UTC day; fixed-seed day cluster',raw_files=list(dict.fromkeys(files)),unique_ids=sorted(items),rows=len(items))
 if path.exists():
  old=json.loads(path.read_text())
  if old!=value:raise ValueError('Completed selection manifest changed unexpectedly')
 else:
  with path.open('x') as f:json.dump(value,f,indent=2)
 return len(items),str(path.relative_to(ROOT))
