"""Date-coverage-first YouTube collection, official Data API v3 only.

Phases (one resumable process, state in provenance/youtube_claude_state.json):
 1. discovery: resume UULF (long-form) and UULV (live) classified upload playlists of the
    truncated channels until a page is entirely older than 2023-01-01 or the playlist ends.
    UUSH (shorts) is not traversed.
 2. candidates: uploads + UULF/UULV items, published 2023-01-01..CUTOFF (UTC date), with
    economic_title_regex_v1. Search-only videos are flagged superseded, not in the main set.
 3. stats: videos.list (50 ids/call) for every main-set candidate; commentCount decides
    whether a video can be a comment target (absent or 0 -> not eligible).
 4. comments, breadth-first with seed 20261015: round 1 one video per date (channel
    rotation), round 2 one per channel-date, round 3 a second per channel-date. Every target
    is traversed to the last commentThreads page; nothing is truncated within a video.
quotaExceeded -> checkpoint and sleep until 00:05 America/Los_Angeles, then continue.
"""
import common
from common import *
from audit_runtime import worker_lock,last_event,retry_fetch
from SM01 import LICENSE
from youtube_details import PATTERN
import os,random,zoneinfo
from contextlib import ExitStack

STATE=PROV/'youtube_claude_state.json'
REPORT=PROV/'youtube_coverage_by_date.csv'
SUMMARY=PROV/'youtube_claude_summary.json'
CANDIDATES=PROV/'youtube_claude_candidates.csv'
RAW=ROOT/'corpus/raw/SM01'
SEED=20261015
# 2026-10-15 22:45Z, user: coarser granularity, faster. Round 1 = every date >=1 video (channel rotation);
# round 'month' = up to MONTH_TARGET seeded-random videos per channel x month (earlier picks count).
ROUNDS=('panel',1,'month')
# 22:47Z coordinator priority: balanced-panel channels (listing covers the whole period) first, election windows.
PANEL={'UC6ZFN9Tx6xh-skXCuRHCDpQ':'2023-08-05','UCvJJ_dzjViJCoLf5uKUTwoA':'2023-01-01','UCNjfNLnQYbjBEvnS8KFuyGQ':'2023-01-01','UCupvZG-5ko_eiXAupbDfxWw':'2024-11-11'}
PANEL_MONTHS=['2024-08','2024-09','2024-10','2024-11','2024-12','2026-08','2026-09','2026-10']
MONTH_TARGET=4
# search.list only for these months, channels whose classified long-form list did not cover the month.
SEARCH_MONTHS=['2024-08','2024-09','2024-10','2024-11','2024-12']
SEARCH_DAILY=90
SE='https://www.googleapis.com/youtube/v3/search'
CANDIDATE_RULE='v2_uploads_classified_plus_search_supplement'
MONTHLY=PROV/'youtube_coverage_by_month.csv'
START='2023-01-01'
WINDOW_END_CAP=dt.datetime.fromisoformat(CUTOFF+'T23:59:59+00:00')
PI='https://www.googleapis.com/youtube/v3/playlistItems'
CT='https://www.googleapis.com/youtube/v3/commentThreads'
VL='https://www.googleapis.com/youtube/v3/videos'
FIELDS_TEXT='nextPageToken,pageInfo,items(id,snippet(totalReplyCount,topLevelComment(id,snippet(textDisplay,publishedAt,updatedAt,likeCount))))'
NOTE_COMMENTS=' Comment body permitted by user; author fields excluded by API fields selection. textDisplay/plainText; top-level only.'
NOTE_PLAYLIST=' User-authorized undocumented classified playlist convention; selected channel-video fields only.'
PACIFIC=zoneinfo.ZoneInfo('America/Los_Angeles')

class Stop(Exception):pass

def now():return dt.datetime.now(dt.timezone.utc)
def parse(t):return dt.datetime.fromisoformat(t.replace('Z','+00:00'))
def log(*a):print(now().isoformat(timespec='seconds'),*a,flush=True)

S={}
def save():
 S['updated_at_utc']=now().isoformat()
 tmp=STATE.with_suffix('.tmp');tmp.write_text(json.dumps(S));tmp.replace(STATE)

