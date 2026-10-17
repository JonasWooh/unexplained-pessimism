"""Shared estimation helpers for the research stage (research/RESEARCH_DESIGN_v1.md).

OLS with Newey-West (Bartlett) HAC covariance, analytic and moving-block-bootstrap prediction
intervals, Clark-West nested-forecast test and Benjamini-Hochberg. All randomness uses SEED.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

ROOT=Path(__file__).resolve().parents[2]
SEED=20261015
MAIN=('2010-01','2019-12')
OOS_START='2020-01'
BASE_YEAR=('2019-01','2019-12')
PERIODS={'2020-01..2021-06':('2020-01','2021-06'),'2021-07..2022-12':('2021-07','2022-12'),'2023-01..2024-12':('2023-01','2024-12'),
 '2025-01..2025-12':('2025-01','2025-12'),'2026-01..2026-10':('2026-01','2026-10')}
GAP_PERIODS=['2021-07..2022-12','2023-01..2024-12','2025-01..2025-12','2026-01..2026-10']  # design: explained-share periods

def between(df,a,b):return df[(df.month>=a)&(df.month<=b)]

def ols(y,X,lags=12):
 """OLS with HAC(Bartlett, `lags`) covariance; X without constant (added)."""
 Xc=sm.add_constant(X,has_constant='add')
 return sm.OLS(y,Xc).fit(cov_type='HAC',cov_kwds={'maxlags':lags,'use_correction':True})

def predict(fit,X):return np.asarray(sm.add_constant(X,has_constant='add')@fit.params)

def analytic_pi(fit,X,levels=(0.80,0.95)):
 """Pointwise interval for y_h: parameter variance (HAC) plus residual variance; normal quantiles."""
 Xc=np.asarray(sm.add_constant(X,has_constant='add'));V=np.asarray(fit.cov_params())
 se=np.sqrt(np.einsum('ij,jk,ik->i',Xc,V,Xc)+fit.mse_resid)
 yhat=Xc@np.asarray(fit.params);out={}
 for lv in levels:
  z=stats.norm.ppf(0.5+lv/2);out[f'pi{int(lv*100)}_lo_analytic']=yhat-z*se;out[f'pi{int(lv*100)}_hi_analytic']=yhat+z*se
 return pd.DataFrame(out,index=X.index)

def mbb_index(n,length,block,rng):
 starts=rng.integers(0,n-block+1,size=int(np.ceil(length/block)))
 return np.concatenate([np.arange(s,s+block) for s in starts])[:length]

def mbb_draws(y,X,Xf,block=12,draws=2000,seed=SEED):
 """Moving block bootstrap of the prediction error path (Stine 1985 style, residual blocks).

 Returns an array (draws, H) of delta* = x_h'b_hat + e*_h - x_h'b*, i.e. draws of y_h - yhat_h.
 Estimation-sample residuals are centred; the future error path is an independent MBB path, so
 period averages of delta* carry the serial dependence of the residuals."""
 rng=np.random.default_rng(seed)
 Xc=np.asarray(sm.add_constant(X,has_constant='add'));Xfc=np.asarray(sm.add_constant(Xf,has_constant='add'))
 y=np.asarray(y,float);b=np.linalg.lstsq(Xc,y,rcond=None)[0];e=y-Xc@b;e=e-e.mean()
 n,H=len(y),len(Xfc);out=np.empty((draws,H))
 for d in range(draws):
  ys=Xc@b+e[mbb_index(n,n,block,rng)]
  bs=np.linalg.lstsq(Xc,ys,rcond=None)[0]
  out[d]=Xfc@(b-bs)+e[mbb_index(n,H,block,rng)]
 return out

def clark_west(y,f_small,f_big,lags=None):
 """One-sided Clark-West (2007) MSPE-adjusted test of H0: equal accuracy, nested models.
 Returns (stat, p, mspe_small, mspe_big); HAC variance with Bartlett lags (default floor(T^(1/3)))."""
 y,f1,f2=map(lambda a:np.asarray(a,float),(y,f_small,f_big))
 adj=(y-f1)**2-((y-f2)**2-(f1-f2)**2);T=len(adj)
 L=int(np.floor(T**(1/3))) if lags is None else lags
 m=sm.OLS(adj,np.ones(T)).fit(cov_type='HAC',cov_kwds={'maxlags':L})
 t=m.tvalues[0];return t,1-stats.norm.cdf(t),np.mean((y-f1)**2),np.mean((y-f2)**2)

def bh(pvals,q=0.10):
 p=np.asarray(pvals,float);n=len(p);o=np.argsort(p);thr=q*np.arange(1,n+1)/n
 ok=p[o]<=thr;k=np.max(np.where(ok)[0])+1 if ok.any() else 0
 rej=np.zeros(n,bool);rej[o[:k]]=True
 adj=np.minimum.accumulate((p[o]*n/np.arange(1,n+1))[::-1])[::-1];padj=np.empty(n);padj[o]=np.minimum(adj,1)
 return rej,padj

def wald(fit,names):
 """HAC Wald test that the named coefficients are jointly zero (chi2)."""
 R=np.zeros((len(names),len(fit.params)));idx=list(fit.params.index)
 for i,nm in enumerate(names):R[i,idx.index(nm)]=1
 r=fit.wald_test(R,scalar=True,use_f=False);return float(r.statistic),float(r.pvalue)
