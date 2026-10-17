"""Corpus main table corpus/items.parquet (task_guide 6.2, 8.2-8.4).

In scope = the unit's own text matches at least one economic TERM (same rule as the annotation
sampling frame), published 2010-01-01..CUTOFF. Units and designs:
 NYT          headline + abstract + lead paragraph (2025+: no lead paragraph in source), full monthly archive
 Guardian     headline + standfirst + full body text (text = standfirst + newline + body; standfirst may be empty), business/US-economy tag, full monthly archive
 Media Cloud  story title, seeded random full-day clusters (US National / US State & Local)
 Reddit       title + selftext; economy/Economics random full-day clusters 2015-2024; personalfinance random
              circular windows 2010-2026; economy/Economics/inflation exhaustive monthly queries 2025-01..CUTOFF;
              inflation exhaustive monthly queries for all months
 YouTube      top-level comments within 30 days of video publication (freeze v1); non-probability
sample_weight = 1 / inclusion probability within source x month (blank for YouTube).
Duplicates: union-find over identical normalized URL, identical normalized text, and near-duplicates
(MinHash LSH over word 3-shingles, 128 permutations, 32 bands x 4 rows, verified Jaccard >= 0.8,
texts with >= 8 words).
"""
import csv,glob,html,json,re,sys,zlib,calendar,collections,datetime as dt
from pathlib import Path
from urllib.parse import urlsplit
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src/collect'))
from youtube_details import TERMS
CUTOFF='2026-10-14'
TERM_RE={t:re.compile(r'\b'+re.escape(t)+r'\b',re.I) for t in TERMS}
SEL=ROOT/'provenance/monthly_cluster_selections'

def clean(t):return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',t or ''))).strip()
def terms(text):return [t for t,r in TERM_RE.items() if r.search(text)]
def days_observable(month):
 y,m=map(int,month.split('-'));n=calendar.monthrange(y,m)[1]
 return min(n,int(CUTOFF[8:])) if month==CUTOFF[:7] else n
def rel(p):return str(Path(p).resolve().relative_to(ROOT))

def nyt():
 for f in sorted(glob.glob(str(ROOT/'corpus/raw/N01/*/[0-9][0-9][0-9][0-9]-[0-9][0-9]*.json'))):
  for d in json.loads(Path(f).read_bytes()).get('response',{}).get('docs',[]):
   if (d.get('document_type') or '').lower()!='article':continue
   title=clean((d.get('headline') or {}).get('main'));body=[]
   for k in ['abstract','lead_paragraph']:
    t=clean(d.get(k))
    if t and t!=title and t not in body:body.append(t)
   tom=(d.get('type_of_material') or '')
   yield dict(source='NYT',outlet_name='The New York Times',source_level='national',platform='news_api',unit_type='headline_abstract_lead' if d.get('lead_paragraph') else 'headline_abstract',
    pub_datetime_utc=d.get('pub_date'),url=d.get('web_url'),title=title,text='\n'.join(body),text_license='snippet_only',source_item_id=d['_id'],
    section=d.get('section_name') or '',type_of_material=tom,raw_file=rel(f),design='full_archive',month_key=None)

def guardian():
 for f in sorted(glob.glob(str(ROOT/'corpus/raw/N02/*/[0-9][0-9][0-9][0-9]-[0-9][0-9]_*.json'))):
  for r in json.loads(Path(f).read_bytes()).get('response',{}).get('results',[]):
   fl=r.get('fields',{})
   if r.get('type')!='article':continue
   yield dict(source='Guardian',outlet_name='The Guardian',source_level='national',platform='news_api',unit_type='full_text',pub_datetime_utc=r.get('webPublicationDate'),url=r.get('webUrl'),
    title=clean(fl.get('headline') or r.get('webTitle')),text=clean(fl.get('trailText'))+'\n'+clean(fl.get('bodyText')),text_license='full',source_item_id=r['id'],
    section=r.get('sectionName',''),type_of_material='hosted' if r.get('isHosted') else '',raw_file=rel(f),design='full_archive',month_key=None)

