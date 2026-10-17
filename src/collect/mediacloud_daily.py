"""Exhaustive per-publication-day queries, breadth-first across the window.

Existing broad-window responses remain immutable. New daily responses overlap
those files and must be deduplicated by story ID for any later use.
"""
from common import *
from N03 import TOPICS,LICENSE
import os,collections
from audit_runtime import retry_fetch,worker_lock
STATE=PROV/'mediacloud_daily_state.json'

def save(s):
 s['updated_at_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
 tmp=STATE.with_suffix('.tmp');tmp.write_text(json.dumps(s,indent=2));tmp.replace(STATE)

def main():
 if STATE.exists():s=json.loads(STATE.read_text())
 else:
  seen=collections.defaultdict(set)
  for p in (ROOT/'corpus/raw/N03').rglob('*_stories_*.json'):
   cid=p.name.split('_')[0]
   for item in json.loads(p.read_bytes()).get('stories',[]):
    seen[(cid,item.get('publish_date','')[:10])].add(str(item['id']))
  days=[];date=dt.date(2025,1,1)
  while date.isoformat()<=CUTOFF:
   for cid in ['38379429','34412234']:
    days.append(dict(collection_id=cid,date=date.isoformat(),page=0,token=None,rows=0,complete=False,existing_unique_rows=len(seen[(cid,date.isoformat())])))
   date+=dt.timedelta(days=1)
  s=dict(days=days)
 s.update(status='running',pid=os.getpid(),scheduling='full day pagination; 2026-10-14 descending to 2025-07-01, then older; old incomplete days nonrandom');save(s)
 hdr={'Authorization':'Token '+keys()['mediacloud']}
 query=' OR '.join('('+v+')' for k,v in TOPICS.items() if k!='all')
 while any(not d['complete'] for d in s['days']):
  d=min((d for d in s['days'] if not d['complete']),key=lambda d:(0 if d['date']>='2025-07-01' else 1,-dt.date.fromisoformat(d['date']).toordinal(),d['collection_id']))
  params=dict(start=d['date'],end=d['date'],q=query,platform='onlinenews-mediacloud',cs=d['collection_id'],page_size=1000,sort_order='asc')
  if d['token']:params['pagination_token']=d['token']
  name=f"daily_{d['collection_id']}_{d['date']}_{d['page']:05}.json"
  p=retry_fetch('N03','https://search.mediacloud.org/api/search/story-list',name,params,state=s,state_path=STATE,headers=hdr,delay=31,license_note=LICENSE+' Daily exhaustive query; overlaps earlier broad-window files; do not sum raw batches.')
  if not p:s.update(status=s['status'] if s['status']=='needs_user_resolution' else 'stopped_api_error',failed_request=name);save(s);return
  o=json.loads(p.read_bytes())
  if any(x.get('publish_date','')[:10]!=d['date'] for x in o['stories']):
   s.update(status='stopped_date_boundary_mismatch',failed_request=name);save(s);return
  d['rows']+=len(o['stories']);d['page']+=1;d['token']=o.get('pagination_token');d['complete']=not bool(d['token']);save(s)
 s['status']='complete_daily_queries';save(s)

if __name__=='__main__':
 with worker_lock('mediacloud_api'):main()
