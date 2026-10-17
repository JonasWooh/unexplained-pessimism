"""Gold-standard labels: A/B agreement, adjudicated `final` value wherever A and B differ."""
import csv,json,collections
from pathlib import Path
import openpyxl
import sys;sys.path.insert(0,str(Path(__file__).parent))
from build_workbooks import CODES
from agreement import load,invalid
ANN=Path(__file__).resolve().parents[2]/'annotation'

def norm(v):
 if v is None or str(v).strip()=='__BLANK__':return ''
 if isinstance(v,float) and v.is_integer():v=int(v)
 return str(v).strip()

def main():
 key={r['item_id']:r for r in csv.DictReader(open(ANN/'sample_key_DO_NOT_SHOW_ANNOTATORS.csv'))}
 ws=openpyxl.load_workbook(ANN/'agreement/adjudication_disagreements.xlsx',read_only=True)['adjudication']
 rows=list(ws.iter_rows(values_only=True));h=rows[0]
 final={};stats=collections.Counter()
 for r in rows[1:]:
  d=dict(zip(h,r));f=norm(d['final'])
  if d['final'] in (None,''):raise ValueError(f"final missing: {d['item_id']} {d['column']}")
  if not str(d['reason'] or '').strip():raise ValueError(f"reason missing: {d['item_id']} {d['column']}")
  final[(d['sheet'],d['item_id'],d['column'])]=(f,str(d['reason']).strip())
  stats['final=A' if f==norm(d['A']) else 'final=B' if f==norm(d['B']) else 'final=neither']+=1
 cols=list(CODES)
 out={};adj_reasons=[]
 for sheet in ['calibration','main']:
  A,B=load('A',sheet),load('B',sheet);G={}
  for iid in A:
   g={}
   for c in cols:
    if c=='notes':continue
    if c=='claim_text':
     # Free text, not adjudicated: union of both annotators' claims (split on ';', order kept, exact duplicates dropped).
     parts=[x.strip() for t in (A[iid].get(c,''),B[iid].get(c,'')) for x in t.split(';') if x.strip()]
     g[c]='; '.join(dict.fromkeys(parts));continue
    if (sheet,iid,c) in final:g[c]=final[(sheet,iid,c)][0]
    elif A[iid].get(c,'')==B[iid].get(c,''):g[c]=A[iid].get(c,'')
    else:raise ValueError(f'unadjudicated difference {sheet} {iid} {c}')
   g['notes']='';G[iid]=g
  for g in G.values():
   if g['numeric_claim']!='yes':g['claim_text']=''
  bad=invalid(G,'gold',sheet)
  if bad:raise ValueError(f'gold inconsistencies: {bad[:5]}')
  out[sheet]=G
 meta=['item_id','split','stratum','tier','source','period','date','source_item_id','weight','unit_type']
 for sheet,fname in [('main','gold_standard_v1.csv'),('calibration','gold_calibration_v1.csv')]:
  with open(ANN/fname,'w',newline='') as f:
   w=csv.DictWriter(f,fieldnames=meta+[c for c in cols if c not in ('notes','claim_text')]+['claim_text']);w.writeheader()
   for iid in sorted(out[sheet]):w.writerow({**{m:key[iid][m] for m in meta},**{c:v for c,v in out[sheet][iid].items() if c!='notes'}})
 rel=collections.Counter(g['relevant'] for g in out['main'].values())
 summ=dict(adjudicated_cells=len(final),**stats,main_items=len(out['main']),main_relevant=dict(rel),files=['gold_standard_v1.csv','gold_calibration_v1.csv'])
 (ANN/'agreement/gold_overview.json').write_text(json.dumps(summ,indent=2,ensure_ascii=False));print(json.dumps(summ,ensure_ascii=False))

if __name__=='__main__':main()
