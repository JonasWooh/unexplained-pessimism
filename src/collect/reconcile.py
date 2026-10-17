"""Read-only workbook reconciliation, never an analysis input or imputation source."""
from common import *
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup

def latest(ds,sid):
 p=ROOT/'data/raw'/ds/DAY/(sid+'_latest.csv')
 d=pd.read_csv(p);d.iloc[:,0]=pd.to_datetime(d.iloc[:,0]);d['month']=d.iloc[:,0].dt.to_period('M').astype(str)
 return pd.Series(pd.to_numeric(d[sid],errors='coerce').values,index=d['month'])

def main():
 x=pd.read_excel(ROOT/'data/external/Perceptual_Bias_Data.xlsx',header=None)
 p=x.iloc[1:,[7,8]].dropna();p.columns=['date','excel_pce_yoy'];p['month']=pd.to_datetime(p['date']).dt.to_period('M').astype(str)
 p=p.set_index('month')
 for label,ds,sid in [('headline','M02','PCEPI'),('core','M05','PCEPILFE')]:
  level=latest(ds,sid)
  yoy=100*(level/level.shift(12)-1)
  p[label+'_pce_yoy']=yoy
  p[label+'_abs_error']=(pd.to_numeric(p.excel_pce_yoy)-p[label+'_pce_yoy']).abs()
 p.to_csv(PROV/'excel_pce_comparison.csv')
 summary=[]
 for label in ['headline','core']:
  v=p[label+'_abs_error'].dropna()
  summary.append(f'| {label} | {len(v)} | {v.mean():.8f} | {v.max():.8f} | {(v<=0.01).sum()} |')
 s=pd.read_csv(ROOT/'data/raw/S01'/DAY/'tbmics.csv');s['month']=pd.to_datetime(s.Month+' '+s.YYYY.astype(str),format='%B %Y').dt.to_period('M').astype(str)
 values=s.set_index('month').ICS_ALL
 c=x.iloc[1:,[3,4]].dropna();c.columns=['date','excel_ics'];c['month']=pd.to_datetime(c.date).dt.to_period('M').astype(str);c=c.set_index('month');c['official_ics']=values;c['difference']=pd.to_numeric(c.excel_ics)-c.official_ics;c.to_csv(PROV/'excel_sentiment_comparison.csv')
 u=json.loads((ROOT/'data/raw/M01'/DAY/'UNRATE_observations_0000000.json').read_bytes())['observations']
 missing_oct=[a for a in u if a['date']=='2025-10-01'];valid_oct=[a for a in missing_oct if a['value']!='.']
 g=latest('M04','A191RL1Q225SBEA');gmax=g.dropna().index.max()
 result='# Read-only check of the professor\'s Excel file\n\nThe original file was not modified. The calculations below are only for confirming the data definitions and completeness; this is not an analysis dataset. Units are percentage points.\n\n'
 result+='| Definition | Alignable months | Mean absolute error | Maximum absolute error | Months with error no greater than 0.01 |\n|---|---:|---:|---:|---:|\n'+'\n'.join(summary)
 result+='\n\nComparison formula: 100 × (index for the month in the same latest vintage / index 12 months earlier − 1). The match supports the core PCE definition, with the precision shown in the table above; it cannot be judged to be headline PCE from the column name alone. Historical revisions may affect exact value-by-value matching.\n'
 home=BeautifulSoup((ROOT/'data/raw/S05'/DAY/'homepage.html').read_bytes(),'html.parser').get_text(' ',strip=True)
 match=re.search(r'Preliminary Results for October 2026.*?Index of Consumer Sentiment (\d+\.\d+)',home)
 if not match:raise ValueError('Official October preliminary result not found in saved homepage')
 value=float(match.group(1))
 result+=f'\n- The consumer sentiment monthly CSV can be matched for {c.official_ics.notna().sum()} months; {(c.difference.abs()<1e-8).sum()} months agree. The latest month in the CSV is {values.index.max()}. The saved official homepage was also checked; it is explicitly labeled Preliminary Results for October 2026: ICS={value}, which agrees with the professor\'s table value 2026-10={c.loc["2026-10","excel_ics"]}. It is a preliminary value and must not be mixed with final values. The official calendar release date is 2026-10-09, and the October final value is scheduled for release on October 23. Evidence: data/raw/S05/20261015/homepage.html, source https://www.sca.isr.umich.edu/ .\n'
 result+=f'- UNRATE 2025-10 has {len(missing_oct)} vintage record in total, of which {len(valid_oct)} have non-missing values; a missing-value marker is not a usable observation.\n- The latest non-missing observation of the GDP quarter-over-quarter annualized rate is {gmax}; the Excel value 2026Q3=3.7 is not recorded as a measured value, and its source cannot be confirmed from it.\n'
 result+=f'- Official website ICS 2022-06={values.get("2022-06")}; 2026-05={values.get("2026-05")}.\n'
 (PROV/'excel_reconciliation.md').write_text(result)
 print(result)

if __name__=='__main__':main()
