"""One reset probe, 90 requests per Pacific day, complete natural months.

Single current project/key only. Never retries a 429 in the same Pacific day.
"""
from common import *
from audit_runtime import worker_lock,checkpoint,last_event
from youtube_details import TERMS
from SM01 import LICENSE
from zoneinfo import ZoneInfo
import os,calendar,math
STATE=PROV/'youtube_monthly_search_state.json'
PACIFIC=ZoneInfo('America/Los_Angeles')

def used_today():
 today=dt.datetime.now(PACIFIC).date();n=0
 for line in (PROV/'requests.jsonl').read_text().splitlines():
  e=json.loads(line)
  if '/youtube/v3/search?' in e.get('url','') and dt.datetime.fromisoformat(e['requested_at_utc']).astimezone(PACIFIC).date()==today:n+=1
 return n

def initial():
 coverage={r['channel_id']:r for r in csv.DictReader((PROV/'youtube_coverage.csv').open())};jobs=[]
 for c in json.loads((PROV/'youtube_inventory_state.json').read_text()):
  r=coverage[c['channel']]
  if r['reached_2023_boundary']=='True':continue
  y,m=map(int,r['earliest'][:7].split('-'))
  while (y,m)>=(2023,1):
   month=f'{y:04}-{m:02}';jobs.append(dict(channel=c['channel'],name=c['title'],month=month,page=0,token=None,rows=0,ids=[],complete=False,status='pending'))
   y,m=(y-1,12) if m==1 else (y,m-1)
 jobs.sort(key=lambda d:(0 if d['month']>='2025-01' else 1,-int(d['month'].replace('-','')),d['channel']))
 return dict(queries=jobs,not_before_pacific_date='2026-10-16',last_429_pacific_date='2026-10-15',daily_limit=90,scope='2023 onward only; natural-month keyword search; same title rule as uploads')

def estimate(s):
 remaining=[d for d in s['queries'] if not d['complete'] and d['status']!='covered_by_classified_long_inventory'];min_calls=len(remaining)
 result=dict(as_of_utc=dt.datetime.now(dt.timezone.utc).isoformat(),remaining_channel_months=len(remaining),minimum_requests=min_calls,minimum_pacific_days=math.ceil(min_calls/90),note='Lower bound assumes one page per unfinished month; actual days depend on result counts, pagination, quota shared with other search calls, and errors.',search_calls_today=used_today())
 (PROV/'youtube_search_estimate.json').write_text(json.dumps(result,indent=2));return result

def main():
 if (PROV/'youtube_api_disabled_by_user.json').exists():print('YouTube API collection disabled by user; no request sent.');return
 s=json.loads(STATE.read_text()) if STATE.exists() else initial();today=dt.datetime.now(PACIFIC).date().isoformat();s['pid']=os.getpid()
 cp=PROV/'youtube_classified_state.json'
 if cp.exists():
  long_covered={d['channel'] for d in json.loads(cp.read_text())['playlists'] if d['kind']=='UULF' and d['status'] in ['reached_2023','playlist_exhausted'] and d.get('earliest','') and d['earliest'][:10]<='2023-01-01'}
  for d in s['queries']:
   if d['channel'] in long_covered:d['status']='covered_by_classified_long_inventory'
 estimate(s)
 if today<s['not_before_pacific_date'] or s.get('last_429_pacific_date')==today:
  s['status']='waiting_for_next_pacific_reset_no_search_request';checkpoint(STATE,s);return
 s.update(status='running',search_calls_today=used_today());checkpoint(STATE,s)
 query='|'.join('"'+t+'"' if ' ' in t else t for t in TERMS)
 while True:
  pending=[d for d in s['queries'] if not d['complete'] and d['status']!='covered_by_classified_long_inventory']
  if not pending:s['status']='complete_scheduled_months';break
  if used_today()>=90:s['status']='waiting_daily_90_request_budget';break
  d=pending[0];y,m=map(int,d['month'].split('-'));end=dt.date(y+1,1,1) if m==12 else dt.date(y,m+1,1)
  params=dict(part='snippet',type='video',channelId=d['channel'],q=query,publishedAfter=d['month']+'-01T00:00:00Z',publishedBefore=end.isoformat()+'T00:00:00Z',order='date',maxResults=50,fields='nextPageToken,pageInfo,items(id/videoId,snippet(publishedAt,title,channelId))')
  if d['token']:params['pageToken']=d['token']
  name=f"search_monthly_{d['channel']}_{d['month']}_{d['page']:03}.json"
  p=fetch('SM01','https://www.googleapis.com/youtube/v3/search',name,params,key='youtube',keyparam='key',delay=1,license_note=LICENSE+' User monthly economic OR search; month eligible only after pagination exhausted; shared 90/day Pacific budget.')
  s['search_calls_today']=used_today()
  if not p:
   e=last_event('https://www.googleapis.com/youtube/v3/search',params);s['error']={k:e.get(k) for k in ['status','api_reasons','api_error_details','requested_at_utc','retry_after']}
   if e.get('status')==429:s['last_429_pacific_date']=today
   s['status']='needs_user_resolution_after_reset_probe' if e.get('status')==429 else 'stopped_api_error';checkpoint(STATE,s);return
  o=json.loads(p.read_bytes());d['rows']+=len(o.get('items',[]));d['ids']=sorted(set(d['ids'])|{i['id']['videoId'] for i in o.get('items',[])})
  d['page']+=1;d['token']=o.get('nextPageToken');d['query_estimate']=o.get('pageInfo',{}).get('totalResults');d['complete']=not bool(d['token'])
  d['status']='complete_pagination' if d['complete'] else 'partial_month_not_eligible'
  if d['complete'] and (len(d['ids'])>=500 or (d['query_estimate'] or 0)>len(d['ids'])):d['status']='pagination_exhausted_api_cap_or_count_mismatch_not_full_inventory'
  checkpoint(STATE,s)
 checkpoint(STATE,s);estimate(s)
if __name__=='__main__':
 with worker_lock('youtube_search'):main()