def milestone(name,**info):
 if any(m['name']==name for m in S.get('milestones',[])):return
 S.setdefault('milestones',[]).append(dict(name=name,at_utc=now().isoformat(),**info));save();log('MILESTONE',name)

def existing(name):
 hits=sorted(RAW.glob('*/'+name))
 return hits[0] if hits else None

def sleep_until_reset(reason):
 local=now().astimezone(PACIFIC)
 target=local.replace(hour=0,minute=5,second=0,microsecond=0)
 if target<=local:target=(local+dt.timedelta(days=1)).replace(hour=0,minute=5,second=0,microsecond=0)
 target=target.astimezone(dt.timezone.utc)
 stop=dict(at_utc=now().isoformat(),phase=S.get('phase'),reason=reason,resume_at_utc=target.isoformat(),requests_since_last_reset=S.get('requests_today',0))
 S.setdefault('quota_stops',[]).append(stop);S['status']='quota_wait';S['resume_at_utc']=target.isoformat()
 report();save();log('QUOTA_STOP sleeping until',target.isoformat())
 while now()<target:time.sleep(min(600,max(1,(target-now()).total_seconds())))
 S['status']='running';S['requests_today']=0;S.pop('resume_at_utc',None);save();log('RESUME after quota reset')

def call(endpoint,name,params,note):
 """Return (path, None) or (None, error event). Sleeps through quotaExceeded; raises Stop on
 persistent errors that retry_fetch's backoff did not clear."""
 while True:
  hit=existing(name)
  if hit:return hit,None
  common.DAY=now().strftime('%Y%m%d')
  p=retry_fetch('SM01',endpoint,name,params,key='youtube',keyparam='key',delay=1,license_note=LICENSE+note)
  S['requests_today']=S.get('requests_today',0)+1;S['requests_total']=S.get('requests_total',0)+1
  if p:return p,None
  e=last_event(endpoint,params);reasons=e.get('api_reasons',[])
  if any(r in ('quotaExceeded','dailyLimitExceeded') for r in reasons):sleep_until_reset(reasons);continue
  return None,{k:e.get(k) for k in ['status','api_reasons','requested_at_utc']}

def persistent(err,where):
 S['status']='stopped_persistent_error';S['stop_event']=dict(where=where,**err);report();save()
 raise Stop(where)

# ---------------- phase 1: discovery ----------------
def discovery():
 if 'discovery' not in S:
  old=json.loads((PROV/'youtube_classified_state.json').read_text())
  S['discovery']=dict(source='tokens resumed from youtube_classified_state.json (stopped_by_user)',playlists=[{k:d.get(k) for k in ['channel','name','kind','playlist','page','token','rows','status','earliest','latest','expected_api_total']} for d in old['playlists'] if d['kind'] in ('UULF','UULV')])
  save()
 for d in S['discovery']['playlists']:
  while d['status']=='available':
   params=dict(playlistId=d['playlist'],part='snippet,contentDetails',maxResults=50,fields='nextPageToken,pageInfo,items(contentDetails/videoId,contentDetails/videoPublishedAt,snippet(title,publishedAt))')
   if d['token']:params['pageToken']=d['token']
   name=f"classified_{d['kind']}_{d['channel']}_{d['page']:04}.json"
   p,err=call(PI,name,params,NOTE_PLAYLIST)
   if not p:
    if err.get('status')==404:d['status']='unavailable';d['error']=err;save();break
    persistent(err,'discovery '+name)
   o=json.loads(p.read_bytes());dates=[i.get('contentDetails',{}).get('videoPublishedAt','') for i in o.get('items',[])];dates=[v for v in dates if v]
   d['rows']+=len(o.get('items',[]));d['page']+=1;d['token']=o.get('nextPageToken');d['expected_api_total']=o.get('pageInfo',{}).get('totalResults')
   if dates:d['earliest']=min(d['earliest'] or min(dates),min(dates));d['latest']=max(d['latest'] or max(dates),max(dates))
   d['status']='reached_2023' if dates and max(dates)<START else 'playlist_exhausted' if not d['token'] else 'available'
   if S['requests_total']%20==0:save()
  save()
 milestone('discovery_complete')

