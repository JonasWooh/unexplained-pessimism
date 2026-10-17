"""Stage 4 (RQ2, RQ6): time order, common shocks, recall path, partisan heterogeneity and the falsification inputs.

Timing as in stage 3: row t = survey month t; Tone_{t-1} = national net_tone of month t-1; X = real-time U, pi, g at
cutoff t; surprises = change of the real-time value between cutoffs t-1 and t (data released during month t-1; no free
consensus forecasts, design section on causal inference). Event dummies (provenance/events.csv) equal 1 if an event of the
class occurred in month t-1 or t: shutdown (any month of a lapse), tariff announcement, bank failure; pandemic = 2020-03..12.
Tone and ICS are standardised (z-scores over 2010-06..2026-10) in the local projections.

1 Two-way local projections, h = 0..6 (HAC 12):
  forward  ICS_{t+h} - ICS_{t-1} on Tone_{t-1} | X_t, surprises, events, ICS_{t-1}, ICS_{t-2}, Tone_{t-2}, month dummies
  reverse  Tone_{t+h} - Tone_{t-1} on ICS_{t-1} | the same controls
  Pre-declared summary test (before results): the average-horizon projection, mean over h = 0..6 of the left-hand side
  on the same right-hand side; 'significant' = one-sided 5% in the expected direction (forward > 0, reverse > 0).
  Variants: without surprises/events; excluding 2020-03..2020-12.
2 Excess tone since 2021 (falsification 1): Tone_m on X(cutoff m+1) and household controls H, fit 2010-01..2019-12;
  mean residual 2021-01..2026-10 tested against 0 (HAC 12). Variant: fit on 2010-01..2026-10.
3 Recall path (H2d, falsification 6), survey months 2010-06..2026-08: news_u_all (share who heard unfavourable news) on
  Tone_{t-1} and on X; unique R2 of each block; ICS on news_u_all | X; topic correspondence: newsrn_u_pri_all on
  topic_prices_rising_{t-1} and newsrn_u_emp_all on topic_layoffs_{t-1}, each with the other topic as placebo, | X.
  Variant ending 2024-03 (before the web-mode change).
4 Partisan heterogeneity (2017-02..2026-08): ics_dem / ics_ind / ics_rep on Tone_{t-1} | X, own lag, rep_admin, month
  dummies; difference Dem - Rep from a stacked regression with group interactions (HAC 12).
5 Group gap shapes (falsification 7): age groups 18-34 vs 55+: group ICS minus a group-specific M1 (2010-01..2019-12, month
  dummies); party Dem vs Rep: index minus own 2017-02..2019-12 mean. Difference in mean gap 2025-01..2026-08 (HAC 12) and
  correlation of the monthly gap paths 2021-01..2026-08.
Outputs: results/stage4_timing/.
"""
import json
import numpy as np
import pandas as pd
from lib import ROOT,ols
import stage3_forecast as S

OUT=ROOT/'results/stage4_timing';OUT.mkdir(parents=True,exist_ok=True)
X1=S.X1;SEAS=S.SEAS
EVENTS=['ev_shutdown','ev_tariff','ev_bank','ev_pandemic']

def event_months():
 E=pd.read_csv(ROOT/'provenance/events.csv');E['month']=E.date.str[:7]
 shut=set()
 for a,b in [('2013-10','2013-10'),('2018-01','2018-02'),('2018-12','2019-01'),('2025-10','2025-11')]:
  shut|=set(pd.period_range(a,b,freq='M').astype(str))
 assert set(E[E.category=='shutdown_start'].month)<=shut
 return {'ev_shutdown':shut,'ev_tariff':set(E[E.category=='tariff_announcement'].month),'ev_bank':set(E[E.category=='bank_resolution'].month),
  'ev_pandemic':set(pd.period_range('2020-03','2020-12',freq='M').astype(str))}

