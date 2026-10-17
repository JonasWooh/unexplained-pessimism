"""Stage 1: H3a (survey mode) and H3b (partisanship) tests on the M1 gap.

Design: research/RESEARCH_DESIGN_v1.md, "H3 tests". Requires results/stage1_m1/m1_gap_monthly.csv.
Outputs: results/stage1_h3/.
Pre-registered: (1) regress the 2023-01..2025-12 gap on a step dummy from 2024-07 and, separately, on the
web-interview share, for ICS, ICC and ICE; repeat dropping 2024-04..2024-06. (2) Party indices relative to
their own 2017-02..2019-12 mean, with the jumps at 2021-01 and 2025-01. (3) Partisan-composition bound
dICS = ds x (ICS_rep - ICS_rest) for ds = 2, 4, 6 percentage points.
Choices fixed here (not spelled out in the design, recorded in spec_registry): jump = mean of months
t..t+2 minus mean of t-3..t-1; party shares for ICS_rest come from least squares of ICS_all on the three
party indices over 2017-02..2026-08 with shares summing to one.
"""
import warnings
warnings.filterwarnings('ignore')
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from lib import *

OUT=ROOT/'results/stage1_h3';OUT.mkdir(parents=True,exist_ok=True)

def mode_tests(gap,econ):
 g=gap.merge(econ[['month','mode_web_share']],on='month')
 g['web_step']=(g.month>='2024-07').astype(float);rows=[]
 for dv in ['ics','icc','ice']:
  for drop in (False,True):
   for reg in ['web_step','mode_web_share']:
    d=between(g[g.dv==dv],'2023-01','2025-12')
    if drop:d=d[~d.month.between('2024-04','2024-06')]
    f=ols(d.gap,d[[reg]])
    rows.append(dict(dv=dv,regressor=reg,drop_2024_04_06=drop,window='2023-01..2025-12',n=int(f.nobs),coef=f.params[reg],se=f.bse[reg],p=f.pvalues[reg],
     ci95_lo=f.conf_int().loc[reg,0],ci95_hi=f.conf_int().loc[reg,1],status='pre-registered'))
  # Exploratory: same step regression ending 2025-03, before the April 2025 tariff announcements.
  d=between(g[g.dv==dv],'2023-01','2025-03');f=ols(d.gap,d[['web_step']])
  rows.append(dict(dv=dv,regressor='web_step',drop_2024_04_06=False,window='2023-01..2025-03',n=int(f.nobs),coef=f.params['web_step'],se=f.bse['web_step'],
   p=f.pvalues['web_step'],ci95_lo=f.conf_int().loc['web_step',0],ci95_hi=f.conf_int().loc['web_step',1],status='exploratory (not pre-registered)'))
 return pd.DataFrame(rows)

def party(surv,econ,gap):
 P=surv[['month','ics_dem','ics_ind','ics_rep']].merge(econ[['month','ics']],on='month')
 P=P[(P.month>='2017-02')&(P.month<='2026-08')].dropna().reset_index(drop=True)
 base=between(P,'2017-02','2019-12');out=P[['month']].copy()
 for p in ['dem','ind','rep']:out[f'dev_{p}']=P[f'ics_{p}']-base[f'ics_{p}'].mean()
 out['dev_all']=P.ics-base.ics.mean()
 g=gap[gap.dv=='ics'][['month','pred','gap']];out=out.merge(g,on='month')
 pbase=between(g,'2017-02','2019-12').pred.mean()
 for p in ['dem','ind','rep','all']:out[f'netgap_{p}']=out[f'dev_{p}']-(out.pred-pbase)  # supplementary: net of aggregate M1 predicted change
 jumps=[]
 for t in ['2021-01','2025-01']:
  i=out.index[out.month==t][0]
  for p in ['dem','ind','rep','all']:
   jumps.append(dict(event=t,party=p,pre_mean=out.loc[i-3:i-1,f'dev_{p}'].mean(),post_mean=out.loc[i:i+2,f'dev_{p}'].mean(),
    jump=out.loc[i:i+2,f'dev_{p}'].mean()-out.loc[i-3:i-1,f'dev_{p}'].mean()))
 per=[]
 for name,(a,b) in PERIODS.items():
  if a<'2017-02':continue
  d=between(out,a,b)
  if d.empty:continue
  per.append(dict(period=name,months=len(d),**{f'{k}_{p}':d[f'{k}_{p}'].mean() for k in ['dev','netgap'] for p in ['dem','ind','rep','all']},m1_gap=d.gap.mean()))
 # Implied party shares (constant over 2017-02..2026-08): min ||ICS - S @ s||, s >= 0, sum s = 1.
 S=P[['ics_dem','ics_ind','ics_rep']].values;y=P.ics.values
 res=minimize(lambda s:np.sum((y-S@s)**2),np.ones(3)/3,bounds=[(0,1)]*3,constraints=({'type':'eq','fun':lambda s:s.sum()-1},),method='SLSQP')
 sh=dict(zip(['dem','ind','rep'],res.x));fit_rmse=float(np.sqrt(np.mean((y-S@res.x)**2)))
 P['ics_rest']=(sh['dem']*P.ics_dem+sh['ind']*P.ics_ind)/(sh['dem']+sh['ind']);P['rep_minus_rest']=P.ics_rep-P.ics_rest
 bound=[]
 for name in ['2025-01..2025-12','2026-01..2026-10']:
  a,b=PERIODS[name];d=between(P,a,b);gp=between(out,a,b).gap.mean()
  for ds in (0.02,0.04,0.06):
   bound.append(dict(period=name,months_with_party=len(d),delta_share=ds,mean_rep_minus_rest=d.rep_minus_rest.mean(),
    dICS_if_rep_share_falls=-ds*d.rep_minus_rest.mean(),m1_mean_gap_same_months=gp,abs_share_of_gap=abs(ds*d.rep_minus_rest.mean()/gp)))
 return out,pd.DataFrame(jumps),pd.DataFrame(per),pd.DataFrame(bound),dict(shares=sh,share_fit_rmse=fit_rmse,months=len(P))

def main():
 econ=pd.read_csv(ROOT/'data/processed/econ_monthly_realtime.csv');surv=pd.read_csv(ROOT/'data/processed/survey_monthly.csv')
 gap=pd.read_csv(ROOT/'results/stage1_m1/m1_gap_monthly.csv')
 M=mode_tests(gap,econ);M.to_csv(OUT/'h3a_mode.csv',index=False)
 out,J,Pp,B,meta=party(surv,econ,gap)
 out.to_csv(OUT/'h3b_party_monthly.csv',index=False);J.to_csv(OUT/'h3b_party_jumps.csv',index=False);Pp.to_csv(OUT/'h3b_party_periods.csv',index=False)
 B.to_csv(OUT/'h3b_composition_bound.csv',index=False);pd.Series(meta).to_json(OUT/'h3b_party_shares.json',indent=1)
 pd.set_option('display.width',250)
 print(M.round(3).to_string());print(J.round(2).to_string());print(Pp.round(2).to_string());print(B.round(3).to_string());print(meta)

if __name__=='__main__':main()
