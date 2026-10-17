"""Collect official event evidence and append source-stated dates only."""
from common import *
from audit_runtime import worker_lock
from bs4 import BeautifulSoup
# Dates and titles were verified against official source pages before inclusion.
EVENTS=[
('2024-09-13','USTR announced final Section 301 tariff modifications','tariff_announcement','https://ustr.gov/about-us/policy-offices/press-office/press-releases/2024/september/ustr-finalizes-action-china-tariffs-following-statutory-four-year-review','tariffs_20240913.html',['September 13, 2024','final']),
('2019-08-13','USTR announced revised timing for proposed China tariffs','tariff_announcement','https://www.ustr.gov/about-us/policy-offices/press-office/press-releases/2019/august/ustr-announces-next-steps-proposed','tariffs_20190813.html',['August 13, 2019','December 15']),
('2020-01-15','United States and China signed Phase One agreement','trade_agreement_signed','https://ustr.gov/about-us/policy-offices/press-office/press-releases/2020/january/economic-and-trade-agreement-between-government-united-states-and-government-peoples-republic-china','phase_one_20200115.html',['January 15, 2020','Agreement']),
('2020-02-14','Phase One agreement entered into force','trade_agreement_effective','https://www.ustr.gov/about-us/policy-offices/press-office/press-releases/2020/february/usda-and-ustr-announce-progress-implementation-us-china-phase-one-agreement','phase_one_effective_20200214.html',['entered into force on February 14, 2020']),
('2023-03-12','FDIC established Signature Bridge Bank following closure of Signature Bank','bank_resolution','https://www.fdic.gov/news/press-releases/2023/pr23018.html','signature_20230312.html',['March 12, 2023','Signature']),
('2023-05-01','First Republic Bank closed and FDIC appointed receiver','bank_resolution','https://www.fdic.gov/resources/resolutions/bank-failures/failed-bank-list/first-republic.html','first_republic_20230501.html',['May 1, 2023','Receiver']),
('2018-01-20','OPM announced lapse in appropriations affecting federal operations','shutdown_start','https://www.opm.gov/policy-data-oversight/snow-dismissal-procedures/status-archives/18/1/20/Due-to-a-lapse-in-appropriations-Federal-government-operations-vary-by-agency_761/','shutdown_20180120.html',['January 20, 2018','lapse']),
('2018-02-09','Federal lapse in appropriations referenced by OPM pay guidance','shutdown_lapse','https://www.opm.gov/chcoc/transmittals/2018/pay-employees-affected-lapse-appropriations-and-continued-pay-freeze-certain-senior_508.pdf','shutdown_20180209.pdf',['February 9','2018']),
]
def main():
 path=PROV/'events.csv';rows=list(csv.DictReader(path.open()));existing={(r['date'],r['event']) for r in rows};checks=[]
 for date,event,category,url,name,phrases in EVENTS:
  p=fetch('R02',url,name,delay=2,license_note='Official event announcement; date explicitly distinguished from effective date; internal evidence collection only.')
  if not p:checks.append(dict(date=date,url=url,status='download_failed'));continue
  if p.suffix=='.pdf':
   import fitz
   with fitz.open(p) as doc:body=' '.join(page.get_text() for page in doc)
  else:body=BeautifulSoup(p.read_bytes(),'html.parser').get_text(' ',strip=True)
  body=' '.join(body.split());ok=all(phrase.casefold() in body.casefold() for phrase in phrases)
  checks.append(dict(date=date,url=url,status='evidence_verified' if ok else 'needs_evidence_check',file=str(p.relative_to(ROOT))))
  if ok and (date,event) not in existing:
   rows.append(dict(date=date,event=event,category=category,source_url=url,evidence_file=str(p.relative_to(ROOT)),notes='Official source evidence verified; no inferred economic impact or labels. Date is stated announcement/effective date as specified by event.'));existing.add((date,event))
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(sorted(rows,key=lambda r:(r['date'],r['event'])))
 (PROV/'audit_event_evidence.json').write_text(json.dumps(checks,indent=2));print('Events',len(rows),'new evidence',len(checks),flush=True)
if __name__=='__main__':
 with worker_lock('official_event_pages'):main()
