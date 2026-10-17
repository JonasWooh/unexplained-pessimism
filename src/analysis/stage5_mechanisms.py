"""Stage 5 (RQ4, R5.2-R5.4): mechanisms, group gaps, survey-mode comparability, pre-election comparison, recent
social and local sources.

Timing and controls as in stages 1-4: survey month t; X = real-time U, pi, g at cutoff t (1st of month t); month dummies;
HAC 12 for every regression; pandemic months = 2020-03..2021-06 (stage 1 F1: M1 errors there are not interpretable).

1 Mechanisms
  a Negativity (confidence side): dICS_t on the bad and good parts of the data news released in month t-1
    (x(cutoff t) - x(cutoff t-1); bad = rise of U or pi, fall of g). Negativity <=> |beta_bad| > |beta_good|,
    i.e. beta_bad + beta_good < 0 (beta_bad < 0 < beta_good). Main 2010-02..2026-10; variants: excluding 2020-03..2021-06,
    2010-02..2019-12, 3-month changes. Mirrors the media-side test of stage 2 (stage2_bias tone_asymmetry).
  b Availability: ICS on X + gas price (level, $/gal) + food CPI 12-month change. Windows: 2010-06..2019-12 (stage 1 main
    window) and 2010-06..2026-10 without the pandemic months (in-sample association including the gap years). The 2010-2019
    fit is also used to recompute the 2025-01..2026-10 ICS gap (as stage 1 did for H1).
  c Anchoring: (i) competition regression ICS on X + 36-month cumulative PCE, same two windows;
    (ii) shares citing high prices as the reason for worse finances (pagorn_hp_all) or a bad time to buy (durrn_hp_all,
    vehrn_hp_all, homrn_hp_all) on 12-month PCE inflation, 36-month cumulative PCE, U, month dummies and a web-mode step
    (2024-07 on), 2010-06..2026-08 without the pandemic months. Anchoring-compatible: cumulative coefficient > 0 with the
    12-month rate held fixed.
  d Confirmation bias: not identifiable; stage 1 party jumps are cited (no new estimate).
2 Group gaps (R5.2): income terciles, age, region, education. Group index minus a group-specific M1 (X + month dummies,
  fit 2010-01..2019-12), mean by stage 1 gap period (last period ends 2026-08), actual change against the group's 2019
  mean, explained share = 1 - gap / change. Differences between groups in 2025-01..2026-08 against a reference group
  (HAC 12 on the monthly difference). ICS, ICC, ICE. Party groups: as in stage 4 (own 2017-02..2019-12 mean).
3 Mode comparability (R5.3): (a) step at 2024-07 in the survey-side mechanism measures (news_u_all, newsrn_u_pri_all,
  pagorn_hp_all, px1_med_all) net of X and month dummies, 2023-01..2025-12, with and without 2024-04..06 (stage 1 H3a
  design); (b) change of the ICS/ICC/ICE gap within the web era (2024-07..12 to 2025 and to 2026-01..08), which does not
  depend on the mode level shift; for reference the change over a phone-only stretch (2022-07..12 to 2024-01..03).
4 Pre-election months (R5.4): midterm years 2010, 2014, 2018, 2022, 2026; ICS gap (stage 1 M1) and national tone in
  January-April vs May-October; regression of the monthly gap change on a May-October midterm-year dummy and a
  presidential-year dummy (2010-02..2026-10 without the pandemic months, month dummies). 2010-2019 gaps are in-sample
  residuals; this is stated with the result.
5 Recent social and local (descriptive): correlation of each source's tone (month t-1) with the ICS gap (month t), in
  levels and in first differences, on the source's own months; national tone on the same months for comparison. Reddit
  in quarters: quarterly tone = monthly net_tone weighted by est_relevant_items (the ratio estimator over the quarter);
  quarterly gap = mean of the monthly gaps.
Outputs: results/stage5_mechanisms/.
"""
import numpy as np
import pandas as pd
from lib import ROOT,ols,GAP_PERIODS,PERIODS