def mediacloud():
 for coll,level,name in [('34412234','national','MediaCloud_National'),('38379429','local','MediaCloud_Local')]:
  files=sorted(SEL.glob(f'mediacloud_{coll}_*.json'));per_month=collections.Counter(json.loads(f.read_text())['date'][:7] for f in files)
  for f in files:
   s=json.loads(f.read_text());ids=set(s['unique_ids']);m=s['date'][:7];w=days_observable(m)/per_month[m]
   for rf in s['raw_files']:
    for st in json.loads((ROOT/rf).read_bytes()).get('stories',[]):
     if st['id'] in ids and st.get('language','en')=='en':
      ids.discard(st['id'])
      yield dict(source=name,outlet_name=st.get('media_name') or '',source_level=level,platform='media_cloud',unit_type='headline',pub_datetime_utc=str(st.get('publish_date') or ''),url=st.get('url'),
       title=clean(st.get('title')),text='',text_license='snippet_only',source_item_id=st['id'],section='',type_of_material='',raw_file=rf,design='random_day_cluster',sample_weight=w,sample_date=s['date'])

def reddit_post(p,rf,design,w,sample_date=''):
 body=p.get('selftext') or ''
 return dict(source='Reddit',outlet_name='r/'+p.get('subreddit',''),source_level='social',platform='reddit',unit_type='post',
  pub_datetime_utc=dt.datetime.fromtimestamp(int(p['created_utc']),dt.timezone.utc).isoformat(),url='https://www.reddit.com/comments/'+p['id'],title=clean(p.get('title')),
  text='' if body.strip() in ('[removed]','[deleted]') else clean(body),text_license='full',source_item_id=p['id'],section='',type_of_material='',raw_file=rf,design=design,sample_weight=w,sample_date=sample_date,
  engagement_likes=p.get('score'),engagement_replies=p.get('num_comments'),body_status=body.strip() if body.strip() in ('[removed]','[deleted]') else '')

def reddit():
 for pat,design in [('reddit_economy_*','random_day_cluster'),('reddit_Economics_*','random_day_cluster'),('reddit_personalfinance_window_v1_*','random_circular_window')]:
  files=sorted(SEL.glob(pat));per_month=collections.Counter(json.loads(f.read_text())['date'][:7] for f in files)
  for f in files:
   s=json.loads(f.read_text());ids=set(s['unique_ids']);m=s['date'][:7]
   w=1/s['inclusion_probability'] if design=='random_circular_window' else days_observable(m)/per_month[m]
   for rf in s['raw_files']:
    for p in json.loads((ROOT/rf).read_bytes()).get('data',[]):
     if p['id'] in ids:ids.discard(p['id']);yield reddit_post(p,rf,design,w,s['date'])
 # Exhaustive monthly archive queries: inflation (all months), economy/Economics (2025-01 onward).
 seen=set()
 for f in sorted(glob.glob(str(ROOT/'corpus/raw/SM02/*/posts_*.json'))):
  sub=Path(f).name.split('_')[1]
  if sub not in ('inflation','economy','Economics'):continue
  for p in json.loads(Path(f).read_bytes()).get('data',[]):
   created=dt.datetime.fromtimestamp(int(p['created_utc']),dt.timezone.utc).date().isoformat()
   if (sub=='inflation' or created>='2025-01-01') and (sub,p['id']) not in seen:
    seen.add((sub,p['id']));yield reddit_post(p,rel(f),'exhaustive_month',1.0)

def youtube():
 freeze=sorted(glob.glob(str(ROOT/'provenance/youtube_freeze_v1_*')))[-1]
 cand={r['video_id']:r for r in csv.DictReader(open(Path(freeze)/'youtube_claude_candidates.csv'))}
 names={r['channel_id']:(r['name'],r['collection_group']) for r in csv.DictReader(open(ROOT/'provenance/youtube_channels.csv'))}
 for r in csv.DictReader(open(Path(freeze)/'youtube_comment_videos_manifest.csv')):
  start=dt.datetime.fromisoformat(r['published'].replace('Z','+00:00'));end=min(start+dt.timedelta(days=30),dt.datetime.fromisoformat(CUTOFF+'T23:59:59+00:00'));seen=set()
  for f in r['comment_files'].split('|'):
   for it in json.loads((ROOT/f).read_bytes()).get('items',[]):
    sn=it['snippet']['topLevelComment']['snippet'];t=dt.datetime.fromisoformat(sn['publishedAt'].replace('Z','+00:00'))
    if start<=t<=end and it['id'] not in seen:
     seen.add(it['id'])
     yield dict(source='YouTube',outlet_name=names.get(r['channel'],(r['channel'],''))[0],source_level='social',platform='youtube',unit_type='comment',pub_datetime_utc=sn['publishedAt'],
      url='https://www.youtube.com/watch?v='+r['video_id'],title='',text=clean(sn['textDisplay']),text_license='full',source_item_id=it['id'],section='',type_of_material='',raw_file=f,
      design='non_probability_video_selection',sample_weight=None,engagement_likes=sn.get('likeCount'),engagement_replies=it['snippet'].get('totalReplyCount'),
      video_id=r['video_id'],video_title=cand.get(r['video_id'],{}).get('title',''),video_channel_group=names.get(r['channel'],('',''))[1],video_search_only_supplement=r['search_only_supplement'])

