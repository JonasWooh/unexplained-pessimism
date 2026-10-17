"""Official authenticated monthly news archives, immutable raw responses."""
from common import *
import argparse,calendar,os

LICENSE='Official authenticated API; user requested local raw collection. Source terms retained; no model training, analysis, or redistribution in this collection task.'

def months(first):
 year,month=map(int,first.split('-'))
 while (year,month)<=tuple(map(int,CUTOFF[:7].split('-'))):
  yield year,month
  year,month=(year+1,1) if month==12 else (year,month+1)

def used(ds):
 today=dt.datetime.now(dt.timezone.utc).date()
 host='api.nytimes.com' if ds=='N01' else 'content.guardianapis.com'
 return sum(host in e.get('url','') and dt.datetime.fromisoformat(e['requested_at_utc']).date()==today for e in (json.loads(line) for line in (PROV/'requests.jsonl').read_text().splitlines()) if 'requested_at_utc' in e)

def main(ds):
 state_path=PROV/(ds+'_archive_state.json');folder=ROOT/'corpus/raw'/ds/DAY
 state=dict(dataset_id=ds,pid=os.getpid(),status='running',started_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),months=[])
 def save():
  state['updated_at_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
  tmp=state_path.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2));tmp.replace(state_path)
 save();calls=used(ds)
 for year,month in months('2009-12' if ds=='N01' else '2010-01'):
  period=f'{year:04}-{month:02}';entry=dict(month=period,rows=0,pages=0,complete=False,missing_body=0);state['months'].append(entry)
  page=1
  while True:
   name=period+'.json' if ds=='N01' else f'{period}_{page:04}.json'
   cached=(folder/name).exists()
   if not cached and calls>=490:
    state['status']='paused_daily_budget';save();return
   if ds=='N01':
    p=fetch(ds,f'https://api.nytimes.com/svc/archive/v1/{year}/{month}.json',name,key='nyt',keyparam='api-key',delay=13,license_note=LICENSE)
   else:
    end=min(f'{period}-{calendar.monthrange(year,month)[1]:02}',CUTOFF)
    params={'tag':'business/useconomy','from-date':period+'-01','to-date':end,'show-fields':'headline,trailText,bodyText,byline,wordcount','show-tags':'keyword','page-size':200,'page':page,'order-by':'oldest'}
    p=fetch(ds,'https://content.guardianapis.com/search',name,params,key='guardian',keyparam='api-key',delay=1.1,license_note=LICENSE)
   if not cached:calls+=1
   if not p:state['status']='stopped_api_error';save();return
   obj=json.loads(p.read_bytes());response=obj.get('response',{})
   if ds=='N01':
    if 'docs' not in response:raise ValueError('Archive response missing docs')
    items=response['docs'];entry['expected_rows']=response['meta']['hits']
    if len(items)!=entry['expected_rows']:raise ValueError('NYT archive count mismatch')
    entry['complete']=True
   else:
    if response.get('status')!='ok':raise ValueError('Guardian response not ok')
    items=response['results'];entry['expected_rows']=response['total'];entry['expected_pages']=response['pages'];entry['complete']=page>=response['pages']
    entry['missing_body']+=sum(not x.get('fields',{}).get('bodyText') for x in items)
   entry['rows']+=len(items);entry['pages']+=1;save()
   if entry['complete']:
    if ds=='N02' and entry['rows']!=entry['expected_rows']:raise ValueError('Guardian page count mismatch')
    break
   page+=1
 state['status']='complete_monthly_archive';save()

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('dataset',choices=['N01','N02']);main(parser.parse_args().dataset)