OUT=ROOT/'results/stage5_mechanisms';OUT.mkdir(parents=True,exist_ok=True)
X1=['unrate_rt','pce_yoy_rt','gdp_qoq_saar_rt'];SEAS=[f'm{m:02}' for m in range(2,13)]
PAND=('2020-03','2021-06')
SIGN={'unrate_rt':1,'pce_yoy_rt':1,'gdp_qoq_saar_rt':-1}   # +1: a rise is bad news

def base():
 P=pd.read_csv(ROOT/'data/processed/research_panel.csv');P=P[P.month>='2009-01'].reset_index(drop=True)
 S=pd.read_csv(ROOT/'data/processed/survey_monthly.csv').drop(columns=['ics','icc','ice'],errors='ignore')
 D=P.merge(S,on='month',how='left')
 mo=D.month.str[5:7].astype(int)
 extra={f'm{m:02}':(mo==m).astype(float) for m in range(2,13)}
 extra.update(web=(D.month>='2024-07').astype(float),pand=D.month.between(*PAND))
 return pd.concat([D,pd.DataFrame(extra)],axis=1)

def coef_row(f,name,**kw):return dict(**kw,term=name,coef=f.params[name],se=f.bse[name],p=f.pvalues[name],n=int(f.nobs),r2=f.rsquared)

def lincomb(f,w):
 R=np.zeros(len(f.params));idx=list(f.params.index)
 for k,v in w.items():R[idx.index(k)]=v
 t=f.t_test(R);return float(np.squeeze(t.effect)),float(np.squeeze(t.sd)),float(np.squeeze(t.pvalue))

# ---------- 1a negativity, confidence side ----------
def negativity(D):
 rows=[]
 for lab,k,a,b,drop in [('main: 1-month, 2010-02..2026-10',1,'2010-02','2026-10',False),('excluding 2020-03..2021-06',1,'2010-02','2026-10',True),
   ('2010-02..2019-12',1,'2010-02','2019-12',False),('3-month changes, excluding 2020-03..2021-06',3,'2010-04','2026-10',True)]:
  T=D.copy();T['dy']=T.ics-T.ics.shift(k);cols=[]
  for x,s in SIGN.items():
   d=s*(T[x]-T[x].shift(k));T[x+'_bad']=d.clip(lower=0);T[x+'_good']=(-d).clip(lower=0);cols+=[x+'_bad',x+'_good']
  Z=T[T.month.between(a,b)&(~T.pand if drop else True)][['dy']+cols+SEAS].dropna();f=ols(Z.dy,Z[cols+SEAS],12)
  for x in SIGN:
   e,se,p=lincomb(f,{x+'_bad':1,x+'_good':1})
   rows.append(dict(spec=lab,indicator=x,beta_bad=f.params[x+'_bad'],p_bad=f.pvalues[x+'_bad'],beta_good=f.params[x+'_good'],p_good=f.pvalues[x+'_good'],
    bad_plus_good=e,se=se,p_two=p,n=int(f.nobs)))
  e,se,p=lincomb(f,{c:1 for c in cols});rows.append(dict(spec=lab,indicator='all three (sum)',bad_plus_good=e,se=se,p_two=p,n=int(f.nobs)))
 return pd.DataFrame(rows)

