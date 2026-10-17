"""Common channel inventory discovery; complete weekly windows, all channels.

No keyword query: apply exactly the same downstream title predicate as uploads.
Older quarters use one seeded seven-day cluster per channel-quarter.
"""
from common import *
from audit_runtime import worker_lock,checkpoint,last_event
from SM01 import LICENSE
import random,os,calendar
STATE=PROV/'youtube_window_search_state.json'

def initial():
 channels=json.loads((PROV/'youtube_inventory_state.json').read_text());earliest={}
 for p in (ROOT/'corpus/raw/SM01').rglob('uploads_*.json'):
  cid=p.name[len('uploads_'):].rsplit('_',1)[0]
  dates=[x.get('contentDetails',{}).get('videoPublishedAt','')[:10] for x in json.loads(p.read_bytes()).get('items',[])];dates=[d for d in dates if d]
  if dates:earliest[cid]=min(earliest.get(cid,'9999'),min(dates))
 rng=random.Random(20261015);modern={};historical={}
 def window(cid,lo,hi,route):return dict(channel=cid,start=lo.isoformat(),end=hi.isoformat(),route=route,page=0,token=None,rows=0,ids=[],complete=False)
 for c in sorted(channels,key=lambda x:x['channel']):
  cid=c['channel'];modern[cid]=[];historical[cid]=[]
  end=dt.date.fromisoformat(min(earliest[cid],CUTOFF))+dt.timedelta(days=1);lo=dt.date(2023,1,1)
  while lo<end:
   hi=min(lo+dt.timedelta(days=7),end);modern[cid].append(window(cid,lo,hi,'full_weekly_gap_search'));lo=hi
  for year in range(2010,2023):
   for month in [1,4,7,10]:
    lo=dt.date(year,month,1);hi=dt.date(year+1,1,1) if month==10 else dt.date(year,month+3,1)
    lo+=dt.timedelta(days=rng.randrange((hi-lo).days-6))
    historical[cid].append(window(cid,lo,lo+dt.timedelta(days=7),'quarter_random_7day_cluster'))
 jobs=[]
 # Every round visits all channels; weekly windows are always exhausted first.
 for i in range(max(max(map(len,modern.values())),52)):
  for group in [modern,historical]:
   for cid in sorted(group):
    if i<len(group[cid]):jobs.append(group[cid][i])
 return dict(queries=jobs,seed=20261015,query='no keyword restriction; same title regex applied to every route')

def main():
 s=json.loads(STATE.read_text()) if STATE.exists() else initial();s.update(status='running',pid=os.getpid());checkpoint(STATE,s)
 while any(not d['complete'] for d in s['queries']):
  d=next(d for d in s['queries'] if not d['complete'])
  params=dict(part='snippet',type='video',channelId=d['channel'],publishedAfter=d['start']+'T00:00:00Z',publishedBefore=d['end']+'T00:00:00Z',order='relevance',maxResults=50,fields='nextPageToken,pageInfo,items(id/videoId,snippet(publishedAt,title,channelId))')
  if d['token']:params['pageToken']=d['token']
  name=f"search_weekly_{d['channel']}_{d['start']}_{d['end']}_{d['page']:03}.json"
  p=fetch('SM01','https://www.googleapis.com/youtube/v3/search',name,params,key='youtube',keyparam='key',delay=1,license_note=LICENSE+' No query keyword filter; full weekly pagination or declared quarterly seven-day cluster.')
  if not p:
   e=last_event('https://www.googleapis.com/youtube/v3/search',params)
   s.update(status='stopped_api_error',error={k:e.get(k) for k in ['status','api_reasons','requested_at_utc']});checkpoint(STATE,s);return
  o=json.loads(p.read_bytes());d['expected_api_estimate']=o.get('pageInfo',{}).get('totalResults');d['rows']+=len(o.get('items',[]));d['ids']=sorted(set(d['ids'])|{v['id']['videoId'] for v in o.get('items',[])})
  d['page']+=1;d['token']=o.get('nextPageToken')
  if not d['token']:
   # Documented 500-result cap: split saturated windows, never call them complete.
   if len(d['ids'])>=500 or (d['expected_api_estimate'] or 0)>len(d['ids']):
    lo=dt.date.fromisoformat(d['start']);hi=dt.date.fromisoformat(d['end'])
    if (hi-lo).days>1:
     mid=lo+dt.timedelta(days=(hi-lo).days//2);idx=s['queries'].index(d)
     children=[dict(channel=d['channel'],start=a.isoformat(),end=b.isoformat(),route=d['route'],page=0,token=None,rows=0,ids=[],complete=False) for a,b in [(lo,mid),(mid,hi)]]
     d.update(complete=True,completion='split_parent_not_complete_inventory');s['queries'][idx+1:idx+1]=children
    else:d.update(complete=True,completion='pagination_exhausted_count_mismatch_or_cap')
   else:d.update(complete=True,completion='pagination_exhausted_not_platform_exhaustive')
  checkpoint(STATE,s)
 s['status']='complete_scheduled_queries';checkpoint(STATE,s)
if __name__=='__main__':
 with worker_lock('youtube_search'):main()
