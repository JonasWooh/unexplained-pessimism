"""Stage 1: H1 (household price, borrowing-cost and income channels) and H3c (estimation windows).

Design: research/RESEARCH_DESIGN_v1.md, "H1 test" and "Estimation windows (corresponding to decision D-A)". Input:
data/processed/research_panel.csv (src/analysis/panel.py). Outputs: results/stage1_h1/, results/stage1_windows/.

H1: add pce_cum36_rt, mortgage30_rt_dd, rdpi_pc_yoy_rt, gas_price_rt_dd to M1 one at a time, then all four.
All H1 models, and the M1 reference they are compared with, use the common window 2010-06..2019-12 (real
disposable income per capita has no vintage before 2010-06) and the seasonal-dummy choice of main M1.
Criteria: change in the mean gap since 2021-01 and out-of-sample RMSE; falsification item 4 asks whether
the all-four model halves the mean gap since 2021 and puts it inside the 95% MBB interval.
Debt-service ratio and U-6 enter only as robustness rows.
H3c: M1 on 2010-01..2019-12 (main), 2000-09..2019-12 (fully real time) and 1978-01..2019-12 (quasi).
"""
import warnings
warnings.filterwarnings('ignore')
import numpy as np
import pandas as pd
from lib import *
from stage1_m1 import SEAS

H=['pce_cum36_rt','mortgage30_rt_dd','rdpi_pc_yoy_rt','gas_price_rt_dd']
X1=['unrate_rt','pce_yoy_rt','gdp_qoq_saar_rt']
XL=['unrate_lw','pce_yoy_lw','gdp_qoq_saar_lw']
COMMON=('2010-06','2019-12')
SINCE=('2021-01','2026-10')

def load():
 df=pd.read_csv(ROOT/'data/processed/research_panel.csv')
 for m in range(2,13):df[f'm{m:02}']=(df.month.str[5:7].astype(int)==m).astype(float)
 return df

def fit_gap(df,dv,X,window,seas,mbb=True):
 Xs=X+(SEAS if seas else []);est=between(df,*window).dropna(subset=[dv]+Xs);fit=ols(est[dv],est[Xs])
 ev=df[df.month>=window[0]].dropna(subset=Xs).copy();ev['pred']=predict(fit,ev[Xs]);ev['gap']=ev[dv]-ev.pred
 r=dict(dv=dv,window=f'{window[0]}..{window[1]}',n=int(fit.nobs),r2=fit.rsquared,seasonal=seas)
 for k in X:r.update({f'b_{k}':fit.params[k],f'se_{k}':fit.bse[k],f'p_{k}':fit.pvalues[k]})
 o=ev[ev.month>=OOS_START];r['oos_rmse']=float(np.sqrt(np.mean(o.gap**2)))
 for name,(a,b) in {**PERIODS,'since_2021':SINCE}.items():r[f'gap_{name}']=between(ev,a,b).gap.mean()
 if mbb:
  f=ev[ev.month>window[1]];d=mbb_draws(est[dv],est[Xs],f[Xs]);idx=np.where(f.month.between(*SINCE).values)[0]
  md=d[:,idx].mean(axis=1);r['since_2021_pi95_lo'],r['since_2021_pi95_hi']=np.percentile(md,[2.5,97.5])
 return r,ev

