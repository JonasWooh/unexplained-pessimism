"""Immutable raw downloads and secret-free append-only provenance."""
import csv, datetime as dt, hashlib, json, time, re, fcntl
from pathlib import Path
from urllib.parse import urlencode, urlsplit
import requests

ROOT=Path(__file__).resolve().parents[2]
NOW=dt.datetime.now(dt.timezone.utc)
DAY=NOW.strftime('%Y%m%d')
CUTOFF='2026-10-14'
PROV=ROOT/'provenance'
PROV.mkdir(exist_ok=True)
FIELDS=['dataset_id','file_path','source_name','url_or_endpoint','downloaded_at_utc','rows','coverage_start','coverage_end','vintage_or_release','license_note','collector','notes']
LAST={}

def keys():
 mapping={'FRED':'fred','NYTimes':'nyt','Guardian':'guardian','Media Cloud':'mediacloud','Google Cloud':'youtube'}
 result={}
 for line in (ROOT/'API_KEY.txt').read_text().splitlines():
  if line.strip():
   label,value=line.rsplit(None,1)
   if label in mapping: result[mapping[label]]=value
 if set(result)!=set(mapping.values()): raise ValueError('API_KEY.txt labels do not match the five supported services')
 return result

def journal(event):
 with (PROV/'requests.jsonl').open('a') as f: f.write(json.dumps(event,ensure_ascii=False)+'\n')

def fetch(ds,url,name,params=None,key=None,keyparam='api_key',headers=None,delay=1,license_note='Terms not yet verified; internal collection only; do not redistribute',text=False,method='GET'):
 folder=ROOT/('corpus' if ds.startswith('N') or ds.startswith('SM') else 'data')/'raw'/ds/DAY
 folder.mkdir(parents=True,exist_ok=True)
 path=folder/name
 if path.exists(): return path
 public=url+('?' + urlencode(params) if params else '')
 args=dict(params or {})
 if key: args[keyparam]=keys()[key]
 host=urlsplit(url).netloc
 time.sleep(max(0,delay-(time.monotonic()-LAST.get(host,0))))
 event=dict(dataset_id=ds,url=public,requested_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
 try:
  r=requests.request(method,url,params=args if method=='GET' else None,data=args if method=='POST' else None,headers=headers,timeout=60)
  LAST[host]=time.monotonic()
 except requests.RequestException as e:
  event.update(status=type(e).__name__);journal(event);print(ds,name,event['status'],flush=True);return None
 event.update(status=r.status_code,content_type=r.headers.get('Content-Type',''),retry_after=r.headers.get('Retry-After',''),method=method)
 # API errors can echo credentials. Never persist error bodies, URLs or exception strings.
 if not r.ok:
  if host=='arctic-shift.photon-reddit.com':
   try:
    error=r.json().get('error')
    if isinstance(error,str):
     for secret in keys().values():error=error.replace(secret,'[REDACTED]')
     event['api_error']=error[:500]
   except (ValueError,AttributeError):pass
  if host=='www.googleapis.com':
   try:
    detail=json.dumps(r.json().get('error',{}),ensure_ascii=False)
    for secret in keys().values():detail=detail.replace(secret,'[REDACTED]')
    event['api_error_details']=json.loads(detail)
    reasons=[x.get('reason','') for x in r.json().get('error',{}).get('errors',[])]
    event['api_reasons']=[x for x in reasons if re.fullmatch(r'[A-Za-z_]{1,80}',x)]
   except (ValueError,AttributeError):pass
  journal(event);print(ds,name,'HTTP',r.status_code,flush=True);return None
 body=r.content
 for secret in keys().values():
  if secret.encode() in body:
   event['status']='response_contains_secret_not_saved';journal(event);return None
 with path.open('xb') as f:f.write(body)
 row=dict.fromkeys(FIELDS,'')
 row.update(dataset_id=ds,file_path=str(path.relative_to(ROOT)),source_name=host,url_or_endpoint=public,downloaded_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),license_note=license_note,collector='Codex',notes='Original response bytes; coverage and counts in inventory.csv')
 if ds=='N03' and name.endswith('.json'):
  obj=json.loads(body)
  if 'stories' in obj:
   entries=obj['stories'];dates=[x['publish_date'] for x in entries if x.get('publish_date')]
   row.update(rows=len(entries),coverage_start=min(dates,default=''),coverage_end=max(dates,default=''),notes='Original story-list response; full collection complete only when pagination token is empty')
  elif 'sample' in obj:
   entries=obj['sample'];dates=[x['publish_date'] for x in entries if x.get('publish_date')]
   row.update(rows=len(entries),coverage_start=min(dates,default=''),coverage_end=max(dates,default=''),notes='Original official random sample; not exhaustive daily records; sample scope in sampling state')
  elif 'count_over_time' in obj:
   entries=obj['count_over_time']['counts'];dates=[x['date'] for x in entries]
   row.update(rows=len(entries),coverage_start=min(dates,default=''),coverage_end=max(dates,default=''),notes='Daily count records, not downloaded articles; archive extent can include anomalous publisher dates')
 if ds=='SM02' and name.startswith(('sample_posts_','cluster_posts_')):
  entries=json.loads(body).get('data',[]);dates=[dt.datetime.fromtimestamp(x['created_utc'],dt.timezone.utc).isoformat() for x in entries]
  row.update(rows=len(entries),coverage_start=min(dates,default=''),coverage_end=max(dates,default=''),notes='Raw author-free interval response; selected day/half-day/window scope in collector state; saturated parent probes are not exhaustive intervals')
 source=PROV/'sources.csv'
 with source.open('a+',newline='') as f:
  fcntl.flock(f,fcntl.LOCK_EX);f.seek(0,2);existed=f.tell()>0
  w=csv.DictWriter(f,fieldnames=FIELDS)
  if not existed:w.writeheader()
  w.writerow(row)
 event['file_path']=row['file_path'];journal(event)
 print(ds,name,'OK',len(body),'bytes',flush=True)
 return path

def links(path,base):
 from bs4 import BeautifulSoup
 from urllib.parse import urljoin
 if not path:return []
 return [(a.get_text(' ',strip=True),urljoin(base,a['href'])) for a in BeautifulSoup(path.read_bytes(),'html.parser').find_all('a',href=True)]

if __name__=='__main__':
 print('Runtime key labels validated:',', '.join(sorted(keys())))
