from common import *
TOPICS={
 'all':'*',
 'prices':'inflation OR prices OR "cost of living" OR "grocery prices" OR "gas prices" OR affordability OR "price increases"',
 'employment':'unemployment OR jobless OR layoffs OR hiring OR "jobs report" OR "labor market"',
 'growth':'GDP OR "economic growth" OR recession OR "economic slowdown"',
 'housing_rates':'"interest rates" OR "mortgage rates" OR "Federal Reserve" OR "housing costs" OR rent',
 'general':'economy OR "consumer sentiment" OR "consumer confidence" OR tariffs',
}
LICENSE='Media Cloud terms permit research and aggregate outputs; third-party article rights not conveyed; raw titles/URLs internal only, no full text requested.'

def main():
 hdr={'Authorization':'Token '+keys()['mediacloud']}
 collections=json.loads((ROOT/'corpus/raw/N03'/DAY/'collections_US.json').read_bytes())['results']
 for c in collections:
  if c['name'] not in ['United States - National','United States - State & Local']:continue
  cid=c['id']
  for topic,q in TOPICS.items():
   params=dict(start='2010-01-01',end=CUTOFF,q=q,platform='onlinenews-mediacloud',cs=cid)
   p=fetch('N03','https://search.mediacloud.org/api/search/count-over-time',f'{cid}_{topic}_counts.json',params,headers=hdr,delay=31,license_note=LICENSE)
   if not p:break
 selected=[c for c in collections if c['name'] in ['United States - National','United States - State & Local']]
 query=' OR '.join('('+v+')' for k,v in TOPICS.items() if k!='all')
 for c in selected:
  for label,start,q in [('archive_extent','1900-01-01','*'),('monitoring_union','2025-01-01',query)]:
   fetch('N03','https://search.mediacloud.org/api/search/count-over-time',f"{c['id']}_{label}_counts.json",dict(start=start,end=CUTOFF,q=q,platform='onlinenews-mediacloud',cs=c['id']),headers=hdr,delay=31,license_note=LICENSE)
 # A single worker enforces the account-wide 2/minute rate. Alternate collections
 # and resume from exact saved page tokens, without sampling or skipping records.
 states=[]
 for c in selected:
  s=dict(collection_id=c['id'],name=c['name'],next_page=0,token=None,rows=0,complete=False,error=False)
  while True:
   p=ROOT/'corpus/raw/N03'/DAY/f"{c['id']}_stories_{s['next_page']:05}.json"
   if not p.exists():break
   o=json.loads(p.read_bytes());s['rows']+=len(o['stories']);s['next_page']+=1;s['token']=o.get('pagination_token')
   if not s['token']:s['complete']=True;break
  states.append(s)
 while any(not s['complete'] and not s['error'] for s in states):
  for s in states:
   if s['complete'] or s['error']:continue
   params=dict(start='2025-01-01',end=CUTOFF,q=query,platform='onlinenews-mediacloud',cs=s['collection_id'],page_size=1000,sort_order='asc')
   if s['token']:params['pagination_token']=s['token']
   p=fetch('N03','https://search.mediacloud.org/api/search/story-list',f"{s['collection_id']}_stories_{s['next_page']:05}.json",params,headers=hdr,delay=31,license_note=LICENSE)
   if not p:s['error']=True
   else:
    o=json.loads(p.read_bytes());s['rows']+=len(o['stories']);s['next_page']+=1;s['token']=o.get('pagination_token');s['complete']=not bool(s['token'])
   state=PROV/'mediacloud_collection_state.json';tmp=state.with_suffix('.tmp')
   tmp.write_text(json.dumps(dict(updated_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),collections=states),ensure_ascii=False,indent=2));tmp.replace(state)

if __name__=='__main__':main()
