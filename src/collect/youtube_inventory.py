"""Round-robin public news upload inventory, starting with the 2023+ priority window."""
from common import *
from SM01 import LICENSE
from zoneinfo import ZoneInfo

def used_today():
 today=dt.datetime.now(ZoneInfo('America/Los_Angeles')).date()
 return sum('www.googleapis.com/youtube/v3/' in e.get('url','') and '/search?' not in e.get('url','') and dt.datetime.fromisoformat(e['requested_at_utc']).astimezone(ZoneInfo('America/Los_Angeles')).date()==today for e in (json.loads(line) for line in (PROV/'requests.jsonl').read_text().splitlines()) if 'requested_at_utc' in e)

def checkpoint(states):
 p=PROV/'youtube_inventory_state.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(states,indent=2));tmp.replace(p)

def main():
 states=[]
 for p in sorted((ROOT/'corpus/raw/SM01'/DAY).glob('channel_*.json')):
  obj=json.loads(p.read_bytes())
  for item in obj.get('items',[]):states.append(dict(channel=item['id'],playlist=item['contentDetails']['relatedPlaylists']['uploads'],page=0,token=None,done=False,title=item['snippet']['title']))
 state_path=PROV/'youtube_inventory_state.json'
 if state_path.exists():states=json.loads(state_path.read_text())
 calls=0
 # Continue until available pages end or the API explicitly rejects a request.
 while any(not s['done'] for s in states):
  for s in states:
   if s['done']:continue
   params={'playlistId':s['playlist'],'part':'snippet,contentDetails','maxResults':50,'fields':'nextPageToken,pageInfo,items(contentDetails/videoId,contentDetails/videoPublishedAt,snippet(title,publishedAt))'}
   if s['token']:params['pageToken']=s['token']
   path=fetch('SM01','https://www.googleapis.com/youtube/v3/playlistItems',f"uploads_{s['channel']}_{s['page']:04}.json",params,key='youtube',keyparam='key',delay=.15,license_note=LICENSE)
   calls+=1
   if not path:
    print('YouTube stopped on failed request; no quota bypass',flush=True);return
   obj=json.loads(path.read_bytes());items=obj.get('items',[])
   dates=[x.get('contentDetails',{}).get('videoPublishedAt','') for x in items]
   s['page']+=1;s['token']=obj.get('nextPageToken')
   s['done']=not s['token'] or bool(dates and all(d and d<'2023-01-01' for d in dates))
   checkpoint(states)
   if s['done']:print('CHANNEL END',s['title'],'pages',s['page'],'oldest',min(dates,default=''),'has_older',bool(s['token']),flush=True)
 checkpoint(states)
 print('New inventory requests:',calls,'all recorded YouTube calls today:',used_today(),flush=True)

if __name__=='__main__':main()
