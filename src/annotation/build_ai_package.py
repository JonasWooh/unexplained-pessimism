"""Prompt v1 (codebook embedded verbatim) and blind JSONL inputs for LLM labeling via Codex.

Inputs carry only item_id, date, unit_type, context, text -- the same blind view the human annotators had.
"""
import csv,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PROMPTS=ROOT/'prompts';INP=ROOT/'labels/ai_inputs'
VERSION='v1'
TOPICS=['T01_layoffs_unemployment_up','T02_hiring_jobs_growth','T03_prices_rising','T04_inflation_easing','T05_economic_growth','T06_recession_risk','T07_interest_rates_borrowing','T08_housing_costs','T09_gas_prices','T10_food_prices','T11_tariffs_trade','T12_stock_market','T13_other']

HEADER="""# Labeling prompt {version}

You are labeling short texts about the US economy for a research project. Apply the codebook below exactly as written.
The codebook is in Chinese with English label values; the texts are in English.

## Procedure (mandatory)
1. Read each input item yourself and decide every label by applying the codebook to that item's `text`
   (use `context` only to understand a video comment; label the comment itself).
2. Do NOT write or run any code, keyword rules, regular expressions or heuristics that assign labels.
   Do NOT look up the items online. Each label must come from your own reading of the item.
3. Judge each item independently. Do not use any information about the source; none is given.
4. For every non-null label except `relevant`, give a verbatim evidence quote copied exactly from `text`
   (or from `context` for comments, prefixed with "context: "). Use "" only when the label is "none"/"no"/"no_fact"/"0"/"not_applicable".
5. If `relevant` is "no", set every other label to null and `evidence_quotes` to {{}}.

## Output format
Write exactly one JSON object per input item, one per line (JSONL), in the same order as the input, with these keys:

```json
{schema}
```

Allowed values:
{allowed}

---

# Codebook (verbatim)

"""

SCHEMA={'item_id':'<copied from input>','relevant':'yes|no|unsure','tone_overall':'...','fact_direction':'...','emotional_intensity':'0|1|2','topics':['T03_prices_rising','...'],
 'price_frame':'...','perspective':'...','time_frame':'...','numeric_claim':'yes|no','claim_text':'verbatim numeric statements separated by "; " or ""','definition_error':'...',
 'actor_1':'...','direction_1':'...','actor_2':'... or null','direction_2':'... or null','evidence_quotes':{'tone_overall':'...','fact_direction':'...','emotional_intensity':'...','topics':'...','price_frame':'...','perspective':'...','time_frame':'...','definition_error':'...','actor_1':'...','actor_2':'...'}}
ALLOWED={'relevant':'yes, no, unsure','tone_overall':'negative, neutral, positive, mixed','fact_direction':'bad, good, neutral, mixed, no_fact','emotional_intensity':'0, 1, 2',
 'topics':'list of: '+', '.join(TOPICS)+' (at least one; use T13_other if none fits)','price_frame':'level, rate, both, none','perspective':'national, household, both, none','time_frame':'current, forecast, both, none',
 'numeric_claim':'yes, no','definition_error':'yes, no, not_applicable','actor_1 / actor_2':'president_admin, congress, fed, democrats, republicans, business, foreign_trade, other, none (actor_2 may be null)',
 'direction_1 / direction_2':'credit, blame, neutral_mention (null when the actor is none or null)'}

def codebook_body():
 t=(ROOT/'annotation/codebook_v1.md').read_text()  # frozen original codebook the prompts were built from
 # Keep the labeling rules (sections 1-7); drop the human workflow (0), the column notes (8) and the change log (9).
 start=re.search(r'^## 1\. ',t,re.M).start();end=re.search(r'^## 8\. ',t,re.M).start()
 return t[start:end].rstrip()+'\n'

def main():
 PROMPTS.mkdir(exist_ok=True);INP.mkdir(parents=True,exist_ok=True)
 prompt=HEADER.format(version=VERSION,schema=json.dumps(SCHEMA,indent=1,ensure_ascii=False),allowed='\n'.join(f'- {k}: {v}' for k,v in ALLOWED.items()))+codebook_body()
 p=PROMPTS/f'label_prompt_{VERSION}.md';p.write_text(prompt)
 sha=hashlib.sha256(prompt.encode()).hexdigest();(PROMPTS/f'label_prompt_{VERSION}.sha256').write_text(f'{sha}  label_prompt_{VERSION}.md\n')
 rows=list(csv.DictReader(open(ROOT/'labels/sample_key.csv')))
 for split in ['dev','test']:
  with open(INP/f'{split}.jsonl','w') as f:
   for r in rows:
    if r['split']==split:f.write(json.dumps({k:r[k] for k in ['item_id','date','unit_type','context','text']},ensure_ascii=False)+'\n')
 print('prompt sha256',sha)

if __name__=='__main__':main()
