"""Stage 2, R3.5 index level: full-frame dictionary tone index for national news, compared with the LLM index
and the San Francisco Fed news sentiment index.

Frame: every NYT and Guardian content unit in corpus/items.parquet (not duplicate/repost/ad/obituary), 2010-01..2026-10,
i.e. the same frame the LLM sample (40 a month) is drawn from; unit text as in the coded sample (unit_text).
Relevance: the tfidf_llm relevance classifier of stage2_r35 (TF-IDF + logistic regression trained on the LLM corpus labels,
gold items excluded, C by 5-fold CV). Items that are in its training data get 5-fold cross-fitted predictions, so no
item is scored by a model that saw its own label.
Tone: Loughran-McDonald classes with the dev-tuned cut-off (results/stage2_r35/dictionary_thresholds.json) and VADER
classes with its dev-tuned cut-offs; net tone = share positive - share negative among predicted-relevant units (all
first-stage weights are 1 in this frame). A continuous LM score (pos - neg) / (pos + neg), 0 when no LM word, is added.
Also computed: the LM index on only the LLM-sampled units (separates method from sample size), and the Guardian check
for the SF Fed correlation: LM tone of Guardian units on the coded unit text (headline + standfirst + first 100 words)
versus the full article body.
Outputs: features/media_dict_monthly.csv, results/stage2_dictindex/.
"""
import json,sys,warnings
warnings.filterwarnings('ignore')
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold,cross_val_predict
from lib import ROOT,SEED
sys.path.insert(0,str(ROOT/'src/annotation'))
from build_corpus_sample import unit_text
import stage2_r35 as R

OUT=ROOT/'results/stage2_dictindex';OUT.mkdir(parents=True,exist_ok=True)

def frame():
 d=pd.read_parquet(ROOT/'corpus/items.parquet',columns=['item_id','source','month','unit_type','title','text','is_duplicate','is_repost','is_ad','is_obituary'])
 d=d[d.source.isin(['NYT','Guardian'])&~d.is_duplicate&~d.is_repost&~d.is_ad&~d.is_obituary&(d.month>='2010-01')].copy()
 d['unit']=[unit_text(r) for r in d[['unit_type','title','text']].itertuples(index=False)]
 return d.reset_index(drop=True)

def relevance(d):
 corp,_=R.training_corpus();rel=corp[corp.relevant.isin(['yes','no'])].reset_index(drop=True)
 model=R.fit_lr(rel.unit,rel.relevant);vec,C=model[1],model[3][0]
 Xtr=vec.transform(rel.unit)
 cf=cross_val_predict(LogisticRegression(C=C,max_iter=2000,class_weight='balanced'),Xtr,np.asarray(rel.relevant,dtype=object),cv=StratifiedKFold(5,shuffle=True,random_state=SEED))
 crossfit=dict(zip(rel.item_id,cf))
 full=model[2].predict(vec.transform(d.unit))
 d['rel_pred']=[crossfit.get(i,f) for i,f in zip(d.item_id,full)]
 d['rel_crossfit']=d.item_id.isin(crossfit)
 return dict(C=C,train_items=len(rel),frame_items_crossfit=int(d.rel_crossfit.sum()))

def net(cls):return float(np.mean(cls=='positive')-np.mean(cls=='negative')) if len(cls) else np.nan

