"""R3.7 counterfactual test package: name/party swap and source-label versions of already-coded corpus items.

Design (research design v0, decision D-F): 120 relevant corpus items that name a president or a party,
stratified by the named actor. The first original run (O1) is the existing corpus label; four new versions
are coded in separate batches by separate Codex agents with the frozen prompt v2:
  O2 original text again (run-to-run baseline), S names and parties swapped,
  F text prefixed with "[Source: Fox News]", M text prefixed with "[Source: MSNBC]".
Every coded unit gets a fresh opaque ID and each batch is shuffled, so no agent can link versions.
"""
import csv,glob,hashlib,json,random,re,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SEED=20261015
STRATA={'trump':40,'biden':30,'obama':25,'party':25}
PKG=ROOT/'codex_runs/R37_package'
PROMPT=ROOT/'prompts/label_prompt_v2.md'
PROMPT_SHA='9f95f20aa319fff0ecf6c4a29d2ab81bfcc9503d72a581ea64cc6a661b6e16bd'
DETECT={'trump':r'\btrump','biden':r'\bbiden','obama':r'\bobama','harris':r'\bharris\b','party':r'\b(republicans?|democrats?|democratic|gop)\b'}

def stratum(t):
 hits=[k for k,p in DETECT.items() if re.search(p,t,re.I)]
 if 'harris' in hits:return None   # Harris: no symmetric counterpart in the pool; excluded
 for k in ['trump','biden','obama','party']:
  if k in hits:return k
 return None

def case_like(src,rep):
 if src.isupper() and len(src)>1 and src!='GOP' and not src.startswith(('R-','D-')):return rep.upper()
 if src.islower():return rep.lower()
 return rep

# Ordered (pattern, replacement) pairs per person swap; applied simultaneously via one regex alternation.
PERSON={
 'trump_biden':[(r'Trumponomics','Bidenomics'),(r'Bidenomics','Trumponomics'),
   (r'Donald J\. Trump','Joseph R. Biden'),(r'Joseph R\. Biden(?: Jr\.)?','Donald J. Trump'),
   (r'Donald Trump','Joe Biden'),(r'Joe Biden','Donald Trump'),(r'Trump','Biden'),(r'Biden','Trump')],
 'obama_trump':[(r'Barack Obama','Donald Trump'),(r'Donald J\. Trump','Barack H. Obama'),(r'Donald Trump','Barack Obama'),
   (r'Obamacare','Trumpcare'),(r'Trump','Obama'),(r'Obama','Trump')]}
# Party words are matched case-sensitively: capitalised forms are party references; lowercase "democrat(s)" and
# "republican(s)" are party references in comments, but lowercase "democratic" is usually generic and is left alone.
PARTY=[(r'Republicans','Democrats'),(r'Democrats','Republicans'),(r'Republican(?=\s+[A-Za-z])','Democratic'),
 (r'Republican','Democrat'),(r'Democratic','Republican'),(r'Democrat','Republican'),(r'GOP','Democratic Party'),
 (r'republicans','democrats'),(r'democrats','republicans'),(r'republican','democrat'),(r'democrat','republican'),
 (r'\(R-','(D-'),(r'\(D-','(R-'),(r'\bR-(?=[A-Z][A-Za-z]*\.?[),\s])','D-'),(r'\bD-(?=[A-Z][A-Za-z]*\.?[),\s])','R-')]
PARTY=[(p,r,False) for p,r in PARTY]

def person_pairs(k):return [(p,r,True) for p,r in PERSON[k]]

def swap(text,pairs):
 if not text:return text,[]
 rx=re.compile('|'.join('(?P<g%d>%s%s%s)'%(i,'(?i:' if ci else '(?:','' if p.startswith(chr(92)) else chr(92)+'b',p+')') for i,(p,_,ci) in enumerate(pairs)))
 log=[]
 def rep(m):
  i=int(m.lastgroup[1:]);src=m.group(0);out=case_like(src,pairs[i][1]) if not src.startswith('(') else pairs[i][1]
  log.append(f'{src}->{out}');return out
 return rx.sub(rep,text),log