def data():
 D=S.panel();P=pd.read_csv(ROOT/'data/processed/research_panel.csv');P=P[P.month>='2009-12'].set_index('month')
 for c in X1:D['s_'+c]=D.month.map(P[c]-P[c].shift(1))
 prev={m:str(pd.Period(m,freq='M')-1) for m in D.month}
 for k,ms in event_months().items():D[k]=[float(m in ms or prev[m] in ms) for m in D.month]
 D['tone_l2']=D.tone_l1.shift(1);D['y_l2']=D.y_l1.shift(1)
 Sv=pd.read_csv(ROOT/'data/processed/survey_monthly.csv').set_index('month')
 for c in ['news_u_all','news_f_all','newsrn_u_pri_all','newsrn_u_emp_all','ics_dem','ics_rep','ics_ind','ics_a1834','ics_a5597']:D[c]=D.month.map(Sv[c])
 D['web']=(D.month>='2024-07').astype(float)
 return D

def z(s,ref):return (s-ref.mean())/ref.std()

def lp(D,controls,label,mask=None):
 T=D.copy() if mask is None else D[mask(D)].copy()
 T['zy']=z(T.y,T.y);T['zt']=z(T.tone_l1,T.tone_l1)
 T['zy_l1']=z(T.y_l1,T.y);T['zy_l2']=z(T.y_l2,T.y);T['zt_l2']=z(T.tone_l2,T.tone_l1)
 # tone of month t+h (h>=0) is tone_l1 shifted by -(h+1)
 rows=[]
 for direction in ('forward','reverse'):
  lhs={}
  for h in range(7):
   lhs[h]=(T.zy.shift(-h)-T.zy_l1) if direction=='forward' else (T.zt.shift(-(h+1))-T.zt)
  lhs['avg 0-6']=pd.concat([lhs[h] for h in range(7)],axis=1).mean(axis=1,skipna=False)
  shock='zt' if direction=='forward' else 'zy_l1'
  rhs=[shock]+[c for c in ['zy_l1','zy_l2','zt','zt_l2'] if c!=shock]+controls+SEAS
  if direction=='reverse':rhs=[r for r in rhs if r!='zt']+['zt']   # Tone_{t-1} is the base of the reverse LHS; kept as control
  rhs=list(dict.fromkeys(rhs))
  for h,y in lhs.items():
   Z=pd.concat([y.rename('lhs'),T[rhs]],axis=1).dropna();f=ols(Z.lhs,Z[rhs],12)
   b,se=f.params[shock],f.bse[shock]
   from scipy import stats
   rows.append(dict(spec=label,direction=direction,horizon=str(h),coef=b,se=se,p_two=f.pvalues[shock],p_one_positive=1-stats.norm.cdf(b/se),n=int(f.nobs)))
 return rows

def excess_since_2021(D):
 M=pd.read_csv(ROOT/'features/media_monthly.csv');M=M[M.group=='national'][['month','net_tone']]
 P=pd.read_csv(ROOT/'data/processed/research_panel.csv').set_index('month')
 F=X1+S.H
 for c in F:M[c]=[P[c].get(str(pd.Period(m,freq='M')+1),np.nan) for m in M.month]   # fundamentals known by end of month m
 out=[]
 for lab,(a,b) in {'fit 2010-01..2019-12':('2010-01','2019-12'),'fit 2010-01..2026-10':('2010-01','2026-10')}.items():
  Z=M[(M.month>=a)&(M.month<=b)].dropna();f=ols(Z.net_tone,Z[F],12)
  M['resid']=M.net_tone-(f.params['const']+M[F].values@f.params[F].values)
  for per,(c,d) in {'2021-01..2026-10':('2021-01','2026-10'),'2021-07..2022-12':('2021-07','2022-12'),'2023-01..2024-12':('2023-01','2024-12'),'2025-01..2026-10':('2025-01','2026-10')}.items():
   R=M[(M.month>=c)&(M.month<=d)].dropna(subset=['resid']);g=ols(R.resid,pd.DataFrame(index=R.index),12)
   out.append(dict(fit=lab,period=per,months=len(R),mean_residual=g.params['const'],se=g.bse['const'],p=g.pvalues['const'],fit_r2=f.rsquared))
 return pd.DataFrame(out)

