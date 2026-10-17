"""Official search for quarters absent from truncated uploads inventories."""
from common import *
from SM01 import LICENSE
from youtube_details import TERMS
from zoneinfo import ZoneInfo
import pandas as pd

def used():
 today=dt.datetime.now(ZoneInfo('America/Los_Angeles')).date()
 return sum('/youtube/v3/search?' in e.get('url','') and dt.datetime.fromisoformat(e['requested_at_utc']).astimezone(ZoneInfo('America/Los_Angeles')).date()==today for e in (json.loads(x) for x in (PROV/'requests.jsonl').read_text().splitlines()) if 'requested_at_utc' in e)

def main():
 folder=ROOT/'corpus/raw/SM01'/DAY;states=[]
 for ch in json.loads((PROV/'youtube_inventory_state.json').read_text()):
  dates=[]
  for p in folder.glob('uploads_'+ch['channel']+'_*.json'):dates.extend(x['contentDetails']['videoPublishedAt'] for x in json.loads(p.read_bytes())['items'] if x['contentDetails'].get('videoPublishedAt'))
  earliest=min(dates)
  if earliest<'2023-01-01':continue
  for q in pd.period_range('2023Q1',pd.Period(earliest[:10],freq='Q'),freq='Q'):
   states.append(dict(channel_id=ch['channel'],channel_name=ch['title'],quarter=str(q),start=q.start_time.strftime('%Y-%m-%dT00:00:00Z'),end=min((q+1).start_time.strftime('%Y-%m-%dT00:00:00Z'),earliest),page=0,token=None,done=False,rows=0))
 states.sort(key=lambda x:(x['quarter'],x['channel_id']))
 query='|'.join('"'+t+'"' if ' ' in t else t for t in TERMS)
 while any(not s['done'] for s in states) and used()<100:
  for s in states:
   if s['done'] or used()>=100:continue
   params=dict(part='snippet',type='video',channelId=s['channel_id'],q=query,publishedAfter=s['start'],publishedBefore=s['end'],order='date',maxResults=50,fields='nextPageToken,pageInfo,items(id/videoId,snippet(publishedAt,title,channelId))')
   if s['token']:params['pageToken']=s['token']
   p=fetch('SM01','https://www.googleapis.com/youtube/v3/search',f"search_{s['channel_id']}_{s['quarter']}_{s['page']:02}.json",params,key='youtube',keyparam='key',license_note=LICENSE,delay=.2)
   if not p:
    (PROV/'youtube_search_state.json').write_text(json.dumps(states,indent=2));print('Stopped on API failure; no further search requests',flush=True);return
   obj=json.loads(p.read_bytes());s['rows']+=len(obj['items']);s['page']+=1;s['token']=obj.get('nextPageToken');s['done']=not bool(s['token'])
   state=PROV/'youtube_search_state.json';tmp=state.with_suffix('.tmp');tmp.write_text(json.dumps(states,indent=2));tmp.replace(state)
 print('Search requests today',used(),'quarter-channel queries',len(states),'queries paginated to end',sum(s['done'] for s in states),flush=True)

if __name__=='__main__':main()
