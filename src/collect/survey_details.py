from common import *
from survey import LICENSE
from bs4 import BeautifulSoup

def collect():
 for year in [2024,2025,2026]:
  page=ROOT/'data/raw/S05'/DAY/f'reports_{year}.html'
  for title,url in links(page,'https://data.sca.isr.umich.edu/'):
   if 'Results' in title:fetch('S05',url,f'{year}_'+title.replace(' ','_')+'.pdf',license_note=LICENSE)
 p=fetch('S05','https://data.sca.isr.umich.edu/technical-docs.php','technical-docs.html',license_note=LICENSE)
 for title,url in links(p,'https://data.sca.isr.umich.edu/'):
  if any(word in title.lower() for word in ['questionnaire','codebook','method','index','calculat']):
   fetch('S05',url,'technical_'+hashlib.sha256(url.encode()).hexdigest()[:10]+'.pdf',license_note=LICENSE)
 for ds,variables,demos in [('S02',['ics','icc','ice'],['age_18','age_35','age_55','inc_1','inc_2','inc_3','region_1','region_2','region_3','region_4','ehs','esc','ecd']),('S03',['news','newsrn'],['all']),('S04',['pagorn','px1','px5','dur','durrn','veh','vehrn','hom','homrn','umex','ratex','govt'],['all'])]:
  params=dict(freq='month',start_year=1978,end_year=2026)
  params.update({v:'on' for v in variables+demos})
  form=BeautifulSoup((ROOT/'data/raw/S02'/DAY/'demographics.html').read_bytes(),'html.parser').find('form')
  for element in form.find_all('input'):
   if element.get('type')=='radio' and element.get('checked') is not None:params[element['name']]=element.get('value','on')
  p=fetch(ds,'https://data.sca.isr.umich.edu/subset/output.php','monthly_subset_response.html',params,method='POST',license_note=LICENSE)
  if p:
   for t,u in links(p,'https://data.sca.isr.umich.edu/subset/'):
    if any(x in u for x in ['.csv','.xls','download']):fetch(ds,u,Path(urlsplit(u).path).name,license_note=LICENSE)
 fetch('S06','https://sda.umsurvey.org/','microdata_access.html',license_note=LICENSE)

if __name__=='__main__':collect()
