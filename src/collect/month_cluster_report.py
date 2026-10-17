"""Monthly collection inventory for the fixed calendar-day cluster design."""
from month_cluster_common import *
from collections import defaultdict
import math,os

def retained_baseline():
 path=PROV/'monthly_cluster_retained_baseline_v2.json'
 if path.exists():return json.loads(path.read_text())
 base=baseline_reddit();result={}
 for sub,index in base.items():
  if sub=='inflation':continue
  start='2010-01-01';end=CUTOFF
  complete={};date=dt.date.fromisoformat(start)
  while date.isoformat()<=end:
   value=date.isoformat();lo,hi=day_bounds(value)
   if not missing_parts(lo,hi,index):complete[value]=set()
   date+=dt.timedelta(days=1)
  for _,_,rel in index['records']:
   for x in json.loads((ROOT/rel).read_bytes()).get('data',[]):
    date=dt.datetime.fromtimestamp(x['created_utc'],dt.timezone.utc).date().isoformat()
    if date in complete:complete[date].add(str(x['id']))
  result[sub]={date:len(ids) for date,ids in complete.items()}
 result['mediacloud']={}
 old=json.loads((PROV/'mediacloud_daily_state.json').read_text())
 for d in old['days']:
  if not d['complete']:continue
  cid,date=d['collection_id'],d['date'];ids=set()
  for page in range(d['page']):
   paths=list((ROOT/'corpus/raw/N03').rglob(f'daily_{cid}_{date}_{page:05}.json'))
   if len(paths)!=1:raise ValueError('Retained complete day has missing/ambiguous page')
   ids.update(str(x['id']) for x in json.loads(paths[0].read_bytes())['stories'] if x['publish_date'][:10]==date)
  result['mediacloud'].setdefault(cid,{})[date]=len(ids)
 with (PROV/'source_month_completeness.csv').open() as f:
  result['mc_month_inventory']={r['source']+'|'+r['month']:int(r['obtained_unique']) for r in csv.DictReader(f) if r['source'].startswith('MediaCloud/')}
 with path.open('x') as f:json.dump(result,f,indent=2)
 return result

def write_csv(path,rows):
 tmp=path.with_name(path.name+f'.{os.getpid()}.tmp')
 with tmp.open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
 tmp.replace(path)

