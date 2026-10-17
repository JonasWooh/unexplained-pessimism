"""Three seeded complete UTC dates/month, with retained interval reuse."""
from month_cluster_common import *
from audit_runtime import worker_lock,retry_fetch
from reddit_posts import SELECT,LICENSE,ENDPOINT,boundary
from month_cluster_report import make_report
from personalfinance_windows import interval_index,prepare_window,save_window_selection
import os
STATE=PROV/'reddit_month_cluster_state.json'

def initial():
 plan=build_plan();base=baseline_reddit();jobs=[]
 for selected in plan['reddit']:
  sub,date=selected['source'],selected['date'];lo,hi=day_bounds(date);missing=missing_parts(lo,hi,base[sub])
  jobs.append(dict(**selected,pending=missing,raw_files=overlapping_files(lo,hi,base[sub]),old_full=not missing,complete=not missing,rows=0))
 return dict(jobs=jobs,seed=SEED,design=plan['design'],monthly_counts={},status='new')

def order(d):
 phase=0 if d['source']=='personalfinance' and '2026-08-05'<=d['date']<=CUTOFF else 1 if d.get('window_pilot') or d.get('reuse_inventory_priority') else 2 if d['source']!='personalfinance' and '2017-01'<=d['month']<='2024-12' else 3 if d['source']!='personalfinance' else 4
 return phase,d['month'],d['source'],d['date']

def month_interval(month):
 y,m=map(int,month.split('-'));end=dt.date(y+1,1,1) if m==12 else dt.date(y,m+1,1)
 end=min(end,dt.date.fromisoformat(CUTOFF)+dt.timedelta(days=1))
 return int(dt.datetime(y,m,1,tzinfo=dt.timezone.utc).timestamp()),int(dt.datetime.combine(end,dt.time(),dt.timezone.utc).timestamp())

def create_weekly_count_plan(s,sub,month,trigger):
 key=sub+'_'+month
 if key in s.setdefault('count_partition_plans',{}):return
 lo,hi=month_interval(month)
 s['count_partition_plans'][key]=dict(start_utc=lo,end_utc=hi,intervals=[[a,min(a+7*86400,hi)] for a in range(lo,hi,7*86400)],completed_parts={},complete=False,trigger=trigger,authorized_by='User-approved uniform rule: exhausted full-month timeout -> exact weekly counts; stop if a weekly interval also exhausts retries')
 s.update(status='running');s.pop('retry',None);s.pop('failed_request',None);checkpoint(STATE,s)
 print('Collecting exact weekly count partitions:',key,flush=True)

def partitioned_month_count(s,sub,month):
 """Add exact aggregate counts over a saved, disjoint partition of a month."""
 key=sub+'_'+month;plan=s['count_partition_plans'][key]
 intervals=plan['intervals']
 if month_interval(month)!=(plan['start_utc'],plan['end_utc']):raise ValueError('Monthly partition bounds differ from source month/cutoff')
 if not intervals or intervals[0][0]!=plan['start_utc'] or intervals[-1][1]!=plan['end_utc']:
  raise ValueError('Monthly count partition does not cover its declared month')
 if any(a>=b for a,b in intervals) or any(a[1]!=b[0] for a,b in zip(intervals,intervals[1:])):
  raise ValueError('Monthly count partition has overlap or a gap')
 parts=plan.setdefault('completed_parts',{})
 for lo,hi in intervals:
  part_key=f'{lo}_{hi}'
  if part_key in parts:continue
  params=dict(subreddit=sub,after=boundary(lo),before=boundary(hi),aggregate='subreddit',limit='')
  p=retry_fetch('SM02',ENDPOINT+'/aggregate',f'cluster_count_part_{sub}_{month}_{lo}_{hi}.json',params,state=s,state_path=STATE,delay=3,license_note=LICENSE+' Exact monthly denominator partition: disjoint UTC intervals covering the whole month; sum only after every interval succeeds.')
  if not p:
   if s['status']!='needs_user_resolution':s['status']='stopped_api_error'
   s['failed_request']=key+' aggregate partition '+part_key;checkpoint(STATE,s);return False
  data=json.loads(p.read_bytes())['data']
  if any(set(row)-{'key','count'} or str(row.get('key','')).casefold()!=sub.casefold() or not str(row.get('count','')).isdigit() for row in data):
   s.update(status='needs_user_resolution_aggregate_schema',failed_request=key+' aggregate partition '+part_key);checkpoint(STATE,s);return False
  parts[part_key]=dict(start_utc=lo,end_utc=hi,file=str(p.relative_to(ROOT)),count=sum(int(row['count']) for row in data));checkpoint(STATE,s)
 ordered=[parts[f'{lo}_{hi}'] for lo,hi in intervals]
 value=dict(source=sub,month=month,start_utc=plan['start_utc'],end_utc=plan['end_utc'],method='sum of exhaustive aggregate counts over disjoint UTC intervals covering the full month',parts=ordered,count=sum(part['count'] for part in ordered),note='Source count snapshots retrieved sequentially, not an atomic source snapshot; no sampled-day extrapolation.')
 path=PROV/'monthly_count_partitions'/f'{key}.json';path.parent.mkdir(exist_ok=True)
 if path.exists():
  if json.loads(path.read_text())!=value:raise ValueError('Completed monthly count partition manifest changed')
 else:
  with path.open('x') as f:json.dump(value,f,indent=2)
 s['monthly_counts'][key]=dict(count=value['count'],method=value['method'],files=[part['file'] for part in ordered],manifest=str(path.relative_to(ROOT)))
 plan['complete']=True;checkpoint(STATE,s);return True