# ---------- 1b availability and 1c(i) anchoring: competition regressions ----------
def competition(D):
 rows=[];gaps=[]
 for extra,mech in [(['gas_price_rt_dd','food_cpi_yoy_rt'],'availability'),(['pce_cum36_rt'],'anchoring'),(['gas_price_rt_dd','food_cpi_yoy_rt','pce_cum36_rt'],'both')]:
  for lab,a,b,drop in [('2010-06..2019-12','2010-06','2019-12',False),('2010-06..2026-10 without 2020-03..2021-06','2010-06','2026-10',True)]:
   cols=X1+extra+SEAS;Z=D[D.month.between(a,b)&(~D.pand if drop else True)][['ics']+cols].dropna();f=ols(Z.ics,Z[cols],12)
   for c in X1+extra:rows.append(coef_row(f,c,mechanism=mech,window=lab))
   if b=='2019-12':
    f0=ols(Z.ics,Z[X1+SEAS],12)
    for per,(c0,c1) in {'2021-07..2022-12':('2021-07','2022-12'),'2023-01..2024-12':('2023-01','2024-12'),'2025-01..2026-10':('2025-01','2026-10')}.items():
     O=D[D.month.between(c0,c1)].dropna(subset=['ics']+cols)
     g1=(O.ics-f.predict(sm_const(O[cols]))).mean();g0=(O.ics-f0.predict(sm_const(O[X1+SEAS]))).mean()
     gaps.append(dict(mechanism=mech,period=per,months=len(O),gap_M1=g0,gap_with_extra=g1,reduction_share=1-g1/g0))
 return pd.DataFrame(rows),pd.DataFrame(gaps)

def sm_const(X):
 import statsmodels.api as sm
 return sm.add_constant(X,has_constant='add')

# ---------- 1c(ii) anchoring: reasons citing high prices ----------
def price_reasons(D):
 rows=[];desc=[]
 for y in ['pagorn_hp_all','durrn_hp_all','vehrn_hp_all','homrn_hp_all']:
  cols=['pce_yoy_rt','pce_cum36_rt','unrate_rt','web']+SEAS
  Z=D[D.month.between('2010-06','2026-08')&~D.pand][[y]+cols].dropna();f=ols(Z[y],Z[cols],12)
  for c in ['pce_yoy_rt','pce_cum36_rt','web']:rows.append(coef_row(f,c,outcome=y))
  for per,(a,b) in {'2019':('2019-01','2019-12'),'2022':('2022-01','2022-12'),'2025-01..2026-08':('2025-01','2026-08')}.items():
   R=D[D.month.between(a,b)];desc.append(dict(outcome=y,period=per,mean_share=R[y].mean(),mean_pce_yoy=R.pce_yoy_rt.mean(),mean_pce_cum36=R.pce_cum36_rt.mean()))
 return pd.DataFrame(rows),pd.DataFrame(desc)

# ---------- 2 group gaps ----------
GROUPS={'income':['y13','y23','y33'],'age':['a1834','a3554','a5597'],'region':['w','nc','ne','s'],'education':['ehs','esc','ecd']}
REF={'income':'y33','age':'a5597','region':'ne','education':'ecd'}
def group_gaps(D):
 rows=[];diffs=[];monthly=D[['month']].copy()
 pers={k:v for k,v in PERIODS.items() if k in GAP_PERIODS};pers['2026-01..2026-10']=('2026-01','2026-08')
 for idx in ('ics','icc','ice'):
  for dim,gs in GROUPS.items():
   for g in gs:
    c=f'{idx}_{g}';Z=D[D.month.between('2010-01','2019-12')][[c]+X1+SEAS].dropna();f=ols(Z[c],Z[X1+SEAS],12)
    gap=D[c]-f.predict(sm_const(D[X1+SEAS]));monthly[f'gap_{c}']=gap
    base=D.loc[D.month.between('2019-01','2019-12'),c].mean()
    for per,(a,b) in pers.items():
     m=D.month.between(a,b);ch=(D.loc[m,c]-base).mean();gp=gap[m].mean()
     rows.append(dict(index=idx,dimension=dim,group=g,period=per.replace('2026-10','2026-08'),actual_change_vs_2019=ch,mean_gap=gp,explained_share=1-gp/ch if ch else np.nan,fit_r2=f.rsquared))
   for g in gs:
    if g==REF[dim]:continue
    for per,(a,b) in {'2021-07..2022-12':('2021-07','2022-12'),'2025-01..2026-08':('2025-01','2026-08')}.items():
     m=D.month.between(a,b);d=(monthly.loc[m,f'gap_{idx}_{g}']-monthly.loc[m,f'gap_{idx}_{REF[dim]}']).dropna();f=ols(d,pd.DataFrame(index=d.index),12)
     diffs.append(dict(index=idx,dimension=dim,group=g,reference=REF[dim],period=per,difference=f.params['const'],se=f.bse['const'],p=f.pvalues['const'],months=len(d)))
 monthly.to_csv(OUT/'group_gaps_monthly.csv',index=False)
 return pd.DataFrame(rows),pd.DataFrame(diffs)