def main():
 thr=json.loads((ROOT/'results/stage2_r35/dictionary_thresholds.json').read_text())
 d=frame();info=relevance(d)
 pn=[R.lm_counts(t) for t in d.unit];d['lm_pos']=[p for p,_ in pn];d['lm_neg']=[n for _,n in pn]
 d['tone_lm']=[R.lm_class(p,n,thr['lm_cut']) for p,n in pn]
 d['lm_score']=[(p-n)/(p+n) if p+n else 0.0 for p,n in pn]
 d['tone_vader']=[R.vader_class(R.VA.polarity_scores(t),thr['vader_compound_cut'],thr['vader_mixed_min_share']) for t in d.unit]
 g=d.source=='Guardian'
 body=[t.split('\n',1)[1] if '\n' in t else t for t in d.loc[g,'text']];pf=[R.lm_counts(t) for t in body]
 d.loc[g,'tone_lm_fulltext']=[R.lm_class(p,n,thr['lm_cut']) for p,n in pf]
 key=pd.read_csv(ROOT/'labels/corpus_sample_key.csv');sampled=set(key.loc[key.group=='national','item_id'])
 d['in_llm_sample']=d.item_id.isin(sampled)
 rows=[]
 for m,x in d.groupby('month'):
  r=x[x.rel_pred=='yes'];rs=r[r.in_llm_sample];gu=x[(x.source=='Guardian')]
  rows.append(dict(month=m,n_frame=len(x),n_pred_relevant=len(r),pred_relevant_share=len(r)/len(x),
   dict_net_tone_lm=net(r.tone_lm.values),dict_net_tone_vader=net(r.tone_vader.values),dict_lm_score=float(r.lm_score.mean()) if len(r) else np.nan,
   n_sample_pred_relevant=len(rs),dict_net_tone_lm_llmsample=net(rs.tone_lm.values),
   n_guardian=len(gu),guardian_lm_unit=net(gu.tone_lm.values),guardian_lm_fulltext=net(gu.tone_lm_fulltext.values)))
 M=pd.DataFrame(rows)
 (ROOT/'features').mkdir(exist_ok=True);M.to_csv(ROOT/'features/media_dict_monthly.csv',index=False)
 d[['item_id','source','month','rel_pred','rel_crossfit','in_llm_sample','lm_pos','lm_neg','tone_lm','lm_score','tone_vader','tone_lm_fulltext']].to_csv(OUT/'item_scores.csv.gz',index=False)
 # Correlations.
 llm=pd.read_csv(ROOT/'features/media_monthly.csv');llm=llm[llm.group=='national'][['month','net_tone','n_relevant']]
 sf=pd.read_csv(ROOT/'features/sffed_news_sentiment_monthly.csv')
 J=M.merge(llm,on='month',how='left').merge(sf,on='month',how='left').sort_values('month')
 series={'llm_net_tone (sample)':'net_tone','dict_net_tone_lm (full frame)':'dict_net_tone_lm','dict_net_tone_vader (full frame)':'dict_net_tone_vader',
  'dict_lm_score (full frame)':'dict_lm_score','dict_net_tone_lm (LLM sample units)':'dict_net_tone_lm_llmsample',
  'guardian_lm_unit':'guardian_lm_unit','guardian_lm_fulltext':'guardian_lm_fulltext','sffed':'sffed_news_sentiment_mean'}
 C=[]
 for a,ca in series.items():
  for b,cb in series.items():
   if a>=b:continue
   for tr in ['level','3-month mean','first difference']:
    x,y=J[ca],J[cb]
    if tr=='3-month mean':x,y=x.rolling(3).mean(),y.rolling(3).mean()
    if tr=='first difference':x,y=x.diff(),y.diff()
    ok=x.notna()&y.notna();C.append(dict(a=a,b=b,transform=tr,months=int(ok.sum()),pearson=float(np.corrcoef(x[ok],y[ok])[0,1])))
 C=pd.DataFrame(C);C.to_csv(OUT/'correlations.csv',index=False)
 info.update(frame_items=len(d),pred_relevant=int((d.rel_pred=='yes').sum()),months=len(M),median_relevant_per_month=float(M.n_pred_relevant.median()),
  guardian_units=int(g.sum()),median_guardian_per_month=float(M.n_guardian.median()))
 (OUT/'info.json').write_text(json.dumps(info,indent=1))
 pd.set_option('display.width',250);print(json.dumps(info))
 print(C[(C.a.str.contains('sffed')|C.b.str.contains('sffed')|C.a.str.contains('llm_net')|C.b.str.contains('llm_net'))].round(3).to_string())

if __name__=='__main__':main()
