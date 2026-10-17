"""Stage 2, R3.3 bias benchmarks for national news (research design v1, section on measurement and benchmarks).

Media side: features/media_monthly.csv, group = national (LLM v2 labels, ~26 relevant items a month).
Economic side: real-time values from data/processed/research_panel.csv. "News released during month t" is
 dx_t = x(cutoff t+1) - x(cutoff t), i.e. the change in the latest published value over month t (new release plus
 revisions). The level known by the end of month t is x(cutoff t+1). Sample 2010-01..2026-09 (2026-10 has no t+1 cutoff).

1 Tone asymmetry (H2a): net_tone_t on the bad and good parts of dU, dpi (PCE yoy), dg (GDP q/q saar):
  bad = max(dU,0), max(dpi,0), max(-dg,0); good = the opposite parts (all >= 0). Negativity asymmetry means
  |b_bad| > |b_good|; with the expected signs (b_bad < 0 < b_good) the test is H0: b_bad + b_good = 0 against < 0.
  Variants: with net_tone_{t-1}; excluding 2020-03..2020-12; 3-month changes x(cutoff t+1) - x(cutoff t-2).
2 Topic selection: topic_prices_rising on max(dpi,0) and topic_inflation_easing on max(-dpi,0); topic_layoffs on
  max(dU,0) and topic_hiring on max(-dU,0). Slopes and elasticities at the means (slope / mean share), difference
  rising - easing (layoffs - hiring) with a 12-month moving-block bootstrap of months (2,000 draws).
3 Framing after inflation falls: price_level_share_of_priced and household_share on pi level, a post-peak dummy
  (months after the real-time PCE inflation peak), and in a second spec the 36-month cumulative PCE increase.
4 Fact errors by period and source: results/stage2_factcal/summary.csv (not recomputed here).
5 Political attribution: blame_admin_share (and credit_admin_share) on U, pi, g levels plus administration dummies
  (Obama to 2016-12, Trump 2017-01..2020-12, Biden 2021-01..2024-12, Trump 2025-01 on, as rep_admin in panel.py);
  Wald test that the four administrations have equal shares given fundamentals. Criticism is not by itself bias.
6 Cross-source: national versus local, Media Cloud national, YouTube and Reddit on each group's months; mean of the
  monthly ratio estimates over common months (Reddit: quarterly cells), difference to national with an item bootstrap
  within group x cell.
All regressions OLS with HAC(12). Outputs: results/stage2_bias/.
"""
import json
import numpy as np
import pandas as pd
from lib import ROOT,SEED,ols,wald,mbb_index

OUT=ROOT/'results/stage2_bias';OUT.mkdir(parents=True,exist_ok=True)
B=2000
X={'U':'unrate_rt','pi':'pce_yoy_rt','g':'gdp_qoq_saar_rt'}

def data():
 P=pd.read_csv(ROOT/'data/processed/research_panel.csv');P=P[P.month>='2009-10'].reset_index(drop=True)
 for k,c in X.items():
  P[k+'_end']=P[c].shift(-1);P['d'+k]=P[c].shift(-1)-P[c];P['d3'+k]=P[c].shift(-1)-P[c].shift(2)
 P['cum36_end']=P.pce_cum36_rt.shift(-1)
 M=pd.read_csv(ROOT/'features/media_monthly.csv');M=M[M.group=='national']
 D=M.merge(P,on='month',how='left')
 D=D[(D.month>='2010-01')&(D.month<='2026-09')].sort_values('month').reset_index(drop=True)
 D['net_tone_l1']=D.net_tone.shift(1)
 return D

def parts(D,pre='d'):
 return pd.DataFrame({'U_bad':D[pre+'U'].clip(lower=0),'U_good':(-D[pre+'U']).clip(lower=0),
  'pi_bad':D[pre+'pi'].clip(lower=0),'pi_good':(-D[pre+'pi']).clip(lower=0),
  'g_bad':(-D[pre+'g']).clip(lower=0),'g_good':D[pre+'g'].clip(lower=0)},index=D.index)

