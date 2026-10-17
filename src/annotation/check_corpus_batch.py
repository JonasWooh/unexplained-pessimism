"""Check Codex outputs for corpus batches: completeness, allowed values, verbatim evidence.

usage: python check_corpus_batch.py <output_dir>   (files named like the inputs, e.g. corpus_batch_001.jsonl)
"""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from score_ai import load_run,ROOT

def main(out_dir):
 out_dir=Path(out_dir);rows=[]
 for inp in sorted((ROOT/'labels/ai_inputs').glob('corpus_batch_*.jsonl')):
  split=inp.stem
  if not list(out_dir.glob(f'{split}*.jsonl')):rows.append(dict(batch=split,status='not run'));continue
  out,inputs,problems,missing,ev=load_run(out_dir,split)
  rows.append(dict(batch=split,status='ok' if not problems and not missing else 'CHECK',returned=len(out),expected=len(inputs),missing=len(missing),problems=len(problems),
   evidence_verbatim=f"{ev['verbatim']}/{ev['quotes']}",first_problems=[p['problem'] for p in problems[:3]]))
 for r in rows:print(json.dumps(r,ensure_ascii=False))
 done=[r for r in rows if r['status']!='not run'];print(f"batches run {len(done)}/{len(rows)}; with issues {sum(r['status']=='CHECK' for r in done)}")

if __name__=='__main__':main(sys.argv[1])
