from common import *
from audit_runtime import worker_lock,checkpoint,retry_fetch
import os
STATE=PROV/'nyt_refresh_state.json'
def main():
 stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S');s=dict(status='running',pid=os.getpid(),months=[]);checkpoint(STATE,s)
 for month in ['2026-01','2026-10']:
  year,number=map(int,month.split('-'))
  p=retry_fetch('N01',f'https://api.nytimes.com/svc/archive/v1/{year}/{number}.json',f'{month}_refresh_{stamp}.json',state=s,state_path=STATE,key='nyt',keyparam='api-key',delay=13,license_note='User requested re-download of source-truncated monthly archive. Separate immutable snapshot; API metadata only.')
  if not p:s['status']='stopped_api_error';checkpoint(STATE,s);return
  o=json.loads(p.read_bytes())['response'];dates=[d.get('pub_date','') for d in o['docs']]
  s['months'].append(dict(month=month,file=str(p.relative_to(ROOT)),response_rows=len(o['docs']),unique_ids=len({d['_id'] for d in o['docs']}),expected=o['meta']['hits'],earliest=min(dates,default=''),latest=max(dates,default='')));checkpoint(STATE,s)
 s['status']='refresh_complete_not_proof_of_temporal_completeness';checkpoint(STATE,s)
if __name__=='__main__':
 with worker_lock('nyt_archive'):main()
