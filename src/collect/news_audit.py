"""Monthly archive completeness and actual field availability; no annotation."""
from common import *
from news_archives import months
from collections import Counter,defaultdict

def main():
 groups=defaultdict(list)
 for r in csv.DictReader((PROV/'inventory.csv').open()):
  if r['record_type'] in ['nyt_articles','guardian_articles']:
   p=ROOT/r['file_path'];groups[(r['dataset_id'],p.name[:7])].append(p)
 rows=[];field_counts=defaultdict(Counter)
 for ds in ['N01','N02']:
  for year,month in months('2009-12' if ds=='N01' else '2010-01'):
   period=f'{year:04}-{month:02}';paths=sorted(groups[(ds,period)]);items=[];expected=0;pages=0
   for p in paths:
    response=json.loads(p.read_bytes())['response']
    if ds=='N01':a=response['docs'];expected=response['meta']['hits'];pages=1
    else:a=response['results'];expected=response['total'];pages=response['pages']
    items.extend(a)
   ids=[x['_id'] if ds=='N01' else x['id'] for x in items]
   for item in items:
    field_counts[ds].update(item.keys() if ds=='N01' else item.get('fields',{}).keys())
   dates=[x.get('pub_date' if ds=='N01' else 'webPublicationDate','') for x in items]
   missing_body=sum(not x.get('fields',{}).get('bodyText') for x in items) if ds=='N02' else ''
   rows.append(dict(dataset_id=ds,month=period,files=len(paths),rows=len(items),expected_rows=expected if paths else '',expected_pages=pages if paths else '',complete=bool(paths) and len(paths)==pages and len(items)==expected,duplicate_ids=len(ids)-len(set(ids)),missing_bodyText=missing_body,dates_outside_month=sum(d[:7]!=period for d in dates),earliest=min(dates,default=''),latest=max(dates,default='')))
 with (PROV/'news_monthly_completeness.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
 summary={ds:dict(months_expected=sum(r['dataset_id']==ds for r in rows),months_complete=sum(r['dataset_id']==ds and r['complete'] for r in rows),rows=sum(r['rows'] for r in rows if r['dataset_id']==ds),duplicate_ids_within_month=sum(r['duplicate_ids'] for r in rows if r['dataset_id']==ds),actual_field_presence=dict(field_counts[ds])) for ds in ['N01','N02']}
 (PROV/'news_integrity_summary.json').write_text(json.dumps(summary,indent=2));print('News archive counts:',{ds:(s['months_complete'],s['rows']) for ds,s in summary.items()})

if __name__=='__main__':main()
