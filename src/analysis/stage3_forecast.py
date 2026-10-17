"""Stage 3 (RQ5, H2b): recursive out-of-sample forecast comparison of M1, M1c, M2 and M3 (research design v1).

Timing (rule D2): the forecast for survey month t is made on the 1st of month t. It uses real-time economic values
at that cutoff (panel *_rt columns of month t), the media index of month t-1 and, in the AR versions, ICS_{t-1}.
Models (all with the stage 1 seasonal choice, i.e. month dummies; constant always):
 M1  = U, pi, g                                   M1c = M1 + H + P
 M2  = M1 + Tone_{t-1}                            M3  = M1c + Tone_{t-1}
 H = pce_cum36_rt, mortgage30_rt_dd, rdpi_pc_yoy_rt, gas_price_rt_dd;  P = rep_admin, pre_election6.
Every model is also run with ICS_{t-1} (AR version). Pre-declared before results (DECISIONS.md stage 3 entry): the AR
version is the primary one for falsification item 2, the no-AR version is reported alongside.
Sample: all models share the window from 2010-06 (first month with real disposable income), so nested comparisons use
identical training rows. Expanding window; first window 2010-06..2016-12; evaluation 2017-01..2026-10 (1-step) and a
3-month direct forecast (target t+2 from the same information set).
Nested tests: Clark-West one-sided with HAC (Bartlett, floor(T^(1/3)) lags; for h=3 at least 2). RMSE ratios with a
12-month moving-block bootstrap of paired forecast errors (2,000 draws). Periods 2017-2019, 2020-2022, 2023-2024,
2025-2026, and the whole period with and without 2020-03..2020-12.
Secondary media variables (each alone on top of M1, lag 1-3 chosen by BIC in every training window; plus the first
principal component of the six, loadings re-estimated in every window); Benjamini-Hochberg q = 0.10 over the seven.
Measurement alternatives for Tone (design robustness table) and the excess-tone version are in stage3_robustness.py.
Outputs: results/stage3_forecast/.
"""
import json
import numpy as np
import pandas as pd
from lib import ROOT,SEED,ols,clark_west,bh,mbb_index

OUT=ROOT/'results/stage3_forecast';OUT.mkdir(parents=True,exist_ok=True)
B=2000
SEAS=[f'm{m:02}' for m in range(2,13)]
X1=['unrate_rt','pce_yoy_rt','gdp_qoq_saar_rt']
H=['pce_cum36_rt','mortgage30_rt_dd','rdpi_pc_yoy_rt','gas_price_rt_dd'];P=['rep_admin','pre_election6']
START='2010-06';FIRST_EVAL='2017-01';LAST='2026-10'
EVAL_PERIODS={'2017-01..2026-10':('2017-01','2026-10'),'2017-01..2026-10 excl. 2020-03..12':('2017-01','2026-10'),
 '2017-2019':('2017-01','2019-12'),'2020-2022':('2020-01','2022-12'),'2023-2024':('2023-01','2024-12'),'2025-2026':('2025-01','2026-10')}
SECONDARY=['net_fact','price_level_share_of_priced','household_share','topic_prices_rising','topic_layoffs_unemployment_up','blame_admin_share']

def models(tone='tone_l1'):
 return {'M1':X1,'M1c':X1+H+P,'M2':X1+[tone],'M3':X1+H+P+[tone]}

def panel(dv='ics',media=None,panel_df=None):
 """One row per survey month t with y_t, regressors at cutoff t, media of t-1, y_{t-1} and month dummies."""
 Pn=pd.read_csv(ROOT/'data/processed/research_panel.csv') if panel_df is None else panel_df.copy()
 Pn=Pn[Pn.month>='2009-12'].sort_values('month').reset_index(drop=True)
 M=pd.read_csv(ROOT/'features/media_monthly.csv') if media is None else media
 M=M[M.group=='national'].copy() if 'group' in M else M.copy()
 M['month']=(pd.PeriodIndex(M.month,freq='M')+1).astype(str)   # media of t-1 is used for survey month t
 cols=[c for c in M.columns if c not in ('group','month')]
 M=M.rename(columns={c:c+'_l1' for c in cols})
 D=Pn.merge(M,on='month',how='left')
 D['y']=D[dv];D['y_l1']=D[dv].shift(1)
 for m in range(2,13):D[f'm{m:02}']=(D.month.str[5:7].astype(int)==m).astype(float)
 D['tone_l1']=D['net_tone_l1'] if 'net_tone_l1' in D else np.nan
 return D[(D.month>=START)&(D.month<=LAST)].reset_index(drop=True)