# ---------------- phase 2: candidate set ----------------
def build_candidates():
 videos={}
 paths=sorted(RAW.rglob('uploads_*.json'))+sorted(RAW.rglob('classified_UULF_*.json'))+sorted(RAW.rglob('classified_UULV_*.json'))+sorted(RAW.rglob('search_*.json'))+sorted(RAW.rglob('claude_search_monthly_*.json'))
 for p in sorted(paths,key=lambda p:(p.stat().st_mtime,str(p))):
  n=p.name
  if n.startswith('uploads_'):route='uploads';channel=n[len('uploads_'):].rsplit('_',1)[0]
  elif n.startswith('classified_'):route='classified_'+n.split('_')[1];channel=n[len('classified_UULF_'):].rsplit('_',1)[0]
  elif n.startswith('claude_search_monthly_'):route='search_monthly_2024H2';channel=None
  else:route='search_superseded';channel=None
  for item in json.loads(p.read_bytes()).get('items',[]):
   sn=item['snippet'];c=item.get('contentDetails',{})
   if route.startswith('search_'):vid=item['id'].get('videoId');date=sn.get('publishedAt','');ch=sn.get('channelId')
   else:vid=c.get('videoId');date=c.get('videoPublishedAt','');ch=channel
   if not vid or not date:continue
   v=videos.setdefault(vid,dict(video_id=vid,channel=ch,published=date,routes=set(),raw_files=set()))
   v['routes'].add(route);v['raw_files'].add(str(p.relative_to(ROOT)));v['title']=sn['title']
   if not route.startswith('search_'):v.update(channel=ch,published=date)
 rows=[]
 for v in videos.values():
  listed=bool(v['routes']-{'search_superseded','search_monthly_2024H2'})
  match=bool(PATTERN.search(v['title']));in_period=START<=v['published'][:10]<=CUTOFF
  rows.append(dict(video_id=v['video_id'],channel=v['channel'],published=v['published'],date_utc=v['published'][:10],title=v['title'],routes='|'.join(sorted(v['routes'])),title_rule_match=match,in_period=in_period,
   search_only_supplement=not listed,main_set=match and in_period,rule_version='economic_title_regex_v1',raw_files='|'.join(sorted(v['raw_files']))))
 rows.sort(key=lambda r:(r['published'],r['channel'] or '',r['video_id']))
 tmp=CANDIDATES.with_suffix('.tmp')
 with tmp.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 tmp.replace(CANDIDATES)
 main=[r for r in rows if r['main_set']]
 S['candidate_counts']=dict(all_listed_or_searched=len(rows),main_set=len(main),of_which_search_only_supplement=sum(1 for r in main if r['search_only_supplement']))
 S['candidate_rule']=CANDIDATE_RULE
 S['phase_candidates_done']=True;save()
 return main

def load_main():
 return [r for r in csv.DictReader(CANDIDATES.open()) if r['main_set']=='True']