TRACKING=re.compile(r'^(utm_|fbclid$|gclid$|mc_cid$|mc_eid$|cmpid$|ref$|ref_src$|taid$|smid$|partner$)')
def norm_url(u):
 # Host and path case-folded, fragment and tracking parameters dropped; other query parameters kept,
 # since many outlets identify the story only in the query string.
 if not u:return ''
 s=urlsplit(u.strip());q='&'.join(sorted(x for x in s.query.split('&') if x and not TRACKING.match(x.split('=',1)[0].lower())))
 return s.netloc.lower().removeprefix('www.')+s.path.rstrip('/').lower()+('?'+q if q else '')

def norm_text(t):return re.sub(r'[^a-z0-9 ]','',re.sub(r'\s+',' ',t.lower())).strip()

class UF:
 def __init__(s,n):s.p=list(range(n))
 def f(s,x):
  while s.p[x]!=x:s.p[x]=s.p[s.p[x]];x=s.p[x]
  return x
 def u(s,a,b):
  a,b=s.f(a),s.f(b)
  if a!=b:s.p[max(a,b)]=min(a,b)

def near_duplicates(texts,uf,threshold=0.8,perms=128,bands=32):
 # h(x) = (a*x + b) mod p with p the largest prime below 2**32, so a*x + b < 2**64 in uint64.
 rows=perms//bands;rng=np.random.default_rng(20261015);P=4294967291
 A=rng.integers(1,P,perms,dtype=np.uint64);B=rng.integers(0,P,perms,dtype=np.uint64)
 shingles={};buckets=collections.defaultdict(list)
 for i,t in enumerate(texts):
  w=t.split()
  if len(w)<8:continue
  sh={zlib.crc32(' '.join(w[j:j+3]).encode()) for j in range(len(w)-2)};shingles[i]=sh
  x=np.fromiter(sh,dtype=np.uint64)%np.uint64(P)
  sig=((np.outer(A,x)+B[:,None])%np.uint64(P)).min(axis=1)
  for k in range(bands):buckets[(k,sig[k*rows:(k+1)*rows].tobytes())].append(i)
 pairs=0
 for ids in buckets.values():
  if len(ids)<2:continue
  for j in ids[1:]:
   if uf.f(j)==uf.f(ids[0]):continue
   s1,s2=shingles[ids[0]],shingles[j]
   if len(s1&s2)/len(s1|s2)>=threshold:uf.u(ids[0],j);pairs+=1
 return pairs