def main():
 s=json.loads(STATE.read_text()) if STATE.exists() else initial();s.update(status='running',pid=os.getpid());s.pop('failed_request',None);s.pop('retry',None);checkpoint(STATE,s)
 reuse_index=interval_index(s.get('personalfinance_window_design',{}).get('reuse_leaf_files',[]))
 for d in s['jobs']:
  if d['complete'] and not d.get('selection_file'):
   d['rows'],d['selection_file']=save_window_selection(d) if d.get('sample_unit')=='circular_time_window' else save_day_selection(d['source'],d['date'],d['raw_files'],'reddit');checkpoint(STATE,s)
 for d in sorted(s['jobs'],key=order):
  sub,month=d['source'],d['month'];key=sub+'_'+month
  if key not in s['monthly_counts'] and key in s.get('count_partition_plans',{}):
   if not partitioned_month_count(s,sub,month):return
  if key not in s['monthly_counts']:
   existing=sorted((ROOT/'corpus/raw/SM02').rglob(f'counts_v3_{sub}_{month}.json'))
   if existing:p=existing[-1]
   else:
    lo,hi=month_interval(month)
    params=dict(subreddit=sub,after=boundary(lo),before=boundary(hi),aggregate='subreddit',limit='')
    p=retry_fetch('SM02','https://arctic-shift.photon-reddit.com/api/posts/search/aggregate',f'cluster_month_count_{sub}_{month}.json',params,state=s,state_path=STATE,delay=3,license_note=LICENSE+' Full-month archive post count denominator; independent of sampled dates.')
    if not p:
     retry=s.get('retry',{})
     automatic=s.get('monthly_count_timeout_policy',{}).get('full_month_timeout_action')=='exact_weekly_partition'
     exhausted_timeout=s['status']=='needs_user_resolution' and retry.get('failed_attempts')==5 and retry.get('error') in ['ReadTimeout','ConnectTimeout','Timeout',422,504]
     if automatic and exhausted_timeout:
      create_weekly_count_plan(s,sub,month,dict(failed_at_utc=s.get('updated_at_utc'),full_month_retry=dict(retry)))
      if not partitioned_month_count(s,sub,month):return
     else:
      if s['status']!='needs_user_resolution':s['status']='stopped_api_error'
      s['failed_request']=key+' aggregate';checkpoint(STATE,s);return
   if p:
    data=json.loads(p.read_bytes())['data'];s['monthly_counts'][key]=dict(file=str(p.relative_to(ROOT)),count=sum(int(r['count']) for r in data));checkpoint(STATE,s)
  if d.get('sample_unit')=='circular_time_window' and not d.get('window_prepared'):
   prepare_window(s,d,reuse_index);checkpoint(STATE,s)
   if d['complete']:make_report()
  while d['pending']:
   lo,hi=d['pending'][0];params=dict(subreddit=sub,after=boundary(lo),before=boundary(hi),limit=100,sort='asc',fields=SELECT)
   window=d.get('sample_unit')=='circular_time_window'
   name=f'cluster_posts_window_{sub}_{lo}_{hi}.json' if window else f'cluster_posts_{sub}_{lo}_{hi}.json'
   scope=' Three seeded dates/month and uniform circular time window per date; expected 150 records/month, exhaust selected windows, not full dates.' if window else ' Three seeded calendar dates/month; complete selected UTC day.'
   p=retry_fetch('SM02',ENDPOINT,name,params,state=s,state_path=STATE,delay=3,license_note=LICENSE+scope+' Exhaustive interval splitting; retrieved_on preserved; author fields excluded.')
   if not p:
    if s['status']!='needs_user_resolution':s['status']='stopped_api_error'
    s['failed_request']=name;checkpoint(STATE,s);return
   items=json.loads(p.read_bytes())['data']
   if any(set(i)-set(SELECT.split(',')) or not isinstance(i.get('created_utc'),int) or not lo<=i['created_utc']<hi for i in items):s.update(status='needs_user_resolution_schema_or_interval');checkpoint(STATE,s);return
   d['pending'].pop(0)
   if len(items)>=100:
    if hi-lo<=1:s.update(status='needs_user_resolution_saturated_second');checkpoint(STATE,s);return
    mid=(lo+hi)//2;d['pending'][:0]=[[lo,mid],[mid,hi]]
   else:d['raw_files'].append(str(p.relative_to(ROOT)))
   if not d['pending']:
    d['complete']=True;d['rows'],d['selection_file']=save_window_selection(d) if window else save_day_selection(sub,d['date'],d['raw_files'],'reddit')
   checkpoint(STATE,s)
   if d['complete']:make_report()
 s['status']='complete_monthly_sampling' if 'personalfinance_window_design' in s else 'complete_monthly_day_clusters';checkpoint(STATE,s)
if __name__=='__main__':
 with worker_lock('arctic_shift_api'):
  try:main()
  finally:make_report()
