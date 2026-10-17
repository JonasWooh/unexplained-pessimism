"""Collect public comment text with server-side exclusion of author fields.

Raw API response bytes remain immutable. textDisplay is API-provided plain text,
not a claim to reproduce the author's original input. Only top-level comments.
"""
from common import *
from youtube_details import candidates
from SM01 import LICENSE
import os
from audit_runtime import worker_lock,retry_fetch

ENDPOINT='https://www.googleapis.com/youtube/v3/commentThreads'
STATE=PROV/'youtube_comment_text_state.json'
FIELDS_TEXT='nextPageToken,pageInfo,items(id,snippet(totalReplyCount,topLevelComment(id,snippet(textDisplay,publishedAt,updatedAt,likeCount))))'

def checkpoint(state):
 state['updated_at_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
 tmp=STATE.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2));tmp.replace(STATE)

def main():
 state=json.loads(STATE.read_text()) if STATE.exists() else dict(videos={},status='new')
 ordered=candidates()
 dates={v['video_id']:v['published'][:10] for v in ordered}
 published={v['video_id']:v['published'] for v in ordered}
 for vid,v in state['videos'].items():
  if vid not in dates:v['status']='excluded_title_rule'
  elif v['status']=='excluded_title_rule':v['status']='pending'
 for v in ordered:
  state['videos'].setdefault(v['video_id'],dict(page=0,token=None,rows=0,status='pending'))
 for v in state['videos'].values():
  if v['status']=='2000_cap' and v.get('token'):v['status']='pending'
 state.update(status='running',pid=os.getpid(),run_requests=0,scheduling='complete eligible video first-30-day window; unfinished existing videos first; raw later comments retained only as unavoidable pagination traversal')
 checkpoint(state)
 calls=0
 discovery_seen=set();last_discovery=0
 while any(v['status']=='pending' for v in state['videos'].values()):
  if time.monotonic()-last_discovery>=600:
   for item in candidates():
    vid=item['video_id'];dates[vid]=item['published'][:10];published[vid]=item['published']
    state['videos'].setdefault(vid,dict(page=0,token=None,rows=0,status='pending'))
   last_discovery=time.monotonic()
  day_pages={}
  for vid,v in state['videos'].items():
   day=dates.get(vid,'unknown');day_pages[day]=day_pages.get(day,0)+v['page']
  pending=[vid for vid,v in state['videos'].items() if v['status']=='pending']
  vid=min(pending,key=lambda vid:(state['videos'][vid]['page']==0,dates.get(vid,'unknown'),vid))
  for vid in [vid]:
   v=state['videos'][vid]
   if v['status']!='pending':continue
   params=dict(videoId=vid,part='snippet',maxResults=100,order='time',textFormat='plainText',fields=FIELDS_TEXT)
   if v['token']:params['pageToken']=v['token']
   name=f'comment_text_{vid}_{v["page"]:02}.json'
   cached=(ROOT/'corpus/raw/SM01'/DAY/name).exists()
   path=retry_fetch('SM01',ENDPOINT,name,params,state=state,state_path=STATE,key='youtube',keyparam='key',delay=1,
      license_note=LICENSE+' User permits comment body; author fields excluded by API fields selection. textDisplay/plainText; top-level only.')
   if not cached:calls+=1
   state['run_requests']=calls
   if path is None:
    public=ENDPOINT+'?'+urlencode(params)
    event=next((json.loads(line) for line in reversed((PROV/'requests.jsonl').read_text().splitlines()) if json.loads(line).get('url')==public),{})
    reasons=event.get('api_reasons',[])
    v['last_error']=dict(status=event.get('status'),reasons=reasons,at=event.get('requested_at_utc'))
    if reasons and all(r in ['commentsDisabled','videoNotFound'] for r in reasons):
     v['status']='unavailable';checkpoint(state);continue
    state['status']=state['status'] if state['status']=='needs_user_resolution' else 'stopped_api_error';state['stop_event']=v['last_error'];checkpoint(state);return
   obj=json.loads(path.read_bytes())
   for item in obj.get('items',[]):
    snippet=item['snippet']['topLevelComment']['snippet']
    if set(snippet)-{'textDisplay','publishedAt','updatedAt','likeCount'}:
     raise ValueError('Unexpected comment fields; inspect saved response schema')
    if 'textDisplay' not in snippet:raise ValueError('Expected comment text missing')
   v['target_window_start']=published[vid]
   v['target_window_end']=(dt.datetime.fromisoformat(published[vid].replace('Z','+00:00'))+dt.timedelta(days=30)).isoformat()
   v['rows']+=len(obj.get('items',[]));v['page']+=1;v['token']=obj.get('nextPageToken')
   if not v['token']:v['status']='complete_top_level'
   checkpoint(state)
 state['status']='complete_top_level_comments';checkpoint(state)

if __name__=='__main__':
 with worker_lock('youtube_commentThreads'):main()