def make_report():
 with (PROV/'monthly_cluster_report.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  return report_locked()

def report_locked():
 plan=build_plan();base=retained_baseline();rows=[]
 states={kind:json.loads((PROV/(kind+'_month_cluster_state.json')).read_text()) for kind in ['mediacloud','reddit']}
 oldmc=json.loads((PROV/'mediacloud_sampling_state.json').read_text())
 counts={cid:{x['date']:x['count'] for x in json.loads((ROOT/rel).read_bytes())['count_over_time']['counts']} for cid,rel in oldmc['count_files'].items()}
 groups=defaultdict(list)
 for kind,state in states.items():
  for d in state['jobs']:groups[(kind,d['source'],d['month'])].append(d)
 for cid,dates in counts.items():
  for month in plan['retained_mc_complete_months'][cid]+[CUTOFF[:7]]:groups.setdefault(('mediacloud',cid,month),[])
 for source in ['economy','Economics','personalfinance']:
  for month in {date[:7] for date in base[source]}:groups.setdefault(('reddit',source,month),[])
 # Full-month Reddit count responses may already exist before this worker reaches a stratum.
 reddit_counts={}
 for path in (ROOT/'corpus/raw/SM02').rglob('counts_v3_*.json'):
  key=path.stem.removeprefix('counts_v3_');reddit_counts[key]=sum(int(x['count']) for x in json.loads(path.read_bytes())['data'])
 reddit_counts.update({k:v['count'] for k,v in states['reddit']['monthly_counts'].items()})
 for (kind,source,month),jobs in sorted(groups.items()):
  complete=[d for d in jobs if d['complete']];selected={d['date'] for d in jobs}
  window=kind=='reddit' and source=='personalfinance' and 'personalfinance_window_design' in states['reddit']
  retained=base['mediacloud'].get(source,{}) if kind=='mediacloud' else base[source]
  if window:retained={**retained,**states['reddit']['personalfinance_window_design']['retained_full_day_inventory']}
  extra={date:n for date,n in retained.items() if date[:7]==month and date not in selected}
  full_inventory={date:n for date,n in retained.items() if date[:7]==month}
  n=sum(d['rows'] for d in complete);denominator='';count_days='';retained_month='';inventory=''
  if kind=='mediacloud':
   available={date:n for date,n in counts[source].items() if date[:7]==month}
   denominator=sum(available.values());count_days=len(available)
   if month in plan['retained_mc_complete_months'][source]:retained_month='complete_pagination_per_prior_audit'
   elif month==CUTOFF[:7]:retained_month='partial_calendar_month_through_cutoff'
   inventory=base['mc_month_inventory'].get('MediaCloud/'+source+'|'+month,'')
  else:denominator=reddit_counts.get(source+'_'+month,'')
  count_method=states['reddit']['monthly_counts'].get(source+'_'+month,{}).get('method','monthly aggregate') if kind=='reddit' else 'sum of existing daily query counts'
  rows.append(dict(source=('MediaCloud/' if kind=='mediacloud' else 'Reddit/')+source,month=month,
   sample_unit='circular_time_window' if window else 'UTC_full_day',planned_sample_dates=len(jobs),completed_sample_dates=len(complete),
   planned_sample_days=0 if window else len(jobs),completed_sample_days=0 if window else len(complete),sample_days_reused=0 if window else sum(d['old_full'] for d in complete),
   sample_days_newly_completed=0 if window else sum(not d['old_full'] for d in complete),
   planned_sample_windows=len(jobs) if window else 0,completed_sample_windows=len(complete) if window else 0,
   sample_windows_reused=sum(d['old_full'] for d in complete) if window else 0,sample_windows_newly_completed=sum(not d['old_full'] for d in complete) if window else 0,sample_unique_records=n,
   sample_plan_completion=len(complete)/len(jobs) if jobs else '',selected_dates=';'.join(sorted(selected)),
   completed_dates=';'.join(d['date'] for d in sorted(complete,key=lambda d:d['date'])),
   retained_other_full_days=len(extra),retained_other_full_day_records=sum(extra.values()),retained_month_status=retained_month,
   retained_full_days_including_selected_dates=len(full_inventory),retained_full_day_records_including_selected_dates=sum(full_inventory.values()),
   retained_prior_month_inventory_records=inventory,source_query_count=denominator,count_snapshot_days=count_days,
   observed_sample_fraction=n/denominator if isinstance(denominator,int) and denominator>0 else '',
   target_expected_monthly_records=states['reddit']['personalfinance_window_design']['target_expected_records_per_month'] if window and jobs else '',
   window_length_seconds=next((d['window_length_seconds'] for d in jobs if d.get('window_prepared')),'') if window else '',
   marginal_inclusion_probability=next((d['inclusion_probability'] for d in jobs if d.get('window_prepared')),'') if window else '',
   selected_time_intervals=json.dumps({d['date']:d['selected_intervals'] for d in jobs if d.get('window_prepared')}) if window else '',
   method='three seeded dates; uniform circular window per date sized by actual monthly count; target expected 150; exhaust windows, not full dates' if window else 'fixed seed 20261015; uniform UTC calendar-day cluster; exhaust selected dates' if jobs else 'retained prior collection',
   route='Media Cloud story-list pagination; daily count snapshots' if kind=='mediacloud' else 'Arctic Shift exhaustive timestamp interval splitting; monthly aggregate',
   notes='Not a story/post-level simple random sample. Extra retained dates are separate from the random draw. Sample fraction is not full-month collection completeness. '+('Old first-page/partial-day samples excluded from completed sampled days; count snapshots may drift.' if kind=='mediacloud' else 'retrieved_on retained; score/num_comments are archive retrieval snapshots, not comparable across years.')+' Count method: '+count_method+(' Window completion does not mean full-day completion. Retained full-day inventory overlaps current samples and must not be added to them.' if window else '')))
 write_csv(PROV/'monthly_cluster_status.csv',rows)
 summary=dict(as_of_utc=dt.datetime.now(dt.timezone.utc).isoformat(),seed=SEED,sources={})
 for source in sorted({r['source'] for r in rows}):
  values=[r for r in rows if r['source']==source]
  summary['sources'][source]={k:sum(r[k] for r in values) for k in ['planned_sample_dates','completed_sample_dates','planned_sample_days','completed_sample_days','sample_days_reused','sample_days_newly_completed','planned_sample_windows','completed_sample_windows','sample_windows_reused','sample_windows_newly_completed','sample_unique_records','retained_other_full_days','retained_other_full_day_records','retained_full_days_including_selected_dates','retained_full_day_records_including_selected_dates']}
  summary['sources'][source]['sample_unit']=next(r['sample_unit'] for r in values)
  summary['sources'][source]['sample_months_complete']=sum(r['planned_sample_dates']>0 and r['planned_sample_dates']==r['completed_sample_dates'] for r in values)
  summary['sources'][source]['sample_months_planned']=sum(r['planned_sample_dates']>0 for r in values)
 mc=states['mediacloud'];remaining_pages=sum(max(1,math.ceil(counts[d['source']].get(d['date'],0)/1000)-d['page']) for d in mc['jobs'] if not d['complete'])
 summary['mediacloud_eta']=dict(remaining_pages_estimate=remaining_pages,remaining_hours_at_35_50_seconds_per_page=[remaining_pages*35/3600,remaining_pages*50/3600],basis='Existing selected-day query counts / 1000, less downloaded pages; rate plus observed network latency, excludes prolonged outage. Count snapshots can drift.')
 rs=states['reddit'];pending=[d for d in rs['jobs'] if not d['complete']];monthly_pending=len({d['source']+'_'+d['month'] for d in rs['jobs']} - set(reddit_counts))
 # A binary interval tree has 2*leaves-1 calls; unknown density remains explicitly unknown.
 known_calls=0;unknown_dates=0;unknown_minimum_calls=0
 for d in pending:
  count=reddit_counts.get(d['source']+'_'+d['month']);intervals=d['pending']
  if count is None:unknown_dates+=1;unknown_minimum_calls+=len(intervals);continue
  ndays=min(int(CUTOFF[8:]),calendar.monthrange(*map(int,d['month'].split('-')))[1]) if d['month']==CUTOFF[:7] else calendar.monthrange(*map(int,d['month'].split('-')))[1]
  for lo,hi in intervals:
   expected=count/ndays*(hi-lo)/86400
   leaves=2**max(0,math.ceil(math.log2(max(1,expected/75))))
   known_calls+=2*leaves-1
 minimum=monthly_pending+sum(len(d['pending']) for d in pending)
 window_design_active='personalfinance_window_design' in rs
 summary['reddit_eta']=dict(pending_sample_dates=len(pending),unprepared_personalfinance_windows=sum(d.get('sample_unit')=='circular_time_window' and not d.get('window_prepared') for d in pending),missing_monthly_counts=monthly_pending,
  minimum_remaining_requests=minimum,minimum_hours_at_5_10_seconds_per_request=[minimum*5/3600,minimum*10/3600],
  density_estimated_calls_for_known_months=known_calls,dates_without_monthly_density=unknown_dates,
  provisional_hours_if_unknown_dates_require_1_to_7_calls=None if window_design_active else [(monthly_pending+known_calls+unknown_minimum_calls)*5/3600,(monthly_pending+known_calls+unknown_minimum_calls*7)*10/3600],
  basis='Request floor for currently prepared intervals and missing counts. Unprepared personalfinance windows need actual monthly counts before their intervals can be fixed; they are not counted as full days. Time projections remain provisional; retries can lengthen them.')
 summary['workers']={k:{key:v for key,v in state.items() if key in ['status','pid','updated_at_utc','retry','failed_request']} for k,state in states.items()}
 if 'monthly_count_timeout_policy' in rs:summary['reddit_monthly_count_timeout_policy']=rs['monthly_count_timeout_policy']
 priority=[d for d in rs['jobs'] if d['source']=='personalfinance' and '2026-08-05'<=d['date']<=CUTOFF]
 summary['personalfinance_priority']=dict(sample_unit='circular_time_window' if 'personalfinance_window_design' in rs else 'UTC_full_day',planned_dates=len(priority),completed_dates=sum(d['complete'] for d in priority),records=sum(d['rows'] for d in priority if d['complete']))
 if 'personalfinance_window_design' in rs:summary['personalfinance_design']=dict(target_expected_records_per_month=rs['personalfinance_window_design']['target_expected_records_per_month'],design_file=rs['personalfinance_window_design']['design_file'],note='Equal marginal inclusion within each month; expected target, not a hard record cap; complete windows, not full dates.')
 if window_design_active:
  summary['reddit_eta']['note']='Previous full-day time projection superseded. Current request floor excludes unprepared personalfinance windows; it is not an ETA for the entire remaining project. See monthly_cluster_eta_snapshot.json for explicit window request scenarios.'
 tmp=PROV/f'monthly_cluster_summary.{os.getpid()}.tmp';tmp.write_text(json.dumps(summary,indent=2));tmp.replace(PROV/'monthly_cluster_summary.json')
 return summary

if __name__=='__main__':print(json.dumps(make_report(),indent=2))
