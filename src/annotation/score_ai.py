"""Validate and score LLM label files against the adjudicated gold standard (R3.4, R3.6).

usage: python score_ai.py <run_dir> <split> [<repeat_run_dir>]
 run_dir    labels/ai/<model_id>__<prompt_version>/   containing <split>*.jsonl output files
 split      dev | test
 repeat_run optional second run over (part of) the same items, for self-consistency
Gold relevant=unsure items are excluded from `relevant` metrics and counted separately (user decision 2026-10-16).
Other dimensions are scored on items both gold and AI coded (relevant in {yes, unsure}).
"""
import csv,json,re,sys,collections
from pathlib import Path
import pandas as pd
from sklearn.metrics import cohen_kappa_score,f1_score,precision_recall_fscore_support
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
from build_workbooks import CODES,TOPICS
DIMS=['tone_overall','fact_direction','emotional_intensity','price_frame','perspective','time_frame','numeric_claim','definition_error','actor_1','direction_1']
ALLOWED={k:v for k,v in CODES.items() if v and not k.startswith('T')}

def norm(s):return re.sub(r'\s+',' ',(s or '')).strip().lower()

def load_run(run,split):
 out={};problems=[]
 inputs={json.loads(l)['item_id']:json.loads(l) for l in open(ROOT/f'labels/ai_inputs/{split}.jsonl')}
 for f in sorted(Path(run).glob(f'{split}*.jsonl')):
  for n,line in enumerate(open(f),1):
   if not line.strip():continue
   try:o=json.loads(line)
   except ValueError:problems.append(dict(file=f.name,line=n,problem='invalid JSON'));continue
   iid=o.get('item_id')
   if iid not in inputs:problems.append(dict(file=f.name,line=n,problem=f'unknown item_id {iid}'));continue
   if iid in out:problems.append(dict(file=f.name,line=n,problem=f'duplicate item_id {iid}'))
   out[iid]=o
 for iid,o in out.items():
  for k,vals in ALLOWED.items():
   v=o.get(k);v='' if v is None else str(v)
   if v and v not in vals:problems.append(dict(file='',line='',problem=f'{iid} {k}={v} not allowed'))
  for t in o.get('topics') or []:
   if t not in TOPICS:problems.append(dict(file='',line='',problem=f'{iid} topic {t} not allowed'))
 missing=sorted(set(inputs)-set(out))
 # Evidence quotes must be verbatim (whitespace/case-normalized) substrings of the item text or context.
 ev_total=ev_ok=0
 for iid,o in out.items():
  src=norm(inputs[iid]['text']);ctx=norm(inputs[iid]['context'])
  for k,q in (o.get('evidence_quotes') or {}).items():
   if not q:continue
   ev_total+=1;q=str(q)
   ev_ok+=norm(q[len('context: '):]) in ctx if q.startswith('context: ') else norm(q) in src
 return out,inputs,problems,missing,dict(quotes=ev_total,verbatim=ev_ok)

def as_label(o,k):
 v=o.get(k);return '' if v is None else str(v)

def score(pairs,name,by):
 g=[a for a,_ in pairs];p=[b for _,b in pairs];labels=sorted(set(g)|set(p))
 P,R,F,S=precision_recall_fscore_support(g,p,labels=labels,zero_division=0)
 row=dict(dimension=name,group=by,n=len(pairs),accuracy=sum(a==b for a,b in pairs)/len(pairs) if pairs else None,
  cohen_kappa=cohen_kappa_score(g,p) if len(labels)>1 else None,macro_f1=f1_score(g,p,labels=labels,average='macro',zero_division=0) if pairs else None)
 per=[dict(dimension=name,group=by,label=l,precision=P[i],recall=R[i],f1=F[i],support=int(S[i])) for i,l in enumerate(labels)]
 return row,per

def main(run,split,repeat=None):
 run=Path(run);out,inputs,problems,missing,ev=load_run(run,split)
 gold=pd.read_csv(ROOT/'labels/adjudicated.csv',dtype=str).fillna('').set_index('item_id')
 key=pd.read_csv(ROOT/'labels/sample_key.csv',dtype=str).set_index('item_id')
 ids=[i for i in out if i in gold.index]
 rows=[];per=[]
 for by in ['all']+sorted(key.loc[ids,'source'].unique()):
  sel=[i for i in ids if by=='all' or key.at[i,'source']==by]
  rel=[(gold.at[i,'relevant'],as_label(out[i],'relevant')) for i in sel if gold.at[i,'relevant']!='unsure']
  r,p=score(rel,'relevant',by);r['gold_unsure_excluded']=sum(1 for i in sel if gold.at[i,'relevant']=='unsure');rows.append(r);per+=p
  both=[i for i in sel if gold.at[i,'relevant'] in ('yes','unsure') and as_label(out[i],'relevant') in ('yes','unsure')]
  for d in DIMS:
   r,p=score([(gold.at[i,d],as_label(out[i],d)) for i in both],d,by);rows.append(r);per+=p
  for t in TOPICS:
   r,p=score([(gold.at[i,t] or '0','1' if t in (out[i].get('topics') or []) else '0') for i in both],t,by);rows.append(r);per+=[x for x in p if x['label']=='1']
 res=ROOT/'results/ai_validation';res.mkdir(parents=True,exist_ok=True);tag=f'{run.name}_{split}'
 pd.DataFrame(rows).to_csv(res/f'{tag}_metrics.csv',index=False);pd.DataFrame(per).to_csv(res/f'{tag}_per_class.csv',index=False)
 summary=dict(run=run.name,split=split,items_expected=len(inputs),items_returned=len(out),missing=missing,problems=problems[:50],n_problems=len(problems),evidence=ev)
 if repeat:
  rep,_,_,_,_=load_run(Path(repeat),split);common=[i for i in rep if i in out]
  summary['self_consistency']={d:sum(as_label(out[i],d)==as_label(rep[i],d) for i in common)/len(common) for d in ['relevant']+DIMS} if common else {}
  summary['self_consistency_items']=len(common)
 (res/f'{tag}_summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False))
 print(json.dumps({k:v for k,v in summary.items() if k!='problems'},ensure_ascii=False));print(pd.DataFrame(rows)[lambda d:d.group=='all'][['dimension','n','accuracy','cohen_kappa','macro_f1']].round(3).to_string(index=False))

if __name__=='__main__':main(*sys.argv[1:])
