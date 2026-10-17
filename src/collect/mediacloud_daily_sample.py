"""Daily official random samples with a 50% target capped at 1,000 stories.

Fully collected days use a seeded local selection index. Other days use the
allowed official sample endpoint exactly once, not denied randomized pagination.
"""
from common import *
from audit_runtime import worker_lock,checkpoint,retry_fetch
from N03 import TOPICS,LICENSE
from daily_sample_rules import SEED,day_ranks
import random,math,os
STATE=PROV/'mediacloud_sampling_state.json'
QUERY=' OR '.join('('+v+')' for k,v in TOPICS.items() if k!='all')
ALLOWED={'id','indexed_date','language','media_name','media_url','publish_date','title','url'}

def initial():
 old=json.loads((PROV/'mediacloud_daily_state.json').read_text());jobs=[]
 for d in old['days']:
  jobs.append(dict(collection_id=d['collection_id'],date=d['date'],old_full_day=d['complete'],full_pages=d['page'] if d['complete'] else 0,status='pending',target=None,rows=0))
 jobs.sort(key=lambda d:(day_ranks(d['date'][:7])[int(d['date'][8:])],0 if d['date']>='2025-07-01' else 1,d['date'][:7],d['collection_id']))
 stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S');backup=PROV/('mediacloud_full_state_before_sampling_'+stamp+'.json')
 with backup.open('x') as f:json.dump(old,f,indent=2)
 old.update(status='superseded_by_daily_random_sampling',sampling_state=str(STATE.relative_to(ROOT)));checkpoint(PROV/'mediacloud_daily_state.json',old)
 return dict(jobs=jobs,stamp=stamp,baseline_state=str(backup.relative_to(ROOT)),count_files={},design='every collection-date; ceil(50% of latest count snapshot), capped at 1000; official server random sample or seeded SRS from verified complete raw day',seed_for_local_selection=SEED,server_seed='not exposed by allowed sample endpoint; exact returned IDs and bytes are retained')

def main():
 s=json.loads(STATE.read_text()) if STATE.exists() else initial();s.update(status='running',pid=os.getpid());checkpoint(STATE,s)
 headers={'Authorization':'Token '+keys()['mediacloud']}
 counts={}
 for cid in ['34412234','38379429']:
  if cid not in s['count_files']:
   params=dict(start='2025-01-01',end=CUTOFF,q=QUERY,platform='onlinenews-mediacloud',cs=cid)
   name=f"sampling_counts_{cid}_{s['stamp']}.json"
   p=retry_fetch('N03','https://search.mediacloud.org/api/search/count-over-time',name,params,state=s,state_path=STATE,headers=headers,delay=31,license_note=LICENSE+' Fresh daily counts for sample-size planning; no replacement of original counts.')
   if not p:
    if s['status']!='needs_user_resolution':s['status']='stopped_api_error'
    checkpoint(STATE,s);return
   s['count_files'][cid]=str(p.relative_to(ROOT));checkpoint(STATE,s)
  for d in json.loads((ROOT/s['count_files'][cid]).read_bytes())['count_over_time']['counts']:counts[(cid,d['date'])]=d['count']
 # Reuse complete raw dates first; this makes no additional API requests.
 ordered=sorted(s['jobs'],key=lambda d:(not d['old_full_day'],day_ranks(d['date'][:7])[int(d['date'][8:])],0 if d['date']>='2025-07-01' else 1,d['date'][:7],d['collection_id']))
 for d in ordered:
  if d['status']!='pending':continue
  cid,date=d['collection_id'],d['date'];n=counts.get((cid,date))
  if n is None:s.update(status='needs_user_resolution_missing_count',date=date,collection_id=cid);checkpoint(STATE,s);return
  d['count_snapshot']=n;target=min(1000,math.ceil(n*.5));d['target']=target
  if d['old_full_day']:
   items={};raw=[]
   for p in (ROOT/'corpus/raw/N03').rglob(f'daily_{cid}_{date}_*.json'):
    raw.append(str(p.relative_to(ROOT)))
    for item in json.loads(p.read_bytes())['stories']:items[str(item['id'])]=item
   target=min(1000,math.ceil(len(items)*.5));d['target']=target;ids=random.Random(f'{SEED}|{cid}|{date}').sample(sorted(items),target)
   method='seeded_simple_random_selection_from_complete_raw_day';d['actual_population']=len(items)
  else:
   # A zero in the count snapshot is still checked once; new source records can appear.
   params=dict(start=date,end=date,q=QUERY,platform='onlinenews-mediacloud',cs=cid,limit=max(1,target),fields=','.join(sorted(ALLOWED)))
   name=f'daily_random_sample_{cid}_{date}_limit{max(1,target)}.json'
   p=retry_fetch('N03','https://search.mediacloud.org/api/search/sample',name,params,state=s,state_path=STATE,headers=headers,delay=31,license_note=LICENSE+' User-selected daily random sample: approx 50%, max 1000; not a complete day. Server random seed not exposed.')
   if not p:
    if s['status']!='needs_user_resolution':s['status']='stopped_api_error'
    d['failed_request']=name;checkpoint(STATE,s);return
   data=json.loads(p.read_bytes())['sample']
   if any(set(i)-ALLOWED or i.get('publish_date','')[:10]!=date for i in data):s.update(status='needs_user_resolution_schema_or_date');checkpoint(STATE,s);return
   ids=list(dict.fromkeys(str(i['id']) for i in data));raw=[str(p.relative_to(ROOT))];method='official_server_random_sample_seed_unavailable'
  selection=PROV/'sampling_selections'/f'mc_{cid}_{date}.json';selection.parent.mkdir(exist_ok=True)
  if not selection.exists():
   with selection.open('x') as f:json.dump(dict(source=cid,date=date,method=method,target=d['target'],selected_ids=ids,raw_files=raw),f,indent=2)
  d.update(status='draw_complete',rows=len(ids),method=method,selection_file=str(selection.relative_to(ROOT)),target_met=len(ids)>=d['target'],observed_fraction=len(ids)/d.get('actual_population',n) if d.get('actual_population',n)>0 else None)
  checkpoint(STATE,s)
 s['status']='complete_daily_sample_queries';checkpoint(STATE,s)
if __name__=='__main__':
 with worker_lock('mediacloud_api'):main()
