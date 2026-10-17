"""Small reproducible channel-month sample from public YouTube browser pages.

No API keys, internal API requests, proxies, login or CAPTCHA handling. One
browser worker. Immutable field-selected DOM captures exclude comment authors.
"""
from common import ROOT,PROV,CUTOFF
from audit_runtime import worker_lock,checkpoint
from youtube_details import PATTERN
import subprocess,json,csv,datetime as dt,time,random,re,os
from urllib.parse import urlencode,urlsplit,parse_qs
STATE=PROV/'youtube_public_web_state.json'
SESSION='nlp-youtube-public'
FOLDER=ROOT/'corpus/raw/SM01_WEB'/dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d')
SEARCH_JS='''(() => ({url:location.href,title:document.title,blocked:/unusual traffic|verify you are|confirm you.re not a bot/i.test(document.body.innerText),items:Array.from(document.querySelectorAll('h3 a[href*="/watch?v="]')).filter(a=>a.getClientRects().length && a.innerText.trim()).map(a=>({title:a.innerText,url:a.href}))}))()'''
WATCH_JS='''(() => {document.querySelectorAll('video').forEach(v=>v.pause());let e=Array.from(document.querySelectorAll('ytd-watch-metadata')).find(x=>x.offsetParent!==null);return {url:location.href,title:e?.querySelector('h1')?.innerText||'',blocked:/unusual traffic|verify you are|confirm you.re not a bot/i.test(document.body.innerText),date_texts:e?Array.from(e.querySelectorAll('tp-yt-paper-tooltip')).map(t=>t.textContent.trim()):[],channel_urls:e?Array.from(e.querySelectorAll('a[href*="/channel/"]')).map(a=>a.href):[],published_meta:Array.from(document.querySelectorAll('meta[itemprop="datePublished"],meta[itemprop="uploadDate"]')).map(m=>({field:m.getAttribute('itemprop'),value:m.content}))};})()'''

def browser(*args,js=None):
 cmd=['agent-browser','--session',SESSION,*args]
 r=subprocess.run(cmd,input=js,text=True,capture_output=True,timeout=45)
 if r.returncode:raise RuntimeError('browser_command_failed')
 if args and args[0]=='eval':return json.loads(r.stdout)
 return r.stdout

def capture(obj,name,source,month):
 FOLDER.mkdir(parents=True,exist_ok=True);p=FOLDER/name
 if not p.exists():
  with p.open('x') as f:json.dump(obj,f,ensure_ascii=False,indent=2)
  with (PROV/'youtube_web_sources.jsonl').open('a') as f:f.write(json.dumps(dict(file_path=str(p.relative_to(ROOT)),source_url=source,downloaded_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),requested_month=month,method='field-selected public DOM capture; not full HTTP body; no authors'),ensure_ascii=False)+'\n')
 return p

def date_of(o):
 for item in o.get('published_meta',[]):
  if re.fullmatch(r'\d{4}-\d{2}-\d{2}.*',item['value']):return item['value'][:10],'public_datePublished_or_uploadDate_meta'
 for t in o.get('date_texts',[]):
  m=re.search(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}, \d{4}\b',t)
  if m:
   for fmt in ['%b %d, %Y','%B %d, %Y']:
    try:return dt.datetime.strptime(m.group(),fmt).date().isoformat(),'public_watch_metadata_date_tooltip'
    except ValueError:pass
 return '', 'exact_date_not_available'

def initial():
 old=json.loads((PROV/'youtube_monthly_search_state.json').read_text());jobs=[]
 # Every month and channel receives one stratum; no quarter-end-only selection.
 for d in old['queries']:
  jobs.append(dict(channel=d['channel'],name=d['name'],month=d['month'],status='pending',selected=[],tried=[],accepted=[],search_files=[]))
 return dict(jobs=jobs,seed=20261015,target_new_videos_per_channel_month=1,method='seeded random ordering of title-matching visible public search results; one first successful new video per channel-month; relevance-ranked search frame, not a uniform population sample',created_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())

