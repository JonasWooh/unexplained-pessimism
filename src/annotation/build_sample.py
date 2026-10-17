"""Stratified human-annotation sample (task_guide 9.3) and blind annotation workbooks.

Frames (each unit must match economic_title_regex_v1 TERMS in its own displayed text):
 national: NYT Archive (headline + abstract + lead paragraph), Guardian business/useconomy
           (headline + standfirst + first 100 body words), Media Cloud US National sample days (title);
 local:    Media Cloud US State & Local sample days (title);
 social:   Reddit sampled days/windows (title + selftext, first 1,200 chars), YouTube v1 window
           comments (comment text; video title shown as context).
Periods: 2010-2019, 2020-2022, 2023-2024, 2025-2026 (to CUTOFF). Simple random sampling without
replacement inside each source x period cell, seed 20261015; weight = frame size / sample size.
30 calibration items are drawn first from the same frames and excluded from the 360.
"""
import csv,glob,hashlib,html,json,random,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src/collect'))
from youtube_details import PATTERN
CUTOFF='2026-10-14'
SEED=20261015
OUT=ROOT/'annotation'
PERIODS=[('P1_2010_2019','2010-01-01','2019-12-31'),('P2_2020_2022','2020-01-01','2022-12-31'),('P3_2023_2024','2023-01-01','2024-12-31'),('P4_2025_2026','2025-01-01',CUTOFF)]
# (tier, source, period) -> main sample size; calibration sizes below.
ALLOC={('national','NYT','P1_2010_2019'):35,('national','Guardian','P1_2010_2019'):10,
 ('national','NYT','P2_2020_2022'):35,('national','Guardian','P2_2020_2022'):10,
 ('national','NYT','P3_2023_2024'):35,('national','Guardian','P3_2023_2024'):10,
 ('national','NYT','P4_2025_2026'):20,('national','Guardian','P4_2025_2026'):10,('national','MediaCloud_National','P4_2025_2026'):15,
 ('local','MediaCloud_Local','P4_2025_2026'):60,
 ('social','Reddit','P1_2010_2019'):30,('social','Reddit','P2_2020_2022'):30,('social','Reddit','P3_2023_2024'):15,('social','YouTube','P3_2023_2024'):15,
 ('social','Reddit','P4_2025_2026'):15,('social','YouTube','P4_2025_2026'):15}
CALIB={('national','NYT'):8,('national','Guardian'):2,('national','MediaCloud_National'):2,('local','MediaCloud_Local'):6,('social','Reddit'):7,('social','YouTube'):5}
DEV_N=100

def period(date):
 for name,a,b in PERIODS:
  if a<=date<=b:return name

def clean(t):
 t=html.unescape(re.sub(r'<[^>]+>',' ',t or ''));return re.sub(r'\s+',' ',t).strip()

def units():
 seen=set()
 def emit(tier,source,uid,date,text,context,unit_type,url,extra=''):
  key=(source,uid)
  if key in seen or not date or not period(date) or not PATTERN.search(text):return None
  seen.add(key);return dict(tier=tier,source=source,source_item_id=uid,date=date,period=period(date),text=text,context=context,unit_type=unit_type,url=url,source_detail=extra)
 for f in sorted(glob.glob(str(ROOT/'corpus/raw/N01/*/[0-9][0-9][0-9][0-9]-[0-9][0-9]*.json'))):
  for d in json.loads(Path(f).read_bytes()).get('response',{}).get('docs',[]):
   # 2025+ archive schema capitalizes document_type and has no lead_paragraph (nyt_schema_crosswalk.csv).
   if (d.get('document_type') or '').lower()!='article':continue
   parts=[clean((d.get('headline') or {}).get('main'))];names=['headline']
   for k in ['abstract','lead_paragraph']:
    t=clean(d.get(k))
    if t and t not in parts:parts.append(t);names.append(k.replace('_',' '))
   u=emit('national','NYT',d['_id'],(d.get('pub_date') or '')[:10],'\n'.join(p for p in parts if p),'',' + '.join(names),d.get('web_url',''),d.get('section_name') or '')
   if u:yield u
 for f in sorted(glob.glob(str(ROOT/'corpus/raw/N02/*/[0-9][0-9][0-9][0-9]-[0-9][0-9]_*.json'))):
  for r in json.loads(Path(f).read_bytes()).get('response',{}).get('results',[]):
   fl=r.get('fields',{});body=clean(fl.get('bodyText')).split()
   if r.get('type')!='article' or not body:continue
   text='\n'.join(x for x in [clean(fl.get('headline') or r.get('webTitle')),clean(fl.get('trailText')),' '.join(body[:100])+(' [...]' if len(body)>100 else '')] if x)
   u=emit('national','Guardian',r['id'],r.get('webPublicationDate','')[:10],text,'','headline + standfirst + first 100 body words',r.get('webUrl',''),r.get('sectionName',''))
   if u:yield u
 for coll,tier,source in [('34412234','national','MediaCloud_National'),('38379429','local','MediaCloud_Local')]:
  for f in sorted(glob.glob(str(ROOT/f'provenance/monthly_cluster_selections/mediacloud_{coll}_*.json'))):
   s=json.loads(Path(f).read_text());ids=set(s['unique_ids'])
   for rf in s['raw_files']:
    for st in json.loads((ROOT/rf).read_bytes()).get('stories',[]):
     if st['id'] in ids and st.get('language','en')=='en':
      u=emit(tier,source,st['id'],str(st.get('publish_date') or '')[:10],clean(st.get('title')),'','headline only',st.get('url',''),st.get('media_name',''))
      if u:yield u
 import datetime as dt
 for pat in ['reddit_economy_*','reddit_Economics_*','reddit_personalfinance_window_v1_*']:
  for f in sorted(glob.glob(str(ROOT/'provenance/monthly_cluster_selections'/pat))):
   s=json.loads(Path(f).read_text());ids=set(s['unique_ids'])
   for rf in s['raw_files']:
    for p in json.loads((ROOT/rf).read_bytes()).get('data',[]):
     if p['id'] not in ids:continue
     body=p.get('selftext') or ''
     body='' if body.strip() in ('[removed]','[deleted]') else clean(body)
     full=clean(p.get('title'))+('\n'+body if body else '')
     text=full[:1200]+(' [...]' if len(full)>1200 else '')
     date=dt.datetime.fromtimestamp(int(p['created_utc']),dt.timezone.utc).date().isoformat()
     u=emit('social','Reddit',p['id'],date,text,'','forum post (title + body, first 1,200 chars)','https://www.reddit.com/comments/'+p['id'],'r/'+p.get('subreddit',''))
     if u:yield u
 freeze=sorted(glob.glob(str(ROOT/'provenance/youtube_freeze_v1_*/youtube_comment_videos_manifest.csv')))[-1]
 titles={r['video_id']:r['title'] for r in csv.DictReader(open(sorted(glob.glob(str(ROOT/'provenance/youtube_freeze_v1_*/youtube_claude_candidates.csv')))[-1]))}
 for r in csv.DictReader(open(freeze)):
  start=dt.datetime.fromisoformat(r['published'].replace('Z','+00:00'));end=min(start+dt.timedelta(days=30),dt.datetime.fromisoformat(CUTOFF+'T23:59:59+00:00'))
  for f in r['comment_files'].split('|'):
   for it in json.loads((ROOT/f).read_bytes()).get('items',[]):
    sn=it['snippet']['topLevelComment']['snippet'];t=dt.datetime.fromisoformat(sn['publishedAt'].replace('Z','+00:00'))
    if start<=t<=end:
     u=emit('social','YouTube',it['id'],t.date().isoformat(),clean(sn['textDisplay']),'Video title: '+titles.get(r['video_id'],''),'video comment (top-level)','https://www.youtube.com/watch?v='+r['video_id'],r['channel'])
     if u:yield u

