from common import *
from bs4 import BeautifulSoup

def main():
 for title,doc in [('historical_release_dates',75443),('historical_interview_dates',75442),('data_revisions',80741)]:fetch('S05','https://data.sca.isr.umich.edu/fetchdoc.php',title+'.pdf',{'docid':doc})
 p=fetch('S05','https://www.sca.isr.umich.edu/','homepage.html')
 for t,u in links(p,'https://www.sca.isr.umich.edu/'):
  if any(x in t.lower() for x in ['release','schedule','calendar']):print('S05',t,u,flush=True)
 for var in ['routput','pcon','pconx','ruc']:
  u='https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/'+var
  p=fetch('M17',u,var+'.html')
  for t,l in links(p,u):
   if any(x in l.lower() for x in ['.xls','.zip']):
    print('M17',t,l,flush=True)
    if any(x in t.lower() for x in ['all','complete','monthly']) or l.lower().endswith('.zip'):fetch('M17',l,Path(urlsplit(l).path).name)
 for ds,u,n in [
  ('R03','https://www.senate.gov/history/partydiv.htm','senate_party_division.html'),
  ('R03','https://history.house.gov/Institution/Party-Divisions/Party-Divisions/','house_party_division.html'),
  ('R03','https://clerk.house.gov/member_info/electionInfo/index.aspx','election_statistics.html'),
  ('R03','https://www.archives.gov/presidential-libraries/contact/libraries','presidential_libraries.html'),
  ('R03','https://www.fec.gov/resources/cms-content/documents/2026pdates.pdf','2026pdates.pdf'),
  ('N06','https://www.allsides.com/media-bias/media-bias-ratings','ratings_license_page.html'),
  ('R02','https://www.who.int/director-general/speeches/detail/who-director-general-s-opening-remarks-at-the-media-briefing-on-covid-19---11-march-2020','who_pandemic_20200311.html'),
 ]:fetch(ds,u,n)
 # GDELT 429 in initial probe: one spaced recheck, then stop on failure.
 p=fetch('N04','https://api.gdeltproject.org/api/v2/doc/doc','general_timelinevolraw.json',{'query':'economy sourcecountry:US sourcelang:english','mode':'timelinevolraw','format':'json','startdatetime':'20170101000000','enddatetime':'20261014235959'},delay=6)
 if not p:print('GDELT unavailable; collection stopped',flush=True)

if __name__=='__main__':main()
