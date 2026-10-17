"""Finish seeded half-day clusters on every planned date, preserving full raw data."""
from common import *
from audit_runtime import worker_lock,checkpoint,retry_fetch
from reddit_posts import SELECT,LICENSE,ENDPOINT,boundary,priority
from daily_sample_rules import SEED,FRACTION,intersect_pending,interval_priority
import os
STATE=PROV/'reddit_sampling_state.json'

def initial():
 base=PROV/'reddit_collection_state.json';old=json.loads(base.read_text())
 backup=PROV/('reddit_full_state_before_sampling_'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S')+'.json')
 with backup.open('x') as f:json.dump(old,f,indent=2)
 subs={}
 for sub,v in old['subreddits'].items():
  pending=intersect_pending(sub,v['pending']);pending.sort(key=lambda x:interval_priority(sub,x))
  subs[sub]=dict(pending=pending,leaf_files=[],probe_files=[],new_rows=0,status='pending' if pending else 'selected_windows_already_covered')
 old.update(status='superseded_by_daily_halfday_sampling',sampling_state=str(STATE.relative_to(ROOT)));checkpoint(base,old)
 return dict(subreddits=subs,seed=SEED,selection_probability=FRACTION,design='independent seeded 00-12 or 12-24 UTC cluster each planned date; exhaust selected windows; old raw responses filtered by same temporal predicate only in selection index',baseline_state=str(backup.relative_to(ROOT)),personalfinance_sampling=old.get('personalfinance_sampling'),monthly_count_files=old.get('monthly_count_files',{}))

def main():
 s=json.loads(STATE.read_text()) if STATE.exists() else initial();s.update(status='running',pid=os.getpid());checkpoint(STATE,s)
 while any(v['pending'] for v in s['subreddits'].values()):
  sub,v=min(((sub,v) for sub,v in s['subreddits'].items() if v['pending']),key=lambda pair:interval_priority(pair[0],pair[1]['pending'][0]))
  lo,hi,month=v['pending'][0];params=dict(subreddit=sub,after=boundary(lo),before=boundary(hi),limit=100,sort='asc',fields=SELECT)
  name=f'sample_posts_{sub}_{lo}_{hi}.json'
  p=retry_fetch('SM02',ENDPOINT,name,params,state=s,state_path=STATE,delay=3,license_note=LICENSE+' Seeded 50% temporal cluster: random half-day, selected interval exhausted. Not first-100 sampling.')
  if not p:
   if s['status']!='needs_user_resolution':s['status']='stopped_api_error'
   s['failed_request']=name;checkpoint(STATE,s);return
  o=json.loads(p.read_bytes());items=o['data']
  if any(set(item)-set(SELECT.split(',')) or not isinstance(item.get('created_utc'),int) or not lo<=item['created_utc']<hi for item in items):raise ValueError('Unexpected fields or interval semantics')
  rel=str(p.relative_to(ROOT));v['pending'].pop(0)
  if len(items)>=100:
   if hi-lo<=1:s.update(status='needs_user_resolution_saturated_second',failed_request=name);checkpoint(STATE,s);return
   mid=(lo+hi)//2;v['pending'][:0]=[[lo,mid,month],[mid,hi,month]];v['probe_files'].append(rel)
  else:v['leaf_files'].append(rel);v['new_rows']+=len(items)
  if not v['pending']:v['status']='complete_selected_windows'
  checkpoint(STATE,s)
 s['status']='complete_current_core_daily_samples' if s.get('scope')=='core_economy_Economics_2017_2024_daily_halfday' else 'complete_selected_halfday_queries';checkpoint(STATE,s)
if __name__=='__main__':
 with worker_lock('arctic_shift_api'):main()
