"""Stage 1: M1 baseline, sentiment gap, prediction intervals, explained share and decomposition (RQ3).

Design: research/RESEARCH_DESIGN_v1.md, section "模型 1". Inputs: data/processed/econ_monthly_realtime.csv
(cutoff D2) and econ_monthly_realtime_prelim_cutoff.csv (robustness). Outputs: results/stage1_m1/.
Only the pre-registered 2010-01..2019-12 window is run here; the 2000-09 and 1978 windows are in
stage1_windows.py because they need the long ALFRED pulls (data/raw/M19).
"""
import json,warnings
warnings.filterwarnings('ignore')
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller,kpss,coint
from lib import *

OUT=ROOT/'results/stage1_m1';OUT.mkdir(parents=True,exist_ok=True)
X1=['unrate_rt','pce_yoy_rt','gdp_qoq_saar_rt']
DVS=['ics','icc','ice']
PANDEMIC=('2020-03','2020-12')

def load(name='econ_monthly_realtime.csv'):
 df=pd.read_csv(ROOT/'data/processed'/name)
 df['moy']=df.month.str[5:7].astype(int)
 for m in range(2,13):df[f'm{m:02}']=(df.moy==m).astype(float)
 return df
SEAS=[f'm{m:02}' for m in range(2,13)]

def seasonal_choice(df,dv,X,lags=12):
 est=between(df,*MAIN);f=ols(est[dv],est[X+SEAS],lags);stat,p=wald(f,SEAS);return stat,p

def run(df,dv,X,lags=12,label='main',est_window=MAIN,seasonal=None,mbb=True):
 """Fit on est_window, predict every month, gap = actual - predicted. Returns (fit, monthly frame, meta)."""
 s_stat,s_p=seasonal_choice(df,dv,X,lags)
 use_seas=(s_p<0.05) if seasonal is None else seasonal
 Xs=X+(SEAS if use_seas else [])
 est=between(df,*est_window);fit=ols(est[dv],est[Xs],lags)
 m=df[['month',dv]+X].copy();m['pred']=predict(fit,df[Xs]);m['gap']=m[dv]-m['pred']
 m['in_sample']=(m.month>=est_window[0])&(m.month<=est_window[1])
 pis=analytic_pi(fit,df[Xs]);m=pd.concat([m,pis],axis=1)
 meta=dict(model='M1',dv=dv,label=label,window=f'{est_window[0]}..{est_window[1]}',n=int(fit.nobs),hac_lags=lags,
  seasonal_wald=s_stat,seasonal_p=s_p,seasonal_included=bool(use_seas),r2=fit.rsquared,adj_r2=fit.rsquared_adj,
  resid_sd=float(np.sqrt(fit.mse_resid)))
 for k in ['const']+X:meta.update({f'b_{k}':fit.params[k],f'se_{k}':fit.bse[k],f'p_{k}':fit.pvalues[k]})
 oos=m[m.month>=OOS_START];ybar=est[dv].mean()
 for tag,o in [('oos',oos),('oos_ex_pandemic',oos[~oos.month.between(*PANDEMIC)])]:
  meta[f'{tag}_rmse']=float(np.sqrt(np.mean(o.gap**2)));meta[f'{tag}_mean_gap']=float(o.gap.mean())
  meta[f'{tag}_r2']=float(1-np.sum(o.gap**2)/np.sum((o[dv]-ybar)**2))
 draws=None
 if mbb:
  f_idx=~m.in_sample.values
  draws=mbb_draws(est[dv],est[Xs],df.loc[f_idx,Xs])
  for lv in (80,95):
   lo,hi=np.percentile(draws,[50-lv/2,50+lv/2],axis=0)
   m.loc[f_idx,f'pi{lv}_lo_mbb']=m.loc[f_idx,'pred'].values+lo;m.loc[f_idx,f'pi{lv}_hi_mbb']=m.loc[f_idx,'pred'].values+hi
 return fit,m,meta,draws

