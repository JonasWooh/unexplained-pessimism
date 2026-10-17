"""Stage 2, R3.5: LLM versus dictionary, keyword rules and TF-IDF + logistic regression (D-E).

Item level, on the 260-item human test set (annotation/gold_standard_v1.csv, split == test):
- llm: frozen prompt v2 labels (labels/ai/codex__v2_isolated_r1/test.jsonl).
- lm, vader: tone only. Loughran-McDonald (data/raw/LEX) and VADER 3.3.2. Cut-offs chosen on the 100-item
  dev set only (macro F1 over the four tone classes), then frozen.
- keyword: topics and price_frame (src/analysis/keyword_rules.py, written before scoring).
- tfidf_llm: TF-IDF (1-2 grams) + logistic regression trained on the LLM labels of the coded corpus sample,
  excluding every item that is in the human gold sample; C chosen by 5-fold CV on the training data.
- tfidf_dev: same model trained only on the 100 human dev labels.
Evaluation follows src/annotation/score_ai.py: gold relevant = unsure is excluded from relevance metrics;
other dimensions are scored on set A = test items where gold and LLM both have relevant in {yes, unsure}
(the LLM's 174-item set), and on set B = all test items with gold relevant in {yes, unsure}, where an
LLM 'not relevant' counts as a miss. Bootstrap: 2,000 item resamples, percentile 95% intervals, and paired
differences against the LLM. Outputs: results/stage2_r35/.
"""
import json,re,sys,warnings
warnings.filterwarnings('ignore')
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold,cross_val_predict
from sklearn.metrics import cohen_kappa_score,f1_score,precision_recall_fscore_support
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from lib import ROOT,SEED
sys.path.insert(0,str(ROOT/'src/annotation'))
from build_corpus_sample import unit_text
from build_workbooks import TOPICS
import keyword_rules as KR

OUT=ROOT/'results/stage2_r35';OUT.mkdir(parents=True,exist_ok=True)
TONES=['negative','neutral','positive','mixed'];PF=['level','rate','both','none']
B=2000

# ---------- dictionaries ----------
LMD=pd.read_csv(ROOT/'data/raw/LEX/LM_MasterDictionary_pysentiment2-0.1.1.csv')
LM_POS=set(LMD.loc[LMD.Positive>0,'Word'].str.upper());LM_NEG=set(LMD.loc[LMD.Negative>0,'Word'].str.upper())
NEGATORS={'NO','NOT','NONE','NEITHER','NEVER','NOBODY'}
TOK=re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
def lm_counts(text):
 """Positive and negative LM word counts; a positive word within three words after a negator is not
 counted (Loughran and McDonald 2011)."""
 w=[x.upper() for x in TOK.findall(text)];p=n=0
 for i,x in enumerate(w):
  if x in LM_NEG:n+=1
  elif x in LM_POS and not NEGATORS.intersection(w[max(0,i-3):i]):p+=1
 return p,n
VA=SentimentIntensityAnalyzer()

def lm_class(p,n,c):
 if p+n==0:return 'neutral'
 s=(p-n)/(p+n)
 return 'negative' if s<-c else 'positive' if s>c else 'mixed' if p and n else 'neutral'
def vader_class(v,a,m):
 if v['compound']<=-a:return 'negative'
 if v['compound']>=a:return 'positive'
 return 'mixed' if v['pos']>=m and v['neg']>=m else 'neutral'

def macro_f1(g,p,labels):return f1_score(g,p,labels=labels,average='macro',zero_division=0)

# ---------- data ----------
def load_split(split):
 gold=pd.read_csv(ROOT/'annotation/gold_standard_v1.csv',dtype=str).fillna('')
 inp=pd.DataFrame([json.loads(l) for l in open(ROOT/f'labels/ai_inputs/{split}.jsonl')])
 d=gold[gold.split==split].merge(inp[['item_id','text','context']],on='item_id',validate='one_to_one')
 return d

def llm_labels(split):
 rows={}
 for l in open(ROOT/f'labels/ai/codex__v2_isolated_r1/{split}.jsonl'):
  o=json.loads(l);t=set(o.get('topics') or [])
  rows[o['item_id']]={'relevant':o.get('relevant') or '','tone_overall':o.get('tone_overall') or '','price_frame':o.get('price_frame') or '',**{k:'1' if k in t else '0' for k in TOPICS}}
 return pd.DataFrame.from_dict(rows,orient='index').rename_axis('item_id').reset_index()

