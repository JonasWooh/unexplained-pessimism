"""Enrich provenance metadata under a lock; raw files are never modified."""
from common import *

def main():
 inv={r['file_path']:r for r in csv.DictReader((PROV/'inventory.csv').open())}
 survey={r['source_url']:r for r in csv.DictReader((PROV/'survey_release_values.csv').open())}
 with (PROV/'sources.csv').open('r+',newline='') as f:
  fcntl.flock(f,fcntl.LOCK_EX);rows=list(csv.DictReader(f));registered=set()
  for r in rows:
   registered.add(r['file_path']);meta=inv.get(r['file_path'])
   if not meta:continue
   r['rows']=meta['rows'] if meta['rows'] else '1'
   r['coverage_start']=meta['coverage_start'] or 'not_applicable_or_not_in_document'
   r['coverage_end']=meta['coverage_end'] or 'not_applicable_or_not_in_document'
   r['notes']=meta['record_type']+'; '+meta['inventory_notes']+'; original response bytes retained'
   if meta['record_type']=='observation_vintage_rows':
    obj=json.loads((ROOT/r['file_path']).read_bytes());a=obj['observations'];r['vintage_or_release']=min(x['realtime_start'] for x in a)+'..'+max(x['realtime_start'] for x in a)+' (validity intervals in raw)'
   if r['url_or_endpoint'] in survey:
    s=survey[r['url_or_endpoint']];r.update(coverage_start=s['month'],coverage_end=s['month'],vintage_or_release=s['release_type']+' '+s['release_date']);r['notes']+='; primary reported month; PDF also contains prior-month comparison data'
   if r['dataset_id']=='R04':r.update(coverage_start='2025-02-05',coverage_end='2025-06-18',vintage_or_release='Pew 2025 publication; coverage is fieldwork period')
  f.seek(0);w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows);f.truncate()
 raw={str(p.relative_to(ROOT)) for root in ['data/raw','corpus/raw'] for p in (ROOT/root).rglob('*') if p.is_file()}
 # New downloads may be in progress; this is only a snapshot, never a repair.
 (PROV/'manifest_coverage_check.json').write_text(json.dumps(dict(checked_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),unregistered_raw_files=sorted(raw-registered),duplicate_file_entries=len(rows)-len(registered)),indent=2))
 print('Manifest metadata enriched:',len(rows),'unregistered raw files:',len(raw-registered))

if __name__=='__main__':main()
