"""Collection-only sample counts, source denominators and selected-window completion."""
from common import *
from daily_sample_rules import halfday
from collections import defaultdict,Counter
import calendar,math

def dates():
 d=dt.date(2010,1,1)
 while d.isoformat()<=CUTOFF:
  yield d.isoformat();d+=dt.timedelta(days=1)

def main():
 rows=[];rs=json.loads((PROV/'reddit_sampling_state.json').read_text());mc=json.loads((PROV/'mediacloud_sampling_state.json').read_text());samples=rs.get('personalfinance_sampling',{}).get('selected_days',{})
 def eligible_date(sub,date):return sub!='personalfinance' or date[:7]>='2025-01' or int(date[8:]) in samples.get(date[:7],[])
 # Exact ID dedup; raw probes and full responses are retained but never summed.
 selected=defaultdict(dict)
 for p in sorted((ROOT/'corpus/raw/SM02').rglob('*.json'),key=lambda p:p.stat().st_mtime):
  if not p.name.startswith(('posts_','probe_','sample_posts_')):continue
  for x in json.loads(p.read_bytes()).get('data',[]):
   if not isinstance(x.get('created_utc'),int):continue
   date=dt.datetime.fromtimestamp(x['created_utc'],dt.timezone.utc).date().isoformat();sub={k.casefold():k for k in rs['subreddits']}.get(x['subreddit'].casefold(),x['subreddit'])
   if not '2010-01-01'<=date<=CUTOFF or not eligible_date(sub,date):continue
   lo,hi=halfday(sub,date)
   if lo<=x['created_utc']<hi:selected[sub][x['id']]=(date,x.get('selftext',''),x.get('retrieved_on'))
 quality=[]
 for sub,v in rs['subreddits'].items():
  planned=Counter(date[:7] for date in dates() if eligible_date(sub,date));unfinished=defaultdict(set)
  for lo,hi,month in v['pending']+v.get('deferred_pending',[]):unfinished[month].add(dt.datetime.fromtimestamp(lo,dt.timezone.utc).date().isoformat())
  bymonth=defaultdict(list)
  for x in selected[sub].values():bymonth[x[0][:7]].append(x)
  for month,days in sorted(planned.items()):
   a=bymonth[month];n=len(a);original='';path=ROOT/'corpus/raw/SM02'
   files=list(path.rglob(f'counts_v3_{sub}_{month}.json'))
   if files:original=sum(int(b['count']) for b in json.loads(sorted(files)[-1].read_bytes())['data'])
   probability=.5 if sub!='personalfinance' or month>='2025-01' else .5*3/calendar.monthrange(*map(int,month.split('-')))[1]
   completed=days-len(unfinished[month]);removed=sum(x[1].strip().casefold()=='[removed]' for x in a);deleted=sum(x[1].strip().casefold()=='[deleted]' for x in a)
   rows.append(dict(source='Reddit/'+sub,month=month,selected_unique_records=n,source_query_count=original,observed_retained_fraction=n/original if isinstance(original,int) and original>0 else '',expected_inclusion_probability=probability,sample_target_records='',planned_dates=days,completed_sample_dates=completed,sample_plan_completion=completed/days,method='seeded half-day cluster; pre2025 personalfinance additionally 3 random dates/month',notes='Complete means selected windows exhausted, not whole day. retrieved_on retained; archive score/comment-count snapshots are not comparable across years.'))
   quality.append(dict(source=sub,month=month,selected_unique=n,removed=removed,deleted=deleted,removed_deleted_ratio=(removed+deleted)/n if n else '',missing_retrieved_on=sum(x[2] is None for x in a)))
 countmap={}
 for cid,rel in mc.get('count_files',{}).items():
  countmap[cid]={d['date']:d['count'] for d in json.loads((ROOT/rel).read_bytes())['count_over_time']['counts']}
 mg=defaultdict(list)
 for d in mc['jobs']:mg[(d['collection_id'],d['date'][:7])].append(d)
 for (cid,month),jobs in sorted(mg.items()):
  original=sum(countmap.get(cid,{}).get(d['date'],0) for d in jobs) if cid in countmap else ''
  target=sum(d['target'] if d.get('target') is not None else min(1000,math.ceil(countmap[cid].get(d['date'],0)*.5)) for d in jobs) if cid in countmap else ''
  complete=sum(d['status']=='draw_complete' for d in jobs);n=sum(d['rows'] for d in jobs)
  rows.append(dict(source='MediaCloud/'+cid,month=month,selected_unique_records=n,source_query_count=original,observed_retained_fraction=n/original if isinstance(original,int) and original>0 else '',expected_inclusion_probability='daily min(ceil(N/2),1000)/N; server random seed not exposed',sample_target_records=target,planned_dates=len(jobs),completed_sample_dates=complete,sample_plan_completion=complete/len(jobs),method='official daily random sample; seeded SRS for already complete raw days',notes='Every date planned. Not complete days; high-volume dates retain less than 50%. Existing nonrandom partial days excluded from local sample frame. Count snapshots may change.'))
 for r in rows:
  core_scope=rs.get('scope')=='core_economy_Economics_2017_2024_daily_halfday'
  r['scope_status']='active' if not core_scope or r['source'].startswith('MediaCloud/') or r['source'] in ['Reddit/economy','Reddit/Economics'] and '2017-01'<=r['month']<='2024-12' else 'already_available' if r['source']=='Reddit/inflation' else 'deferred_previous_scope'
 for name,records in [('sampling_monthly_status.csv',rows),('reddit_sample_monthly_content_availability.csv',quality)]:
  path=PROV/name;tmp=path.with_suffix('.tmp')
  with tmp.open('w',newline='') as f:
   w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
  tmp.replace(path)
 # Keep the common report's original raw-data rows and add explicit sample scopes.
 common=PROV/'source_month_completeness.csv'
 if common.exists():
  with common.open() as f:
   reader=csv.DictReader(f);fields=reader.fieldnames;old=[r for r in reader if not r['source'].startswith(('MediaCloudSample/','RedditSample/'))]
  for r in rows:
   x=dict.fromkeys(fields,'');x.update(source=r['source'].replace('MediaCloud/','MediaCloudSample/').replace('Reddit/','RedditSample/'),month=r['month'],obtained_unique=r['selected_unique_records'],eligible_unique=r['selected_unique_records'],retrieved_in_count_scope=r['selected_unique_records'],query_count=r['sample_target_records'],completeness_ratio=r['selected_unique_records']/r['sample_target_records'] if isinstance(r['sample_target_records'],int) and r['sample_target_records']>0 else '',count_scope=r['method']+'; selected sample target, not full population',complete_units=r['completed_sample_dates'],planned_units=r['planned_dates'],notes=r['notes']+' See sampling_monthly_status.csv for population count and sampling fraction.');old.append(x)
  tmp=common.with_suffix('.tmp')
  with tmp.open('w',newline='') as f:
   w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(old)
  tmp.replace(common)
 summary=dict(as_of_utc=dt.datetime.now(dt.timezone.utc).isoformat(),sources={})
 for source in sorted({r['source'] for r in rows}):
  a=[r for r in rows if r['source']==source];summary['sources'][source]=dict(selected_unique=sum(r['selected_unique_records'] for r in a),planned_dates=sum(r['planned_dates'] for r in a),completed_sample_dates=sum(r['completed_sample_dates'] for r in a))
 if rs.get('scope')=='core_economy_Economics_2017_2024_daily_halfday':
  a=[r for r in rows if r['source'] in ['Reddit/economy','Reddit/Economics'] and r['scope_status']=='active']
  summary['reddit_current_core_scope']=dict(planned_dates=sum(r['planned_dates'] for r in a),completed_sample_dates=sum(r['completed_sample_dates'] for r in a),selected_unique=sum(r['selected_unique_records'] for r in a),deferred_intervals=sum(len(v.get('deferred_pending',[])) for v in rs['subreddits'].values()))
 (PROV/'sampling_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