# ---------- 3 mode comparability ----------
def mode(D):
 rows=[]
 for y in ['news_u_all','newsrn_u_pri_all','pagorn_hp_all','px1_med_all']:
  for lab,drop in [('2023-01..2025-12',False),('2023-01..2025-12 without 2024-04..06',True)]:
   Z=D[D.month.between('2023-01','2025-12')&(~D.month.between('2024-04','2024-06') if drop else True)][[y,'web']+X1+SEAS].dropna()
   f=ols(Z[y],Z[['web']+X1+SEAS],12);rows.append(coef_row(f,'web',outcome=y,sample=lab))
 G=pd.read_csv(ROOT/'results/stage1_m1/m1_gap_monthly.csv')
 ch=[]
 for dv in ('ics','icc','ice'):
  g=G[G.dv==dv].set_index('month').gap
  for lab,(a0,a1),(b0,b1) in [('web era: 2024-07..12 to 2026-01..08',('2024-07','2024-12'),('2026-01','2026-08')),('web era: 2024-07..12 to 2025-01..12',('2024-07','2024-12'),('2025-01','2025-12')),
    ('phone era: 2022-07..12 to 2024-01..03',('2022-07','2022-12'),('2024-01','2024-03'))]:
   ch.append(dict(index=dv,comparison=lab,gap_before=g[a0:a1].mean(),gap_after=g[b0:b1].mean(),change=g[b0:b1].mean()-g[a0:a1].mean()))
 return pd.DataFrame(rows),pd.DataFrame(ch)

# ---------- 4 pre-election months ----------
def pre_election(D):
 G=pd.read_csv(ROOT/'results/stage1_m1/m1_gap_monthly.csv');G=G[G.dv=='ics'][['month','gap']]
 M=pd.read_csv(ROOT/'features/media_monthly.csv');M=M[M.group=='national'][['month','net_tone']]
 T=D[['month']+SEAS].merge(G,on='month').merge(M,on='month',how='left')
 T['year']=T.month.str[:4].astype(int);T['mo']=T.month.str[5:7].astype(int)
 desc=[]
 for y in (2010,2014,2018,2022,2026):
  E=T[T.year==y];a=E[E.mo.between(1,4)];b=E[E.mo.between(5,10)]
  desc.append(dict(year=y,gap_jan_apr=a.gap.mean(),gap_may_oct=b.gap.mean(),gap_change=b.gap.mean()-a.gap.mean(),tone_jan_apr=a.net_tone.mean(),tone_may_oct=b.net_tone.mean(),
   tone_change=b.net_tone.mean()-a.net_tone.mean(),gap_in_sample=bool(y<=2019)))
 T['dgap']=T.gap.diff()
 T['mid_pre']=((T.year%4==2)&T.mo.between(5,10)).astype(float);T['pres_pre']=((T.year%4==0)&T.mo.between(5,10)).astype(float)
 rows=[]
 for lab,a,b in [('2010-02..2026-10 without 2020-03..2021-06','2010-02','2026-10'),('2010-02..2019-12 (in-sample gaps)','2010-02','2019-12')]:
  Z=T[T.month.between(a,b)&~T.month.between(*PAND)].dropna(subset=['dgap']);f=ols(Z.dgap,Z[['mid_pre','pres_pre']+SEAS],12)
  for c in ('mid_pre','pres_pre'):rows.append(coef_row(f,c,sample=lab))
 return pd.DataFrame(desc),pd.DataFrame(rows)

