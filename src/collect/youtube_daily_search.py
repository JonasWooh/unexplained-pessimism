"""Date-stratified discovery in gaps of truncated channel uploads lists."""
from common import *
from youtube_details import TERMS
from SM01 import LICENSE
import os,collections
STATE=PROV/'youtube_daily_search_state.json'

def save(s):
 s['updated_at_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
 tmp=STATE.with_suffix('.tmp');tmp.write_text(json.dumps(s,indent=2));tmp.replace(STATE)

def main():
 if STATE.exists():s=json.loads(STATE.read_text())
 else:
  earliest={}
  for p in (ROOT/'corpus/raw/SM01').rglob('uploads_*.json'):
   channel=p.name[len('uploads_'):].rsplit('_',1)[0]
   dates=[v.get('contentDetails',{}).get('videoPublishedAt','')[:10] for v in json.loads(p.read_bytes()).get('items',[])]
   dates=[d for d in dates if d]
   if dates:earliest[channel]=min(earliest.get(channel,'9999'),min(dates))
  queries=[]
  for channel,end in earliest.items():
   day=dt.date(2023,1,1)
   while day.isoformat()<=min(end,CUTOFF):
    queries.append(dict(channel=channel,date=day.isoformat(),page=0,token=None,rows=0,complete=False));day+=dt.timedelta(days=1)
  s=dict(queries=queries)
 s.update(status='running',pid=os.getpid(),scheduling='fewest requests per publication date first, across truncated channel inventories');save(s)
 query='|'.join('"'+t+'"' if ' ' in t else t for t in TERMS)
 while any(not d['complete'] for d in s['queries']):
  requests_by_day=collections.Counter()
  for d in s['queries']:requests_by_day[d['date']]+=d['page']
  d=min((d for d in s['queries'] if not d['complete']),key=lambda d:(requests_by_day[d['date']],d['page'],d['date'],d['channel']))
  # Preserve API timestamps and raw boundary results for coverage auditing.
  end=(dt.date.fromisoformat(d['date'])+dt.timedelta(days=1)).isoformat()
  params=dict(part='snippet',type='video',channelId=d['channel'],q=query,publishedAfter=d['date']+'T00:00:00Z',publishedBefore=end+'T00:00:00Z',order='date',maxResults=50,fields='nextPageToken,pageInfo,items(id/videoId,snippet(publishedAt,title,channelId))')
  if d['token']:params['pageToken']=d['token']
  name=f"search_daily_{d['channel']}_{d['date']}_{d['page']:03}.json"
  p=fetch('SM01','https://www.googleapis.com/youtube/v3/search',name,params,key='youtube',keyparam='key',delay=1,license_note=LICENSE+' Daily discovery; absence of search hits is not proof that the platform has no videos.')
  if not p:s.update(status='stopped_api_error',failed_request=name);save(s);return
  o=json.loads(p.read_bytes());d['rows']+=len(o.get('items',[]));d['page']+=1;d['token']=o.get('nextPageToken');d['complete']=not bool(d['token']);save(s)
 s['status']='complete_daily_search_queries';save(s)

if __name__=='__main__':main()
