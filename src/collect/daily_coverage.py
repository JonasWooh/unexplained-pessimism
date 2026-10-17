"""Date coverage only: no text analysis, labels, raw edits or file hashes."""
from common import *
import collections

def days(start):
 day=dt.date.fromisoformat(start)
 while day.isoformat()<=CUTOFF:
  yield day.isoformat();day+=dt.timedelta(days=1)

def main():
 rows=[];summary={};now=dt.datetime.now(dt.timezone.utc).isoformat()
 def emit(source,group,start,records,statuses,note):
  counts=collections.Counter()
  for day in days(start):
   count=len(records.get(day,set()));status=statuses.get(day,'not_confirmed')
   rows.append(dict(source=source,group=group,date=day,unique_records=count,query_status=status,notes=note));counts[status]+=1
  summary[source+'/'+group]=dict(days=sum(counts.values()),days_with_records=sum(bool(records.get(d)) for d in days(start)),status_days=dict(counts))
 # Reddit probes and leaves overlap; ID sets count each post once per group/day.
 s=json.loads((PROV/'reddit_collection_state.json').read_text())
 records=collections.defaultdict(lambda:collections.defaultdict(set))
 for p in (ROOT/'corpus/raw/SM02').rglob('*.json'):
  if not(p.name.startswith('posts_') or p.name.startswith('probe_')):continue
  for item in json.loads(p.read_bytes()).get('data',[]):
   if isinstance(item.get('created_utc'),int):
    day=dt.datetime.fromtimestamp(item['created_utc'],dt.timezone.utc).date().isoformat();records[item['subreddit'].lower()][day].add(item['id'])
 for sub,v in s['subreddits'].items():
  unfinished=collections.Counter()
  for lo,hi,_ in v['pending']:
   while lo<hi:
    end=min(hi,(lo//86400+1)*86400);day=dt.datetime.fromtimestamp(lo,dt.timezone.utc).date().isoformat();unfinished[day]+=end-lo;lo=end
  r=records[sub.lower()];statuses={d:('complete_nonzero' if r.get(d) else 'complete_zero') if not unfinished[d] else ('partial' if r.get(d) or unfinished[d]<86400 else 'not_queried') for d in days('2010-01-01')}
  emit('Reddit',sub,'2010-01-01',r,statuses,'Archive-query completeness only; not a guarantee of live Reddit archive completeness. UTC dates.')
 # Media Cloud: daily pagination is the completeness evidence, not broad-window pages.
 mc=collections.defaultdict(lambda:collections.defaultdict(set))
 for p in (ROOT/'corpus/raw/N03').rglob('*.json'):
  if '_stories_' not in p.name and not p.name.startswith('daily_'):continue
  cid=p.name.split('_')[1] if p.name.startswith('daily_') else p.name.split('_')[0]
  for item in json.loads(p.read_bytes()).get('stories',[]):mc[cid][item.get('publish_date','')[:10]].add(str(item['id']))
 ds=json.loads((PROV/'mediacloud_daily_state.json').read_text()) if (PROV/'mediacloud_daily_state.json').exists() else dict(days=[])
 for cid in ['38379429','34412234']:
  statuses={d:('partial' if mc[cid].get(d) else 'not_queried') for d in days('2025-01-01')}
  for d in ds['days']:
   if d['collection_id']==cid and d['complete']:statuses[d['date']]='complete_nonzero' if d['rows'] else 'complete_zero'
  emit('Media Cloud',cid,'2025-01-01',mc[cid],statuses,'Publisher date; old and new query batches deduplicated by story ID in this coverage report only.')
 # Comment day is deliberately separate from video publication day.
 comments=collections.defaultdict(set);videos=collections.defaultdict(set)
 for p in (ROOT/'corpus/raw/SM01').rglob('comment_text_*.json'):
  for item in json.loads(p.read_bytes()).get('items',[]):
   c=item['snippet']['topLevelComment'];comments[c['snippet']['publishedAt'][:10]].add(c['id'])
 for p in (ROOT/'corpus/raw/SM01').rglob('search_*.json'):
  for item in json.loads(p.read_bytes()).get('items',[]):videos[item['snippet']['publishedAt'][:10]].add(item['id']['videoId'])
 with (PROV/'youtube_acquisition_candidates.csv').open() as f:
  for v in csv.DictReader(f):videos[v['published'][:10]].add(v['video_id'])
 for label,r in [('comment_publication',comments),('video_publication',videos)]:
  emit('YouTube',label,'2023-01-01',r,{d:'observed_incomplete' if r.get(d) else 'not_confirmed' for d in days('2023-01-01')},'A nonzero day is not exhaustive coverage; comment API has no date filter. UTC dates.')
 for source,folder,key in [('NYT','N01','pub_date'),('Guardian','N02','webPublicationDate')]:
  r=collections.defaultdict(set)
  for p in (ROOT/'corpus/raw'/folder).rglob('*.json'):
   o=json.loads(p.read_bytes());response=o.get('response',{})
   for item in response.get('docs',response.get('results',[])):
    if item.get(key):r[item[key][:10]].add(item.get('_id',item.get('id',item.get('web_url',''))))
  emit(source,'publication','2010-01-01',r,{d:'observed_month_batch' if r.get(d) else 'zero_or_source_gap' for d in days('2010-01-01')},'Monthly query batches downloaded; zero-date requires source comparison, not automatically zero reporting.')
 with (PROV/'daily_coverage.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 (PROV/'daily_coverage_summary.json').write_text(json.dumps(dict(as_of_utc=now,cutoff=CUTOFF,series=summary),indent=2))
 print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
