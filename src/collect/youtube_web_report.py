from common import *
from collections import defaultdict

def main():
 s=json.loads((PROV/'youtube_public_web_state.json').read_text());groups=defaultdict(dict)
 p=PROV/'youtube_web_video_records.jsonl'
 if p.exists():
  for line in p.read_text().splitlines():
   r=json.loads(line);groups[(r['channel'],r['requested_month'])][r['video_id']]=r
 rows=[]
 for job in s['jobs']:
  records=list(groups[(job['channel'],job['month'])].values());n=sum(r['eligible'] for r in records)
  rows.append(dict(source='YouTube public web/'+job['name'],channel=job['channel'],month=job['month'],obtained_verified_new_videos=n,examined_video_pages=len(records),visible_new_title_match_candidates=len(job['selected']),whole_month_query_count='',whole_month_completeness='',acquisition='fixed-seed sample from visible economy/inflation public search results; target one verified new video per channel-month',status=job['status'],month_complete=False))
 p=PROV/'youtube_web_monthly_status.csv'
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 # Incorporate the public-web sample into the common source x month report.
 common=PROV/'source_month_completeness.csv'
 if common.exists():
  with common.open() as f:
   reader=csv.DictReader(f);fields=reader.fieldnames;old=[r for r in reader if not r['source'].startswith('YouTubeWeb/')]
  for r in rows:
   x=dict.fromkeys(fields,'');x.update(source='YouTubeWeb/'+r['source'].split('/')[-1],month=r['month'],obtained_unique=r['obtained_verified_new_videos'],eligible_unique=r['obtained_verified_new_videos'],count_scope='reduced sample from public search results; no whole-month denominator',notes=r['acquisition']+'; '+r['status']);old.append(x)
  tmp=common.with_suffix('.tmp')
  with tmp.open('w',newline='') as f:
   w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(old)
  tmp.replace(common)
 print(json.dumps(dict(status=s['status'],verified_new_videos=sum(r['obtained_verified_new_videos'] for r in rows),strata_with_new_video=sum(r['obtained_verified_new_videos']>0 for r in rows),planned_strata=len(rows),as_of_utc=dt.datetime.now(dt.timezone.utc).isoformat())))
if __name__=='__main__':main()
