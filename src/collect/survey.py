from common import *
from urllib.parse import parse_qs,urlsplit
LICENSE='University of Michigan, Survey Research Center, Surveys of Consumers. Organization internal use allowed with attribution; redistribution/publication requires express written consent.'
GROUPS={'S01':['1a','1b'],'S02':['2n','3n','4n','5a','5b'],'S03':['23','24'],'S04':['7','30','31','32','33','34','35','36','37','38','41','42']}

def collect():
 for ds,names in [('S01',['tbmics.csv','tbmiccice.csv']),('S04',['tbmpx1px5.csv'])]:
  for name in names:fetch(ds,'https://www.sca.isr.umich.edu/files/'+name,name,license_note=LICENSE)
 page=ROOT/'data/raw/S05'/DAY/'tables.php.html'
 for title,url in links(page,'https://data.sca.isr.umich.edu/'):
  q=parse_qs(urlsplit(url).query)
  if q.get('f')!=['xls'] or q.get('c')!=['YB']:continue
  n=q['n'][0]
  for ds,ns in GROUPS.items():
   if n in ns:fetch(ds,url,'table_'+n+'_YB_'+q['y'][0]+'_'+q['m'][0]+'.xls',license_note=LICENSE)
 for year in [2024,2025,2026]:fetch('S05','https://data.sca.isr.umich.edu/reports.php',f'reports_{year}.html',{'year':year},license_note=LICENSE)
 for filename in ['methodtransitionannouncement2024.pdf','partisaneconomy202607_revised.pdf','partisaneconomy202504.pdf','partisaneconomy202402.pdf']:
  fetch('S05','https://www.sca.isr.umich.edu/files/'+filename,filename,license_note=LICENSE)
 for ds,url,name in [('S02','https://data.sca.isr.umich.edu/subset/subset.php','demographics.html'),('S06','https://data.sca.isr.umich.edu/sda.php','cross_section.html')]:fetch(ds,url,name,license_note=LICENSE)

if __name__=='__main__':collect()
