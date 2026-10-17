from common import *
from macro import SERIES
import re,pymupdf
from bs4 import BeautifulSoup

def main():
 rows=[];value_rows=[]
 source='https://data.sca.isr.umich.edu/fetchdoc.php?docid=75443'
 doc=pymupdf.open(ROOT/'data/raw/S05'/DAY/'historical_release_dates.pdf')
 text='\n'.join(p.get_text() for p in doc)
 schedule={}
 for month,year,prelim,final in re.findall(r'([A-Z][a-z]{2})\s+(\d{4})\s+(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}/\d{1,2}/\d{4})',text):
  ym=dt.datetime.strptime(month+' '+year,'%b %Y').strftime('%Y-%m')
  for kind,date in [('prelim',prelim),('final',final)]:
   iso=dt.datetime.strptime(date,'%m/%d/%Y').date().isoformat();schedule[(ym,kind)]=iso
   rows.append(dict(indicator='Michigan ICS/ICC/ICE',reference_period=ym,release_date=iso,release_type=kind,source_url=source,notes='scheduled' if iso>CUTOFF else 'official historical release calendar'))
 sources=list(csv.DictReader((PROV/'sources.csv').open()))
 bypath={r['file_path']:r['url_or_endpoint'] for r in sources}
 for p in sorted((ROOT/'data/raw/S05'/DAY).glob('*_Results.pdf')):
  year,month,kind,_=p.stem.split('_');ym=dt.datetime.strptime(month+' '+year,'%B %Y').strftime('%Y-%m');kind='prelim' if kind=='Preliminary' else 'final'
  s=pymupdf.open(p)[0].get_text()
  m=re.search(r'Index of Consumer Sentiment\s+((?:\d+\.\d+\s+)+)Current Economic Conditions',s)
  nums=re.findall(r'\d+\.\d+',m.group(1)) if m else []
  if len(nums)!=13:
   journal({'dataset_id':'S05','file_path':str(p.relative_to(ROOT)),'status':'release_value_requires_manual_verification','number_count':len(nums)});continue
  date_match=re.search(r'([A-Z][a-z]+ \d{1,2}, \d{4})',s)
  header_date=dt.datetime.strptime(date_match.group(1),'%B %d, %Y').date().isoformat() if date_match else ''
  value_rows.append(dict(month=ym,release_type=kind,value=nums[-1],release_date=schedule.get((ym,kind),''),report_header_date=header_date,source_url=bypath[str(p.relative_to(ROOT))],calendar_source_url=source))
 home=ROOT/'data/raw/S05'/DAY/'homepage.html'
 if home.exists():
  text=BeautifulSoup(home.read_bytes(),'html.parser').get_text(' ',strip=True)
  m=re.search(r'Preliminary Results for ([A-Z][a-z]+ \d{4}).*?Index of Consumer Sentiment (\d+\.\d+)',text)
  if m:
   ym=dt.datetime.strptime(m.group(1),'%B %Y').strftime('%Y-%m')
   value_rows.append(dict(month=ym,release_type='prelim',value=m.group(2),release_date=schedule.get((ym,'prelim'),''),report_header_date='',source_url=bypath[str(home.relative_to(ROOT))],calendar_source_url=source))
 with (PROV/'survey_release_values.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['month','release_type','value','release_date','report_header_date','source_url','calendar_source_url']);w.writeheader();w.writerows(value_rows)
 for ds,sids in SERIES.items():
  for sid in sids:
   for p in (ROOT/'data/raw'/ds/DAY).glob(sid+'_vintagedates_*.json'):
    for day in json.loads(p.read_bytes())['vintage_dates']:
     rows.append(dict(indicator=sid,reference_period='',release_date=day,release_type='alfred_vintage',source_url=bypath[str(p.relative_to(ROOT))],notes='ALFRED vintage date; observation reference periods and validity intervals are in raw observations; not assumed source release date'))
 with (PROV/'release_calendar.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['indicator','reference_period','release_date','release_type','source_url','notes']);w.writeheader();w.writerows(rows)
 print('Calendar rows',len(rows),'Survey release values',len(value_rows))
 for kind,month,url in [
  ('advance','2024-04','https://www.bea.gov/sites/default/files/2024-04/gdp1q24-adv.pdf'),
  ('second','2024-05','https://www.bea.gov/sites/default/files/2024-05/gdp1q24-2nd.pdf'),
  ('third','2024-06','https://www.bea.gov/sites/default/files/2024-06/gdp1q24-3rd.pdf')]:fetch('M04',url,Path(urlsplit(url).path).name)

if __name__=='__main__':main()
