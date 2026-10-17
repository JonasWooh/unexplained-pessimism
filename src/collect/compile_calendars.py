"""Transcribe source dates into provenance tables; never alter source files."""
from common import *
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re,pymupdf,pandas as pd

def write(name,rows,fields):
 with (PROV/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
 sources={r['file_path']:r for r in csv.DictReader((PROV/'sources.csv').open())}
 def source(p):return sources[str(p.relative_to(ROOT))]['url_or_endpoint']
 calendar=list(csv.DictReader((PROV/'release_calendar.csv').open()))
 calendar=[r for r in calendar if r['release_type'] in ['prelim','final','alfred_vintage']]
 ridmap={}
 for p in (ROOT/'data/raw/R01'/DAY).glob('*_release_metadata.json'):
  sid=p.name.removesuffix('_release_metadata.json')
  for r in json.loads(p.read_bytes()).get('releases',[]):ridmap.setdefault(r['id'],[]).append(sid)
 for p in (ROOT/'data/raw/R01'/DAY).glob('release_*_dates_*.json'):
  for r in json.loads(p.read_bytes())['release_dates']:
   for sid in ridmap[r['release_id']]:
    calendar.append(dict(indicator=sid,reference_period='',release_date=r['date'],release_type='source_release_schedule',source_url=source(p),notes='FRED release calendar; reference period and estimate type not supplied; future dates are scheduled'))
 p=ROOT/'data/raw/R01'/DAY/'bea_schedule.html'
 for tr in BeautifulSoup(p.read_bytes(),'html.parser').find_all('tr'):
  t=tr.get_text(' ',strip=True)
  m=re.match(r'([A-Z][a-z]+) (\d{1,2}) 8:30 AM .*?(GDP|Personal Income and Outlays)(.*2026.*)',t)
  if not m:continue
  month,day,indicator,tail=m.groups();date=dt.datetime.strptime(f'{month} {day} 2026','%B %d %Y').date().isoformat()
  if date<CUTOFF:continue
  if indicator=='GDP':
   typ=re.search(r'(Advance|Second|Third) Estimate',tail);q=re.search(r'(\d)(?:st|nd|rd|th) Quarter 2026',tail)
   if not typ or not q:continue
   kind=typ.group(1).lower();period='2026Q'+q.group(1)
  else:
   kind='monthly';mth=re.search(r'([A-Z][a-z]+) 2026',tail)
   if not mth:continue
   period=dt.datetime.strptime(mth.group(1)+' 2026','%B %Y').strftime('%Y-%m')
  calendar.append(dict(indicator=indicator,reference_period=period,release_date=date,release_type=kind,source_url=source(p),notes='BEA scheduled release at 08:30 America/New_York; not yet observed'))
 write('release_calendar.csv',calendar,['indicator','reference_period','release_date','release_type','source_url','notes'])
 events=[];seen=set()
 for p in sorted((ROOT/'data/raw/R02'/DAY).glob('fomc*.htm')):
  for a in BeautifulSoup(p.read_bytes(),'html.parser').find_all('a',href=True):
   label=a.get_text(' ',strip=True);parent=a.parent.get_text(' ',strip=True)
   m=re.search(r'(?:monetary|monetary/)(\d{8})a\.htm$',a['href'])
   if not m or not (label=='Statement' or (label=='HTML' and parent.startswith('Statement:'))):continue
   date=dt.datetime.strptime(m.group(1),'%Y%m%d').date().isoformat()
   if date>CUTOFF:continue
   url=urljoin('https://www.federalreserve.gov/',a['href'])
   if url in seen:continue
   seen.add(url);events.append(dict(date=date,event='FOMC statement published',category='monetary_policy_statement',source_url=url,evidence_file=str(p.relative_to(ROOT)),notes='Date transcribed from statement link on official meeting archive; includes unscheduled statements'))
 for date,name,category,filename in [
  ('2020-03-11','WHO characterized COVID-19 as a pandemic','pandemic','who_pandemic_speech.html'),
  ('2023-03-10','Silicon Valley Bank closed; FDIC appointed receiver','bank_resolution','svb_20230310.html'),
  ('2023-03-12','Federal Reserve announced Bank Term Funding Program','financial_policy','btfp_20230312.html'),
  ('2018-06-15','USTR announced Section 301 tariff product list','tariff_announcement','tariffs_20180615.html'),
  ('2025-04-02','Reciprocal tariff executive order signed','tariff_announcement','tariffs_20250402.html'),
  ('2025-10-01','Lapse in appropriations began','shutdown_start','shutdown_2025_end.html'),
  ('2025-11-12','Appropriations restoration legislation enacted','shutdown_end','shutdown_2025_end.html'),
  ('2013-10-01','Lapse in appropriations began','shutdown_start','shutdown_2013_pay.pdf'),
  ('2013-10-17','OPM announced restoration of Federal employees to pay status','shutdown_reopening_notice','shutdown_2013_pay.pdf'),
  ('2018-12-22','Lapse in appropriations began','shutdown_start','shutdown_2019_pay.pdf'),
  ('2019-01-25','Lapse in appropriations ended','shutdown_end','shutdown_2019_pay.pdf'),
  ('2020-06-08','NBER announced February 2020 business cycle peak','business_cycle_announcement','nber_announcement_20200608.html'),
 ]:
  p=ROOT/'data/raw/R02'/DAY/filename
  if p.exists():events.append(dict(date=date,event=name,category=category,source_url=source(p),evidence_file=str(p.relative_to(ROOT)),notes='Verified in saved official source; announcement date distinguished from effective date'))
 write('events.csv',sorted(events,key=lambda r:r['date']),['date','event','category','source_url','evidence_file','notes'])
 elections=[]
 for p in sorted((ROOT/'data/raw/R03'/DAY).glob('election_*.pdf')):
  t=' '.join(pymupdf.open(p)[0].get_text().split());m=re.search(r'ELECTION OF (NOVEMBER \d{1,2}, \d{4})',t)
  if not m:raise ValueError('Election date not found: '+p.name)
  date=dt.datetime.strptime(m.group(1),'%B %d, %Y').date().isoformat()
  elections.append(dict(date=date,event='US federal general election',source_url=source(p),status='historical'))
 p=ROOT/'data/raw/R03'/DAY/'2026pdates.pdf';t=pymupdf.open(p)[0].get_text();m=re.search(r'General Election Date (\d{2}/\d{2}/\d{4})',t)
 if m:elections.append(dict(date=dt.datetime.strptime(m.group(1),'%m/%d/%Y').date().isoformat(),event='US federal general election',source_url=source(p),status='scheduled; FEC source dated 2026-05-18'))
 write('political_elections.csv',elections,['date','event','source_url','status'])
 for filename in ['presidents_terms.html','senate_party_division.html','house_party_division.html']:
  p=ROOT/'data/raw/R03'/DAY/filename
  for i,table in enumerate(pd.read_html(p)):
   table.to_csv(PROV/(p.stem+f'_table_{i}.csv'),index=False)
 print('Release calendar',len(calendar),'events',len(events),'elections',len(elections))

if __name__=='__main__':main()
