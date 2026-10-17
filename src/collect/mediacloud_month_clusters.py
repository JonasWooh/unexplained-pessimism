"""Two seeded complete days per collection-month; one API worker."""
from month_cluster_common import *
from audit_runtime import worker_lock,retry_fetch
from N03 import TOPICS,LICENSE
from month_cluster_report import make_report
import os
STATE=PROV/'mediacloud_month_cluster_state.json'
QUERY=' OR '.join('('+v+')' for k,v in TOPICS.items() if k!='all')

def initial():
 plan=build_plan();old=json.loads((PROV/'mediacloud_daily_state.json').read_text());index={(d['collection_id'],d['date']):d for d in old['days']};jobs=[]
 for selected in plan['mediacloud']:
  cid,date=selected['source'],selected['date'];d=index[(cid,date)]
  files=[]
  for page in range(d['page']):
   matches=list((ROOT/'corpus/raw/N03').rglob(f'daily_{cid}_{date}_{page:05}.json'))
   if len(matches)!=1:raise ValueError('Ambiguous/missing retained daily page')
   files.append(str(matches[0].relative_to(ROOT)))
  jobs.append(dict(**selected,page=d['page'],token=d['token'],raw_files=files,old_full=d['complete'],complete=d['complete'],rows=0))
 return dict(jobs=jobs,seed=SEED,design=plan['design'],retained_complete_months=plan['retained_mc_complete_months'],status='new')

def main():
 s=json.loads(STATE.read_text()) if STATE.exists() else initial();s.update(status='running',pid=os.getpid());checkpoint(STATE,s)
 headers={'Authorization':'Token '+keys()['mediacloud']}
 # Mark reused full sampled days before making any network requests.
 for d in s['jobs']:
  if d['complete'] and not d.get('selection_file'):
   d['rows'],d['selection_file']=save_day_selection(d['source'],d['date'],d['raw_files'],'mediacloud');checkpoint(STATE,s)
 ordered=sorted(s['jobs'],key=lambda d:([x['date'] for x in s['jobs'] if x['source']==d['source'] and x['month']==d['month']].index(d['date']),d['month'],d['source']))
 for d in ordered:
  while not d['complete']:
   params=dict(start=d['date'],end=d['date'],q=QUERY,platform='onlinenews-mediacloud',cs=d['source'],page_size=1000,sort_order='asc')
   if d['token']:params['pagination_token']=d['token']
   name=f"month_cluster_{d['source']}_{d['date']}_{d['page']:05}.json"
   p=retry_fetch('N03','https://search.mediacloud.org/api/search/story-list',name,params,state=s,state_path=STATE,headers=headers,delay=31,license_note=LICENSE+' User monthly day-cluster design: 2 seeded dates/month, exhaust selected date. Not article-level simple random sample.')
   if not p:
    if s['status']!='needs_user_resolution':s['status']='stopped_api_error'
    s['failed_request']=name;checkpoint(STATE,s);return
   o=json.loads(p.read_bytes())
   if any(i.get('publish_date','')[:10]!=d['date'] for i in o['stories']):s.update(status='needs_user_resolution_date_mismatch');checkpoint(STATE,s);return
   d['raw_files'].append(str(p.relative_to(ROOT)));d['page']+=1;d['token']=o.get('pagination_token');d['complete']=not bool(d['token'])
   if d['complete']:d['rows'],d['selection_file']=save_day_selection(d['source'],d['date'],d['raw_files'],'mediacloud')
   checkpoint(STATE,s)
   if d['complete']:make_report()
 s['status']='complete_monthly_day_clusters';checkpoint(STATE,s)
if __name__=='__main__':
 with worker_lock('mediacloud_api'):
  try:main()
  finally:make_report()
