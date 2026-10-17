"""Coverage, pagination, duplicates and chronology; no substantive analysis."""
from common import *
from macro import SERIES
import pandas as pd,collections

def main():
 checks=[];monthly=[]
 for ds,sids in SERIES.items():
  for sid in sids:
   paths=sorted((ROOT/'data/raw'/ds/DAY).glob(sid+'_observations_*.json'))
   if not paths:continue
   objs=[json.loads(p.read_bytes()) for p in paths];a=[x for o in objs for x in o['observations']]
   # Real-time intervals are the source's version validity, not reconstructed releases.
   keys_=[(x['date'],x['realtime_start'],x['realtime_end']) for x in a]
   checks.append(dict(dataset_id=ds,series=sid,rows=len(a),expected_rows=objs[0]['count'],pagination_complete=len(a)==objs[0]['count'],duplicate_keys=len(keys_)-len(set(keys_)),missing_values=sum(x['value']=='.' for x in a),coverage_start=min(x['date'] for x in a),coverage_end=max(x['date'] for x in a),earliest_vintage=min(x['realtime_start'] for x in a),latest_vintage=max(x['realtime_start'] for x in a),future_vintages=sum(x['realtime_start']>CUTOFF for x in a),reference_after_version=sum(x['date']>x['realtime_start'] for x in a)))
   for period,n in sorted(collections.Counter(x['date'][:7] for x in a).items()):monthly.append(dict(dataset_id=ds,series=sid,period=period,rows=n,unit='observation-version rows'))
 with (PROV/'macro_completeness.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=checks[0].keys());w.writeheader();w.writerows(checks)
 # Explicit survey revisions remain visible; mismatches are not silently overwritten.
 ics=pd.read_csv(ROOT/'data/raw/S01'/DAY/'tbmics.csv');dates=pd.to_datetime(ics.Month+' '+ics.YYYY.astype(str),format='%B %Y').dt.strftime('%Y-%m')
 values=dict(zip(dates,ics.iloc[:,-1]));releases=list(csv.DictReader((PROV/'survey_release_values.csv').open()));comparison=[]
 for r in releases:
  if r['release_type']=='final':comparison.append(dict(month=r['month'],report_final=float(r['value']),current_csv=values.get(r['month'],''),equal=float(r['value'])==values.get(r['month']),source_url=r['source_url']))
 with (PROV/'survey_final_reconciliation.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=comparison[0].keys());w.writeheader();w.writerows(comparison)
 story_ids=collections.defaultdict(list);anomalies=[];story_months=collections.Counter()
 for p in (ROOT/'corpus/raw/N03'/DAY).glob('*_stories_*.json'):
  cid=p.name.split('_')[0]
  for x in json.loads(p.read_bytes())['stories']:
   story_ids[cid].append(str(x['id']))
   story_months[(cid,x['publish_date'][:7])]+=1
   if not ('2025-01-01'<=x['publish_date'][:10]<=CUTOFF):anomalies.append(dict(file=p.name,id=x['id'],date=x['publish_date'],issue='outside requested monitoring window'))
 counts=[]
 for p in (ROOT/'corpus/raw/N03'/DAY).glob('*_counts.json'):
  o=json.loads(p.read_bytes());a=o['count_over_time']['counts'];dates=[x['date'] for x in a];nz=[x['date'] for x in a if x['count']>0]
  counts.append(dict(file=p.name,rows=len(a),first_returned=min(dates),last_returned=max(dates),first_nonzero=min(nz,default=''),duplicate_dates=len(dates)-len(set(dates)),api_total=o['count_over_time']['total'],note='Old publication dates can be indexing errors; earliest returned date is not proof of complete historical coverage'))
 with (PROV/'mediacloud_counts_check.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=counts[0].keys());w.writeheader();w.writerows(counts)
 summary=dict(checked_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),macro_all_pages_complete=all(r['pagination_complete'] for r in checks),macro_duplicate_keys=sum(r['duplicate_keys'] for r in checks),macro_future_vintages=sum(r['future_vintages'] for r in checks),macro_reference_after_version=sum(r['reference_after_version'] for r in checks),survey_final_compared=len(comparison),survey_final_mismatches=[r for r in comparison if not r['equal']],stories={cid:dict(rows=len(ids),unique=len(set(ids)),duplicates=len(ids)-len(set(ids))) for cid,ids in story_ids.items()},story_date_anomalies=anomalies)
 (PROV/'completeness_check.json').write_text(json.dumps(summary,indent=2))
 for (cid,month),n in sorted(story_months.items()):monthly.append(dict(dataset_id='N03',series=cid,period=month,rows=n,unit='downloaded story rows; incomplete collection snapshot'))
 with (PROV/'monthly_record_counts.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['dataset_id','series','period','rows','unit']);w.writeheader();w.writerows(monthly)
 print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