def unique_r2(Z,y,A,Bk,ctrl):
 r=lambda cols:ols(Z[y],Z[cols+ctrl],12).rsquared if cols+ctrl else 0.0
 full=r(A+Bk);return dict(r2_full=full,r2_A_only=r(A),r2_B_only=r(Bk),unique_A=full-r(Bk),unique_B=full-r(A))

def recall(D):
 rows=[];reg=[]
 for lab,end in [('2010-06..2026-08','2026-08'),('2010-06..2024-03 (before web mode)','2024-03')]:
  T=D[D.month<=end].copy()
  for lag in ('topic_prices_rising_l1','topic_layoffs_unemployment_up_l1'):T[lag]=T[lag]
  Z=T[['news_u_all','tone_l1','y']+X1+SEAS+['web']].dropna()
  ctrl=SEAS+(['web'] if end>'2024-06' else [])
  u=unique_r2(Z,'news_u_all',['tone_l1'],X1,ctrl);rows.append(dict(sample=lab,outcome='news_u_all',A='tone_l1',B='U, pi, g',n=len(Z),**u))
  f=ols(Z.news_u_all,Z[['tone_l1']+X1+ctrl],12);reg.append(dict(sample=lab,equation='news_u_all ~ tone_l1 | X',coef=f.params['tone_l1'],se=f.bse['tone_l1'],p=f.pvalues['tone_l1'],n=int(f.nobs)))
  f=ols(Z.y,Z[['news_u_all']+X1+ctrl],12);reg.append(dict(sample=lab,equation='ICS ~ news_u_all | X',coef=f.params['news_u_all'],se=f.bse['news_u_all'],p=f.pvalues['news_u_all'],n=int(f.nobs)))
  f=ols(Z.y,Z[['news_u_all','tone_l1']+X1+ctrl],12);reg.append(dict(sample=lab,equation='ICS ~ tone_l1 | news_u_all, X',coef=f.params['tone_l1'],se=f.bse['tone_l1'],p=f.pvalues['tone_l1'],n=int(f.nobs)))
  for y,own,other in [('newsrn_u_pri_all','topic_prices_rising_l1','topic_layoffs_unemployment_up_l1'),('newsrn_u_emp_all','topic_layoffs_unemployment_up_l1','topic_prices_rising_l1')]:
   Z2=T[[y,own,other]+X1+SEAS+['web']].dropna();f=ols(Z2[y],Z2[[own,other]+X1+ctrl],12)
   R=np.zeros(len(f.params));idx=list(f.params.index);R[idx.index(own)]=1;R[idx.index(other)]=-1;t=f.t_test(R)
   reg.append(dict(sample=lab,equation=f'{y} ~ {own} (own) + {other} (placebo) | X',coef=f.params[own],se=f.bse[own],p=f.pvalues[own],placebo_coef=f.params[other],placebo_p=f.pvalues[other],
    own_minus_placebo=float(np.squeeze(t.effect)),own_minus_placebo_p=float(np.squeeze(t.pvalue)),n=int(f.nobs)))
 return pd.DataFrame(rows),pd.DataFrame(reg)

def partisan(D):
 T=D[(D.month>='2017-02')&(D.month<='2026-08')].copy();out=[];stack=[]
 for g in ('dem','ind','rep'):
  T['gy']=T['ics_'+g];T['gy_l1']=T['gy'].shift(1)
  cols=['tone_l1']+X1+['gy_l1','rep_admin']+SEAS;Z=T[['gy']+cols].dropna();f=ols(Z.gy,Z[cols],12)
  out.append(dict(group=g,gamma=f.params['tone_l1'],se=f.bse['tone_l1'],p=f.pvalues['tone_l1'],n=int(f.nobs)))
  s=Z.copy();s['grp']=g;stack.append(s)
 St=pd.concat(stack).reset_index(drop=True)
 for g in ('dem','ind'):
  St[g]=(St.grp==g).astype(float)
 base=['tone_l1']+X1+['gy_l1','rep_admin']+SEAS
 for c in base:
  for g in ('dem','ind'):St[f'{c}_x_{g}']=St[c]*St[g]
 cols=base+['dem','ind']+[f'{c}_x_{g}' for c in base for g in ('dem','ind')]
 f=ols(St.gy,St[cols],12)
 out.append(dict(group='dem - rep (stacked)',gamma=f.params['tone_l1_x_dem'],se=f.bse['tone_l1_x_dem'],p=f.pvalues['tone_l1_x_dem'],n=int(f.nobs)))
 return pd.DataFrame(out)