# ---------------- phase 3: videos.list statistics ----------------
def stats(main):
 st=S.setdefault('stats',{})
 S.setdefault('stats_files',[])
 pending=[r['video_id'] for r in main if r['video_id'] not in st]
 for i in range(0,len(pending),50):
  ids=pending[i:i+50];digest=hashlib.sha256(','.join(ids).encode()).hexdigest()[:12]
  p,err=call(VL,'claude_videos_'+digest+'.json',{'id':','.join(ids),'part':'snippet,contentDetails,statistics','fields':'items(id,snippet(title,publishedAt),contentDetails/duration,statistics)'},'')
  if not p:persistent(err,'videos.list '+digest)
  got={x['id']:x for x in json.loads(p.read_bytes()).get('items',[])}
  for vid in ids:
   x=got.get(vid)
   if x is None:st[vid]=dict(available=False,file=str(p.relative_to(ROOT)))
   else:
    cc=x.get('statistics',{}).get('commentCount')
    st[vid]=dict(available=True,comment_count=int(cc) if cc is not None else None,views=x.get('statistics',{}).get('viewCount'),duration=x.get('contentDetails',{}).get('duration'),file=str(p.relative_to(ROOT)))
  S['stats_files'].append(str(p.relative_to(ROOT)))
  if (i//50)%10==0:save()
 save()

# ---------------- phase 4: comments ----------------
def old_comment_files():
 idx={}
 for p in RAW.rglob('comment_text_*.json'):
  vid=p.name[len('comment_text_'):].rsplit('_',1)[0];idx.setdefault(vid,[]).append(str(p.relative_to(ROOT)))
 return {k:sorted(v) for k,v in idx.items()}

def init_videos(main):
 old=json.loads((PROV/'youtube_comment_text_state.json').read_text())['videos'];files=old_comment_files()
 vids=S.setdefault('videos',{})
 for r in main:
  if r['video_id'] in vids:continue
  o=old.get(r['video_id'])
  if not o:continue
  if o['status']=='complete_top_level':vids[r['video_id']]=dict(status='complete',page=o['page'],token=None,files=files.get(r['video_id'],[]),origin='earlier_run_complete')
  elif o['status']=='unavailable':vids[r['video_id']]=dict(status='unavailable',page=o['page'],token=None,files=files.get(r['video_id'],[]),origin='earlier_run_unavailable',last_error=o.get('last_error'))
  elif o['status']=='pending' and o['page']>0:vids[r['video_id']]=dict(status='partial',page=o['page'],token=o['token'],files=files.get(r['video_id'],[]),origin='earlier_run_partial')
 save()

def eligible(vid):
 st=S['stats'].get(vid,{});v=S['videos'].get(vid,{})
 if v.get('status')=='unavailable':return False
 return v.get('status')=='complete' or (st.get('available') and (st.get('comment_count') or 0)>0)

def counted(vid):
 """Videos that satisfy a round: complete, or already targeted and not failed."""
 v=S['videos'].get(vid);return bool(v) and (v['status']=='complete' or v.get('targeted_round'))and v['status']!='unavailable'

def fetch_video(vid,published):
 v=S['videos'].setdefault(vid,dict(status='partial',page=0,token=None,files=[],origin='this_run'))
 while v['status']!='complete':
  params=dict(videoId=vid,part='snippet',maxResults=100,order='time',textFormat='plainText',fields=FIELDS_TEXT)
  if v['token']:params['pageToken']=v['token']
  name=f'claude_comments_{vid}_{v["page"]:04}.json'
  p,err=call(CT,name,params,NOTE_COMMENTS)
  if not p:
   reasons=err.get('api_reasons') or []
   if reasons and all(r in ('commentsDisabled','videoNotFound','forbidden') for r in reasons):
    v['status']='unavailable';v['last_error']=err;save();return False
   if err.get('status')==400 and v['token'] and v.get('origin')=='earlier_run_partial' and not v.get('restarted'):
    # The stored token from the earlier run was rejected: restart this video from page 0.
    v.update(restarted=dict(at_utc=now().isoformat(),error=err,superseded_files=v['files']),files=[],page=0,token=None);save();continue
   persistent(err,'commentThreads '+name)
  obj=json.loads(p.read_bytes())
  for item in obj.get('items',[]):
   sn=item['snippet']['topLevelComment']['snippet']
   if set(sn)-{'textDisplay','publishedAt','updatedAt','likeCount'} or 'textDisplay' not in sn:raise ValueError('Unexpected comment schema in '+name)
  v['files'].append(str(p.relative_to(ROOT)));v['page']+=1;v['token']=obj.get('nextPageToken')
  if not v['token']:v['status']='complete';v['completed_at_utc']=now().isoformat()
  if S['requests_total']%25==0:save()
 v.update(window_counts(v['files'],published));save()
 return True

def window_counts(files,published):
 start=parse(published);end=min(start+dt.timedelta(days=30),WINDOW_END_CAP);ids=set();inwin=set()
 for f in files:
  for item in json.loads((ROOT/f).read_bytes()).get('items',[]):
   ids.add(item['id']);t=parse(item['snippet']['topLevelComment']['snippet']['publishedAt'])
   if start<=t<=end:inwin.add(item['id'])
 return dict(top_level_total=len(ids),window_comments=len(inwin),window_end_utc=end.isoformat())

def panel_rows(main):
 # Listed (uploads/classified) videos only, so the panel's sampling frame is the same in every month.
 return [r for r in main if r['channel'] in PANEL and r['search_only_supplement']=='False' and r['date_utc']>=PANEL[r['channel']] and r['date_utc'][:7] in PANEL_MONTHS]

def plan_round(rnd,main,rng):
 by_date={};by_cd={}
 for r in main:
  by_date.setdefault(r['date_utc'],[]).append(r);by_cd.setdefault((r['date_utc'],r['channel']),[]).append(r)
 targets=[];empty=[]
 if rnd==1:
  load={}
  day=dt.date.fromisoformat(START)
  while day.isoformat()<=CUTOFF:
   d=day.isoformat();day+=dt.timedelta(days=1);rows=by_date.get(d,[])
   done=[r for r in rows if counted(r['video_id'])]
   if done:
    for r in done[:1]:load[r['channel']]=load.get(r['channel'],0)+1
    continue
   el=[r for r in rows if eligible(r['video_id'])]
   if not el:empty.append(d);continue
   chans=sorted({r['channel'] for r in el});order={c:rng.random() for c in chans}
   ch=min(chans,key=lambda c:(load.get(c,0),order[c]));load[ch]=load.get(ch,0)+1
   targets.append(rng.choice(sorted((r for r in el if r['channel']==ch),key=lambda r:r['video_id'])))
 elif rnd=='panel':
  by_cm={}
  for r in panel_rows(main):by_cm.setdefault((r['date_utc'][:7],r['channel']),[]).append(r)
  for (m,ch),rows in sorted(by_cm.items()):
   have=sum(1 for r in rows if counted(r['video_id']))
   if have>=MONTH_TARGET:continue
   el=sorted((r for r in rows if eligible(r['video_id']) and not counted(r['video_id'])),key=lambda r:r['video_id'])
   if not el:
    if not have:empty.append(f'{m}|{ch}')
    continue
   targets+=rng.sample(el,min(MONTH_TARGET-have,len(el)))
 elif rnd=='month':
  by_cm={}
  for r in main:by_cm.setdefault((r['date_utc'][:7],r['channel']),[]).append(r)
  for (m,ch),rows in sorted(by_cm.items()):
   have=sum(1 for r in rows if counted(r['video_id']))
   if have>=MONTH_TARGET:continue
   el=sorted((r for r in rows if eligible(r['video_id']) and not counted(r['video_id'])),key=lambda r:r['video_id'])
   if not el:
    if not have:empty.append(f'{m}|{ch}')
    continue
   targets+=rng.sample(el,min(MONTH_TARGET-have,len(el)))
 else:
  need=rnd-1
  for (d,ch),rows in sorted(by_cd.items()):
   done=[r for r in rows if counted(r['video_id'])]
   if len(done)>=need:continue
   el=[r for r in rows if eligible(r['video_id']) and not counted(r['video_id'])]
   if not el:empty.append(f'{d}|{ch}');continue
   targets.append(rng.choice(sorted(el,key=lambda r:r['video_id'])))
 return targets,empty

def est_pages(vid):
 cc=S['stats'].get(vid,{}).get('comment_count') or 0;v=S['videos'].get(vid,{})
 return max(1,-(-cc//100)-v.get('page',0))

def run_round(rnd,main,tag=''):
 key=f'round{rnd}{tag}'
 R=S.setdefault('rounds',{}).get(key)
 if R is None:
  rng=random.Random(f'{SEED}:{key}')
  targets,empty=plan_round(rnd,main,rng)
  tiebreak={r['video_id']:rng.random() for r in targets}
  targets.sort(key=lambda r:(est_pages(r['video_id']),tiebreak[r['video_id']]))
  R=S['rounds'][key]=dict(queue=[r['video_id'] for r in targets],units_without_eligible=empty,replacements=[],status='running',started_at_utc=now().isoformat())
  for r in targets:
   v=S['videos'].setdefault(r['video_id'],dict(status='partial',page=0,token=None,files=[],origin='this_run'));v['targeted_round']=key
  S['phase']=key;save();log(key,'targets',len(targets),'units without eligible video',len(empty))
 info={r['video_id']:r for r in main}
 while R['queue']:
  vid=R['queue'][0];r=info[vid]
  if S['videos'][vid]['status']!='complete':
   ok=fetch_video(vid,r['published'])
   if not ok:
    # Target cannot return comments: draw a replacement for the same unit with the round's rule.
    rng=random.Random(f'{SEED}:{key}:replace:{vid}')
    if rnd==1:pool=[x for x in main if x['date_utc']==r['date_utc'] and eligible(x['video_id']) and not counted(x['video_id'])]
    elif rnd=='panel':pool=[x for x in panel_rows(main) if x['date_utc'][:7]==r['date_utc'][:7] and x['channel']==r['channel'] and eligible(x['video_id']) and not counted(x['video_id'])]
    elif rnd=='month':pool=[x for x in main if x['date_utc'][:7]==r['date_utc'][:7] and x['channel']==r['channel'] and eligible(x['video_id']) and not counted(x['video_id'])]
    else:pool=[x for x in main if x['date_utc']==r['date_utc'] and x['channel']==r['channel'] and eligible(x['video_id']) and not counted(x['video_id'])]
    if rnd==1 and any(counted(x['video_id']) for x in main if x['date_utc']==r['date_utc']):pool=[]
    if pool:
     new=rng.choice(sorted(pool,key=lambda x:x['video_id']))
     S['videos'].setdefault(new['video_id'],dict(status='partial',page=0,token=None,files=[],origin='this_run'))['targeted_round']=key
     R['queue'].append(new['video_id'])
    R['replacements'].append(dict(failed=vid,replacement=new['video_id'] if pool else None))
  R['queue'].pop(0);R['done']=R.get('done',0)+1
  if search_due():search_step()
  if R['done']%50==0:report()
  save()
 R['status']='complete';R['completed_at_utc']=now().isoformat();report()
 milestone(key+'_complete')

# ---------------- search.list, 2024-08..2024-12 only ----------------
def first_reset_after(t):
 local=t.astimezone(PACIFIC);target=local.replace(hour=0,minute=5,second=0,microsecond=0)
 if target<=local:target=(local+dt.timedelta(days=1)).replace(hour=0,minute=5,second=0,microsecond=0)
 return target.astimezone(dt.timezone.utc)

def search_init():
 if 'search' in S:return
 jobs=[]
 for d in S['discovery']['playlists']:
  if d['kind']!='UULF':continue
  for m in SEARCH_MONTHS:
   if m<=d['earliest'][:7]:jobs.append(dict(channel=d['channel'],name=d['name'],month=m,page=0,token=None,ids=[],rows=0,status='pending'))
 S['search']=dict(jobs=jobs,status='waiting_first_window',not_before_utc=first_reset_after(now()).isoformat(),daily_limit=SEARCH_DAILY,calls_by_pacific_date={},
  query_rule='channel x natural month, economic TERMS OR query, order=date, full pagination; same title regex afterwards');save()

def search_due():
 x=S.get('search')
 if not x or x['status'] not in ('waiting_first_window','running','waiting_daily_budget'):return False
 if now()<parse(x['not_before_utc']):return False
 day=now().astimezone(PACIFIC).date().isoformat()
 return x['calls_by_pacific_date'].get(day,0)<SEARCH_DAILY and any(j['status'] in ('pending','partial') for j in x['jobs'])

def search_step():
 from youtube_details import TERMS
 x=S['search'];x['status']='running';query='|'.join('"'+t+'"' if ' ' in t else t for t in TERMS)
 while search_due():
  j=next(j for j in x['jobs'] if j['status'] in ('pending','partial'))
  y,m=map(int,j['month'].split('-'));end=dt.date(y+1,1,1) if m==12 else dt.date(y,m+1,1)
  params=dict(part='snippet',type='video',channelId=j['channel'],q=query,publishedAfter=j['month']+'-01T00:00:00Z',publishedBefore=end.isoformat()+'T00:00:00Z',order='date',maxResults=50,fields='nextPageToken,pageInfo,items(id/videoId,snippet(publishedAt,title,channelId))')
  if j['token']:params['pageToken']=j['token']
  name=f"claude_search_monthly_{j['channel']}_{j['month']}_{j['page']:03}.json"
  p=existing(name)
  if not p:
   common.DAY=now().strftime('%Y%m%d');day=now().astimezone(PACIFIC).date().isoformat()
   p=fetch('SM01',SE,name,params,key='youtube',keyparam='key',delay=1,license_note=LICENSE+' Channel x month economic OR search, 2024-08..2024-12 only; at most 90 calls per Pacific day.')
   x['calls_by_pacific_date'][day]=x['calls_by_pacific_date'].get(day,0)+1;S['requests_total']=S.get('requests_total',0)+1
  if not p:
   e=last_event(SE,params);reasons=e.get('api_reasons',[]);err={k:e.get(k) for k in ['status','api_reasons','requested_at_utc']}
   if any(r in ('quotaExceeded','dailyLimitExceeded') for r in reasons):sleep_until_reset(reasons);continue
   x['error']=err;x['status']='skipped_429' if e.get('status')==429 else 'stopped_api_error';save();milestone('search_'+x['status'],**err);return
  o=json.loads(p.read_bytes());j['rows']+=len(o.get('items',[]));j['ids']=sorted(set(j['ids'])|{i['id']['videoId'] for i in o.get('items',[]) if i['id'].get('videoId')})
  j['page']+=1;j['token']=o.get('nextPageToken');j['query_estimate']=o.get('pageInfo',{}).get('totalResults')
  j['status']='partial' if j['token'] else 'complete_pagination'
  if not j['token'] and (len(j['ids'])>=500 or (j['query_estimate'] or 0)>len(j['ids'])):j['status']='pagination_exhausted_api_cap_or_count_mismatch'
  save()
 if not any(j['status'] in ('pending','partial') for j in x['jobs']):x['status']='complete';save();milestone('search_complete',calls=sum(x['calls_by_pacific_date'].values()))
 elif x['status']=='running':x['status']='waiting_daily_budget';save()

# ---------------- reporting ----------------
def report():
 if not CANDIDATES.exists() or 'videos' not in S:return
 main=load_main();names={r['channel_id']:r['name'] for r in csv.DictReader((PROV/'youtube_channels.csv').open())}
 cache=S.setdefault('window_cache',{})
 cells={}
 for r in main:
  c=cells.setdefault((r['date_utc'],r['channel']),dict(candidate_videos=0,eligible_for_comments=0,targeted=0,comments_complete_videos=0,window_comments=0))
  vid=r['video_id'];v=S['videos'].get(vid)
  c['candidate_videos']+=1;c['eligible_for_comments']+=bool(eligible(vid))
  if v and v.get('targeted_round'):c['targeted']+=1
  if v and v['status']=='complete':
   if 'window_comments' not in v:
    if vid not in cache:cache[vid]=window_counts(v['files'],r['published'])
    w=cache[vid]
   else:w=v
   c['comments_complete_videos']+=1;c['window_comments']+=w['window_comments']
 rows=[];day=dt.date.fromisoformat(START)
 while day.isoformat()<=CUTOFF:
  d=day.isoformat();day+=dt.timedelta(days=1)
  for ch in names:
   c=cells.get((d,ch),dict(candidate_videos=0,eligible_for_comments=0,targeted=0,comments_complete_videos=0,window_comments=0))
   rows.append(dict(date=d,channel_id=ch,channel=names[ch],**c))
 tmp=REPORT.with_suffix('.tmp')
 with tmp.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 tmp.replace(REPORT)
 months={}
 for x in rows:
  a=months.setdefault((x['date'][:7],x['channel_id']),dict(month=x['date'][:7],channel_id=x['channel_id'],channel=x['channel'],candidate_videos=0,eligible_for_comments=0,targeted=0,comments_complete_videos=0,window_comments=0,days_with_complete_video=0))
  for k in ['candidate_videos','eligible_for_comments','targeted','comments_complete_videos','window_comments']:a[k]+=x[k]
  a['days_with_complete_video']+=x['comments_complete_videos']>0
 mrows=list(months.values());tmp=MONTHLY.with_suffix('.tmp')
 with tmp.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(mrows[0]));w.writeheader();w.writerows(mrows)
 tmp.replace(MONTHLY)
 mon={}
 for x in mrows:
  a=mon.setdefault(x['month'],[0,0]);a[0]+=x['comments_complete_videos']>0;a[1]+=x['window_comments']
 dates={}
 for x in rows:
  a=dates.setdefault(x['date'],[0,0,0]);a[0]+=x['candidate_videos'];a[1]+=x['comments_complete_videos'];a[2]+=x['window_comments']
 summ=dict(generated_at_utc=now().isoformat(),total_dates=len(dates),dates_with_candidate=sum(1 for a in dates.values() if a[0]),dates_with_complete_video=sum(1 for a in dates.values() if a[1]),
  dates_with_window_comment=sum(1 for a in dates.values() if a[2]),channel_dates_with_candidate=sum(1 for x in rows if x['candidate_videos']),channel_dates_with_complete_video=sum(1 for x in rows if x['comments_complete_videos']),
  channel_dates_with_two_complete=sum(1 for x in rows if x['comments_complete_videos']>=2),main_set_videos=len(main),search_only_supplement_videos=sum(1 for r in main if r['search_only_supplement']=='True'),
  months_total=len(mon),months_with_complete_video=sum(1 for a in mon.values() if a[0]),channel_months_with_candidate=sum(1 for x in mrows if x['candidate_videos']),channel_months_with_complete_video=sum(1 for x in mrows if x['comments_complete_videos']),
  min_window_comments_per_month=min(a[1] for a in mon.values()),complete_videos=sum(1 for v in S['videos'].values() if v['status']=='complete'),
  window_comments_in_main_set=sum(x['window_comments'] for x in rows),status=S.get('status'),phase=S.get('phase'),rounds={k:dict(status=v['status'],queue_left=len(v['queue']),done=v.get('done',0),units_without_eligible=len(v['units_without_eligible'])) for k,v in S.get('rounds',{}).items()},
  quota_stops=S.get('quota_stops',[]),requests_total=S.get('requests_total',0),
  limitations=['UUSH (shorts) playlists not traversed; shorts enter the main set only through uploads pages, i.e. only for dates the 20,000-item uploads listing reached per channel.',
   'Date = UTC calendar date of contentDetails.videoPublishedAt.','Window comments = unique top-level comments published within 30 days of video publication and no later than '+CUTOFF+'T23:59:59Z.',
   'commentCount from videos.list includes replies and is a snapshot; it only decides eligibility (present and >0) and processing order.'])
 tmp=SUMMARY.with_suffix('.tmp');tmp.write_text(json.dumps(summ,indent=2));tmp.replace(SUMMARY)

def main():
 global S
 S=json.loads(STATE.read_text()) if STATE.exists() else dict(created_at_utc=now().isoformat(),seed=SEED,requests_total=0,requests_today=0)
 S.update(status='running',pid=os.getpid());save()
 try:
  S['phase']='discovery';discovery()
  S['phase']='candidates'
  main_rows=build_candidates() if S.get('candidate_rule')!=CANDIDATE_RULE else load_main()
  S['phase']='stats';stats(main_rows)
  init_videos(main_rows);report()
  milestone('candidates_and_stats_complete',**S['candidate_counts'])
  hold=PROV/'youtube_claude_hold'
  if hold.exists() and 'rounds' not in S:
   S['status']='hold_awaiting_user_decision';save();report();milestone('hold_before_round1')
   while hold.exists():time.sleep(60)
   S['status']='running';save()
  search_init()
  for rnd in ROUNDS:run_round(rnd,main_rows)
  milestone('rounds_complete')
  while S['search']['status'] in ('waiting_first_window','running','waiting_daily_budget'):
   if search_due():search_step()
   else:S['phase']='waiting_search_window';save();time.sleep(60)
  if any(j['page'] for j in S['search']['jobs']):
   S['phase']='candidates_after_search';main_rows=build_candidates();stats(main_rows);init_videos(main_rows)
   for rnd in ROUNDS:run_round(rnd,main_rows,'_after_search')
  S['status']='complete';S['phase']='done';report();milestone('all_rounds_complete')
 except Stop as e:
  log('STOPPED',e)
 except Exception as e:
  S['status']='crashed';S['stop_event']=dict(type=type(e).__name__,message=str(e)[:300]);save();raise

if __name__=='__main__':
 with ExitStack() as stack:
  for lock in ['youtube_claude','youtube_playlistItems','youtube_commentThreads','youtube_search']:stack.enter_context(worker_lock(lock))
  main()
