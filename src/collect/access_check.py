"""One direct connectivity request per planned host; no circumvention or retries."""
import concurrent.futures
import csv
import datetime as dt
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
TARGETS = [
 ('Michigan','https://www.sca.isr.umich.edu/tables.html'),
 ('Michigan data','https://data.sca.isr.umich.edu/tables.php'),
 ('FRED API','https://api.stlouisfed.org/fred/series?series_id=UNRATE&file_type=json'),
 ('FRED','https://fred.stlouisfed.org/'),
 ('ALFRED','https://alfred.stlouisfed.org/'),
 ('BLS API','https://api.bls.gov/publicAPI/v2/timeseries/data/LNS14000000'),
 ('BLS','https://www.bls.gov/schedule/'),
 ('BEA apps','https://apps.bea.gov/'),
 ('BEA','https://www.bea.gov/news/schedule'),
 ('NYT API','https://api.nytimes.com/svc/archive/v1/2009/12.json'),
 ('Guardian API','https://content.guardianapis.com/search?page-size=1'),
 ('Media Cloud','https://search.mediacloud.org/'),
 ('GDELT','https://api.gdeltproject.org/api/v2/doc/doc?query=economy&mode=timelinevolraw&format=json&timespan=1d'),
 ('FRBSF','https://www.frbsf.org/research-and-insights/data-and-indicators/daily-news-sentiment-index/'),
 ('YouTube API','https://www.googleapis.com/youtube/v3/channels?part=id&forHandle=CNN'),
 ('Philadelphia Fed','https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/real-time-data-set-for-macroeconomists'),
 ('EPU','https://www.policyuncertainty.com/us_monthly.html'),
 ('Atlanta Fed','https://www.atlantafed.org/'),
 ('Pew','https://www.pewresearch.org/internet/2025/11/20/americans-social-media-use-2025/'),
 ('Federal Reserve','https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm'),
]

def probe(target):
 name,url=target
 row=dict(source=name,url=url,checked_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),http_status='',outcome='',content_type='')
 try:
  r=requests.get(url,timeout=25)
  row.update(http_status=r.status_code,content_type=r.headers.get('Content-Type',''),outcome='accessible' if r.ok else 'HTTP error; distinguish authentication from access restriction')
 except requests.RequestException as e:
  row['outcome']=type(e).__name__
 return row

if __name__=='__main__':
 out=ROOT/'provenance';out.mkdir(exist_ok=True)
 rows=list(concurrent.futures.ThreadPoolExecutor(max_workers=6).map(probe,TARGETS))
 p=out/('access_check_'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.csv')
 with p.open('x') as f:
  w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
 for row in rows: print(row['source'],row['http_status'],row['outcome'])
 print('Reddit: not contacted, pending user confirmation')