# ---------- 5 recent social and local ----------
def recent_sources():
 G=pd.read_csv(ROOT/'results/stage1_m1/m1_gap_monthly.csv');G=G[G.dv=='ics'][['month','gap']].set_index('month').gap
 M=pd.read_csv(ROOT/'features/media_monthly.csv')
 nat=M[M.group=='national'].set_index('month').net_tone
 rows=[]
 def assoc(tone,gap,label,unit,nat_tone):
  Z=pd.concat([tone.rename('t'),gap.rename('g'),nat_tone.rename('n')],axis=1).dropna()
  r=dict(source=label,unit=unit,first=Z.index.min(),last=Z.index.max(),n=len(Z),corr_level=Z.t.corr(Z.g),corr_level_national_same_periods=Z.n.corr(Z.g),
   corr_diff=Z.t.diff().corr(Z.g.diff()),corr_diff_national_same_periods=Z.n.diff().corr(Z.g.diff()),mean_tone=Z.t.mean(),mean_tone_national=Z.n.mean())
  f=ols(Z.g,Z[['t']],min(12,max(1,len(Z)//4)));r.update(slope=f.params['t'],slope_p=f.pvalues['t']);rows.append(r)
 lag=lambda s:s.rename(index=lambda m:str(pd.Period(m,freq='M')+1))   # tone of month t-1 aligned to survey month t
 for grp in ('youtube','local','mc_national'):
  s=M[M.group==grp].set_index('month').net_tone;assoc(lag(s),G,grp,'month',lag(nat))
 R=M[M.group=='reddit'].copy();R['q']=pd.PeriodIndex(R.month,freq='M').asfreq('Q').astype(str)
 N=M[M.group=='national'].copy();N['q']=pd.PeriodIndex(N.month,freq='M').asfreq('Q').astype(str)
 qt=lambda X:X.groupby('q').apply(lambda x:np.average(x.net_tone,weights=x.est_relevant_items) if x.est_relevant_items.sum()>0 else np.nan,include_groups=False)
 qi=pd.PeriodIndex(G.index,freq='M').asfreq('Q').astype(str);Gq=G.groupby(qi).mean()[G.groupby(qi).count()==3]   # complete quarters only
 lq=lambda s:s.rename(index=lambda q:str(pd.Period(q,freq='Q')+1))   # previous quarter's tone
 assoc(lq(qt(R)),Gq,'reddit','quarter (tone of previous quarter)',lq(qt(N)))
 return pd.DataFrame(rows)

def main():
 D=base()
 neg=negativity(D);neg.to_csv(OUT/'negativity_confidence.csv',index=False)
 comp,cg=competition(D);comp.to_csv(OUT/'competition_regressions.csv',index=False);cg.to_csv(OUT/'competition_gap_reduction.csv',index=False)
 pr,pd_=price_reasons(D);pr.to_csv(OUT/'price_reasons.csv',index=False);pd_.to_csv(OUT/'price_reasons_periods.csv',index=False)
 gg,gd=group_gaps(D);gg.to_csv(OUT/'group_gaps.csv',index=False);gd.to_csv(OUT/'group_gap_differences.csv',index=False)
 ms,mc=mode(D);ms.to_csv(OUT/'mode_steps.csv',index=False);mc.to_csv(OUT/'mode_gap_changes.csv',index=False)
 pe,pr2=pre_election(D);pe.to_csv(OUT/'pre_election_years.csv',index=False);pr2.to_csv(OUT/'pre_election_regression.csv',index=False)
 rs=recent_sources();rs.to_csv(OUT/'recent_sources.csv',index=False)
 pd.set_option('display.width',260);pd.set_option('display.max_columns',30)
 for t in (neg,comp,cg,pr,pd_,gg[gg['index']=='ics'],gd[gd['index']=='ics'],ms,mc,pe,pr2,rs):print(t.round(3).to_string(),'\n')

if __name__=='__main__':main()
