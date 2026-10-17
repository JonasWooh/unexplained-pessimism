from common import *
from survey import LICENSE
def main():
 for ds,variables in [('S03',['news','newsrn']),('S04',['pagorn','px1','px5','dur','durrn','veh','vehrn','hom','homrn','umex','ratex','govt'])]:
  p=dict(freq='month',start_year=1978,end_year=2026,scores='all',all='on')
  p.update({v:'on' for v in variables})
  fetch(ds,'https://data.sca.isr.umich.edu/subset/output.php','monthly_all_response_codes.csv',p,method='POST',license_note=LICENSE)
 fetch('S05','https://data.sca.isr.umich.edu/subset/codebook.php','subset_codebook.pdf',license_note=LICENSE)
 for ds,stem in [('M17','routput'),('M17','pcon'),('M17','pconx'),('M17','ruc')]:
  p=ROOT/'data/raw'/ds/DAY/(stem+'.html')
  for t,u in links(p,'https://www.philadelphiafed.org/'):
   if '.xlsx' in u or '.xls?' in u:fetch(ds,u,Path(urlsplit(u).path).name)

if __name__=='__main__':main()
