"""Video metadata and privacy-minimized comment metadata, with explicit quota budget."""
from common import *
from SM01 import LICENSE
from N03 import TOPICS
import re,collections

TERMS=['inflation','prices','cost of living','grocery prices','gas prices','affordability','price increases','unemployment','jobless','layoffs','hiring','jobs report','labor market','GDP','economic growth','recession','economic slowdown','interest rates','mortgage rates','Federal Reserve','housing costs','rent','economy','consumer sentiment','consumer confidence','tariffs']
PATTERN=re.compile(r'\b(?:'+'|'.join(re.escape(t) for t in TERMS)+r')\b',re.I)

def candidates():
 videos={}
 paths=sorted((ROOT/'corpus/raw/SM01').rglob('uploads_*.json'))+sorted((ROOT/'corpus/raw/SM01').rglob('search_*.json'))+sorted((ROOT/'corpus/raw/SM01').rglob('classified_*.json'))
 for p in sorted(paths,key=lambda p:(p.stat().st_mtime,str(p))):
  route='uploads' if p.name.startswith('uploads_') else ('classified_'+p.name.split('_')[1] if p.name.startswith('classified_') else 'monthly_search' if p.name.startswith('search_monthly_') else 'weekly_search_superseded' if p.name.startswith('search_weekly_') else 'legacy_search_nonrandom_incomplete')
  for item in json.loads(p.read_bytes()).get('items',[]):
   sn=item['snippet'];c=item.get('contentDetails',{})
   vid=c.get('videoId') if route=='uploads' or route.startswith('classified_') else item['id']['videoId']
   date=c.get('videoPublishedAt','') if route=='uploads' or route.startswith('classified_') else sn.get('publishedAt','')
   channel=p.name[len('uploads_'):].rsplit('_',1)[0] if route=='uploads' else p.name.split('_')[2] if route.startswith('classified_') else sn['channelId']
   if not vid or not date:continue
   # Latest acquisition determines title; all routes and raw references retained.
   v=videos.setdefault(vid,dict(video_id=vid,channel=channel,published=date,title=sn['title'],routes=set(),raw_files=set()))
   v['routes'].add(route);v['raw_files'].add(str(p.relative_to(ROOT)))
   v.update(title=sn['title'],title_source=str(p.relative_to(ROOT)))
 monthly_path=PROV/'youtube_monthly_search_state.json'
 monthly={(d['channel'],d['month']):set(d['ids']) for d in json.loads(monthly_path.read_text())['queries'] if d.get('status')=='complete_pagination'} if monthly_path.exists() else {}
 rows=[];eligible=[]
 for v in videos.values():
  match=bool(PATTERN.search(v['title']));in_period='2023-01-01'<=v['published'][:10]<=CUTOFF
  superseded=(v['channel'],v['published'][:7]) in monthly and v['video_id'] not in monthly[(v['channel'],v['published'][:7])]
  row={**v,'routes':'|'.join(sorted(v['routes'])),'raw_files':'|'.join(sorted(v['raw_files'])),'title_rule_match':match,'in_period':in_period,'included':match and in_period and not superseded,'superseded_by_complete_monthly_search':superseded,'rule_version':'economic_title_regex_v1'};rows.append(row)
  if row['included']:eligible.append({k:v[k] for k in ['video_id','channel','published','title']})
 for name,records,fields in [('youtube_video_acquisition_registry.csv',rows,list(rows[0]) if rows else []),('youtube_acquisition_candidates.csv',eligible,['video_id','channel','published','title'])]:
  path=PROV/name;tmp=path.with_suffix('.tmp')
  with tmp.open('w',newline='') as f:
   w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(records)
  tmp.replace(path)
 return sorted(eligible,key=lambda v:(v['published'],v['channel'],v['video_id']))

def main():
 ordered=candidates()
 collected=set()
 for p in (ROOT/'corpus/raw/SM01'/DAY).glob('videos_*.json'):
  collected.update(v['id'] for v in json.loads(p.read_bytes()).get('items',[]))
 pending=[v for v in ordered if v['video_id'] not in collected]
 for start in range(0,len(pending),50):
  ids=[v['video_id'] for v in pending[start:start+50]]
  digest=hashlib.sha256(','.join(ids).encode()).hexdigest()[:12]
  p=fetch('SM01','https://www.googleapis.com/youtube/v3/videos','videos_'+digest+'.json',{'id':','.join(ids),'part':'snippet,contentDetails,statistics','fields':'items(id,snippet(title,publishedAt),contentDetails/duration,statistics)'},key='youtube',keyparam='key',delay=1,license_note=LICENSE)
  if p is None:return False
 print('Video candidates',len(ordered),'new metadata requests',(len(pending)+49)//50,flush=True)
 return True

if __name__=='__main__':main()