def lincomb(fit,w):
 r=np.zeros(len(fit.params));idx=list(fit.params.index)
 for k,v in w.items():r[idx.index(k)]=v
 t=fit.t_test(r);est=float(np.squeeze(t.effect));se=float(np.squeeze(t.sd))
 from scipy import stats
 return est,se,float(stats.norm.cdf(est/se))  # one-sided p for H1: combination < 0

def tone_asymmetry(D):
 rows=[];coefs=[]
 specs={'main (1-month changes)':(D.index,'d',False),'with lagged tone':(D.index,'d',True),
  'excluding 2020-03..2020-12':(D.index[~D.month.between('2020-03','2020-12')],'d',False),'3-month changes':(D.index,'d3',False)}
 for name,(idx,pre,lag) in specs.items():
  Z=parts(D,pre)
  if lag:Z['net_tone_l1']=D.net_tone_l1
  Z['y']=D.net_tone;Z=Z.loc[idx].dropna()
  f=ols(Z.y,Z.drop(columns='y'))
  for k in f.params.index:coefs.append(dict(spec=name,term=k,coef=f.params[k],se=f.bse[k],p=f.pvalues[k],n=int(f.nobs)))
  for ind in ['U','pi','g']:
   est,se,p=lincomb(f,{ind+'_bad':1,ind+'_good':1})
   rows.append(dict(spec=name,indicator=ind,b_bad=f.params[ind+'_bad'],b_good=f.params[ind+'_good'],sum_bad_plus_good=est,se=se,p_one_sided_negativity=p,n=int(f.nobs)))
  st,pj=wald_sum(f);rows.append(dict(spec=name,indicator='joint (3 sums = 0)',sum_bad_plus_good=np.nan,se=np.nan,p_one_sided_negativity=np.nan,wald_chi2=st,wald_p=pj,n=int(f.nobs)))
 return pd.DataFrame(rows),pd.DataFrame(coefs)

def wald_sum(fit):
 idx=list(fit.params.index);R=np.zeros((3,len(idx)))
 for i,ind in enumerate(['U','pi','g']):R[i,idx.index(ind+'_bad')]=1;R[i,idx.index(ind+'_good')]=1
 r=fit.wald_test(R,scalar=True,use_f=False);return float(r.statistic),float(r.pvalue)

def topic_selection(D):
 pairs={'inflation':('topic_prices_rising','pi_bad','topic_inflation_easing','pi_good'),'labor':('topic_layoffs_unemployment_up','U_bad','topic_hiring_jobs_growth','U_good')}
 rng=np.random.default_rng(SEED);rows=[]
 for pre,label in [('d','1-month changes'),('d3','3-month changes')]:
  Z=pd.concat([parts(D,pre),D[[c for p in pairs.values() for c in (p[0],p[2])]]],axis=1).dropna().reset_index(drop=True)
  def est(Z):
   out={}
   for k,(ya,xa,yb,xb) in pairs.items():
    ba=np.polyfit(Z[xa],Z[ya],1)[0];bb=np.polyfit(Z[xb],Z[yb],1)[0]
    out[k]=(ba,bb,ba/Z[ya].mean(),bb/Z[yb].mean())
   return out
  e=est(Z);draws={k:[] for k in pairs}
  for _ in range(B):
   s=Z.iloc[mbb_index(len(Z),len(Z),12,rng)].reset_index(drop=True);eb=est(s)
   for k in pairs:draws[k].append(eb[k])
  for k,(ya,xa,yb,xb) in pairs.items():
   a=np.array(draws[k]);fa=ols(Z[ya],Z[[xa]]);fb=ols(Z[yb],Z[[xb]])
   rows.append(dict(changes=label,pair=k,rising_topic=ya,rising_slope=e[k][0],rising_slope_p=fa.pvalues[xa],falling_topic=yb,falling_slope=e[k][1],falling_slope_p=fb.pvalues[xb],
    slope_diff=e[k][0]-e[k][1],slope_diff_lo=np.percentile(a[:,0]-a[:,1],2.5),slope_diff_hi=np.percentile(a[:,0]-a[:,1],97.5),
    rising_elasticity=e[k][2],falling_elasticity=e[k][3],elasticity_diff=e[k][2]-e[k][3],
    elasticity_diff_lo=np.percentile(a[:,2]-a[:,3],2.5),elasticity_diff_hi=np.percentile(a[:,2]-a[:,3],97.5),
    mean_rising_share=Z[ya].mean(),mean_falling_share=Z[yb].mean(),n=len(Z)))
 return pd.DataFrame(rows)

