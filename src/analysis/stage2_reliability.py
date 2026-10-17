"""Stage 2: reliability of the monthly national media index and the three checks on its 0.37 correlation with the
San Francisco Fed news sentiment index (research design v1: sampling noise, headline+abstract vs full text, topic scope).

Reliability: within each month the 40 coded national units are resampled with replacement (2,000 draws) and net_tone
(and net_fact) is recomputed with the same ratio estimator as features/media_monthly.csv. Sampling variance s_t^2 is
multiplied by the finite-population correction (1 - n_t/N_t), since the target is the tone of the month's frame of
NYT + Guardian units; the uncorrected value is also reported. Reliability = 1 - mean(s_t^2) / Var(index_t). For the
3-month mean the variance is sum of the three monthly variances / 9 (draws are independent across months).
Disattenuated correlation with the SF Fed index = r / sqrt(reliability), treating the SF Fed index as error-free (it is
built from many more articles), so it is an upper-bound style correction.
Checks: (1) 3-month means; (2) Guardian full text vs coded unit text (results/stage2_dictindex); (3) macro-topic units
only (LLM topics T01-T06: labour market, prices and inflation, growth and recession), for the LLM index and for the
full-frame dictionary index (keyword-rule topics T01-T06). Outputs: results/stage2_reliability/.
"""
import json
import numpy as np
import pandas as pd
from lib import ROOT,SEED
import keyword_rules as KR

OUT=ROOT/'results/stage2_reliability';OUT.mkdir(parents=True,exist_ok=True)
B=2000
MACRO=['T01_layoffs_unemployment_up','T02_hiring_jobs_growth','T03_prices_rising','T04_inflation_easing','T05_economic_growth','T06_recession_risk']

def ratio(v,w,rel):
 m=rel&~np.isnan(v);return np.sum(v[m]*w[m])/np.sum(w[m]) if m.any() else np.nan

