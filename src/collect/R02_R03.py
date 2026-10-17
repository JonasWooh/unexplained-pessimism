from common import *
from bs4 import BeautifulSoup
import re

def main():
 for ds,u,n in [
  ('R02','https://www.who.int/news-room/speeches/item/who-director-general-s-opening-remarks-at-the-media-briefing-on-covid-19---11-march-2020','who_pandemic_speech.html'),
  ('R03','https://www.archives.gov/research/census/presidents','presidents_terms.html'),
  ('R03','https://history.house.gov/Institution/Election-Statistics/','election_statistics_current.html'),
  ('R02','https://www.federalreserve.gov/monetarypolicy/fomc_historical_year.htm','fomc_historical_year.html'),
 ]:fetch(ds,u,n)
 p=ROOT/'data/raw/R03'/DAY/'election_statistics_current.html'
 for t,u in links(p,'https://history.house.gov/'):
  m=re.search(r'(20(?:10|12|14|16|18|20|22|24))election',u)
  if m:fetch('R03',u,'election_'+m.group(1)+'.pdf')
 p=ROOT/'data/raw/R02'/DAY/'fomc_historical_year.html'
 if p.exists():
  for t,u in links(p,'https://www.federalreserve.gov/'):
   if re.search(r'fomchistorical20(1\d|20)\.htm',u):fetch('R02',u,Path(urlsplit(u).path).name)

if __name__=='__main__':main()
