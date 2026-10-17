"""Stage 2, R3.7: name/party swap and source-label test of the frozen LLM coder (design D-F).

Versions per item (120 items, labels/r37/r37_items.csv): O1 = the formal corpus label (labels/ai_corpus_labels.csv),
O2 = original text coded again, S = president names and parties swapped, F = '[Source: Fox News]' prefix,
M = '[Source: MSNBC]' prefix (labels/ai/codex__v2_r37/, mapped by labels/r37/r37_unit_key_DO_NOT_GIVE_CODEX.csv).

Flip rate of version V on a dimension = share of items whose label differs from O1. Excess flip rate =
flip(V) - flip(O2): the change beyond ordinary run-to-run variation. A label missing because the version was coded
not relevant counts as a flip. For S, party actor codes are mapped back (democrats <-> republicans) before comparison,
because the swap changes which party is named. Paired item bootstrap, 2,000 draws, percentile 95% intervals.

Directional tests (tone score negative=-1, neutral/mixed=0, positive=+1; admin blame = 1 if the president/administration
is blamed in either actor slot):
- Person swap: d = score(S) - score(O2) per item. If the coder favours one president, d has opposite signs in the
  Trump->Biden and Biden->Trump strata. Statistic: mean d(Trump->Biden) - mean d(Biden->Trump); bootstrap within strata.
  Obama->Trump and party-only strata are reported separately (one direction each).
- Source label: score(F) - score(M) per item, and each against O2.
Outputs: results/stage2_r37/.
"""
import json,re,sys
from pathlib import Path
import numpy as np
import pandas as pd
from lib import ROOT,SEED
sys.path.insert(0,str(ROOT/'src/annotation'))
from build_workbooks import CODES,TOPICS

OUT=ROOT/'results/stage2_r37';OUT.mkdir(parents=True,exist_ok=True)
B=2000
DIMS=['relevant','tone_overall','fact_direction','emotional_intensity','price_frame','perspective','time_frame','numeric_claim',
 'definition_error','actor_1','direction_1','admin_attribution','topics']
PARTY_BACK={'democrats':'republicans','republicans':'democrats'}
TONE_SCORE={'negative':-1,'neutral':0,'mixed':0,'positive':1}

def s(v):return '' if v is None or (isinstance(v,float) and np.isnan(v)) else str(v)
def norm(x):return re.sub(r'\s+',' ',x or '').strip().lower()

def admin(r):
 for a,d in (('actor_1','direction_1'),('actor_2','direction_2')):
  if r.get(a)=='president_admin':return r.get(d) or 'neutral_mention'
 return 'none'

def record(o):
 r={k:s(o.get(k)) for k in ['relevant','tone_overall','fact_direction','emotional_intensity','price_frame','perspective','time_frame',
  'numeric_claim','definition_error','actor_1','direction_1','actor_2','direction_2']}
 r['admin_attribution']=admin(r);r['topics']='|'.join(sorted(o.get('topics') or []));return r

def load():
 key=pd.read_csv(ROOT/'labels/r37/r37_unit_key_DO_NOT_GIVE_CODEX.csv');items=pd.read_csv(ROOT/'labels/r37/r37_items.csv')
 inputs={}
 for f in sorted((ROOT/'codex_runs/R37_package/inputs').glob('r37_batch_*.jsonl')):
  for l in open(f):o=json.loads(l);inputs[o['item_id']]=o
 out={};problems=[];ev=[0,0]
 for f in sorted((ROOT/'labels/ai/codex__v2_r37').glob('r37_batch_*.jsonl')):
  for n,l in enumerate(open(f),1):
   if not l.strip():continue
   o=json.loads(l);uid=o['item_id']
   if uid in out:problems.append(f'duplicate {uid}')
   if uid not in inputs:problems.append(f'unknown {uid}');continue
   kb=key.loc[key.unit_id==uid,'batch']
   if kb.empty or kb.iloc[0]!=f.stem:problems.append(f'{uid} returned in {f.name}, key says {kb.tolist()}')
   for k,vals in CODES.items():
    if vals and not k.startswith('T'):
     v=s(o.get(k))
     if v and v not in vals:problems.append(f'{uid} {k}={v}')
   for t in o.get('topics') or []:
    if t not in TOPICS:problems.append(f'{uid} topic {t}')
   src=norm(inputs[uid]['text']);ctx=norm(inputs[uid].get('context'))
   for q in (o.get('evidence_quotes') or {}).values():
    if not q:continue
    ev[0]+=1;q=str(q);ev[1]+=norm(q[len('context: '):]) in ctx if q.startswith('context: ') else norm(q) in src
   out[uid]=record(o)
 missing=sorted(set(key.unit_id)-set(out))
 lab=pd.read_csv(ROOT/'labels/ai_corpus_labels.csv',dtype=str).set_index('coding_id')
 V={}
 for cid in items.coding_id:
  r=lab.loc[cid].to_dict();r['topics']=[t for t in TOPICS if s(r.get(t))=='1'];V[(cid,'O1')]=record(r)
 for u in key.itertuples():
  if u.unit_id in out:V[(u.coding_id,u.version)]=out[u.unit_id]
 qa=dict(units_expected=len(key),units_returned=len(out),missing=missing,n_problems=len(problems),problems=problems[:30],
  evidence_quotes=ev[0],evidence_verbatim=ev[1])
 return items,V,qa

