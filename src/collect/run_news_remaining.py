"""One-shot independent official news collectors, followed by local checks."""
from common import *
import subprocess,sys,os

def main():
 workers=[];handles=[];state=dict(pid=os.getpid(),status='running',not_a_scheduled_task=True,started_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),workers={})
 path=PROV/'news_running_collection.json'
 for ds in ['N01','N02']:
  log=(PROV/(ds+'_archive_progress.log')).open('a');handles.append(log)
  p=subprocess.Popen([sys.executable,str(ROOT/'src/collect/news_archives.py'),ds],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
  workers.append((ds,p));state['workers'][ds]=p.pid
 path.write_text(json.dumps(state,indent=2))
 state['exit_codes']={ds:p.wait() for ds,p in workers}
 for log in handles:log.close()
 state.update(status='workers_finished_check_dataset_states',finished_at_utc=dt.datetime.now(dt.timezone.utc).isoformat());path.write_text(json.dumps(state,indent=2))
 with (PROV/'news_final_check.log').open('a') as log:subprocess.run([sys.executable,str(ROOT/'src/collect/finalize_snapshot.py')],stdout=log,stderr=subprocess.STDOUT,check=True)

if __name__=='__main__':main()