def training_corpus():
 lab=pd.read_csv(ROOT/'labels/ai_corpus_labels.csv',dtype={'emotional_intensity':str})
 items=pd.read_parquet(ROOT/'corpus/items.parquet',columns=['item_id','unit_type','title','text'])
 gold=pd.read_csv(ROOT/'labels/sample_key.csv',dtype=str);gold_ids=set(gold.source+':'+gold.source_item_id)
 d=lab.merge(items,on='item_id',suffixes=('','_c'),validate='one_to_one')
 n0=len(d);d=d[~d.item_id.isin(gold_ids)].copy()
 d['unit']=[unit_text(r) for r in d[['unit_type_c','title','text']].rename(columns={'unit_type_c':'unit_type'}).itertuples(index=False)]
 for t in TOPICS:d[t]=d[t].fillna(0).astype(int).astype(str)
 return d,n0-len(d)

def fit_lr(texts,y,seed=SEED):
 """TF-IDF(1-2 grams, sublinear tf, min_df=2) + multinomial/binary LR; C by 5-fold CV macro F1."""
 y=np.asarray(y);classes,counts=np.unique(y,return_counts=True)
 if len(classes)<2:return ('constant',classes[0])
 vec=TfidfVectorizer(ngram_range=(1,2),min_df=2,sublinear_tf=True,lowercase=True);X=vec.fit_transform(texts)
 folds=min(5,int(counts.min()))
 best=(None,-1)
 for C in (0.25,1.0,4.0,16.0):
  m=LogisticRegression(C=C,max_iter=2000,class_weight='balanced')
  if folds>=2:
   p=cross_val_predict(m,X,y,cv=StratifiedKFold(folds,shuffle=True,random_state=seed));s=macro_f1(y,p,list(classes))
  else:s=0
  if s>best[1]:best=(C,s)
 m=LogisticRegression(C=best[0] if best[0] else 1.0,max_iter=2000,class_weight='balanced').fit(X,y)
 return ('lr',vec,m,best)
def predict_lr(model,texts):
 if model[0]=='constant':return np.array([model[1]]*len(texts))
 return model[2].predict(model[1].transform(texts))

# ---------- scoring ----------
def _codes(g,p,labels):
 """Integer codes for gold and prediction. Kappa uses every observed category (so an LLM 'missing' in set B
 counts as a disagreement); macro F1 averages over the gold classes only, with a 'missing' prediction
 counted as a false negative (same as sklearn f1_score(labels=labels))."""
 cats=list(labels)+sorted((set(g)|set(p))-set(labels));ix={c:i for i,c in enumerate(cats)}
 return np.array([ix[x] for x in g]),np.array([ix[x] for x in p]),len(cats),len(labels)

def _kappa_f1(cm,nl):
 n=cm.sum();po=np.trace(cm)/n;pe=(cm.sum(0)@cm.sum(1))/n**2
 k=np.nan if ((cm.sum(0)>0)|(cm.sum(1)>0)).sum()<2 else (po-pe)/(1-pe) if pe<1 else np.nan
 tp=np.diag(cm)[:nl];den=2*tp+(cm.sum(0)[:nl]-tp)+(cm.sum(1)[:nl]-tp)
 f1=np.where(den>0,2*tp/np.where(den>0,den,1),0.0)
 return float(k),float(f1.mean())

def metrics(g,p,labels):
 gi,pi,K,nl=_codes(g,p,labels);cm=np.bincount(gi*K+pi,minlength=K*K).reshape(K,K).astype(float)
 k,f=_kappa_f1(cm,nl)
 return dict(n=len(gi),accuracy=float(np.mean(gi==pi)),kappa=k,macro_f1=f)

def boot(g,preds,labels,ref='llm'):
 """Percentile CIs for kappa and macro F1 of every method, and paired differences vs the reference."""
 rng=np.random.default_rng(SEED);n=len(g);out={k:{'kappa':[],'macro_f1':[]} for k in preds}
 codes={k:_codes(g,p,labels) for k,p in preds.items()}
 for _ in range(B):
  w=np.bincount(rng.integers(0,n,n),minlength=n).astype(float)
  for k,(gi,pi,K,nl) in codes.items():
   cm=np.bincount(gi*K+pi,weights=w,minlength=K*K).reshape(K,K)
   kk,ff=_kappa_f1(cm,nl);out[k]['kappa'].append(kk);out[k]['macro_f1'].append(ff)
 res={}
 for k in preds:
  for s in ('kappa','macro_f1'):
   a=np.array(out[k][s],float);res[(k,s)]=np.nanpercentile(a,[2.5,97.5])
   if ref in preds and k!=ref:
    d=np.array(out[ref][s],float)-a;res[(k,s+'_diff_vs_llm')]=(np.nanmean(d),*np.nanpercentile(d,[2.5,97.5]))
 return res