def main():
 L=pd.read_csv(ROOT/'labels/ai_corpus_labels.csv',dtype={'emotional_intensity':str});L=L[L.group=='national'].copy()
 fr=pd.read_csv(ROOT/'labels/corpus_sample_frames.csv');fr=fr[fr.group=='national'].set_index('month')
 L['tone']=np.select([L.tone_overall=='positive',L.tone_overall=='negative'],[1.0,-1.0],0.0)
 L['fact']=np.select([L.fact_direction=='good',L.fact_direction=='bad'],[1.0,-1.0],0.0)
 L['macro']=L[MACRO].fillna(0).astype(int).sum(axis=1)>0
 rng=np.random.default_rng(SEED);rows=[]
 for m,g in L.groupby('month'):
  w=g.w.astype(float).to_numpy();rel=(g.relevant=='yes').to_numpy();mac=rel&g.macro.to_numpy()
  est={k:ratio(g[c].to_numpy(),w,r) for k,c,r in [('net_tone','tone',rel),('net_fact','fact',rel),('net_tone_macro','tone',mac)]}
  n=len(g);bs={k:[] for k in est}
  for _ in range(B):
   i=rng.integers(0,n,n);wi,ri,mi=w[i],rel[i],mac[i]
   bs['net_tone'].append(ratio(g.tone.to_numpy()[i],wi,ri));bs['net_fact'].append(ratio(g.fact.to_numpy()[i],wi,ri));bs['net_tone_macro'].append(ratio(g.tone.to_numpy()[i],wi,mi))
  fpc=1-n/fr.loc[m,'frame_size']
  r=dict(month=m,n_coded=n,frame_size=int(fr.loc[m,'frame_size']),fpc=fpc,n_relevant=int(rel.sum()),n_macro=int(mac.sum()))
  for k in est:r[k]=est[k];r[k+'_var_boot']=float(np.nanvar(bs[k]));r[k+'_var_fpc']=r[k+'_var_boot']*fpc
  rows.append(r)
 M=pd.DataFrame(rows).sort_values('month').reset_index(drop=True)
 sf=pd.read_csv(ROOT/'features/sffed_news_sentiment_monthly.csv');M=M.merge(sf,on='month',how='left')
 D=pd.read_csv(ROOT/'features/media_dict_monthly.csv');M=M.merge(D[['month','dict_net_tone_lm','dict_net_tone_lm_llmsample']],on='month',how='left')
 # sanity: matches features/media_monthly.csv
 F=pd.read_csv(ROOT/'features/media_monthly.csv');F=F[F.group=='national'].set_index('month')
 assert np.allclose(M.set_index('month').net_tone,F.net_tone.reindex(M.month),equal_nan=True)
 out=[]
 for k in ['net_tone','net_fact','net_tone_macro']:
  for corr in ['fpc','boot']:
   s2=M[k+'_var_'+corr];v=M[k].var();lam=1-s2.mean()/v
   m3=M[k].rolling(3).mean();s3=(s2+s2.shift(1)+s2.shift(2))/9;lam3=1-s3.mean()/m3.var()
   r1=M[k].corr(M.sffed_news_sentiment_mean);r3=m3.corr(M.sffed_news_sentiment_mean.rolling(3).mean())
   out.append(dict(index=k,variance=('with' if corr=='fpc' else 'without')+' finite-population correction',months=int(M[k].notna().sum()),
    mean_sampling_sd=float(np.sqrt(s2.mean())),sd_of_index=float(np.sqrt(v)),reliability=lam,reliability_3m=lam3,
    r_sffed=r1,r_sffed_disattenuated=r1/np.sqrt(lam) if lam>0 else np.nan,r_sffed_3m=r3,r_sffed_3m_disattenuated=r3/np.sqrt(lam3) if lam3>0 else np.nan))
 R=pd.DataFrame(out);R.to_csv(OUT/'reliability.csv',index=False);M.to_csv(OUT/'monthly_sampling_variance.csv',index=False)
 # check (3), dictionary side: full-frame units with keyword-rule macro topics.
 S=pd.read_csv(ROOT/'results/stage2_dictindex/item_scores.csv.gz')
 items=pd.read_parquet(ROOT/'corpus/items.parquet',columns=['item_id','unit_type','title','text'])
 import sys;sys.path.insert(0,str(ROOT/'src/annotation'));from build_corpus_sample import unit_text
 S=S.merge(items,on='item_id',how='left');S['unit']=[unit_text(r) for r in S[['unit_type','title','text']].itertuples(index=False)]
 kw=pd.DataFrame([KR.topics(t) for t in S.unit]);S['kw_macro']=kw[MACRO].sum(axis=1).to_numpy()>0
 net=lambda c:float((c=='positive').mean()-(c=='negative').mean()) if len(c) else np.nan
 dm=S[(S.rel_pred=='yes')&S.kw_macro].groupby('month').tone_lm.apply(net).rename('dict_net_tone_lm_macro').reset_index()
 dm=dm.merge(S[(S.rel_pred=='yes')&S.kw_macro].groupby('month').size().rename('n_macro_units').reset_index(),on='month')
 M=M.merge(dm,on='month',how='left');M.to_csv(OUT/'monthly_sampling_variance.csv',index=False)
 checks=[]
 sfx=M.sffed_news_sentiment_mean
 for name,col,note in [('LLM index, all relevant (baseline)','net_tone','40 coded units a month'),('(1) LLM index, 3-month mean','net_tone','rolling 3'),
  ('(3) LLM index, macro-topic units only','net_tone_macro','LLM topics T01-T06'),
  ('dictionary LM, LLM-sample units only','dict_net_tone_lm_llmsample','same units as LLM index, dictionary tone'),
  ('dictionary LM, full frame','dict_net_tone_lm','all predicted-relevant units, about 120 a month'),
  ('(3) dictionary LM, full frame, macro-topic units only','dict_net_tone_lm_macro','keyword-rule topics T01-T06')]:
  x=M[col].rolling(3).mean() if 'rolling' in note else M[col];y=sfx.rolling(3).mean() if 'rolling' in note else sfx
  ok=x.notna()&y.notna();checks.append(dict(check=name,series=col,note=note,months=int(ok.sum()),r_sffed=float(np.corrcoef(x[ok],y[ok])[0,1]),
   r_sffed_first_difference=float(x.diff().corr(y.diff()))))
 C=pd.read_csv(ROOT/'results/stage2_dictindex/correlations.csv')
 for nm in ['guardian_lm_unit','guardian_lm_fulltext']:
  c=C[((C.a==nm)&(C.b=='sffed'))|((C.b==nm)&(C.a=='sffed'))].set_index('transform').pearson
  checks.append(dict(check=f'(2) Guardian only, LM dictionary on {"coded unit text" if nm.endswith("unit") else "full article body"}',series=nm,note='about 17 Guardian units a month',
   months=int(C[(C.a==nm)|(C.b==nm)].months.max()),r_sffed=c['level'],r_sffed_first_difference=c['first difference']))
 K=pd.DataFrame(checks);K.to_csv(OUT/'sffed_checks.csv',index=False)
 pd.set_option('display.width',250);print(R.round(3).to_string());print(K.round(3).to_string())
 print(M[['n_relevant','n_macro']].describe().round(1).to_string())

if __name__=='__main__':main()
