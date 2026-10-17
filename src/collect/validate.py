"""Integrity checks and file inventory only. Does not clean, label, or model data."""
from common import *
import pandas as pd
import re

def describe(path):
 name=path.name;ds=path.parts[-3];b=path.read_bytes()
 rows='';start='';end='';kind='documentation';note=''
 if name.endswith('.json'):
  o=json.loads(b)
  if ds=='N01' and 'docs' in o.get('response',{}):
   a=o['response']['docs'];rows=len(a);dates=[x['pub_date'] for x in a if x.get('pub_date')];start=min(dates,default='');end=max(dates,default='');kind='nyt_articles';note='Whole monthly archive, no economic filtering; current month partial and UTC dates may exceed cutoff day'
  elif ds=='N02' and 'results' in o.get('response',{}) and not name.startswith('tag_'):
   r=o['response'];a=r['results'];rows=len(a);dates=[x['webPublicationDate'] for x in a if x.get('webPublicationDate')];start=min(dates,default='');end=max(dates,default='');kind='guardian_articles';note=f"page={r.get('currentPage')}/{r.get('pages')}; total={r.get('total')}; missing_bodyText={sum(not x.get('fields',{}).get('bodyText') for x in a)}; canonical US economy tag"
  elif ds=='SM02' and name.startswith(('posts_','probe_','sample_posts_','cluster_posts_')) and isinstance(o.get('data'),list):
   a=o['data'];rows=len(a);dates=[dt.datetime.fromtimestamp(x['created_utc'],dt.timezone.utc).isoformat() for x in a];start=min(dates,default='');end=max(dates,default='');kind='reddit_interval_probe' if name.startswith('probe_') or len(a)>=100 else 'reddit_window_cluster_leaf' if name.startswith('cluster_posts_window_') else 'reddit_temporal_sample' if name.startswith('sample_posts_') else 'reddit_day_cluster_leaf' if name.startswith('cluster_posts_') else 'reddit_posts';note='Arctic Shift community archive; server-selected author-free fields; saturated parent probes overlap leaf responses and must not be added to unique post counts; window leaves do not imply whole-day completeness'
  elif ds=='SM02' and name.startswith('subreddit_'):
   rows=len(o.get('data',[]));kind='subreddit_metadata';note='Archive snapshot, not a live subscriber count'
  elif 'observations' in o:
   a=o['observations'];rows=len(a);dates=[x['date'] for x in a];start=min(dates,default='');end=max(dates,default='');kind='observation_vintage_rows'
   note=f"API total={o['count']}; page offset={o['offset']}; missing-value rows={sum(x['value']=='.' for x in a)}"
   if name.startswith('NASDAQCOM_window_'):
    kind='observation_window_rows';note+='; contiguous real-time query windows clip validity intervals; rows are not distinct revisions'
  elif 'vintage_dates' in o:
   a=o['vintage_dates'];rows=len(a);start=min(a,default='');end=max(a,default='');kind='vintage_dates'
  elif 'release_dates' in o:
   a=o['release_dates'];rows=len(a);dates=[x['date'] for x in a];start=min(dates,default='');end=max(dates,default='');kind='source_release_dates'
  elif 'count_over_time' in o:
   a=o['count_over_time']['counts'];rows=len(a);dates=[x['date'] for x in a];start=min(dates,default='');end=max(dates,default='');kind='daily_news_counts';note='API counts; article totals are not downloaded article counts'
  elif 'sample' in o:
   a=o['sample'];rows=len(a);dates=[x['publish_date'] for x in a if x.get('publish_date')];start=min(dates,default='');end=max(dates,default='');kind='news_random_sample';note='Official random sample, not a complete day'
  elif 'stories' in o:
   a=o['stories'];rows=len(a);dates=[x['publish_date'] for x in a if x.get('publish_date')];start=min(dates,default='');end=max(dates,default='');kind='news_stories';note='next_page='+str(bool(o.get('pagination_token')))
  elif ds=='SM01' and name.startswith('uploads_'):
   a=o['items'];rows=len(a);dates=[x['contentDetails']['videoPublishedAt'] for x in a if x.get('contentDetails',{}).get('videoPublishedAt')];start=min(dates,default='');end=max(dates,default='');kind='video_inventory';note='Unfiltered public news uploads; no private author fields requested'
  elif ds=='SM01' and name.startswith('channel_'):rows=len(o.get('items',[]));kind='channel_metadata'
  elif ds=='SM01' and name.startswith('search_'):
   a=o.get('items',[]);rows=len(a);dates=[x['snippet']['publishedAt'] for x in a];start=min(dates,default='');end=max(dates,default='');kind='video_search_results';note='Official API search; quarter boundaries and pagination state recorded; not a census'
  elif ds=='SM01' and name.startswith('videos_'):
   a=o.get('items',[]);rows=len(a);dates=[x['snippet']['publishedAt'] for x in a];start=min(dates,default='');end=max(dates,default='');kind='video_statistics'
  elif ds=='SM01' and name.startswith('comment_text_'):
   a=o.get('items',[]);rows=len(a);dates=[x['snippet']['topLevelComment']['snippet']['publishedAt'] for x in a];start=min(dates,default='');end=max(dates,default='');kind='comment_text';note='API textDisplay plain text; no author fields; top-level comments only; may overlap earlier metadata snapshots'
  elif ds=='SM01' and name.startswith('comments_'):
   a=o.get('items',[]);rows=len(a);dates=[x['snippet']['topLevelComment']['snippet']['publishedAt'] for x in a];start=min(dates,default='');end=max(dates,default='');kind='comment_metadata'
 elif name.endswith('.csv') or b.startswith(b'yyyymm,'):
  d=pd.read_csv(path,low_memory=False);rows=len(d);kind='time_series_rows'
  if 'yyyymm' in d:dates=pd.to_datetime(d['yyyymm'].astype(str),format='%Y%m').dt.strftime('%Y-%m-%d')
  elif 'YYYYMM' in d:dates=pd.to_datetime(d['YYYYMM'].astype(str),format='%Y%m').dt.strftime('%Y-%m-%d');kind='anonymous_survey_cases'
  elif 'Month' in d and 'YYYY' in d:dates=pd.to_datetime(d.Month+' '+d.YYYY.astype(str),format='%B %Y').dt.strftime('%Y-%m-%d')
  else:
   dates=pd.to_datetime(d.iloc[:,0],errors='coerce').dropna().dt.strftime('%Y-%m-%d')
  if len(dates):start=min(dates);end=max(dates)
  note=f'columns={len(d.columns)}; missing cells={int(d.isna().sum().sum())}; original values retained'
 elif name.endswith(('.xls','.xlsx')):
  if ds in ['S01','S02','S03','S04']:
   d=pd.read_excel(path,header=None);kind='survey_table';rows=d.shape[0];note='Rows include headers and notes; not the count of statistical observations'
   # Historical table is one observation month per row, with year in column 2.
   if 'historical' in name:
    obs=d[d.iloc[:,1].astype(str).str.fullmatch(r'\d{4}\.0')];dates=pd.to_datetime(obs.iloc[:,0].str.strip()+' '+obs.iloc[:,1].astype(int).astype(str),format='%B %Y').dt.strftime('%Y-%m-%d')
    rows=len(obs);start=min(dates);end=max(dates);kind='party_month_rows';note='Sparse before monthly party questions began; do not interpolate'
  elif ds=='M13':
   d=pd.read_excel(path);rows=len(d);start=d.Month.min();end=d.Month.max();kind='monthly_affordability';note='Latest snapshot only; source does not supply a vintage archive in this file'
  elif ds=='N05':
   d=pd.read_excel(path,sheet_name='Data');rows=len(d);dates=pd.to_datetime(d.iloc[:,0]).dt.strftime('%Y-%m-%d');start=min(dates);end=max(dates);kind='daily_sentiment'
  elif ds=='R05':
   b=pd.ExcelFile(path);kind='professional_forecasts';counts=[];dates=[]
   for sheet in (['RGDP','UNEMP','PCE'] if 'Level' in name else ['RGDP']):
    d=pd.read_excel(b,sheet_name=sheet);counts.append(len(d));dates.extend(d.YEAR.astype(int).astype(str)+'Q'+d.QUARTER.astype(int).astype(str))
   rows=sum(counts);start=min(dates);end=max(dates);note='Count sums requested sheets only; workbook contains additional series'
  elif ds=='M17':
   book=pd.ExcelFile(path)
   if 'DATA' in book.sheet_names:d=pd.read_excel(book,sheet_name='DATA',header=None)
   else:d=pd.read_excel(book,header=None)
   a=d[d.iloc[:,0].astype(str).str.fullmatch(r'\d{4}:(?:Q[1-4]|\d{2})')]
   if len(a):
    rows=len(a);start=a.iloc[:,0].min();end=a.iloc[:,0].max();kind='realtime_crosscheck_periods';note=f'{len(d.columns)-1} version/value columns; blank values retained; period rows, not cell count'
   else:rows=len(d);kind='release_date_workbook';note='Original historical release-date matrix; includes headers and notes'
  elif ds=='M12':
   d=pd.read_excel(path);a=d[pd.to_numeric(d.Year,errors='coerce').notna()];dates=pd.to_datetime(dict(year=a.Year.astype(int),month=a.Month.astype(int),day=1)).dt.strftime('%Y-%m-%d');rows=len(a);start=min(dates);end=max(dates);kind='monthly_epu';note='Original EPU download; latest snapshot; attribution footnote excluded from row count'
  elif ds=='R02' and name=='nber_business_cycle_dates.xlsx':
   d=pd.read_excel(path,header=None);rows=len(d);kind='business_cycle_reference_table';note='Original NBER chronology workbook; rows include headings, not a count of events; retrospective dating'
 return dict(rows=rows,coverage_start=start,coverage_end=end,record_type=kind,inventory_notes=note)