def periods(df,fit,m,draws,dv,X):
 """Mean gap per period with MBB interval for the period mean, explained share S and decomposition."""
 base=between(m,*BASE_YEAR);xbar19=base[X].mean();ybar19=base[dv].mean();pred19=base.pred.mean()
 f_months=m.loc[~m.in_sample,'month'].tolist();rows=[]
 for name,(a,b) in PERIODS.items():
  p=between(m,a,b);idx=[f_months.index(x) for x in p.month]
  r=dict(dv=dv,period=name,n_months=len(p),actual_mean=p[dv].mean(),pred_mean=p.pred.mean(),mean_gap=p.gap.mean(),
   actual_change_vs_2019=p[dv].mean()-ybar19,pred_change_vs_2019=p.pred.mean()-pred19,resid_2019_mean=ybar19-pred19)
  r['explained_share']=1-r['mean_gap']/r['actual_change_vs_2019']
  if draws is not None:
   md=draws[:,idx].mean(axis=1)  # draws of (period mean actual - period mean predicted) under the model
   for lv in (80,95):
    lo,hi=np.percentile(md,[50-lv/2,50+lv/2]);r[f'gap_mean_pi{lv}_lo']=lo;r[f'gap_mean_pi{lv}_hi']=hi
   r['gap_mean_p_two_sided']=float(2*min(np.mean(md>=r['mean_gap']),np.mean(md<=r['mean_gap'])))
  for k in X:
   r[f'x_{k}_mean']=p[k].mean();r[f'x_{k}_2019']=xbar19[k];r[f'contrib_{k}']=fit.params[k]*(p[k].mean()-xbar19[k])
  rows.append(r)
 return rows

def first_difference(df,dv,X,lags=12,const=False):
 """Robustness: dDV on dX over the main window; level path = 2019-12 actual + cumulated predicted changes.
 Without a constant by default: a constant in differences is a linear trend in levels, which M1 excludes."""
 d=df[['month',dv]+X].copy();d[[dv]+X]=d[[dv]+X].diff()
 est=between(d,*MAIN).dropna()
 if const:fit=ols(est[dv],est[X],lags);f=d[d.month>=OOS_START].copy();f['dpred']=predict(fit,f[X])
 else:
  fit=sm.OLS(est[dv],est[X]).fit(cov_type='HAC',cov_kwds={'maxlags':lags,'use_correction':True})
  f=d[d.month>=OOS_START].copy();f['dpred']=np.asarray(f[X]@fit.params)
 start=df.loc[df.month=='2019-12',dv].item();lvl=start+f.dpred.cumsum()
 out=df.loc[df.month>=OOS_START,['month',dv]].copy();out['pred']=lvl.values;out['gap']=out[dv]-out['pred']
 return fit,out

def unit_roots(df,cols):
 rows=[]
 for c in cols:
  x=between(df,*MAIN)[c].dropna().values
  a=adfuller(x,autolag='AIC');k=kpss(x,regression='c',nlags='auto')
  rows.append(dict(series=c,adf_stat=a[0],adf_p=a[1],kpss_stat=k[0],kpss_p_bounded=k[1]))
 return rows