def main():
 s=json.loads(STATE.read_text()) if STATE.exists() else initial();s.update(status='running',pid=os.getpid());checkpoint(STATE,s)
 existing={r['video_id'] for r in csv.DictReader((PROV/'youtube_video_acquisition_registry.csv').open())}
 for job in s['jobs']:
  if job['status'] not in ['pending','in_progress']:continue
  job['status']='in_progress';checkpoint(STATE,s)
  month=job['month'];y,m=map(int,month.split('-'));end=dt.date(y+1,1,1) if m==12 else dt.date(y,m+1,1)
  if not job['selected']:
   # Two predefined topical queries; selection title predicate remains unchanged.
   pool={}
   for topic in ['economy','inflation']:
    query=f'"{job["name"]}" {topic} after:{month}-01 before:{end.isoformat()}'
    url='https://www.youtube.com/results?'+urlencode({'search_query':query})
    name=f"search_{job['channel']}_{month}_{topic}.json"
    old=next((ROOT/rel for rel in job['search_files'] if (ROOT/rel).name==name),None)
    if old is not None:o=json.loads(old.read_text())
    else:
     browser('open',url)
     browser('wait','--fn',"document.querySelectorAll('h3 a[href*=\"/watch?v=\"]').length>0 || /No results found|unusual traffic|confirm you.re not a bot/i.test(document.body.innerText)")
     o=browser('eval','--stdin',js=SEARCH_JS)
     if o['blocked']:s.update(status='needs_user_resolution_access_challenge');checkpoint(STATE,s);return
     p=capture(o,name,url,month);job['search_files'].append(str(p.relative_to(ROOT)));checkpoint(STATE,s)
    for v in o['items']:
     vid=parse_qs(urlsplit(v['url']).query).get('v',[''])[0]
     if vid and PATTERN.search(v['title']) and vid not in existing:pool[vid]=dict(video_id=vid,**v)
    time.sleep(3)
   job['selected']=sorted(pool.values(),key=lambda v:v['video_id']);random.Random(f"20261015:{job['channel']}:{month}").shuffle(job['selected']);checkpoint(STATE,s)
  for v in job['selected']:
   if v['video_id'] in job['tried']:continue
   url='https://www.youtube.com/watch?'+urlencode({'v':v['video_id']})
   browser('open',url);browser('wait','--fn',"!!document.querySelector('ytd-watch-metadata h1') || /Video unavailable|unusual traffic|confirm you.re not a bot/i.test(document.body.innerText)")
   o=browser('eval','--stdin',js=WATCH_JS)
   if o['blocked']:s.update(status='needs_user_resolution_access_challenge');checkpoint(STATE,s);return
   p=capture(o,f"watch_{v['video_id']}.json",url,month);date,evidence=date_of(o)
   channel_ok=any('/channel/'+job['channel'] in u for u in o['channel_urls'])
   eligible=channel_ok and date[:7]==month and date<=CUTOFF and bool(PATTERN.search(o['title']))
   row=dict(video_id=v['video_id'],channel=job['channel'],requested_month=month,published_date=date,date_evidence=evidence,title=o['title'],title_rule_match=bool(PATTERN.search(o['title'])),channel_verified=channel_ok,eligible=eligible,acquisition_route='public_web_search_sample',file_path=str(p.relative_to(ROOT)),retrieved_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
   with (PROV/'youtube_web_video_records.jsonl').open('a') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
   job['tried'].append(v['video_id'])
   if eligible:job['accepted'].append(v['video_id']);existing.add(v['video_id'])
   checkpoint(STATE,s);time.sleep(3)
   if job['accepted']:break
  job['status']='sample_obtained_not_month_complete' if job['accepted'] else 'no_verified_new_match_in_search_frame';checkpoint(STATE,s)
 s['status']='complete_reduced_sample_attempts';checkpoint(STATE,s)

if __name__=='__main__':
 with worker_lock('youtube_public_browser'):
  try:main()
  except (RuntimeError,subprocess.TimeoutExpired,json.JSONDecodeError) as e:
   s=json.loads(STATE.read_text());s.update(status='needs_user_resolution_browser_error',error_type=type(e).__name__);checkpoint(STATE,s)