def main():
 items={}
 for f in sorted(glob.glob(str(ROOT/'labels/ai_inputs/corpus_batch_*.jsonl'))):
  for l in open(f):r=json.loads(l);items[r['item_id']]=r
 o1={}
 for f in sorted(glob.glob(str(ROOT/'labels/ai/codex__v2_isolated_r1_corpus/*.jsonl'))):
  for l in open(f):r=json.loads(l);o1[r['item_id']]=r
 key={r['coding_id']:r for r in csv.DictReader(open(ROOT/'labels/corpus_sample_key.csv'))}
 pool={k:[] for k in STRATA}
 for i,r in items.items():
  if o1.get(i,{}).get('relevant')!='yes':continue
  s=stratum(r['text']+' '+(r.get('context') or ''))
  if s:pool[s].append(i)
 rng=random.Random(SEED);chosen=[]
 for s,n in STRATA.items():
  for i in rng.sample(sorted(pool[s]),n):chosen.append((i,s))
 versions={'O2':[],'S':[],'F':[],'M':[]};keyrows=[]
 for i,s in chosen:
  r=items[i];person='trump_biden' if s in('trump','biden') else 'obama_trump' if s=='obama' else None
  pairs=(person_pairs(person) if person else [])+PARTY
  st,lt=swap(r['text'],pairs);sc,lc=swap(r.get('context') or '',pairs)
  base={k:r[k] for k in ['date','unit_type','context','text']}
  versions['O2'].append((i,dict(base)))
  versions['S'].append((i,dict(base,text=st,context=sc if r.get('context') else r.get('context'))))
  versions['F'].append((i,dict(base,text='[Source: Fox News] '+r['text'])))
  versions['M'].append((i,dict(base,text='[Source: MSNBC] '+r['text'])))
  keyrows.append({'coding_id':i,'stratum':s,'group':key[i]['group'],'source':key[i]['source'],'date':r['date'],'person_swap':person or '',
   'swaps_text':' | '.join(lt),'swaps_context':' | '.join(lc),'n_swaps':len(lt)+len(lc)})
 # fresh opaque IDs across all 480 units; batch order: O2,S,F,M shuffled into neutral file names
 ids=[f'X{n:04d}' for n in rng.sample(range(1,10000),480)]
 order=list(versions);rng.shuffle(order)
 (PKG/'inputs').mkdir(parents=True,exist_ok=True);(PKG/'prompts').mkdir(exist_ok=True)  # files are overwritten in place
 shutil.copy(PROMPT,PKG/'prompts/label_prompt_v2.md')
 assert hashlib.sha256((PKG/'prompts/label_prompt_v2.md').read_bytes()).hexdigest()==PROMPT_SHA
 unit_key=[];k=0
 for b,v in enumerate(order,1):
  rows=versions[v][:];rng.shuffle(rows)
  with open(PKG/f'inputs/r37_batch_{b}.jsonl','w') as f:
   for i,rec in rows:
    uid=ids[k];k+=1
    f.write(json.dumps(dict(item_id=uid,**rec),ensure_ascii=False)+'\n')
    unit_key.append({'unit_id':uid,'batch':f'r37_batch_{b}','version':v,'coding_id':i})
 out=ROOT/'labels/r37';out.mkdir(exist_ok=True)
 for name,rows in [('r37_items.csv',keyrows),('r37_unit_key_DO_NOT_GIVE_CODEX.csv',unit_key)]:
  with open(out/name,'w',newline='') as f:
   w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 # review file: original vs swapped text for every item
 with open(out/'r37_swap_review.md','w') as f:
  for (i,s),(_,o),(_,sw) in zip(chosen,versions['O2'],versions['S']):
   f.write(f'## {i} [{s}]\n- O: {o["text"]}\n- S: {sw["text"]}\n'+(f'- O ctx: {o["context"]}\n- S ctx: {sw["context"]}\n' if o.get('context') else '')+'\n')
 print('pool sizes',{s:len(v) for s,v in pool.items()},'chosen',len(chosen),'batch order',order)
 print('items with zero swaps',sum(1 for r in keyrows if r['n_swaps']==0))

if __name__=='__main__':main()
