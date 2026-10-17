"""Equal-marginal-probability circular time-window sampling within seeded dates."""
from month_cluster_common import *

def interval_index(files):
 records=sorted((*file_interval(rel),rel) for rel in set(files));merged=[]
 for lo,hi,_ in records:
  if merged and lo<=merged[-1][1]:merged[-1][1]=max(merged[-1][1],hi)
  else:merged.append([lo,hi])
 return dict(records=records,merged=merged,starts=[x[0] for x in merged])

def circular_intervals(day_start,offset,length):
 if not 0<=offset<86400 or not 0<=length<=86400:raise ValueError('Invalid circular window')
 if length==0:return []
 if length==86400:return [[day_start,day_start+86400]]
 end=offset+length
 if end<=86400:return [[day_start+offset,day_start+end]]
 return [[day_start,day_start+end-86400],[day_start+offset,day_start+86400]]

def prepare_window(state,job,reuse_index):
 if job.get('window_prepared'):return
 config=state['personalfinance_window_design'];month=job['month'];count=state['monthly_counts']['personalfinance_'+month]['count']
 ndays=min(calendar.monthrange(*map(int,month.split('-')))[1],int(CUTOFF[8:])) if month==CUTOFF[:7] else calendar.monthrange(*map(int,month.split('-')))[1]
 length=min(86400,max(1,round(86400*ndays*config['target_expected_records_per_month']/(3*count)))) if count else 0
 month_value=dict(source='personalfinance',month=month,population_count=count,eligible_utc_dates=ndays,target_expected_records=config['target_expected_records_per_month'],window_length_seconds=length,inclusion_probability=3/ndays*length/86400,expected_sample_records=count*3/ndays*length/86400,count_provenance=state['monthly_counts']['personalfinance_'+month],design_file=config['design_file'])
 folder=PROV/'personalfinance_window_month_plans';folder.mkdir(exist_ok=True);path=folder/(month+'.json')
 if path.exists():
  if json.loads(path.read_text())!=month_value:raise ValueError('Frozen monthly window plan changed')
 else:
  with path.open('x') as f:json.dump(month_value,f,indent=2)
 lo,hi=day_bounds(job['date']);offset=random.Random(f"{SEED}|personalfinance|{job['date']}|circular_window_v1").randrange(86400)
 intervals=circular_intervals(lo,offset,length);pending=[];files=[]
 for start,end in intervals:
  pending.extend(missing_parts(start,end,reuse_index));files.extend(overlapping_files(start,end,reuse_index))
 job.update(window_prepared=True,selected_intervals=intervals,window_start_second=offset,window_length_seconds=length,population_count=count,eligible_utc_dates=ndays,inclusion_probability=month_value['inclusion_probability'],expected_monthly_records=month_value['expected_sample_records'],month_plan_file=str(path.relative_to(ROOT)),pending=pending,raw_files=list(dict.fromkeys(files)),old_full=not pending,complete=not pending,rows=0)
 if job['complete']:job['rows'],job['selection_file']=save_window_selection(job)

def save_window_selection(job):
 intervals=job['selected_intervals'];items={}
 for rel in job['raw_files']:
  for item in json.loads((ROOT/rel).read_bytes())['data']:
   if any(lo<=item['created_utc']<hi for lo,hi in intervals):items[str(item['id'])]=item
 value=dict(source='personalfinance',date=job['date'],sample_unit='circular_time_window',selected_intervals=intervals,window_start_second=job['window_start_second'],window_length_seconds=job['window_length_seconds'],inclusion_probability=job['inclusion_probability'],month_plan_file=job['month_plan_file'],raw_files=list(dict.fromkeys(job['raw_files'])),unique_ids=sorted(items),rows=len(items),removed=sum(x.get('selftext','').strip().casefold()=='[removed]' for x in items.values()),deleted=sum(x.get('selftext','').strip().casefold()=='[deleted]' for x in items.values()),missing_retrieved_on=sum(x.get('retrieved_on') is None for x in items.values()))
 path=PROV/'monthly_cluster_selections'/f"reddit_personalfinance_window_v1_{job['date']}.json"
 if path.exists():
  if json.loads(path.read_text())!=value:raise ValueError('Completed window selection changed')
 else:
  with path.open('x') as f:json.dump(value,f,indent=2)
 return len(items),str(path.relative_to(ROOT))
