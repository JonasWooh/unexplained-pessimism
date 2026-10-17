"""Single-worker locks and resumable retries for genuine transient failures."""
from common import *
import os,email.utils
from contextlib import contextmanager

@contextmanager
def worker_lock(interface):
 with (PROV/(interface+'.lock')).open('a+') as f:
  try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:raise RuntimeError('Another worker owns '+interface)
  yield

def checkpoint(path,state):
 state['updated_at_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
 tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2));tmp.replace(path)

def last_event(url,params=None):
 public=url+('?' + urlencode(params) if params else '')
 for line in reversed((PROV/'requests.jsonl').read_text().splitlines()):
  event=json.loads(line)
  if event.get('url')==public:return event
 return {}

def retry_fetch(ds,url,name,params=None,*,state=None,state_path=None,**kwargs):
 attempt=0
 while True:
  p=fetch(ds,url,name,params,**kwargs)
  if p:
   if state is not None and state_path:
    state.update(status='running');state.pop('retry',None);checkpoint(state_path,state)
   return p
  e=last_event(url,params);status=e.get('status')
  transient=status in ['ReadTimeout','ConnectTimeout','ConnectionError','Timeout',429,500,502,503,504] or (status==422 and e.get('api_error','').startswith('Timeout'))
  if not transient:return None
  if attempt>=4:
   if state is not None and state_path:
    state.update(status='needs_user_resolution',retry=dict(error=status,failed_attempts=attempt+1,request_file=name));checkpoint(state_path,state)
   return None
  wait=min(300,10*2**min(attempt,5));attempt+=1
  after=e.get('retry_after','')
  if after:
   try:wait=max(wait,float(after))
   except ValueError:
    try:wait=max(wait,(email.utils.parsedate_to_datetime(after)-dt.datetime.now(dt.timezone.utc)).total_seconds())
    except (ValueError,TypeError):pass
  if status==429:wait=max(wait,60)
  if state is not None and state_path:
   state.update(status='waiting_retry',retry=dict(error=status,attempt=attempt,wait_seconds=wait,next_retry_utc=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(seconds=wait)).isoformat()));checkpoint(state_path,state)
  print('Retry after',wait,'seconds;',status,flush=True)
  time.sleep(wait)