def main():
 df=load();seas=bool(pd.read_csv(ROOT/'results/stage1_m1/m1_fit.csv').query("dv=='ics'").seasonal_included.item())
 out=ROOT/'results/stage1_h1';out.mkdir(parents=True,exist_ok=True);rows=[];gaps=[]
 specs=[('M1_common',[])]+[(f'M1+{h}',[h]) for h in H]+[('M1+household_all',H)]
 for dv in ['ics','icc','ice']:
  for name,add in specs:
   r,ev=fit_gap(df,dv,X1+add,COMMON,seas);r['spec']=name;r['status']='pre-registered';rows.append(r)
   ev=ev[['month',dv,'pred','gap']].rename(columns={dv:'actual'});ev.insert(0,'spec',name);ev.insert(0,'dv',dv);gaps.append(ev)
 for name,add,win in [('M1+household_all+tdsp',H+['tdsp_rt'],COMMON),('M1+household_all+u6',H+['u6rate_rt'],('2011-04','2019-12')),
                      ('M1_u6window',[],('2011-04','2019-12'))]:
  r,_=fit_gap(df,'ics',X1+add,win,seas);r['spec']=name;r['status']='robustness';rows.append(r)
 R=pd.DataFrame(rows);base=R[R.spec=='M1_common'].set_index('dv')
 R['gap_since_2021_change_vs_M1']=R.gap_since_2021-R.dv.map(base.gap_since_2021)
 R['gap_since_2021_share_closed']=1-R.gap_since_2021/R.dv.map(base.gap_since_2021)
 R['falsification4_met']=(R.gap_since_2021_share_closed>=0.5)&(R.gap_since_2021>=R.since_2021_pi95_lo)&(R.gap_since_2021<=R.since_2021_pi95_hi)
 R.to_csv(out/'h1_models.csv',index=False);pd.concat(gaps).to_csv(out/'h1_gap_monthly.csv',index=False)
 # In-sample support of the household regressors versus the out-of-sample values (extrapolation check).
 sup=[]
 for c in X1+H:
  a=between(df,*COMMON)[c];b=between(df,*SINCE)[c]
  sup.append(dict(variable=c,est_min=a.min(),est_max=a.max(),oos_min=b.min(),oos_max=b.max(),oos_share_outside=float(((b<a.min())|(b>a.max())).mean())))
 pd.DataFrame(sup).to_csv(out/'h1_support.csv',index=False)
 # H3c windows.
 wout=ROOT/'results/stage1_windows';wout.mkdir(parents=True,exist_ok=True);wr=[];wg=[]
 for dv in ['ics','icc','ice']:
  for name,win,X in [('main_2010_2019',MAIN,XL),('realtime_2000_09_2019',('2000-09','2019-12'),XL),('quasi_1978_2019',('1978-01','2019-12'),XL)]:
   e=between(df,*win).dropna(subset=[dv]+X);s_stat,s_p=wald(ols(e[dv],e[X+SEAS]),SEAS)
   r,ev=fit_gap(df,dv,X,win,s_p<0.05);r.update(spec=name,seasonal_p=s_p);wr.append(r)
   ev=ev[['month',dv,'pred','gap']].rename(columns={dv:'actual'});ev.insert(0,'spec',name);ev.insert(0,'dv',dv);wg.append(ev)
 # Exploratory (not pre-registered): H1a on the 2000-09..2019 window, the only fully real-time window with
 # pce_cum36_rt and enough price variation; the other household series have no vintages before 2008.
 for dv in ['ics','icc','ice']:
  for name,X in [('exploratory_2000_M1',XL),('exploratory_2000_M1+pce_cum36',XL+['pce_cum36_rt'])]:
   r,_=fit_gap(df,dv,X,('2000-09','2019-12'),False);r.update(spec=name,status='exploratory (not pre-registered)');rows.append(r)
 pd.DataFrame(rows).to_csv(out/'h1_models_with_exploratory.csv',index=False)
 W=pd.DataFrame(wr);W.to_csv(wout/'m1_windows.csv',index=False);pd.concat(wg).to_csv(wout/'m1_windows_gap_monthly.csv',index=False)
 sup=[]
 for name,win in [('main_2010_2019',MAIN),('realtime_2000_09_2019',('2000-09','2019-12')),('quasi_1978_2019',('1978-01','2019-12'))]:
  a=between(df,*win)
  sup.append(dict(spec=name,**{f'{c}_{f}':getattr(a[c],f)() for c in XL for f in ('min','max')}))
 pd.DataFrame(sup).to_csv(wout/'m1_windows_support.csv',index=False)
 pd.set_option('display.width',250)
 cols=['dv','spec','n','r2']+[f'b_{h}' for h in H]+[f'p_{h}' for h in H]+['oos_rmse','gap_since_2021','since_2021_pi95_lo','since_2021_pi95_hi','gap_since_2021_share_closed','falsification4_met']
 print(R[[c for c in cols if c in R]].round(3).to_string());print(pd.DataFrame(sup).round(2).to_string())
 print(W[['dv','spec','n','r2','seasonal','b_unrate_lw','b_pce_yoy_lw','b_gdp_qoq_saar_lw','oos_rmse']+[c for c in W if c.startswith('gap_')]].round(2).to_string())

if __name__=='__main__':main()