def framing(D):
 w=D[D.month.between('2021-01','2023-12')];peak=w.loc[w.pi_end.idxmax(),'month']
 D=D.assign(post_peak=(D.month>peak).astype(int));rows=[]
 for y in ['price_level_share_of_priced','household_share','price_frame_share']:
  for name,cols in [('pi + post-peak',['pi_end','post_peak']),('pi + cum36 + post-peak',['pi_end','cum36_end','post_peak']),('pi + cum36',['pi_end','cum36_end'])]:
   Z=D[[y]+cols].dropna();f=ols(Z[y],Z[cols])
   for c in cols:rows.append(dict(outcome=y,spec=name,term=c,coef=f.params[c],se=f.bse[c],p=f.pvalues[c],n=int(f.nobs),r2=f.rsquared))
 per=[]
 for lab,(a,b) in {'2010-2019':('2010-01','2019-12'),'2020-01..peak':('2020-01',peak),'after peak..2026-09':(peak,'2026-09')}.items():
  s=D[(D.month>=a)&(D.month<=b)] if lab!='after peak..2026-09' else D[D.month>a]
  per.append(dict(period=lab,months=len(s),pi_mean=s.pi_end.mean(),cum36_mean=s.cum36_end.mean(),price_level_share_of_priced=s.price_level_share_of_priced.mean(),
   household_share=s.household_share.mean(),price_frame_share=s.price_frame_share.mean(),topic_prices_rising=s.topic_prices_rising.mean(),topic_inflation_easing=s.topic_inflation_easing.mean()))
 return pd.DataFrame(rows),pd.DataFrame(per),peak

def attribution(D):
 D=D.assign(trump1=D.month.between('2017-01','2020-12').astype(int),biden=D.month.between('2021-01','2024-12').astype(int),trump2=(D.month>='2025-01').astype(int))
 rows=[]
 for y in ['blame_admin_share','credit_admin_share']:
  for name,cols in [('fundamentals + administration',['U_end','pi_end','g_end','trump1','biden','trump2']),('administration only',['trump1','biden','trump2'])]:
   Z=D[[y]+cols].dropna();f=ols(Z[y],Z[cols]);st,p=wald(f,['trump1','biden','trump2'])
   for c in ['const']+cols:rows.append(dict(outcome=y,spec=name,term=c,coef=f.params[c],se=f.bse[c],p=f.pvalues[c],n=int(f.nobs),wald_equal_admins_chi2=st,wald_equal_admins_p=p))
 means=D.groupby(np.select([D.trump1==1,D.biden==1,D.trump2==1],['Trump 2017-2020','Biden 2021-2024','Trump 2025-'],'Obama 2010-2016'))[['blame_admin_share','credit_admin_share','net_tone','U_end','pi_end']].mean()
 return pd.DataFrame(rows),means.reset_index().rename(columns={'index':'administration'})

# ---------- 6 cross-source ----------
MET={'net_tone':lambda r:(r.tone_overall=='positive').astype(float)-(r.tone_overall=='negative').astype(float),
 'share_negative':lambda r:(r.tone_overall=='negative').astype(float),
 'net_fact':lambda r:(r.fact_direction=='good').astype(float)-(r.fact_direction=='bad').astype(float),
 'household_share':lambda r:r.perspective.isin(['household','both']).astype(float),
 'price_frame_share':lambda r:r.price_frame.isin(['level','rate','both']).astype(float),
 'level_share_all':lambda r:r.price_frame.isin(['level','both']).astype(float),
 'blame_admin_share':lambda r:(((r.actor_1=='president_admin')&(r.direction_1=='blame'))|((r.actor_2=='president_admin')&(r.direction_2=='blame'))).astype(float),
 'topic_prices_rising':lambda r:(r.T03_prices_rising.astype(int)==1).astype(float),
 'topic_layoffs_unemployment_up':lambda r:(r.T01_layoffs_unemployment_up.astype(int)==1).astype(float)}

