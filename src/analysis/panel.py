"""Research panel: real-time monthly regressors for M1/M1c/M2/M3 and the long M1 windows.

Design: research/RESEARCH_DESIGN_v1.md (D-A, D-D, "Data and variables"). Output: data/processed/research_panel.csv
(1978-01..2026-10, one row per survey month, cutoff tau_t = last day of month t-1, rule D2).

Columns added on top of data/processed/econ_monthly_realtime.csv (2010-01 onward, copied unchanged):
- pce_cum36_rt: 100*(P_d/P_{d-36m}-1) for the latest PCEPI observation d in the vintage valid at tau
  (numerator and denominator from the same vintage). Uses the long PCEPI pull data/raw/M19.
- mortgage30_rt_dd, gas_price_rt_dd: D-D fill. PMMS and EIA weekly prices are not revised, so for tau
  before the first ALFRED vintage the value is the latest observation dated <= tau in the earliest vintage.
  *_dd_filled flags those months.
- rep_admin (Republican president: 2017-01..2020-12 and 2025-01 on, as pre-registered), pre_election6
  (the six months before each federal general election in provenance/political_elections.csv).
- Long-window M1 regressors 1978-01..2026-10: unrate_lw, pce_yoy_lw, gdp_qoq_saar_lw with provenance:
  * UNRATE: ALFRED vintage valid at tau (data/raw/M19).
  * PCEPI: ALFRED vintage valid at tau when tau >= first PCEPI vintage (2000-08); before that the earliest
    vintage, keeping observations up to month t-2 to mimic the usual one-month publication lag
    (quasi-real-time, pce_lw_source = earliest_vintage; pce_cum36_rt is left empty there).
  * GDP: ALFRED GDPC1 vintage valid at tau when tau >= first GDPC1 vintage; before that the Philadelphia Fed
    monthly vintage of month t-1 (routputMvQd.xlsx; real GNP before 1992). Month t-1 rather than t keeps
    the vintage before tau: in 2010-2026 the month-t vintage matches ALFRED at tau in 200 of 202 months,
    and the two exceptions (2013-11, 2019-02) are releases made during month t.
pce_yoy_lw is empty for 2004-01: the PCEPI vintage of 2003-12-23 (comprehensive revision) published
only recent observations until 2004-01-05, so no same-vintage 12-month change existed at tau.
For 2010-01 onward the long-window regressors must equal the econ_monthly_realtime values; the script
checks this and stops otherwise.
"""
import json,datetime as dt
import numpy as np
import pandas as pd
from lib import ROOT

RAW=ROOT/'data/raw';OUT=ROOT/'data/processed'
START='1978-01';END='2026-10'

class Series:
 """ALFRED observations (output_type=1) for one series from one dataset folder."""
 def __init__(self,sid,ds):
  files=sorted(RAW.glob(f'{ds}/*/{sid}_observations_*.json'))
  if not files:raise FileNotFoundError(f'{ds}/{sid}: run src/collect/alfred_extra.py')
  self.recs=[r for f in files for r in json.loads(f.read_text())['observations']]
  self.first_vintage=min(r['realtime_start'] for r in self.recs)
 def vintage(self,tau):
  return {r['date']:float(r['value']) for r in self.recs if r['realtime_start']<=tau<=r['realtime_end'] and r['value']!='.'}
 def latest(self,tau,max_obs=None):
  v=self.vintage(tau);obs=[d for d in v if max_obs is None or d<=max_obs]
  if not obs:return None,None,v
  d=max(obs);return v[d],d,v

def shift(date,months):
 y,m=int(date[:4]),int(date[5:7]);k=y*12+m-1+months;return f'{k//12:04}-{k%12+1:02}-01'
def pct(a,b):return None if a is None or b is None else 100*(a/b-1)
def tau_of(month):return (dt.date.fromisoformat(month+'-01')-dt.timedelta(days=1)).isoformat()

def philly_gdp(month):
 """Latest-quarter q/q SAAR from the Philadelphia Fed monthly vintage of month t-1."""
 y,m=int(month[:4]),int(month[5:7]);y,m=(y,m-1) if m>1 else (y-1,12)
 col=f'ROUTPUT{y%100:02}M{m}';s=PH[['DATE',col]].dropna()
 x,q1=s[col].iloc[-1],s[col].iloc[-2];return 100*((x/q1)**4-1),s.DATE.iloc[-1].replace(':',''),col

def fill_weekly(sid,ds,tau):
 """Value valid at tau; before the first vintage, latest obs <= tau in the earliest vintage (D-D)."""
 s=SER[(sid,ds)]
 if tau>=s.first_vintage:
  x,d,_=s.latest(tau);return x,d,False
 x,d,_=s.latest(s.first_vintage,max_obs=tau);return x,d,True