def lstsq_fit(Y,X):
 Xc=np.column_stack([np.ones(len(X)),X]);b=np.linalg.lstsq(Xc,Y,rcond=None)[0];return b

def recursive(D,cols,h=1,ar=False,seasonal=True,first_eval=FIRST_EVAL,lag_select=None):
 """Expanding-window direct h-step forecasts. Row t holds the information set at cutoff t; the target is y_{t+h-1}.
 Training uses rows whose target month is at most origin-1. lag_select: dict var -> candidate columns (BIC in window)."""
 X=list(cols)+(['y_l1'] if ar else [])+(SEAS if seasonal else [])
 D=D.copy();D['target']=D.y.shift(-(h-1));D['target_month']=D.month.shift(-(h-1))
 idx=D.index[(D.month>=first_eval)&D.target.notna()]
 out=[];chosen=[]
 for o in idx:
  tr=D.loc[:o-h]  # rows t <= o-h  ->  target month t+h-1 <= o-1
  Xs=list(X)
  if lag_select:
   for var,cands in lag_select.items():
    best=None
    for c in cands:
     Z=tr[[c]+[x for x in Xs if x!=var]+['target']].dropna()
     b=lstsq_fit(Z.target.values,Z.drop(columns='target').values);e=Z.target.values-np.column_stack([np.ones(len(Z)),Z.drop(columns='target').values])@b
     n=len(Z);k=Z.shape[1];bic=n*np.log(np.mean(e**2))+k*np.log(n)
     if best is None or bic<best[0]:best=(bic,c)
    Xs=[best[1] if x==var else x for x in Xs];chosen.append(best[1])
  Z=tr[Xs+['target']].dropna()
  b=lstsq_fit(Z.target.values,Z[Xs].values)
  xo=D.loc[o,Xs].values.astype(float)
  out.append(dict(origin=D.loc[o,'month'],target_month=D.loc[o,'target_month'],y=D.loc[o,'target'],f=float(b[0]+xo@b[1:]),n_train=len(Z)))
 R=pd.DataFrame(out)
 if lag_select:R['lag_chosen']=chosen[:len(R)] if len(chosen)==len(R) else [chosen[i*len(lag_select)] for i in range(len(R))]
 return R

def period_mask(F,name):
 a,b=EVAL_PERIODS[name];m=(F.target_month>=a)&(F.target_month<=b)
 if 'excl.' in name:m&=~F.target_month.between('2020-03','2020-12')
 return m.to_numpy()