def main():
 frames={}
 for u in units():frames.setdefault((u['tier'],u['source'],u['period']),[]).append(u)
 for k in frames:frames[k].sort(key=lambda u:u['source_item_id'])
 rng=random.Random(SEED)
 # Calibration: per tier x source, pooled over periods, drawn before the main sample.
 calib=[];taken=set()
 for (tier,source),n in sorted(CALIB.items()):
  pool=sorted((u for k,v in frames.items() if k[:2]==(tier,source) for u in v),key=lambda u:(u['period'],u['source_item_id']))
  for u in rng.sample(pool,n):taken.add((u['source'],u['source_item_id']));calib.append(dict(u,stratum=f'{tier}|{source}|calibration',frame_size=len(pool),weight=''))
 main=[];sizes=[]
 for key,n in sorted(ALLOC.items()):
  pool=[u for u in frames.get(key,[]) if (u['source'],u['source_item_id']) not in taken]
  if len(pool)<n:raise ValueError(f'frame too small for {key}: {len(pool)}<{n}')
  pick=rng.sample(pool,n);sizes.append(dict(tier=key[0],source=key[1],period=key[2],frame_size=len(pool),sample_size=n,weight=len(pool)/n))
  for u in pick:main.append(dict(u,stratum='|'.join(key),frame_size=len(pool),weight=len(pool)/n))
 # Dev/test split: largest-remainder allocation of 100 dev items across cells, random within cell.
 cells={}
 for u in main:cells.setdefault(u['stratum'],[]).append(u)
 quota={k:DEV_N*len(v)/len(main) for k,v in cells.items()};base={k:int(q) for k,q in quota.items()}
 for k in sorted(quota,key=lambda k:(-(quota[k]-base[k]),k))[:DEV_N-sum(base.values())]:base[k]+=1
 for k,v in sorted(cells.items()):
  dev={id(u) for u in rng.sample(v,base[k])}
  for u in v:u['split']='dev' if id(u) in dev else 'test'
 for u in calib:u['split']='calibration'
 rng.shuffle(main);rng.shuffle(calib)
 for i,u in enumerate(calib,1):u['item_id']=f'C{i:03}'
 for i,u in enumerate(main,1):u['item_id']=f'A{i:03}'
 OUT.mkdir(exist_ok=True)
 keyf=['item_id','split','stratum','tier','source','period','date','source_item_id','source_detail','url','unit_type','frame_size','weight','context','text']
 with open(OUT/'sample_key_DO_NOT_SHOW_ANNOTATORS.csv','w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=keyf,extrasaction='ignore');w.writeheader();w.writerows(calib+main)
 with open(OUT/'sampling_frame_sizes.csv','w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(sizes[0]));w.writeheader();w.writerows(sizes)
 design=dict(seed=SEED,rule='economic_title_regex_v1 TERMS must match the displayed unit text',periods=PERIODS,allocation={'|'.join(k):v for k,v in ALLOC.items()},calibration={'|'.join(k):v for k,v in CALIB.items()},dev_n=DEV_N,
  main_n=len(main),calibration_n=len(calib),frame_totals={'|'.join(k):len(v) for k,v in sorted(frames.items())},
  digest=hashlib.sha256('\n'.join(u['source']+':'+u['source_item_id'] for u in calib+main).encode()).hexdigest())
 (OUT/'sampling_design.json').write_text(json.dumps(design,indent=2))
 return calib,main

if __name__=='__main__':
 calib,main=main()
 print('calibration',len(calib),'main',len(main))
