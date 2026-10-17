"""One-shot continuation of the already requested Media Cloud download."""
from common import *
import subprocess,sys,os

def main():
 state=dict(started_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),supervisor_pid=os.getpid(),task='Media Cloud monitoring-window full pagination',status='running',log='provenance/mediacloud_background_progress.log',not_a_scheduled_task=True)
 with (PROV/'mediacloud_background_progress.log').open('a') as log:
  p=subprocess.Popen([sys.executable,str(ROOT/'src/collect/N03.py')],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
  state['worker_pid']=p.pid;(PROV/'running_collection.json').write_text(json.dumps(state,indent=2))
  code=p.wait()
 state.update(finished_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),exit_code=code)
 collection=json.loads((PROV/'mediacloud_collection_state.json').read_text())
 state['status']='complete' if code==0 and all(s['complete'] for s in collection['collections']) else 'stopped_incomplete'
 (PROV/'running_collection.json').write_text(json.dumps(state,indent=2))
 with (PROV/'background_final_check.log').open('a') as log:subprocess.run([sys.executable,str(ROOT/'src/collect/finalize_snapshot.py')],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)

if __name__=='__main__':main()
