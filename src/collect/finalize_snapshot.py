"""Produce a new local integrity snapshot. No network calls or raw edits."""
from common import *
import subprocess,sys

def main():
 for script in ['validate.py','check_completeness.py','compile_calendars.py','youtube_audit.py','news_audit.py','enrich_manifest.py','report_status.py']:
  subprocess.run([sys.executable,str(ROOT/'src/collect'/script)],cwd=ROOT,check=True)
 report=json.loads((PROV/'privacy_check.json').read_text())
 if report['failures']:raise RuntimeError('Privacy failures recorded; inspect privacy_check.json')

if __name__=='__main__':main()