def cross_source():
 L=pd.read_csv(ROOT/'labels/ai_corpus_labels.csv',dtype={'emotional_intensity':str})
 L=L[L.relevant=='yes'].copy();L['w']=L.w.astype(float)
 vals={k:f(L).to_numpy() for k,f in MET.items()}
 rng=np.random.default_rng(SEED);rows=[]
 L['quarter']=pd.PeriodIndex(L.month,freq='M').asfreq('Q').astype(str)
 for grp in ['local','mc_national','youtube','reddit']:
  unit='quarter' if grp=='reddit' else 'month'   # Reddit: quarterly cells (about 5 relevant items a month)
  cells={k:np.where(((L.group==k[0])&(L[unit]==k[1])).to_numpy())[0] for k in L[L.group.isin([grp,'national'])].groupby(['group',unit]).groups}
  periods=sorted(set(L.loc[L.group==grp,unit])&set(L.loc[L.group=='national',unit]))
  if grp=='reddit':periods=[q for q in periods if set(L.loc[(L.group=='reddit')&(L.quarter==q),'month'])>=set(L.loc[(L.group=='national')&(L.quarter==q),'month'])]
  def est(sample):
   out={}
   for g in (grp,'national'):
    per=[]
    for m in periods:
     ix=sample[(g,m)];w=L.w.to_numpy()[ix]
     per.append([np.sum(vals[k][ix]*w)/np.sum(w) for k in MET])
    out[g]=np.nanmean(np.array(per),axis=0)
   return out
  base=est({(g,m):cells[(g,m)] for g in (grp,'national') for m in periods})
  bs=[]
  for _ in range(B):
   s={}
   for g in (grp,'national'):
    for m in periods:c=cells[(g,m)];s[(g,m)]=c[rng.integers(0,len(c),len(c))]
   e=est(s);bs.append(e[grp]-e['national'])
  bs=np.array(bs)
  for i,k in enumerate(MET):
   rows.append(dict(group=grp,cell=unit,window=f'{periods[0]}..{periods[-1]}',cells=len(periods),items_group=int(sum(len(cells[(grp,m)]) for m in periods)),
    items_national=int(sum(len(cells[('national',m)]) for m in periods)),metric=k,group_mean=base[grp][i],national_mean=base['national'][i],
    diff=base[grp][i]-base['national'][i],diff_lo=np.percentile(bs[:,i],2.5),diff_hi=np.percentile(bs[:,i],97.5),boot_mean_diff=bs[:,i].mean()))
 return pd.DataFrame(rows)

def main():
 D=data()
 A,Ac=tone_asymmetry(D);A.to_csv(OUT/'tone_asymmetry.csv',index=False);Ac.to_csv(OUT/'tone_asymmetry_coefs.csv',index=False)
 T=topic_selection(D);T.to_csv(OUT/'topic_selection.csv',index=False)
 F,Fp,peak=framing(D);F.to_csv(OUT/'framing.csv',index=False);Fp.to_csv(OUT/'framing_periods.csv',index=False)
 At,Am=attribution(D);At.to_csv(OUT/'attribution.csv',index=False);Am.to_csv(OUT/'attribution_means.csv',index=False)
 S=cross_source();S.to_csv(OUT/'cross_source.csv',index=False)
 (OUT/'info.json').write_text(json.dumps(dict(months=len(D),first=D.month.min(),last=D.month.max(),pce_peak_month_realtime=peak),indent=1))
 pd.set_option('display.width',250);pd.set_option('display.max_columns',30)
 print('peak',peak);print(A.round(3).to_string());print(T.round(4).to_string());print(F.round(3).to_string());print(Fp.round(3).to_string())
 print(At[At.term.isin(['trump1','biden','trump2'])].round(3).to_string());print(Am.round(3).to_string());print(S.round(3).to_string())

if __name__=='__main__':main()
