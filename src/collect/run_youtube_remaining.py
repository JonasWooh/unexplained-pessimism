"""One-shot continuation; no automatic retries after API failures."""
from common import *
import os,sys,subprocess

def main():
 status_path=PROV/'youtube_running_collection.json'
 state=dict(started_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),pid=os.getpid(),status='running',stage='comment_text',not_a_scheduled_task=True)
 status_path.write_text(json.dumps(state,indent=2))
 try:
  subprocess.run([sys.executable,str(ROOT/'src/collect/youtube_comment_text.py')],check=True)
  body=json.loads((PROV/'youtube_comment_text_state.json').read_text())
  if body['status']!='stopped_api_error':
   state['stage']='video_metadata';status_path.write_text(json.dumps(state,indent=2))
   from youtube_details import main as details
   state['metadata_finished']=bool(details())
  state['status']=body['status']
 except Exception as e:
  state['status']='stopped_error';state['error_type']=type(e).__name__
 finally:
  state['finished_at_utc']=dt.datetime.now(dt.timezone.utc).isoformat();status_path.write_text(json.dumps(state,indent=2))
  subprocess.run([sys.executable,str(ROOT/'src/collect/finalize_snapshot.py')],check=True)

if __name__=='__main__':main()