def compare(Fs,Fb,h,name_s,name_b,tag,rng):
 rows=[]
 e_s=(Fs.y-Fs.f).to_numpy();e_b=(Fb.y-Fb.f).to_numpy()
 for per in EVAL_PERIODS:
  m=period_mask(Fs,per)
  if m.sum()<6:continue
  L=max(int(np.floor(m.sum()**(1/3))),h-1)
  st,p,ms,mb=clark_west(Fs.y[m],Fs.f[m],Fb.f[m],lags=L)
  es,eb=e_s[m],e_b[m];n=len(es);bl=min(12,max(2,n//4))
  ratios=[]
  for _ in range(B):
   i=mbb_index(n,n,bl,rng);ratios.append(np.sqrt(np.mean(eb[i]**2)/np.mean(es[i]**2)))
  rows.append(dict(comparison=f'{name_s} vs {name_b}',version=tag,h=h,period=per,n=int(n),rmse_small=np.sqrt(ms),rmse_big=np.sqrt(mb),
   mae_small=np.mean(np.abs(es)),mae_big=np.mean(np.abs(eb)),rmse_ratio_big_over_small=np.sqrt(mb/ms),
   ratio_lo=np.percentile(ratios,2.5),ratio_hi=np.percentile(ratios,97.5),cw_stat=st,cw_p=p,cw_lags=L))
 return rows

def secondary_lags(D,var):
 M=pd.read_csv(ROOT/'features/media_monthly.csv');M=M[M.group=='national'].sort_values('month').reset_index(drop=True)
 lagged={}
 for L in (1,2,3):
  s=M[['month',var]].copy();s['month']=(pd.PeriodIndex(s.month,freq='M')+L).astype(str);lagged[f'{var}_lag{L}']=s.set_index('month')[var]
 for k,s in lagged.items():D[k]=D.month.map(s)
 return D,[f'{var}_lag{L}' for L in (1,2,3)]

def pc1_forecasts(D,h,ar,seasonal=True):
 """M1 + first principal component of the six secondary variables (t-1), loadings estimated in each window."""
 V=[v+'_l1' for v in SECONDARY];X=X1+(['y_l1'] if ar else [])+(SEAS if seasonal else [])
 D=D.copy();D['target']=D.y.shift(-(h-1));D['target_month']=D.month.shift(-(h-1))
 out=[]
 for o in D.index[(D.month>=FIRST_EVAL)&D.target.notna()]:
  tr=D.loc[:o-h].dropna(subset=V+X+['target'])
  mu,sd=tr[V].mean(),tr[V].std();Z=((tr[V]-mu)/sd).values;w=np.linalg.svd(Z,full_matrices=False)[2][0]
  w=w*np.sign(w[0]) if w[0]!=0 else w
  pc=Z@w;xo_pc=((D.loc[o,V]-mu)/sd).values@w
  b=lstsq_fit(tr.target.values,np.column_stack([tr[X].values,pc]))
  out.append(dict(origin=D.loc[o,'month'],target_month=D.loc[o,'target_month'],y=D.loc[o,'target'],f=float(b[0]+np.r_[D.loc[o,X].values.astype(float),xo_pc]@b[1:])))
 return pd.DataFrame(out)

def main():
 rng=np.random.default_rng(SEED)
 D=panel();res=[];fc={}
 for h in (1,3):
  for ar in (True,False):
   tag='AR' if ar else 'no AR'
   for name,cols in models().items():
    F=recursive(D,cols,h=h,ar=ar);fc[(name,h,tag)]=F
    F.assign(model=name,h=h,version=tag).to_csv(OUT/f'forecasts_{name}_h{h}_{tag.replace(" ","")}.csv',index=False)
   for s,b in [('M1','M2'),('M1','M1c'),('M1c','M3'),('M1','M3')]:
    res+=compare(fc[(s,h,tag)],fc[(b,h,tag)],h,s,b,tag,rng)
 R=pd.DataFrame(res);R.to_csv(OUT/'comparisons.csv',index=False)
 # secondary media hypotheses (h=1), each alone on M1, lag 1-3 by BIC within window; PC1 with lag 1
 sec=[]
 for ar in (True,False):
  tag='AR' if ar else 'no AR';base=fc[('M1',1,tag)]
  for v in SECONDARY:
   Dv,c=secondary_lags(D.copy(),v)
   F=recursive(Dv,X1+[v],ar=ar,lag_select={v:c});F.to_csv(OUT/f'secondary_{v}_{tag.replace(" ","")}.csv',index=False)
   r=compare(base,F,1,'M1','M1+'+v,tag,rng)[0];r['lag_choice_counts']=json.dumps(F.lag_chosen.value_counts().to_dict());sec.append(r)
  F=pc1_forecasts(D,1,ar);F.to_csv(OUT/f'secondary_pc1_{tag.replace(" ","")}.csv',index=False)
  sec.append(compare(base,F,1,'M1','M1+PC1(six)',tag,rng)[0])
 S=pd.DataFrame(sec)
 for tag in ('AR','no AR'):
  m=S.version==tag;rej,padj=bh(S.loc[m,'cw_p'].values,q=0.10);S.loc[m,'bh_reject_q10']=rej;S.loc[m,'bh_p_adj']=padj
 S.to_csv(OUT/'secondary.csv',index=False)
 # in-sample coefficients of the media term (HAC 12), full window and 2010-06..2019-12
 coef=[]
 for win,(a,b) in {'2010-06..2026-10':(START,LAST),'2010-06..2019-12':(START,'2019-12')}.items():
  for ar in (True,False):
   for name in ('M2','M3'):
    cols=models()[name]+(['y_l1'] if ar else [])+SEAS;Z=D[(D.month>=a)&(D.month<=b)][cols+['y']].dropna()
    for lags in (12,6,18):
     f=ols(Z.y,Z[cols],lags);coef.append(dict(model=name,version='AR' if ar else 'no AR',window=win,hac_lags=lags,n=int(f.nobs),gamma=f.params['tone_l1'],se=f.bse['tone_l1'],p=f.pvalues['tone_l1'],r2=f.rsquared))
 C=pd.DataFrame(coef);C.to_csv(OUT/'media_coefficients.csv',index=False)
 pd.set_option('display.width',250);pd.set_option('display.max_columns',30)
 print(R[R.period.isin(['2017-01..2026-10','2017-01..2026-10 excl. 2020-03..12'])].round(3).to_string())
 print(R[(R.h==1)&R.comparison.isin(['M1 vs M2','M1c vs M3'])].round(3).to_string())
 print(S.round(3).to_string());print(C[C.hac_lags==12].round(3).to_string())

if __name__=='__main__':main()
