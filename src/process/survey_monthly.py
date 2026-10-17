"""Michigan survey monthly panel: demographic groups (S02), party (table 5b historical),
news heard (S03) and reasons/expectations (S04). One row per survey month; values as published."""
import csv,io
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];RAW=ROOT/'data/raw';OUT=ROOT/'data/processed'
MONTHS=['January','February','March','April','May','June','July','August','September','October','November','December']

def subset_csv(ds):
 # The subset service returned CSV text; it was saved under the response name monthly_subset_response.html.
 if ds=='S02':return pd.read_csv(next(RAW.glob('S02/*/monthly_subset_response.html')),dtype={'yyyymm':str})
 return pd.read_csv(next(RAW.glob(f'{ds}/*/monthly_all_response_codes.csv')),dtype={'yyyymm':str})

def party():
 x=pd.read_excel(next(RAW.glob('S02/*/table_5b_historical.xls')),header=None)
 rows=[]
 for _,r in x.iloc[7:].iterrows():
  if r[0] in MONTHS and pd.notna(r[1]):
   vals=[pd.to_numeric(v,errors='coerce') for v in r[2:11]]
   rows.append(dict(month=f'{int(r[1]):04}-{MONTHS.index(r[0])+1:02}',**dict(zip([f'{i}_{p}' for i in ['ics','icc','ice'] for p in ['dem','ind','rep']],vals))))
 return pd.DataFrame(rows)

def main():
 out=None
 for ds in ['S02','S03','S04']:
  d=subset_csv(ds);d.insert(0,'month',d['yyyymm'].str[:4]+'-'+d['yyyymm'].str[4:6]);d=d.drop(columns='yyyymm')
  out=d if out is None else out.merge(d,on='month',how='outer')
 out=out.merge(party(),on='month',how='left')
 px=pd.read_csv(next(RAW.glob('S04/*/tbmpx1px5.csv')))
 px['month']=px.apply(lambda r:f"{int(r['YYYY']):04}-{MONTHS.index(r['Month'])+1:02}",axis=1)
 out=out.merge(px[['month','PX_MD','PX5_MD']].rename(columns={'PX_MD':'px1_median_tb','PX5_MD':'px5_median_tb'}),on='month',how='outer').sort_values('month')
 OUT.mkdir(parents=True,exist_ok=True);out.to_csv(OUT/'survey_monthly.csv',index=False);print(out.shape,out.month.min(),out.month.max())

if __name__=='__main__':main()
