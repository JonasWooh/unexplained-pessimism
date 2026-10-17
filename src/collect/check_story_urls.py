"""Read-only link/metadata spot check. Does not save article bodies or label content."""
from common import *
from bs4 import BeautifulSoup

def main():
 selected=[];domains=set();seen=set()
 for p in sorted((ROOT/'corpus/raw/N03'/DAY).glob('*_stories_*.json')):
  for r in json.loads(p.read_bytes())['stories']:
   host=urlsplit(r['url']).netloc.lower()
   if host in domains or r['id'] in seen:continue
   if any(x in host for x in ['nytimes.com','theguardian.com','bls.gov','allsides.com']):continue
   domains.add(host);seen.add(r['id']);selected.append(r)
   if len(selected)==20:break
  if len(selected)==20:break
 results=[]
 for r in selected:
  audit=dict(story_id=r['id'],url=r['url'],api_title=r['title'],api_publish_date=r['publish_date'],checked_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),status='',page_title='',page_date='',title_exact_match='',date_exact_match='')
  try:
   response=requests.get(r['url'],timeout=20);audit['status']=response.status_code
   if response.ok:
    soup=BeautifulSoup(response.content,'html.parser')
    title=soup.find('meta',attrs={'property':'og:title'})
    date=soup.find('meta',attrs={'property':'article:published_time'})
    audit['page_title']=title.get('content','') if title else ''
    audit['page_date']=date.get('content','') if date else ''
    if audit['page_title']:audit['title_exact_match']=audit['page_title']==r['title']
    if audit['page_date']:audit['date_exact_match']=audit['page_date'][:10]==r['publish_date'][:10]
  except requests.RequestException as e:audit['status']=type(e).__name__
  results.append(audit);print('URL check',len(results),audit['status'],flush=True)
 with (PROV/'news_url_spotcheck.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=results[0].keys());w.writeheader();w.writerows(results)

if __name__=='__main__':main()