def main():
 df=load();pre=load('econ_monthly_realtime_prelim_cutoff.csv')
 metas=[];monthly=[];prows=[];rob=[];draws_store={}
 for dv in DVS:
  fit,m,meta,draws=run(df,dv,X1);metas.append(meta);m.insert(0,'dv',dv);monthly.append(m);draws_store[dv]=draws
  prows+=periods(df,fit,m,draws,dv,X1)
 pd.DataFrame(metas).to_csv(OUT/'m1_fit.csv',index=False)
 pd.concat(monthly).to_csv(OUT/'m1_gap_monthly.csv',index=False)
 pd.DataFrame(prows).to_csv(OUT/'m1_periods.csv',index=False)
 # Robustness on the M1 gap (ICS); every variant is logged with the period mean gaps.
 def summarize(label,m,meta=None,dv='ics'):
  r=dict(variant=label,dv=dv)
  for name,(a,b) in PERIODS.items():r[f'gap_{name}']=between(m,a,b).gap.mean()
  o=m[m.month>=OOS_START];r['oos_rmse']=float(np.sqrt(np.mean(o.gap**2)))
  if meta:r.update(r2=meta['r2'],seasonal_included=meta['seasonal_included'],b_unrate=meta['b_unrate_rt'],b_pce=meta['b_pce_yoy_rt'],b_gdp=meta.get('b_gdp_qoq_saar_rt',meta.get('b_gdp_yoy_rt')))
  return r
 for dv in DVS:
  fit,m,meta,_=run(df,dv,X1,mbb=False);rob.append(summarize('main',m,meta,dv))
 for lags in (6,18):
  fit,m,meta,_=run(df,'ics',X1,lags=lags,mbb=False);rob.append(summarize(f'hac_lags_{lags}',m,meta))
 s_main=next(x for x in metas if x['dv']=='ics')['seasonal_included']
 fit,m,meta,_=run(df,'ics',X1,seasonal=not s_main,mbb=False);rob.append(summarize('seasonal_excluded' if s_main else 'seasonal_forced',m,meta))
 Xy=['unrate_rt','pce_yoy_rt','gdp_yoy_rt'];fit,m,meta,_=run(df,'ics',Xy,mbb=False);meta['b_gdp_yoy_rt']=fit.params['gdp_yoy_rt'];rob.append(summarize('gdp_yoy',m,meta))
 fit,m,meta,_=run(pre,'ics',X1,mbb=False);rob.append(summarize('cutoff_mich_prelim',m,meta))
 fit,m=first_difference(df,'ics',X1);rob.append(summarize('first_difference_no_const',m))
 fit,m=first_difference(df,'ics',X1,const=True);rob.append(summarize('first_difference_with_const',m))
 # Expanding-window recursive M1 (reference only; absorbs the gap over time). Seasonal choice fixed to main.
 use_seas=next(x for x in metas if x['dv']=='ics')['seasonal_included'];Xs=X1+(SEAS if use_seas else [])
 rec=[]
 for t in df.loc[df.month>=OOS_START,'month']:
  est=df[(df.month>=MAIN[0])&(df.month<t)];f=ols(est['ics'],est[Xs])
  row=df[df.month==t];rec.append(dict(month=t,ics=row.ics.item(),pred=predict(f,row[Xs]).item()))
 rec=pd.DataFrame(rec);rec['gap']=rec.ics-rec.pred;rec.to_csv(OUT/'m1_recursive_expanding.csv',index=False)
 rob.append(summarize('expanding_recursive',rec))
 pd.DataFrame(rob).to_csv(OUT/'m1_robustness.csv',index=False)
 ur=unit_roots(df,['ics','icc','ice']+X1)
 for dv in DVS:  # Engle-Granger: are M1 residuals stationary (cointegration of DV with the I(1)-looking regressors)?
  e=between(df,*MAIN);s,p,_=coint(e[dv],e[X1],trend='c',autolag='aic');ur.append(dict(series=f'engle_granger_{dv}_on_M1',adf_stat=s,adf_p=p))
 pd.DataFrame(ur).to_csv(OUT/'unit_roots_main_window.csv',index=False)
 # Figure: ICS actual vs M1 prediction with MBB 80/95% bands.
 m=monthly[0];fig,ax=plt.subplots(2,1,figsize=(10,7),sharex=True)
 x=pd.to_datetime(m.month)
 ax[0].plot(x,m.ics,'k',lw=1.2,label='ICS (actual)');ax[0].plot(x,m.pred,'C0',lw=1.2,label='M1 prediction')
 f=~m.in_sample
 ax[0].fill_between(x[f],m.loc[f,'pi95_lo_mbb'],m.loc[f,'pi95_hi_mbb'],color='C0',alpha=.15,label='95% PI (MBB)')
 ax[0].fill_between(x[f],m.loc[f,'pi80_lo_mbb'],m.loc[f,'pi80_hi_mbb'],color='C0',alpha=.25,label='80% PI (MBB)')
 ax[0].axvline(pd.Timestamp('2020-01-01'),color='grey',ls=':');ax[0].legend(fontsize=8);ax[0].set_ylabel('Index')
 ax[1].bar(x,m.gap,width=25,color=np.where(m.gap<0,'C3','C2'));ax[1].axhline(0,color='k',lw=.8)
 ax[1].axvline(pd.Timestamp('2020-01-01'),color='grey',ls=':');ax[1].set_ylabel('Gap = actual - M1')
 fig.suptitle('Michigan ICS vs real-time fundamentals (M1, fit 2010-2019)');fig.tight_layout();fig.savefig(OUT/'fig_m1_gap_ics.png',dpi=150)
 print(pd.DataFrame(metas)[['dv','n','r2','seasonal_p','seasonal_included','b_unrate_rt','p_unrate_rt','b_pce_yoy_rt','p_pce_yoy_rt','b_gdp_qoq_saar_rt','p_gdp_qoq_saar_rt','oos_rmse','oos_r2','oos_mean_gap']].round(3).to_string())
 P=pd.DataFrame(prows);print(P[['dv','period','actual_change_vs_2019','mean_gap','gap_mean_pi95_lo','gap_mean_pi95_hi','explained_share']+[c for c in P if c.startswith('contrib_')]].round(2).to_string())
 print(pd.DataFrame(rob).round(2).to_string())

if __name__=='__main__':main()