def main():
 sources_csv={r['file_path']:r['downloaded_at_utc'] for r in csv.DictReader(open(ROOT/'provenance/sources.csv'))}
 collected=collections.Counter();items=[]
 for gen in [nyt,guardian,mediacloud,reddit,youtube]:
  for u in gen():
   date=(u['pub_datetime_utc'] or '')[:10]
   if not ('2010-01-01'<=date<=CUTOFF):continue
   month=date[:7];collected[(u['source'],u['outlet_name'] if u['source']=='Reddit' else '',month)]+=1
   hit=terms(u['title']+'\n'+u['text'])
   if not hit:continue
   u['query_terms_matched']='|'.join(hit);u['month']=month;items.append(u)
 df=pd.DataFrame(items)
 df=df.drop_duplicates(subset=['source','source_item_id'],keep='first').reset_index(drop=True)
 if 'sample_weight' not in df:df['sample_weight']=None
 df.loc[df.design=='full_archive','sample_weight']=1.0
 df['collected_at_utc']=df.raw_file.map(sources_csv)
 url_l=df.url.fillna('').str.lower()
 df['is_ad']=(df.type_of_material.isin(['hosted','Advertisement','Paid Post'])|url_l.str.contains(r'/(?:sponsored|sponsor-content|paid-content|advertorial)s?/',regex=True)).astype(bool)
 df['is_obituary']=(df.type_of_material.isin(['Obituary','Obituary (Obit)','Paid Death Notice'])|url_l.str.contains('/obituar',regex=False)).astype(bool)
 # Duplicate clusters.
 uf=UF(len(df));first={}
 nt=(df.title+' '+df.text).map(norm_text)
 for key in [df.url.map(norm_url).where(df.platform.isin(['news_api','media_cloud']),''),nt]:
  for i,k in enumerate(key):
   if not k:continue
   if k in first:uf.u(first[k],i)
   else:first[k]=i
  first={}
 pairs=near_duplicates(list(nt),uf)
 root=[uf.f(i) for i in range(len(df))];df['dedup_cluster_id']=root
 df['_t']=pd.to_datetime(df.pub_datetime_utc.str[:19],errors='coerce')
 order=df.sort_values(['_t','source','source_item_id']).index
 first_in_cluster={};first_outlet={};dup=[False]*len(df);rep=[False]*len(df)
 for i in order:
  c=root[i];o=df.at[i,'outlet_name']
  if c in first_in_cluster:
   if (c,o) in first_outlet:dup[i]=True
   else:rep[i]=True
  first_in_cluster.setdefault(c,i);first_outlet.setdefault((c,o),i)
 df['is_duplicate']=dup;df['is_repost']=rep;df['cluster_size']=df.groupby('dedup_cluster_id').source.transform('size')
 df['dedup_cluster_id']=df.dedup_cluster_id.map(lambda c:f'c{c:07}')
 df['is_suspected_automated']=pd.NA
 df['geo_state']=pd.NA
 subs={}
 for f in glob.glob(str(ROOT/'corpus/raw/SM02/*/subreddit_*.json')):
  o=json.loads(Path(f).read_bytes());d=o.get('data',o)
  d=d[0] if isinstance(d,list) and d else d
  if isinstance(d,dict) and d.get('subscribers') is not None:subs['r/'+Path(f).stem.split('_',1)[1]]=f"subscribers={d['subscribers']} (archive snapshot)"
 df['audience_info']=df.outlet_name.map(subs)
 df['engagement_reposts']=pd.NA
 df['item_id']=[f'{s}:{i}' for s,i in zip(df.source,df.source_item_id)]
 cols=['item_id','source','outlet_name','source_level','platform','unit_type','pub_datetime_utc','month','url','title','text','text_license','query_terms_matched','geo_state','audience_info',
  'dedup_cluster_id','cluster_size','is_duplicate','is_repost','is_ad','is_obituary','is_suspected_automated','engagement_likes','engagement_reposts','engagement_replies','collected_at_utc',
  'design','sample_weight','sample_date','section','type_of_material','body_status','video_id','video_title','video_channel_group','video_search_only_supplement','source_item_id','raw_file']
 for c in cols:
  if c not in df:df[c]=pd.NA
 df=df[cols].sort_values(['pub_datetime_utc','item_id']).reset_index(drop=True)
 for c in ['sample_weight']:df[c]=pd.to_numeric(df[c])
 for c in ['engagement_likes','engagement_replies','engagement_reposts']:df[c]=pd.to_numeric(df[c]).astype('Int64')
 for c in ['sample_date','section','type_of_material','body_status','video_id','video_title','video_channel_group','video_search_only_supplement','audience_info','geo_state','collected_at_utc']:df[c]=df[c].astype('string')
 df['is_suspected_automated']=df.is_suspected_automated.astype('boolean')
 (ROOT/'corpus').mkdir(exist_ok=True);df.to_parquet(ROOT/'corpus/items.parquet',index=False)
 with open(ROOT/'corpus/source_month_counts.csv','w',newline='') as f:
  w=csv.writer(f);w.writerow(['source','subreddit','month','collected_in_period','in_scope_keyword','in_scope_not_duplicate','in_scope_not_duplicate_not_repost'])
  d=df.assign(sub=df.outlet_name.where(df.source=='Reddit',''))
  n_all=d.groupby(['source','sub','month']).size();n_nd=d[~d.is_duplicate].groupby(['source','sub','month']).size();n_ndr=d[~d.is_duplicate&~d.is_repost].groupby(['source','sub','month']).size()
  for (s,sub,m),n in sorted(collected.items()):
   k=(s,sub,m);w.writerow([s,sub,m,n,int(n_all.get(k,0)),int(n_nd.get(k,0)),int(n_ndr.get(k,0))])
 stats=dict(rows=len(df),by_source=df.source.value_counts().to_dict(),near_duplicate_merges=pairs,duplicates=int(df.is_duplicate.sum()),reposts=int(df.is_repost.sum()),ads=int(df.is_ad.sum()),obituaries=int(df.is_obituary.sum()),
  generated_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
 (ROOT/'corpus/items_stats.json').write_text(json.dumps(stats,indent=2));print(json.dumps(stats))

if __name__=='__main__':main()
