"""Author-free Reddit archive collection via documented Arctic Shift fields.

Split saturated time intervals until each returned page is exhaustive (<100).
Integer-second creation timestamps and half-second interval boundaries avoid
losing tied timestamps. Parent probe pages are retained but not counted as
additional posts. No arbitrary total request or record cap.
"""
from common import *
import calendar,os,random
from audit_runtime import retry_fetch,worker_lock

SUBREDDITS=['economy','Economics','personalfinance','inflation']
ENDPOINT='https://arctic-shift.photon-reddit.com/api/posts/search'
SELECT='id,subreddit,created_utc,retrieved_on,title,selftext,score,num_comments'
LICENSE='Arctic Shift community archive of Reddit, not Reddit official API. User explicitly requested collection. Author identity fields excluded server-side; raw selected response preserved; no analysis or redistribution.'
STATE=PROV/'reddit_collection_state.json'

def timestamp(year,month,day):
 return int(dt.datetime(year,month,day,tzinfo=dt.timezone.utc).timestamp())

def boundary(second):
 return dt.datetime.fromtimestamp(second-.5,dt.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')

def initial():
 windows=[]
 for year in range(2010,int(CUTOFF[:4])+1):
  for month in range(1,13):
   label=f'{year:04}-{month:02}'
   if label>CUTOFF[:7]:break
   end=min(timestamp(year+1,1,1) if month==12 else timestamp(year,month+1,1),int((dt.datetime.fromisoformat(CUTOFF).replace(tzinfo=dt.timezone.utc)+dt.timedelta(days=1)).timestamp()))
   windows.append([timestamp(year,month,1),end,label])
 windows.sort(key=lambda x:(0 if x[2]>='2025-01' else 1,x[2]))
 return dict(status='new',subreddits={s:dict(pending=list(windows),leaf_files=[],probe_files=[],rows=0,status='pending') for s in SUBREDDITS})

def daily_queue(state):
 # Partition only unfinished intervals, preserving every completed raw response.
 # Breadth-first splitting gives each day a first pass before deeper pagination.
 for sub in state['subreddits'].values():
  pending=[]
  for lo,hi,label in sub['pending']:
   while lo<hi:
    end=min(hi,(lo//86400+1)*86400)
    pending.append([lo,end,label]);lo=end
  pending.sort(key=lambda x:(0 if x[2]>='2025-01' else 1,x[0]))
  sub['pending']=pending
 state['scheduling']='daily breadth-first; monitoring window first; saturated intervals queued at tail'

def save(state):
 state['updated_at_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
 tmp=STATE.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2));tmp.replace(STATE)

def archive_fetch(state,endpoint,name,params):
 return retry_fetch('SM02',endpoint,name,params,state=state,state_path=STATE,delay=3,license_note=LICENSE)

def priority(sub,interval):
 lo,hi,label=interval
 return (0 if sub in ['economy','Economics'] and '2017-01'<=label<='2024-12' else 1, label,lo,sub)

def audit_queue(state):
 rng=random.Random(20261015);sample={}
 for year in range(2010,2025):
  for month in range(1,13):
   label=f'{year:04}-{month:02}'
   sample[label]=sorted(rng.sample(range(1,calendar.monthrange(year,month)[1]+1),3))
 selected=[];excluded=[]
 for lo,hi,label in state['subreddits']['personalfinance']['pending']:
  if label>='2025-01':selected.append([lo,hi,label]);continue
  cursor=lo
  while cursor<hi:
   end=min(hi,(cursor//86400+1)*86400)
   day=dt.datetime.fromtimestamp(cursor,dt.timezone.utc).day
   (selected if day in sample[label] else excluded).append([cursor,end,label]);cursor=end
 state['subreddits']['personalfinance']['pending']=selected
 state['personalfinance_sampling']=dict(seed=20261015,method='uniform without replacement, 3 UTC days per calendar month, collect selected days exhaustively; cluster sample, not uniform posts',selected_days=sample,excluded_pending_intervals=excluded)
 state['queue_version']=3
 for sub,s in state['subreddits'].items():s['pending'].sort(key=lambda x:priority(sub,x))
 state['scheduling']='economy/Economics 2017-2024 first; then remaining years; personalfinance pre2025 monthly random-day clusters'

def main():
 state=json.loads(STATE.read_text()) if STATE.exists() else initial()
 state.pop('failed_request',None);state.pop('error_type',None)
 if state.get('queue_version')!=3:audit_queue(state)
 state.update(status='running',pid=os.getpid(),run_requests=0);save(state)
 for sub in SUBREDDITS:
  endpoint='https://arctic-shift.photon-reddit.com/api/subreddits/search';params=dict(subreddit=sub,fields='id,display_name,created_utc,retrieved_on,subscribers')
  p=archive_fetch(state,endpoint,f'subreddit_{sub}.json',params)
  if not p:
   public=endpoint+'?'+urlencode(params)
   event=next((json.loads(line) for line in reversed((PROV/'requests.jsonl').read_text().splitlines()) if json.loads(line).get('url')==public),{})
   state.setdefault('metadata_errors',{})[sub]=dict(status=event.get('status'),at=event.get('requested_at_utc'));save(state)
   if event.get('status')!=422:
    state.update(status='stopped_api_error',failed_request='subreddit metadata '+sub);save(state);return
   # Optional subscriber metadata can be unavailable independently of posts.
   # Record the endpoint's actual 422; do not silently invent metadata.
 while any(s['pending'] for s in state['subreddits'].values()):
  available=[(sub,v) for sub,v in state['subreddits'].items() if v['pending']]
  sub,s=min(available,key=lambda pair:priority(pair[0],pair[1]['pending'][0]))
  for sub,s in [(sub,s)]:
   lo,hi,label=s['pending'][0]
   month_key=sub+'_'+label+'_v3'
   if month_key not in state.setdefault('monthly_count_files',{}):
    year,month=map(int,label.split('-'));end=timestamp(year+1,1,1) if month==12 else timestamp(year,month+1,1)
    params_count=dict(subreddit=sub,after=boundary(timestamp(year,month,1)),before=boundary(min(end,timestamp(2026,10,15))),aggregate='subreddit',limit='')
    count_path=archive_fetch(state,'https://arctic-shift.photon-reddit.com/api/posts/search/aggregate',f'counts_v3_{sub}_{label}.json',params_count)
    if count_path:state['monthly_count_files'][month_key]=str(count_path.relative_to(ROOT));save(state)
    else:
     state.setdefault('count_errors',{})[month_key]='unavailable';save(state)
     if state['status']=='needs_user_resolution':return
   params=dict(subreddit=sub,after=boundary(lo),before=boundary(hi),limit=100,sort='asc',fields=SELECT)
   name=f'posts_{sub}_{lo}_{hi}.json'
   p=archive_fetch(state,ENDPOINT,name,params)
   if not p:state.update(status=state['status'] if state['status']=='needs_user_resolution' else 'stopped_api_error',failed_request=name);save(state);return
   obj=json.loads(p.read_bytes())
   if not isinstance(obj.get('data'),list):raise ValueError('Expected archive data list')
   items=obj['data']
   for item in items:
    if set(item)-set(SELECT.split(',')):raise ValueError('Unexpected fields in archive response')
    date=item.get('created_utc')
    if not isinstance(date,int) or not lo<=date<hi:raise ValueError('Unexpected creation timestamp or interval semantics')
   relative=str(p.relative_to(ROOT))
   if len(items)>=100:
    if hi-lo<=1:
     state.update(status='stopped_saturated_second',failed_request=name);save(state);return
    mid=(lo+hi)//2;s['pending'].pop(0);s['pending'][:0]=[[lo,mid,label],[mid,hi,label]];s['probe_files'].append(relative)
   else:
    s['pending'].pop(0);s['leaf_files'].append(relative);s['rows']+=len(items)
   if not s['pending']:s['status']='complete'
   save(state)
 state['status']='complete_archive_query';save(state)

if __name__=='__main__':
 try:
  with worker_lock('arctic_shift_api'):main()
 except Exception as exc:
  state=json.loads(STATE.read_text());state.update(status='stopped_error',error_type=type(exc).__name__);save(state);raise