def evaluate(dim,g,preds,labels,group,eval_set,rows,per):
 bs=boot(g,preds,labels) if group=='all' else {}
 for k,p in preds.items():
  r=dict(dimension=dim,eval_set=eval_set,group=group,method=k,**metrics(g,p,labels))
  if bs:
   r.update(kappa_lo=bs[(k,'kappa')][0],kappa_hi=bs[(k,'kappa')][1],macro_f1_lo=bs[(k,'macro_f1')][0],macro_f1_hi=bs[(k,'macro_f1')][1])
   if (k,'macro_f1_diff_vs_llm') in bs:
    r.update(llm_minus_method_macro_f1=bs[(k,'macro_f1_diff_vs_llm')][0],diff_lo=bs[(k,'macro_f1_diff_vs_llm')][1],diff_hi=bs[(k,'macro_f1_diff_vs_llm')][2])
  rows.append(r)
  P,R,F,S=precision_recall_fscore_support(g,p,labels=labels,zero_division=0)
  per+=[dict(dimension=dim,eval_set=eval_set,group=group,method=k,label=l,precision=P[i],recall=R[i],f1=F[i],support=int(S[i])) for i,l in enumerate(labels)]

def main():
 dev,test=load_split('dev'),load_split('test')
 # Dictionary cut-offs on dev (gold relevant in {yes, unsure}, i.e. items with a gold tone).
 dv=dev[dev.tone_overall!=''].copy();dv['lm']=[lm_counts(t) for t in dv.text];dv['va']=[VA.polarity_scores(t) for t in dv.text]
 lm_grid=[(c,macro_f1(dv.tone_overall,[lm_class(p,n,c) for p,n in dv.lm],TONES)) for c in np.round(np.arange(0,1.0,0.05),2)]
 c_lm=max(lm_grid,key=lambda x:(x[1],-x[0]))[0]
 va_grid=[(a,m,macro_f1(dv.tone_overall,[vader_class(v,a,m) for v in dv.va],TONES)) for a in np.round(np.arange(0.05,0.85,0.05),2) for m in (0.05,0.10,0.15,0.20)]
 a_va,m_va,_=max(va_grid,key=lambda x:(x[2],-x[0],-x[1]))
 thr=dict(lm_cut=c_lm,lm_dev_macro_f1=max(x[1] for x in lm_grid),vader_compound_cut=a_va,vader_mixed_min_share=m_va,vader_dev_macro_f1=max(x[2] for x in va_grid),dev_items=len(dv))
 (OUT/'dictionary_thresholds.json').write_text(json.dumps(thr,indent=1))
 # Classifiers.
 corp,n_excl=training_corpus();models={}
 rel=corp[corp.relevant.isin(['yes','no'])];models[('tfidf_llm','relevant')]=fit_lr(rel.unit,rel.relevant)
 yes=corp[corp.relevant=='yes']
 for dim in ['tone_overall','price_frame']+TOPICS:models[('tfidf_llm',dim)]=fit_lr(yes.unit,yes[dim].astype(str))
 dr=dev[dev.relevant.isin(['yes','no'])];models[('tfidf_dev','relevant')]=fit_lr(dr.text,dr.relevant)
 dy=dev[dev.relevant.isin(['yes','unsure'])]
 for dim in ['tone_overall','price_frame']+TOPICS:models[('tfidf_dev',dim)]=fit_lr(dy.text,dy[dim].replace('','0') if dim in TOPICS else dy[dim])
 cv=[dict(method=k[0],dimension=k[1],C=v[3][0],cv_macro_f1=v[3][1]) for k,v in models.items() if v[0]=='lr']
 pd.DataFrame(cv).to_csv(OUT/'classifier_cv.csv',index=False)
 # Predictions on test.
 llm=llm_labels('test');t=test.merge(llm,on='item_id',suffixes=('','_llm'),validate='one_to_one')
 t['lm_counts']=[lm_counts(x) for x in t.text];t['tone_lm']=[lm_class(p,n,c_lm) for p,n in t.lm_counts]
 t['tone_vader']=[vader_class(VA.polarity_scores(x),a_va,m_va) for x in t.text]
 kw=pd.DataFrame([KR.topics(x) for x in t.text]);t[[f'{k}_kw' for k in kw]]=kw.astype(str).values;t['price_frame_kw']=[KR.price_frame(x) for x in t.text]
 for meth in ['tfidf_llm','tfidf_dev']:
  for dim in ['relevant','tone_overall','price_frame']+TOPICS:t[f'{dim}_{meth}']=predict_lr(models[(meth,dim)],t.text.tolist())
 for k in TOPICS:t[k]=t[k].replace('','0')
 t.drop(columns=['lm_counts']).to_csv(OUT/'test_predictions.csv',index=False)
 rows=[];per=[]
 for group in ['all','national','local','social']:
  s=t if group=='all' else t[t.tier==group]
  r=s[s.relevant.isin(['yes','no'])]
  evaluate('relevant',r.relevant.tolist(),{'llm':r.relevant_llm.replace('unsure','yes').tolist(),'keyword_all_yes':['yes']*len(r),'tfidf_llm':r.relevant_tfidf_llm.tolist(),'tfidf_dev':r.relevant_tfidf_dev.tolist()},['yes','no'],group,'gold yes/no',rows,per)
  for eval_set,sel in [('A: gold and LLM relevant',s.relevant.isin(['yes','unsure'])&s.relevant_llm.isin(['yes','unsure'])),('B: gold relevant',s.relevant.isin(['yes','unsure']))]:
   e=s[sel]
   if e.empty:continue
   miss=lambda col,fill:e[col].where(e.relevant_llm.isin(['yes','unsure']),fill).tolist()
   evaluate('tone_overall',e.tone_overall.tolist(),{'llm':miss('tone_overall_llm','missing'),'lm':e.tone_lm.tolist(),'vader':e.tone_vader.tolist(),'tfidf_llm':e.tone_overall_tfidf_llm.tolist(),'tfidf_dev':e.tone_overall_tfidf_dev.tolist()},TONES,group,eval_set,rows,per)
   evaluate('price_frame',e.price_frame.tolist(),{'llm':miss('price_frame_llm','missing'),'keyword':e.price_frame_kw.tolist(),'tfidf_llm':e.price_frame_tfidf_llm.tolist(),'tfidf_dev':e.price_frame_tfidf_dev.tolist()},PF,group,eval_set,rows,per)
   if group=='all':
    for k in TOPICS:
     evaluate(k,e[k].tolist(),{'llm':miss(k+'_llm','0'),'keyword':e[k+'_kw'].tolist(),'tfidf_llm':e[k+'_tfidf_llm'].tolist(),'tfidf_dev':e[k+'_tfidf_dev'].tolist()},['0','1'],group,eval_set,rows,per)
 M=pd.DataFrame(rows);M.to_csv(OUT/'item_metrics.csv',index=False);pd.DataFrame(per).to_csv(OUT/'item_per_class.csv',index=False)
 # Topic summary: mean kappa over the 13 topics per method.
 tk=M[M.dimension.isin(TOPICS)].groupby(['eval_set','method']).agg(mean_kappa=('kappa','mean'),mean_macro_f1=('macro_f1','mean')).reset_index()
 tk.to_csv(OUT/'topics_summary.csv',index=False)
 (OUT/'training_info.json').write_text(json.dumps(dict(corpus_labels=int(len(corp)+n_excl),excluded_gold_overlap=int(n_excl),train_relevance=int(len(rel)),train_content=int(len(yes)),dev_relevance=int(len(dr)),dev_content=int(len(dy))),indent=1))
 pd.set_option('display.width',250)
 print(thr);print(M[(M.group=='all')&~M.dimension.isin(TOPICS)][['dimension','eval_set','method','n','accuracy','kappa','kappa_lo','kappa_hi','macro_f1','macro_f1_lo','macro_f1_hi','llm_minus_method_macro_f1','diff_lo','diff_hi']].round(3).to_string())
 print(tk.round(3).to_string())
 print(M[(M.group!='all')&(M.eval_set!='B: gold relevant')][['dimension','group','method','n','kappa','macro_f1']].round(3).to_string())

if __name__=='__main__':main()
