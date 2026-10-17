"""Source x month collection completeness, deterministic eligibility, no text analysis."""
from common import *
from collections import defaultdict,Counter

def write(name,rows):
 if not rows:return
 p=PROV/name;tmp=p.with_suffix('.tmp')
 with tmp.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 tmp.replace(p)

def periods(first='2010-01'):
 y,m=map(int,first.split('-'))
 while f'{y:04}-{m:02}'<=CUTOFF[:7]:
  yield f'{y:04}-{m:02}';y,m=(y+1,1) if m==12 else (y,m+1)

def main():
 out=[];notes={}
 def add(source,month,n,expected,method,note,eligible='',scope_n=None,complete='',planned=''):
  numerator=n if scope_n is None else scope_n
  ratio=numerator/expected if isinstance(expected,(int,float)) and expected>0 else ''
  out.append(dict(source=source,month=month,obtained_unique=n,eligible_unique=eligible,retrieved_in_count_scope=numerator,query_count=expected,completeness_ratio=ratio,count_scope=method,complete_units=complete,planned_units=planned,notes=note))
 # Latest snapshot of each NYT requested month; global IDs assigned once.
 paths={}
 for p in sorted((ROOT/'corpus/raw/N01').rglob('*.json')):
  label=p.name[:7]
  if re.fullmatch(r'\d{4}-\d{2}',label):paths[label]=p
 canon={};hits={};membership=defaultdict(set);fields=defaultdict(Counter);latest_snapshot={}
 for month,p in sorted(paths.items()):
  o=json.loads(p.read_bytes())['response'];hits[month]=o['meta']['hits'];latest_snapshot[month]=len({x['_id'] for x in o['docs']})
  for item in o['docs']:
   identifier=item['_id'];date=item.get('pub_date','')[:7];membership[identifier].add(month)
   # Prefer the response whose requested month equals the publication month.
   if identifier not in canon or date==month:canon[identifier]=(month,date)
   period='pre2025' if month<'2025-01' else '2025on'
   for field in ['section_name','document_type','type_of_material']:
    fields[(field,str(item.get(field,'')))][period]+=1
 counts=Counter(x[0] for x in canon.values());cross=sum(len(v)>1 for v in membership.values())
 for month in sorted(paths):
  add('NYT',month,counts[month],hits[month],'latest monthly Archive snapshot; API-count ratio not calendar completeness', 'Globally deduplicated by _id; known source-truncated month.' if month in ['2026-01','2026-10'] else 'Globally deduplicated by _id; response-count ratio is not calendar completeness.',scope_n=latest_snapshot[month])
 crosswalk=[]
 for (field,value),c in sorted(fields.items()):
  normalized=('Business' if field=='section_name' and value in ['Business Day','Business'] else value.casefold() if field in ['document_type','type_of_material'] else value)
  crosswalk.append(dict(field=field,raw_value=value,pre2025_rows=c['pre2025'],from2025_rows=c['2025on'],comparison_key=normalized,mapping_basis='Business Day / Business explicit user-audit correspondence' if normalized=='Business' else 'case normalization only; distinct meanings not merged'))
 write('nyt_schema_crosswalk.csv',crosswalk)
 notes['nyt']=dict(unique_ids=len(canon),ids_present_in_multiple_requested_months=cross,allocation='Prefer requested month equal to pub_date month; otherwise first requested month. No raw changes.',refresh=json.loads((PROV/'nyt_refresh_state.json').read_text()))
 write('nyt_cross_month_duplicates.csv',[dict(id=k,requested_months='|'.join(sorted(v)),month_count=len(v)) for k,v in membership.items() if len(v)>1])
 del canon,membership
 # Guardian body absence is described using source-provided content type.
 guardian=defaultdict(dict);ghits={};missing=[]
 for p in (ROOT/'corpus/raw/N02').rglob('*.json'):
  if not re.fullmatch(r'\d{4}-\d{2}_\d{4}\.json',p.name):continue
  month=p.name[:7];r=json.loads(p.read_bytes())['response'];ghits[month]=r['total']
  for item in r['results']:guardian[month][item['id']]=item
 for month,items in sorted(guardian.items()):
  missing_types=Counter()
  for item in items.values():
   if not item.get('fields',{}).get('bodyText'):
    typ=item.get('type','unknown');missing_types[typ]+=1;missing.append(dict(id=item['id'],month=month,source_type=typ,missing_body=True,interpretation='non_article_format' if typ in ['video','gallery','picture','interactive'] else 'body_missing_needs_source_check'))
  add('Guardian',month,len(items),ghits[month],'business/useconomy tag; monthly API result count','Missing body by source type: '+json.dumps(missing_types),eligible=sum(bool(i.get('fields',{}).get('bodyText')) for i in items.values()))
 write('guardian_missing_body_status.csv',missing);notes['guardian_missing_body']=dict(Counter(r['source_type'] for r in missing))
 del guardian
 # MC old broad-window and daily responses overlap; count each story ID once.
 mc=defaultdict(dict);expected=Counter();completed=Counter();planned=Counter()
 for p in (ROOT/'corpus/raw/N03').rglob('*.json'):
  if p.name.endswith('_monitoring_union_counts.json'):
   cid=p.name.split('_')[0]
   for d in json.loads(p.read_bytes())['count_over_time']['counts']:expected[(cid,d['date'][:7])]+=d['count']
  elif '_stories_' in p.name or p.name.startswith('daily_'):
   cid=p.name.split('_')[1] if p.name.startswith('daily_') else p.name.split('_')[0]
   for item in json.loads(p.read_bytes()).get('stories',[]):mc[cid][str(item['id'])]=item.get('publish_date','')[:7]
 state=json.loads((PROV/'mediacloud_daily_state.json').read_text())
 for d in state['days']:
  planned[(d['collection_id'],d['date'][:7])]+=1;completed[(d['collection_id'],d['date'][:7])]+=d['complete']
 daily_status=[dict(collection_id=d['collection_id'],date=d['date'],rows=d['rows'],pages=d['page'],status='complete_day' if d['complete'] else 'nonrandom_partial_day' if d['page'] else 'not_started',eligible_as_complete_day=d['complete']) for d in state['days']]
 write('mediacloud_day_eligibility.csv',daily_status)
 for cid,items in mc.items():
  counts=Counter(items.values())
  for month in periods('2025-01'):
   add('MediaCloud/'+cid,month,counts[month],expected.get((cid,month),''),'full-month matching-query count snapshot; broad and daily responses deduplicated','Incomplete old days are nonrandom indexed-time prefixes, not eligible as complete-day data; counts can drift across snapshots.',complete=completed[(cid,month)],planned=planned[(cid,month)])
 del mc
 # Reddit: exact ID dedup across overlapping probe/leaf pages; snapshot metrics.
 reddit=defaultdict(dict)
 for p in sorted((ROOT/'corpus/raw/SM02').rglob('*.json')):
  if not(p.name.startswith('posts_') or p.name.startswith('probe_')):continue
  for x in json.loads(p.read_bytes()).get('data',[]):
   if 'created_utc' not in x:continue
   month=dt.datetime.fromtimestamp(x['created_utc'],dt.timezone.utc).strftime('%Y-%m');day=dt.datetime.fromtimestamp(x['created_utc'],dt.timezone.utc).day
   reddit[x['subreddit'].lower()][x['id']]=(month,day,x.get('selftext',''),x.get('retrieved_on'))
 rs=json.loads((PROV/'reddit_collection_state.json').read_text());sampling=rs.get('personalfinance_sampling',{}).get('selected_days',{});denoms={};sampledenoms={};quality=[]
 for p in (ROOT/'corpus/raw/SM02').rglob('counts_v3_*.json'):
  sub,month=p.stem[len('counts_v3_'):].rsplit('_',1);buckets=json.loads(p.read_bytes()).get('data',[])
  denoms[(sub.lower(),month)]=sum(int(x['count']) for x in buckets)
 for sub,items in reddit.items():
  groups=defaultdict(list)
  for x in items.values():groups[x[0]].append(x)
  for month in periods():
   records=groups[month];sample=sub=='personalfinance' and month<'2025-01';chosen=[x for x in records if x[1] in sampling.get(month,[])] if sample else records
   exp=(sampledenoms if sample else denoms).get((sub,month),'');n=len(chosen)
   count_note=''
   if isinstance(exp,int) and exp<n:count_note='API count lower than acquired unique rows: denominator invalid, ratio withheld';exp=''
   add('Reddit/'+sub,month,len(records),exp,'3 seeded uniform days/month; complete selected-day clusters' if sample else 'exhaustive monthly archive query',count_note+'; retrieved_on retained. score/num_comments are archive-retrieval snapshots, not comparable across years.',eligible=n,scope_n=n)
   removed=sum(x[2].strip().casefold()=='[removed]' for x in chosen);deleted=sum(x[2].strip().casefold()=='[deleted]' for x in chosen)
   quality.append(dict(source=sub,month=month,scope='selected_random_days' if sample else 'all_acquired_unique_posts',records=n,removed=removed,deleted=deleted,removed_ratio=removed/n if n else '',deleted_ratio=deleted/n if n else '',combined_ratio=(removed+deleted)/n if n else '',missing_retrieved_on=sum(x[3] is None for x in chosen)))
 write('reddit_monthly_content_availability.csv',quality)
 del reddit
 # YouTube: separate search count scope from uniform title eligibility.
 registry={r['video_id']:r for r in csv.DictReader((PROV/'youtube_video_acquisition_registry.csv').open())}
 vg=defaultdict(set);ve=defaultdict(set);vr=defaultdict(set)
 for vid,v in registry.items():
  if v['in_period']!='True':continue
  key=(v['channel'],v['published'][:7]);vg[key].add(vid);vr[key].update(v['routes'].split('|'))
  if v['included']=='True':ve[key].add(vid)
 for (cid,month),ids in sorted(vg.items()):add('YouTubeVideo/'+cid,month,len(ids),'','|'.join(sorted(vr[(cid,month)])),'Uniform title regex; API search totals approximate and not a denominator for combined upload+search universe.',eligible=len(ve[(cid,month)]))
 ys=json.loads((PROV/'youtube_window_search_state.json').read_text());qrows=[]
 for d in ys['queries']:
  qrows.append(dict(channel=d['channel'],start=d['start'],end=d['end'],method=d['route'],pages=d['page'],unique_ids=len(d['ids']),query_estimate=d.get('expected_api_estimate',''),pagination_complete=d['complete'],completion=d.get('completion','pending')))
 write('youtube_search_window_completeness.csv',qrows)
 # No exact API denominator exists for comments in only the first 30 days.
 comments=defaultdict(set);outside=Counter()
 for p in (ROOT/'corpus/raw/SM01').rglob('comment_text_*.json'):
  vid=p.name[len('comment_text_'):].rsplit('_',1)[0];v=registry.get(vid)
  if not v or v['included']!='True':continue
  pub=dt.datetime.fromisoformat(v['published'].replace('Z','+00:00'));end=min(pub+dt.timedelta(days=30),dt.datetime.fromisoformat(CUTOFF).replace(tzinfo=dt.timezone.utc)+dt.timedelta(days=1));key=(v['channel'],v['published'][:7])
  for item in json.loads(p.read_bytes()).get('items',[]):
   c=item['snippet']['topLevelComment'];when=dt.datetime.fromisoformat(c['snippet']['publishedAt'].replace('Z','+00:00'))
   if pub<=when<end:comments[key].add(c['id'])
   else:outside[key]+=1
 cs=json.loads((PROV/'youtube_comment_text_state.json').read_text());done=Counter();planned=Counter()
 for vid,v in registry.items():
  if v['included']!='True':continue
  key=(v['channel'],v['published'][:7]);planned[key]+=1;done[key]+=cs['videos'].get(vid,{}).get('status')=='complete_top_level'
 for key,n in sorted(planned.items()):
  add('YouTubeComment30d/'+key[0],key[1],len(comments[key]),'','eligible video publication month; first 30 days intersected with study cutoff','No exact 30-day comment denominator. Later comments retained in immutable responses only because time pagination must traverse them.',complete=done[key],planned=n)
 for source in ['GDELT','MediaBiasRatings']:
  for month in periods():add(source,month,0,'','unavailable','GDELT: no further retries by user instruction.' if source=='GDELT' else 'No numerical rating data acquired; not daily-frequency data.')
 write('source_month_completeness.csv',out)
 notes.update(as_of_utc=dt.datetime.now(dt.timezone.utc).isoformat(),rows=len(out),ratios='Only comparable API count scopes. Blank means unavailable/invalid denominator; never interpreted as zero or 100%. NYT response-count ratio is separate from temporal gaps.')
 (PROV/'monthly_audit_summary.json').write_text(json.dumps(notes,indent=2))
 print(json.dumps(notes,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