def group_gaps(D):
 P=pd.read_csv(ROOT/'data/processed/research_panel.csv');Sv=pd.read_csv(ROOT/'data/processed/survey_monthly.csv')
 A=P[['month']+X1].merge(Sv[['month','ics_a1834','ics_a5597','ics_dem','ics_rep']],on='month');A=A[A.month>='2010-01'].reset_index(drop=True)
 for m in range(2,13):A[f'm{m:02}']=(A.month.str[5:7].astype(int)==m).astype(float)
 for g in ('ics_a1834','ics_a5597'):
  Z=A[A.month<='2019-12'].dropna(subset=[g]);f=ols(Z[g],Z[X1+SEAS],12)
  A['gap_'+g]=A[g]-(f.params['const']+A[X1+SEAS].values@f.params[X1+SEAS].values)
 for g in ('ics_dem','ics_rep'):A['gap_'+g]=A[g]-A[A.month.between('2017-02','2019-12')][g].mean()
 out=[]
 for name,a,b in [('age 18-34 minus 55+','gap_ics_a1834','gap_ics_a5597'),('Democrats minus Republicans','gap_ics_dem','gap_ics_rep')]:
  for per,(c,d) in {'2025-01..2026-08':('2025-01','2026-08'),'2021-07..2022-12':('2021-07','2022-12'),'2023-01..2024-12':('2023-01','2024-12')}.items():
   R=A[A.month.between(c,d)].dropna(subset=[a,b]);diff=R[a]-R[b];f=ols(diff,pd.DataFrame(index=R.index),12)
   W=A[A.month.between('2021-01','2026-08')].dropna(subset=[a,b])
   out.append(dict(comparison=name,period=per,months=len(R),mean_gap_first=R[a].mean(),mean_gap_second=R[b].mean(),difference=f.params['const'],se=f.bse['const'],p=f.pvalues['const'],
    corr_monthly_gap_paths_2021_2026=W[a].corr(W[b])))
 A.to_csv(OUT/'group_gaps_monthly.csv',index=False)
 return pd.DataFrame(out)

def main():
 D=data()
 surprises=['s_'+c for c in X1]
 L=[]
 L+=lp(D,X1+surprises+EVENTS,'main: X, surprises, events')
 L+=lp(D,X1,'X only')
 L+=lp(D,X1+surprises+[e for e in EVENTS if e!='ev_pandemic'],'excluding 2020-03..2020-12',mask=lambda T:~T.month.between('2020-03','2020-12'))
 L=pd.DataFrame(L);L.to_csv(OUT/'local_projections.csv',index=False)
 E=excess_since_2021(D);E.to_csv(OUT/'excess_tone_since_2021.csv',index=False)
 U,R=recall(D);U.to_csv(OUT/'recall_unique_r2.csv',index=False);R.to_csv(OUT/'recall_regressions.csv',index=False)
 Pt=partisan(D);Pt.to_csv(OUT/'partisan_gamma.csv',index=False)
 G=group_gaps(D);G.to_csv(OUT/'group_gap_differences.csv',index=False)
 pd.set_option('display.width',250);pd.set_option('display.max_columns',30)
 print(L.round(3).to_string());print(E.round(3).to_string());print(U.round(3).to_string());print(R.round(3).to_string());print(Pt.round(3).to_string());print(G.round(3).to_string())

if __name__=='__main__':main()