def main():
 sources=list(csv.DictReader((PROV/'sources.csv').open()));inventory=[];fail=[]
 for r in sources:
  p=ROOT/r['file_path']
  try:meta=describe(p)
  except (ValueError,KeyError,TypeError,IndexError) as e:
   meta=dict(rows='',coverage_start='',coverage_end='',record_type='unparsed',inventory_notes=type(e).__name__)
  inventory.append(dict(dataset_id=r['dataset_id'],file_path=r['file_path'],**meta))
 # Check secrets without displaying any matched bytes.
 secrets=[v.encode() for v in keys().values()]
 for folder in ['data','corpus','provenance','src']:
  for p in (ROOT/folder).rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts and any(k in p.read_bytes() for k in secrets):fail.append({'file':str(p.relative_to(ROOT)),'failure':'credential bytes found'})
 for p in (ROOT/'corpus/raw/SM01').rglob('*.json'):
  b=p.read_bytes()
  if any(x in b for x in [b'authorDisplayName',b'authorProfileImageUrl',b'authorChannelUrl',b'authorChannelId']):fail.append({'file':str(p.relative_to(ROOT)),'failure':'personal author field found'})
 fields=['dataset_id','file_path','rows','coverage_start','coverage_end','record_type','inventory_notes']
 with (PROV/'inventory.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(inventory)
 (PROV/'privacy_check.json').write_text(json.dumps(dict(checked_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),registered_files=len(sources),failures=fail),indent=2))
 print('Registered files:',len(sources),'privacy failures:',len(fail));print('Unparsed:',sum(r['record_type']=='unparsed' for r in inventory))

if __name__=='__main__':main()