def main():
 global PH,SER
 PH=pd.read_excel(next(RAW.glob('M17/*/routputMvQd.xlsx')))
 SER={k:Series(*k) for k in [('UNRATE','M19'),('PCEPI','M19'),('GDPC1','M19'),('MORTGAGE30US','M10'),('GASREGW','M08')]}
 elections=pd.read_csv(ROOT/'provenance/political_elections.csv').date.tolist()
 rows=[];month=START+'-01'
 while month[:7]<=END:
  m=month[:7];tau=tau_of(m);r=dict(month=m)
  x,d,_=SER[('UNRATE','M19')].latest(tau);r.update(unrate_lw=x,unrate_lw_ref=d)
  P=SER[('PCEPI','M19')];ptau=tau if tau>=P.first_vintage else P.first_vintage;src='alfred' if tau>=P.first_vintage else 'earliest_vintage'
  x,d,v=P.latest(ptau,max_obs=None if src=='alfred' else shift(tau[:8]+'01',-1))
  r.update(pce_yoy_lw=pct(x,v.get(shift(d,-12))),pce_cum36_rt=pct(x,v.get(shift(d,-36))) if src=='alfred' else None,pce_lw_ref=d,pce_lw_source=src)
  G=SER[('GDPC1','M19')]
  if tau>=G.first_vintage:
   x,d,v=G.latest(tau);r.update(gdp_qoq_saar_lw=100*((x/v[shift(d,-3)])**4-1),gdp_lw_ref=f"{d[:4]}Q{(int(d[5:7])-1)//3+1}",gdp_lw_source='alfred')
  else:
   g,q,col=philly_gdp(m);r.update(gdp_qoq_saar_lw=g,gdp_lw_ref=q,gdp_lw_source=f'philly_{col}')
  for sid,ds,col in [('MORTGAGE30US','M10','mortgage30'),('GASREGW','M08','gas_price')]:
   x,d,f=fill_weekly(sid,ds,tau);r.update({f'{col}_rt_dd':x,f'{col}_dd_ref':d,f'{col}_dd_filled':f})
  r['rep_admin']=int(('2017-01'<=m<='2020-12') or m>='2025-01')
  r['pre_election6']=int(any(shift(e[:8]+'01',-6)[:7]<=m<=shift(e[:8]+'01',-1)[:7] for e in elections))
  rows.append(r);month=shift(month,1)
 L=pd.DataFrame(rows)
 econ=pd.read_csv(OUT/'econ_monthly_realtime.csv')
 # ICS/ICC/ICE before 2010 from the official monthly tables.
 mon={x:i for i,x in enumerate(['January','February','March','April','May','June','July','August','September','October','November','December'],1)}
 s=pd.read_csv(next(RAW.glob('S01/*/tbmics.csv')));c=pd.read_csv(next(RAW.glob('S01/*/tbmiccice.csv')))
 for d in (s,c):d['month']=[f'{int(y):04}-{mon[x]:02}' for y,x in zip(d.YYYY,d.Month)]
 hist=s[['month','ICS_ALL']].merge(c[['month','ICC','ICE']],on='month',how='outer').rename(columns={'ICS_ALL':'ics_hist','ICC':'icc_hist','ICE':'ice_hist'})
 panel=L.merge(hist,on='month',how='left').merge(econ,on='month',how='left')
 for k in ['ics','icc','ice']:panel[k]=panel[k].where(panel.month>='2010-01',panel[f'{k}_hist'])
 chk=panel[panel.month>='2010-01']
 for a,b in [('unrate_lw','unrate_rt'),('pce_yoy_lw','pce_yoy_rt'),('gdp_qoq_saar_lw','gdp_qoq_saar_rt')]:
  bad=chk[(chk[a]-chk[b]).abs()>1e-9]
  if len(bad):raise SystemExit(f'{a} != {b} in {len(bad)} months, e.g. {bad.month.iloc[0]}')
 bad=chk[chk.mortgage30_rt.notna()&((chk.mortgage30_rt-chk.mortgage30_rt_dd).abs()>1e-9)]
 if len(bad):raise SystemExit('mortgage fill differs where ALFRED value exists')
 hk=panel[(panel.month>='2010-01')&panel.ics_hist.notna()]
 if (hk.ics-hk.ics_hist).abs().max()>1e-9:raise SystemExit('ICS mismatch with tbmics.csv')
 panel.drop(columns=['ics_hist','icc_hist','ice_hist']).to_csv(OUT/'research_panel.csv',index=False)
 print('research_panel.csv',panel.shape)

if __name__=='__main__':main()