def label(V,cid,ver,dim):
 r=V.get((cid,ver))
 if r is None:return None
 v=r[dim]
 if ver=='S' and dim in ('actor_1',):v=PARTY_BACK.get(v,v)
 return v

def flips(items,V):
 ids=items.coding_id.tolist();rng=np.random.default_rng(SEED);n=len(ids)
 draws=[np.bincount(rng.integers(0,n,n),minlength=n) for _ in range(B)]
 rows=[]
 for dim in DIMS:
  base=np.array([label(V,c,'O1',dim) for c in ids],object)
  F={v:np.array([float(label(V,c,v,dim)!=b) for c,b in zip(ids,base)]) for v in ['O2','S','F','M']}
  for v in ['O2','S','F','M']:
   r=dict(dimension=dim,version=v,n=n,flip_rate_vs_O1=F[v].mean(),flip_rate_vs_O2=np.mean([label(V,c,v,dim)!=label(V,c,'O2',dim) for c in ids]) if v!='O2' else np.nan)
   if v!='O2':
    d=F[v]-F['O2'];bs=np.array([np.dot(w,d)/n for w in draws])
    r.update(excess_flip=d.mean(),excess_lo=np.percentile(bs,2.5),excess_hi=np.percentile(bs,97.5),p_one_sided=float(np.mean(bs<=0)))
   rows.append(r)
 return pd.DataFrame(rows)

def score_tone(V,c,v):r=V.get((c,v));return TONE_SCORE.get(r['tone_overall'],np.nan) if r and r['relevant']!='no' else np.nan
def blame(V,c,v):r=V.get((c,v));return float(r['admin_attribution']=='blame') if r else np.nan

def boot_mean(x,rng):
 x=np.asarray(x,float);x=x[~np.isnan(x)];n=len(x)
 b=np.array([x[rng.integers(0,n,n)].mean() for _ in range(B)]);return x.mean(),np.percentile(b,2.5),np.percentile(b,97.5),n

def directional(items,V):
 rng=np.random.default_rng(SEED+1);rows=[]
 strata={'trump->biden':items[items.stratum=='trump'],'biden->trump':items[items.stratum=='biden'],
  'obama->trump':items[items.stratum=='obama'],'party swap only':items[items.stratum=='party']}
 for name,f in [('tone score',score_tone),('admin blame',blame)]:
  d={k:np.array([f(V,c,'S')-f(V,c,'O2') for c in g.coding_id]) for k,g in strata.items()}
  for k,x in d.items():
   m,lo,hi,n=boot_mean(x,rng);rows.append(dict(measure=name,contrast=f'S - O2, {k}',estimate=m,lo=lo,hi=hi,n=n))
  a,b=d['trump->biden'],d['biden->trump'];a=a[~np.isnan(a)];b=b[~np.isnan(b)]
  bs=np.array([a[rng.integers(0,len(a),len(a))].mean()-b[rng.integers(0,len(b),len(b))].mean() for _ in range(B)])
  rows.append(dict(measure=name,contrast='mean(S-O2 | trump->biden) - mean(S-O2 | biden->trump)',estimate=a.mean()-b.mean(),lo=np.percentile(bs,2.5),hi=np.percentile(bs,97.5),n=len(a)+len(b)))
  for k,(v1,v2) in {'F - M':('F','M'),'F - O2':('F','O2'),'M - O2':('M','O2')}.items():
   x=np.array([f(V,c,v1)-f(V,c,v2) for c in items.coding_id]);m,lo,hi,n=boot_mean(x,rng)
   rows.append(dict(measure=name,contrast=k+', all items',estimate=m,lo=lo,hi=hi,n=n))
 return pd.DataFrame(rows)

def main():
 items,V,qa=load()
 Fl=flips(items,V);Fl.to_csv(OUT/'flip_rates.csv',index=False)
 D=directional(items,V);D.to_csv(OUT/'directional.csv',index=False)
 long=pd.DataFrame([dict(coding_id=c,version=v,**r) for (c,v),r in V.items()]).merge(items[['coding_id','stratum','group','person_swap']],on='coding_id')
 long.to_csv(OUT/'labels_long.csv',index=False)
 (OUT/'qa.json').write_text(json.dumps(qa,indent=1,ensure_ascii=False))
 pd.set_option('display.width',250);print(json.dumps({k:v for k,v in qa.items() if k!='problems'}));print(qa['problems'][:10])
 print(Fl.round(3).to_string());print(D.round(3).to_string())

if __name__=='__main__':main()
