"""Stratified random sample of corpus items for LLM coding, written as blind JSONL batches of 200.

Frame: corpus/items.parquet content units (not is_duplicate, not is_repost, not is_ad, not is_obituary).
Strata (source group x month), seed 20261015, simple random sampling without replacement:
 national  NYT + Guardian pooled          40 per month, 2010-01..2026-10 (user 2026-10-16T06:31Z; was 20)
 mc_national Media Cloud US National      20 per month (sampled months only)
 local     Media Cloud US State & Local   40 per month (sampled months only)
 reddit    Reddit, all subreddits pooled  10 per month, 2015-01..2026-10
 youtube   YouTube window comments        20 per month, 2023-01..2026-10
Months with fewer units than the target take all units. Final weight = first-stage design weight x
(stratum frame size / stratum sample size); YouTube has no design weight (non-probability), so its
weight is left blank and only the within-month expansion factor is recorded.
Batch item ids are opaque (K00001...) so the model sees no source information.
"""
import json,random
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'labels/ai_inputs'
SEED=20261015;BATCH=200
GROUPS=[('national',lambda d:d.source.isin(['NYT','Guardian']),40,'2010-01'),('mc_national',lambda d:d.source=='MediaCloud_National',20,'2010-01'),
 ('local',lambda d:d.source=='MediaCloud_Local',40,'2010-01'),('reddit',lambda d:d.source=='Reddit',10,'2015-01'),('youtube',lambda d:d.source=='YouTube',20,'2023-01')]
# Unit text and labels identical to the human-annotation sample (src/annotation/build_sample.py).
UNIT={'headline_abstract_lead':'headline + abstract + lead paragraph','headline_abstract':'headline + abstract','full_text':'headline + standfirst + first 100 body words','headline':'headline only','post':'forum post (title + body, first 1,200 chars)','comment':'video comment (top-level)'}

def unit_text(r):
 if r.unit_type=='full_text':
  stand,body=r.text.split('\n',1);w=body.split()
  return '\n'.join(x for x in [r.title,stand,' '.join(w[:100])+(' [...]' if len(w)>100 else '')] if x)
 if r.unit_type=='post':
  full=r.title+('\n'+r.text if r.text else '');return full[:1200]+(' [...]' if len(full)>1200 else '')
 if r.unit_type=='comment':return r.text
 return '\n'.join(x for x in [r.title,r.text] if x)

def main():
 d=pd.read_parquet(ROOT/'corpus/items.parquet')
 d=d[~d.is_duplicate&~d.is_repost&~d.is_ad&~d.is_obituary].sort_values('item_id').reset_index(drop=True)
 rng=random.Random(SEED);picked=[];frames=[]
 for name,sel,n,start in GROUPS:
  g=d[sel(d)&(d.month>=start)]
  for m,x in sorted(g.groupby('month'),key=lambda t:t[0]):
   ids=list(x.item_id);k=min(n,len(ids));take=set(rng.sample(ids,k))
   frames.append(dict(group=name,month=m,frame_size=len(ids),sample_size=k))
   for _,r in x[x.item_id.isin(take)].iterrows():
    w1=r.sample_weight;exp=len(ids)/k
    picked.append(dict(group=name,month=m,item_id=r.item_id,source=r.source,frame_size=len(ids),sample_size=k,expansion=exp,design_weight=w1,final_weight=None if pd.isna(w1) else w1*exp,
     date=str(r.pub_datetime_utc)[:10],unit_type=UNIT[r.unit_type],context=('Video title: '+r.video_title) if r.source=='YouTube' else '',
     text=unit_text(r)))
 rng.shuffle(picked)
 for i,p in enumerate(picked,1):p['coding_id']=f'K{i:05}'
 key=pd.DataFrame(picked);OUT.mkdir(parents=True,exist_ok=True)
 key.drop(columns=['text','context']).to_csv(ROOT/'labels/corpus_sample_key.csv',index=False)
 pd.DataFrame(frames).to_csv(ROOT/'labels/corpus_sample_frames.csv',index=False)
 for b in range(0,len(picked),BATCH):
  with open(OUT/f'corpus_batch_{b//BATCH+1:03}.jsonl','w') as f:
   for p in picked[b:b+BATCH]:f.write(json.dumps(dict(item_id=p['coding_id'],date=p['date'],unit_type=p['unit_type'],context=p['context'],text=p['text']),ensure_ascii=False)+'\n')
 print(key.group.value_counts().to_dict(),len(picked),'batches',(len(picked)+BATCH-1)//BATCH)

if __name__=='__main__':main()
