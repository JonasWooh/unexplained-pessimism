"""User-requested probes of undocumented public classified upload playlists."""
from common import *
from audit_runtime import worker_lock,checkpoint,last_event
from SM01 import LICENSE
import os
STATE=PROV/'youtube_classified_state.json'

def initial():
 coverage={r['channel_id']:r for r in csv.DictReader((PROV/'youtube_coverage.csv').open())};items=[]
 for c in json.loads((PROV/'youtube_inventory_state.json').read_text()):
  if coverage[c['channel']]['reached_2023_boundary']=='True':continue
  for kind in ['UULF','UULV','UUSH']:
   items.append(dict(channel=c['channel'],name=c['title'],kind=kind,playlist=kind+c['playlist'][2:],page=0,token=None,rows=0,status='probe',earliest='',latest=''))
 return dict(playlists=items)

def main():
 s=json.loads(STATE.read_text()) if STATE.exists() else initial();s.update(status='running',pid=os.getpid());checkpoint(STATE,s)
 def pull(d):
  params=dict(playlistId=d['playlist'],part='snippet,contentDetails',maxResults=50,fields='nextPageToken,pageInfo,items(contentDetails/videoId,contentDetails/videoPublishedAt,snippet(title,publishedAt))')
  if d['token']:params['pageToken']=d['token']
  name=f"classified_{d['kind']}_{d['channel']}_{d['page']:04}.json"
  p=fetch('SM01','https://www.googleapis.com/youtube/v3/playlistItems',name,params,key='youtube',keyparam='key',delay=1,license_note=LICENSE+' User-authorized undocumented classified playlist convention; selected channel-video fields only.')
  if not p:
   e=last_event('https://www.googleapis.com/youtube/v3/playlistItems',params);d['error']={k:e.get(k) for k in ['status','api_reasons','api_error_details','requested_at_utc']}
   if e.get('status')==404:d['status']='unavailable';checkpoint(STATE,s);return True
   s['status']='stopped_api_error';checkpoint(STATE,s);return False
  o=json.loads(p.read_bytes());dates=[i.get('contentDetails',{}).get('videoPublishedAt','') for i in o.get('items',[])];dates=[v for v in dates if v]
  d['rows']+=len(o.get('items',[]));d['page']+=1;d['token']=o.get('nextPageToken');d['expected_api_total']=o.get('pageInfo',{}).get('totalResults')
  if dates:d['earliest']=min(d['earliest'] or min(dates),min(dates));d['latest']=max(d['latest'],max(dates))
  d['status']='reached_2023' if dates and max(dates)<'2023-01-01' else 'playlist_exhausted' if not d['token'] else 'available'
  checkpoint(STATE,s);return True
 # Exactly up to two probe pages per convention/channel before deep traversal.
 for _ in range(2):
  for d in s['playlists']:
   if d['page']<2 and d['status'] not in ['unavailable','playlist_exhausted','reached_2023']:
    if not pull(d):return
 s['probe_complete']=True;checkpoint(STATE,s)
 while any(d['kind']=='UULF' and d['status']=='available' for d in s['playlists']):
  for d in s['playlists']:
   if d['kind']=='UULF' and d['status']=='available':
    if not pull(d):return
 s['status']='classified_probe_and_long_inventory_complete';checkpoint(STATE,s)
if __name__=='__main__':
 with worker_lock('youtube_playlistItems'):main()
