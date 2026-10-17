from common import *
from macro import SERIES,LICENSE

def main():
 release_ids=set()
 for ds,sids in SERIES.items():
  for sid in sids:
   p=fetch('R01','https://api.stlouisfed.org/fred/series/release',sid+'_release_metadata.json',{'series_id':sid,'file_type':'json'},key='fred',license_note=LICENSE)
   if p:
    release_ids.update(x['id'] for x in json.loads(p.read_bytes()).get('releases',[]))
 for rid in sorted(release_ids):
  offset=0
  while True:
   p=fetch('R01','https://api.stlouisfed.org/fred/release/dates',f'release_{rid}_dates_{offset:06}.json',{'release_id':rid,'file_type':'json','realtime_start':'2008-01-01','realtime_end':'2027-12-31','include_release_dates_with_no_data':'true','limit':1000,'offset':offset},key='fred',license_note=LICENSE)
   if not p:break
   obj=json.loads(p.read_bytes());offset+=len(obj.get('release_dates',[]))
   if offset>=obj.get('count',0) or not obj.get('release_dates'):break

if __name__=='__main__':main()
