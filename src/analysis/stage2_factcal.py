"""Stage 2: factual calibration of numeric claims (the fourth measurement dimension).

Rule-based extraction from the LLM's verbatim `claim_text` (labels/ai_corpus_labels.csv, relevant = yes),
compared with the ALFRED vintage valid on the item's publication date. Indicators:
- unemployment rate (UNRATE, percent);
- inflation: CPI (CPIAUCSL) when the fragment names CPI or consumer prices, PCE (PCEPI) when it names PCE,
  either one when it just says "inflation" (the claim is correct if it matches either official measure);
  12-month change by default, 1-month change when the fragment says so or reports a sub-1.5 change of
  "consumer prices" without a yearly reference;
- real GDP growth (GDPC1): quarterly change at an annual rate, or the same quarter not annualized (both are
  published conventions), or the 4-quarter change when the fragment says "from a year earlier";
- nonfarm payroll change (PAYEMS), thousands.
The reference period is the month or quarter named in the fragment, otherwise the latest observation in the
vintage. The number used is the one after "to" in "from X to Y" phrasing, otherwise the first number.
Fragments are not scored ("excluded") when the fragment or the 120 characters of unit text before it point to
a forecast or hypothetical, another place or group (US states, cities, demographic groups, other countries),
another period (a named year before the previous one, "since", "under/during" an administration,
cumulative or average figures), or a measure that was not pulled (core, underlying, expectations, wages,
breakeven, sector payrolls, private payrolls).
Inflation figures must name the measure (CPI / consumer prices / consumer inflation, or PCE); a bare "inflation" figure
is unverifiable (revised after the 30-claim manual parse check). For description only, such claims are compared
with every admissible reading (CPI or PCE, 12-month or 1-month change) and flagged when no reading matches.
An unemployment-rate number after a change verb without "to" ("fell 4%") is unverifiable (level not stated).
A month introduced as the comparison period ("compared to March", "from December") is not the reference month.
Inequality claims ("above", "below", "more than", "at least", ...) are correct when the official value
satisfies the inequality, allowing the same tolerance.
Categories: correct (|claim - official| <= 0.1 point; payrolls <= 1,000 jobs), correct within rounding
(official value rounded to the claim's precision equals the claim, or an approximate word and a difference
of at most one unit of the last digit), wrong, unverifiable (reference period missing from the vintage).
Known limitation: CPIAUCSL is seasonally adjusted, press reports usually quote the unadjusted 12-month change;
CPI 12-month claims are also reported with a 0.2-point tolerance.
Outputs: results/stage2_factcal/ (claims.csv, fragment_status.csv, summary.csv, review_sample_30.csv).
"""
import json,re,sys
import numpy as np
import pandas as pd
from lib import ROOT,SEED
sys.path.insert(0,str(ROOT/'src/annotation'))
from build_corpus_sample import unit_text

OUT=ROOT/'results/stage2_factcal';OUT.mkdir(parents=True,exist_ok=True)
MONTHS={m:i for i,m in enumerate(['january','february','march','april','may','june','july','august','september','october','november','december'],1)}
MRX=r'(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sept?|oct|nov|dec)\.?'
NUM=r'(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)'
PCT=NUM+r'\s?(?:%|percent|per cent|pct)'
STATES='alabama|alaska|arizona|arkansas|california|colorado|connecticut|delaware|florida|georgia|hawaii|idaho|illinois|indiana|iowa|kansas|kentucky|louisiana|maine|maryland|massachusetts|michigan|minnesota|mississippi|missouri|montana|nebraska|nevada|new hampshire|new jersey|new mexico|new york state|north carolina|north dakota|ohio|oklahoma|oregon|pennsylvania|rhode island|south carolina|south dakota|tennessee|texas|utah|vermont|virginia|washington state|west virginia|wisconsin|wyoming|puerto rico'
FORECAST=re.compile(r"\b(expect\w*|forecast\w*|project\w*|predict\w*|could|would|will|might|may|estimate[sd]? to|to (grow|rise|fall|reach|hit)|target|goal|if|should|aim\w*|outlook|thought to be|seen at|results? in)\b",re.I)
PLACE=re.compile(r"\bcompared (to|with) the (u\.?s\.?|national|nation\w*)\b|\b(city|city's|cities|county|counties|local|statewide|state's|metro\w*|region\w*|"+STATES+r")\b|\b(youth|teen\w*|black|white|hispanic|latino|asian|women|men|veterans|college|graduates|workers aged|immigrants?|tribes?|tribal|reservations?|native americans?|rural|disabled|disabilit\w*)\b|\b(uk|u\.k\.|britain|british|england|eurozone|euro area|europe\w*|china|chinese|japan\w*|germany|german|canada|canadian|mexic\w*|india|global|world|argentin\w*|turkey|venezuela\w*)\b",re.I)
PERIOD=re.compile(r"\b(since|(under|during) (president|the|his|her|their|trump|biden|obama|bush)|averag\w*|cumulative\w*|lifetime|decades?|in (19|20)\d\d|took office|era|presidency|first term|last time|for (a |only |the past |the last )?(few|one|two|three|four|five|\d+) years|this year|for the year|per month|each month)\b|\b(trump|biden|obama|bush|carter|reagan)('s)?\b",re.I)
MEASURE_X=re.compile(r"\b(core|underlying|excluding|expectations?|wages?|earnings|breakeven|real (inflation|unemployment)|true (inflation|unemployment)|u-?6|manufacturing|construction|retail|private[- ]sector|private payrolls|government jobs|health care|leisure|hospitality|of gdp|share of|debt|deficit|adjusted for inflation|than inflation|including inflation|mortgage|rates? (to|at)|interest|adjust\w* for inflation|food|grocer\w*|housing|rents?|shelter|gas|energy|medical|tuition|insurance|really|artificial\w*|studies show|% of|revis\w*|industry|sector|services|federal|business(es)?|compan(y|ies)|firm|employees|work ?force|small business\w*|(off|shave\w*|knock\w*|boost\w*) (\S+ ){0,3}(gdp|growth))\b",re.I)
INEQ=re.compile(r"(?<![-\w])(above|below|over|under|more than|less than|at least|at most|higher than|lower than|exceed\w*|nearly|almost|just under|just over)(?![-\w])",re.I)
APPROX=re.compile(r'\b(about|nearly|almost|roughly|around|approximately|close to|some|~)\b|~',re.I)

class Vint:
 def __init__(self,sid,ds):
  self.r=[x for f in sorted((ROOT/'data/raw'/ds).glob(f'*/{sid}_observations_*.json')) for x in json.loads(f.read_text())['observations']]
 def at(self,day):return {x['date']:float(x['value']) for x in self.r if x['realtime_start']<=day<=x['realtime_end'] and x['value']!='.'}
V={'UNRATE':Vint('UNRATE','M19'),'CPI':Vint('CPIAUCSL','M18'),'PCE':Vint('PCEPI','M19'),'GDP':Vint('GDPC1','M19'),'PAYEMS':Vint('PAYEMS','M18')}

def shift(d,k):y,m=int(d[:4]),int(d[5:7]);n=y*12+m-1+k;return f'{n//12:04}-{n%12+1:02}-01'
def num(s):return float(s.replace(',',''))
def decimals(s):s=s.replace(',','').lstrip('-');return len(s.split('.')[1]) if '.' in s else 0

def ref_month(frag,pub):
 # a month introduced as the comparison period ('compared to March', 'from December') is not the reference period
 m=next((x for x in re.finditer(r'\b'+MRX+r'\b(?:\s+(\d{4}))?',frag,re.I)
   if not re.search(r'\b(compared (to|with)|from|than|vs\.?|versus|since)\s+(the end of |late |early |mid-?)?$',frag[:x.start()],re.I)),None)
 if not m:return None
 w=m.group(1).lower();mo=MONTHS.get(w) or {k[:3]:v for k,v in MONTHS.items()}[w[:3]];y=int(m.group(2)) if m.group(2) else int(pub[:4])
 if not m.group(2) and re.search(r'\blast year\b',frag,re.I):y=int(pub[:4])-1
 elif not m.group(2) and (y,mo)>(int(pub[:4]),int(pub[5:7])):y-=1
 return f'{y:04}-{mo:02}-01'
def ref_quarter(frag,pub):
 """First quarter mentioned in the fragment; a bare quarter is the latest one starting before publication."""
 rx=r'\b(?:(first|second|third|fourth|1st|2nd|3rd|4th)[- ]quarter(?: of (\d{4}))?|(?:last|final)[- ]quarter of (\d{4}))\b|\bq([1-4])(?:\s+(\d{4}))?\b|\b(first|last) three months\b|\b(start|beginning) of (?:the|this) year\b'
 m=re.search(rx,frag,re.I)
 if not m:return None
 if m.group(7):q,yr=1,None
 elif m.group(6):q,yr=(1 if m.group(6).lower()=='first' else 4),None
 elif m.group(3):q,yr=4,m.group(3)
 elif m.group(4):q,yr=int(m.group(4)),m.group(5)
 else:q,yr={'first':1,'second':2,'third':3,'fourth':4,'1st':1,'2nd':2,'3rd':3,'4th':4}[m.group(1).lower()],m.group(2)
 if yr:return f'{int(yr):04}-{3*q-2:02}-01'
 y=int(pub[:4]);d=f'{y:04}-{3*q-2:02}-01'
 return d if d<pub[:8]+'01' else f'{y-1:04}-{3*q-2:02}-01'

def pick_number(frag,rx):
 """The number after 'to' in 'from X to Y', else the first match of rx."""
 m=re.search(r'\bfrom\s+'+NUM+r'\s?(?:%|percent)?\s+to\s+'+NUM,frag,re.I)
 if m:return m.group(2)
 m=re.search(rx,frag,re.I);return m.group(1) if m else None

def judge(cs,off,tol,approx,ineq):
 c=num(cs)
 if ineq:
  w=ineq.lower()
  if w in ('nearly','almost','just under'):return 'correct' if c-1-tol<=off<=c+tol else 'wrong'
  if w=='just over':return 'correct' if c-tol<=off<=c+1+tol else 'wrong'
  up=w in ('above','over','more than','at least','higher than') or w.startswith('exceed')
  return 'correct' if (off>=c-tol if up else off<=c+tol) else 'wrong'
 if abs(c-off)<=tol+1e-9:return 'correct'
 dec=decimals(cs);step=10**-dec
 if round(off,dec)==round(c,dec) or (approx and abs(c-off)<=step+1e-9):return 'correct_within_rounding'
 return 'wrong'

def judge_payroll(c,off,approx,ineq):
 if ineq:return judge(f'{c}',off,1.0,approx,ineq)
 if abs(c-off)<=1.0:return 'correct'
 for step in (10,100,1000):
  if round(c/step)*step==c and (round(off/step)*step==c or (approx and abs(c-off)<=step)):return 'correct_within_rounding'
 return 'wrong'

def context_before(unit,frag,n=120):
 u=re.sub(r'\s+',' ',unit).lower();f=re.sub(r'\s+',' ',frag).lower();i=u.find(f)
 return u[max(0,i-n):i] if i>=0 else ''

def sentence_before(unit,frag,n=400):
 """The part of the fragment's own sentence that precedes it in the unit text (time, place and modality
 qualifiers often sit there, e.g. 'During the Bush years, ... the economy added 110,000 jobs')."""
 c=context_before(unit,frag,n);b=max(c.rfind('. '),c.rfind('! '),c.rfind('? '),c.rfind('\n'))
 return c[b+1:] if b>=0 else c

def extract(frag,pub,unit,group):
 """Return (list of claim dicts, status). A fragment can carry several indicators."""
 sent=sentence_before(unit,frag);low=frag.lower();both=sent+' '+low
 wide=context_before(unit,frag)+' '+low  # place often set by an earlier sentence ('DENVER — ... The unemployment rate is below 3 percent')
 if not re.search(r'\d',frag):return [],'no_indicator'
 kinds=[]
 if re.search(r'\b(unemployment|jobless) rate\b',low):kinds.append('unemployment_rate')
 if re.search(r'\b(inflation|consumer price index|cpi|consumer prices|pce price|personal consumption expenditures? price)\b',low):kinds.append('inflation')
 if re.search(r'\b(gdp|gross domestic product|economy (grew|expanded|contracted|shrank|grow|expand))\b',low):kinds.append('gdp_growth')
 if re.search(r'\b(jobs|payrolls?|positions)\b',low) and re.search(r'\b(added|add|adds|gained|gain|created|lost|shed|cut|increase|rose|grew|loss|decline)\b',low) \
  and re.search(r'\b(economy|employers|payrolls?|nonfarm|non-farm|labor department|jobs report|u\.s\.|us|nation|american)\b',low):kinds.append('payroll_change')
 if not kinds:return [],'no_indicator'
 for name,rx,text in [('forecast',FORECAST,both),('place_or_group',PLACE,wide),('other_period',PERIOD,both),('other_measure',MEASURE_X,low)]:
  if rx.search(text):return [],f'excluded_{name}'
 if group=='local' and not re.search(r'\b(u\.s\.|us|national|nation\'?s?|american)\b',low):return [],'excluded_place_or_group'
 yrs=[int(y) for y in re.findall(r'\b(19\d\d|20\d\d)\b',low)]
 if any(y<int(pub[:4])-1 for y in yrs):return [],'excluded_other_period'
 approx=bool(APPROX.search(low));iq=INEQ.search(low);ineq=iq.group(1) if iq else None
 def near(cue):
  for rx in (cue+r'[^;%]{0,45}?'+PCT,PCT+r'[^;]{0,25}?'+cue):
   for m in re.finditer(rx,frag,re.I):
    num_s=[g for g in m.groups() if g][-1] if rx.startswith(cue) else m.group(1)
    if not re.match(r'\s?(?:%|percent|per cent|pct)\s+(unemployment|jobless|gdp|growth)\b',frag[frag.find(num_s,m.start())+len(num_s):],re.I):
     fm=re.search(r'\bfrom\s+'+NUM+r'\s?(?:%|percent)?\s+to\s+'+NUM,frag,re.I)
     return fm.group(2) if fm else num_s
  return None
 out=[]
 if 'unemployment_rate' in kinds:
  cs=near(r'\b(?:unemployment|jobless) rate\b')
  if cs:
   v=V['UNRATE'].at(pub);r=ref_month(frag,pub) or (max(v) if v else None)
   # 'the rate fell 4%' (no 'to') or 'fell by 0.1' does not state the level; it may be a change in points or in percent
   amb=re.search(r'\b(fell|fall|falls|dropped|drops|declined|declines|rose|rises|increased|increases|climbed|jumped|edged \w+|ticked \w+|went \w+)\s+(?:\w+ly\s+)?(?:by\s+)?'+re.escape(cs)+r'\s?(?:%|percent|per cent|pct|points?|percentage)',frag,re.I)
   out.append(dict(indicator='unemployment_rate',measure='level',claim=cs,ref=r,official=None if amb else v.get(r),matched='UNRATE',tol=0.1,
    why='level ambiguous (change verb without "to")' if amb else None))
 if 'inflation' in kinds:
  cue=r'\b(?:inflation|consumer price index|cpi|consumer prices|pce|prices)\b'
  yoy_cs=pick_number(frag,PCT+r'\s*(?:from|over|compared with|than) (?:a|the) year (?:earlier|ago|before)') or pick_number(frag,PCT+r'\s*(?:year[- ]over[- ]year|annual|on an annual basis|over the (?:past|last) (?:year|12 months))')
  cs=near(cue)
  claims=[]
  if yoy_cs:claims.append((yoy_cs,False))
  if cs and cs!=yoy_cs:
   monthly=bool(re.search(r'\b(from|over) (the previous|a|the prior|last) month\b|\bmonth[- ]over[- ]month\b|\bmonthly\b|\bon the month\b|\bfrom '+MRX+r'\b',low)) or \
    (num(cs)<1.5 and re.search(r'\bconsumer prices\b|\bcpi\b|\bconsumer price index\b',low) is not None) or yoy_cs is not None
   claims.append((cs,monthly))
  # The measure must be named: a bare 'inflation' figure is not attributed to CPI or PCE by closeness or by date.
  sers=['PCE'] if re.search(r'\bpce\b|personal consumption',low) else ['CPI'] if re.search(r'\bcpi\b|consumer price|consumer inflation',low) else []
  for cs,monthly in claims:
   if monthly and re.search(r'\b(fell|fall|falls|declin\w*|dropped|drops)\b[^;%]{0,25}'+re.escape(cs),low):cs='-'+cs
   if not sers:
    # Not scored. For description only: the official values under every admissible reading
    # (CPI or PCE, 12-month or 1-month change, stated month or else the latest month in the vintage).
    alts=[]
    for s_ in ('CPI','PCE'):
     v=V[s_].at(pub);r=ref_month(frag,pub) or (max(v) if v else None)
     for k in (-12,-1):
      if r in v and shift(r,k) in v:alts.append((100*(v[r]/v[shift(r,k)]-1),0.2 if (s_,k)==('CPI',-12) else 0.1))  # CPI 12-month: SA vs NSA, see docstring
    out.append(dict(indicator='inflation',measure='unnamed',claim=cs,ref=ref_month(frag,pub),official=None,matched=None,tol=0.1,why='measure not named (CPI or PCE)',alts=alts))
    continue
   s=sers[0];v=V[s].at(pub);r=ref_month(frag,pub) or (max(v) if v else None);off=None
   if r in v:
    b=shift(r,-1 if monthly else -12);off=100*(v[r]/v[b]-1) if b in v else None
   out.append(dict(indicator='inflation',measure='1-month change' if monthly else '12-month change',claim=cs,ref=r,official=off,matched=s,tol=0.1))
 if 'gdp_growth' in kinds:
  cs=near(r'\b(?:gdp|gross domestic product|economy|growth|grew|expanded|contracted|shrank)\b')
  if cs:
   if re.search(r'\b(contract\w*|shr[ai]nk\w*|fell|declin\w*|negative)\b',low):cs='-'+cs
   v=V['GDP'].at(pub);q=ref_quarter(frag,pub) or (max(v) if v else None)
   yoy=bool(re.search(r'\b(from|than) a year (earlier|ago|before)\b|\byear[- ]over[- ]year\b',low));off=None;matched=None
   # GDP growth is quoted on several bases (q/q annualized, q/q, 4-quarter, calendar year); without a quarter or
   # rate cue the base is undetermined and the claim is not verifiable.
   based=yoy or ref_quarter(frag,pub) or re.search(r'\b(annual(ized)? (rate|pace)|annualized|quarter\w*|pace)\b',low)
   if q in v and based:
    if yoy and shift(q,-12) in v:off=100*(v[q]/v[shift(q,-12)]-1);matched='4-quarter'
    elif shift(q,-3) in v:
     ann=100*((v[q]/v[shift(q,-3)])**4-1);qq=100*(v[q]/v[shift(q,-3)]-1)
     off,matched=(ann,'q/q annualized') if abs(num(cs)-ann)<=abs(num(cs)-qq) else (qq,'q/q not annualized')
   out.append(dict(indicator='gdp_growth',measure='4-quarter change' if yoy else 'quarterly change',claim=cs,ref=q,official=off,matched=matched,tol=0.1))
 if 'payroll_change' in kinds:
  m=re.search(r'\b(added|add|adds|gained|created|lost|shed|cut|rose by|grew by|increased by)\s+(?:just |only |about |nearly |almost |roughly |around |some |more than |over )?'+NUM+r'(\s*million|\s*m\b|\s*k\b)?\s*(?:new\s+)?(?:jobs|positions|workers)?',frag,re.I) or \
    re.search(r'\b(gain|increase|loss|decline|rise) of\s+(?:just |only |about |nearly |almost |roughly |around |some |more than |over )?'+NUM+r'(\s*million|\s*m\b)?',frag,re.I) or \
    re.search(r'()'+NUM+r'(\s*million|\s*m\b|\s*k\b)?\s*(?:new\s+)?(?:jobs|positions)\s+(?:were\s+)?(?:added|created|gained|lost)',frag,re.I)
  if m:
   n=num(m.group(2));suf=(m.group(3) or '').strip().lower();ck=n*1000 if suf in ('million','m') else n if suf=='k' else n/1000
   if re.search(r'\b(lost|shed|cut|loss|decline)\b',(m.group(1) or '')+' '+frag[m.end():m.end()+12],re.I):ck=-ck
   v=V['PAYEMS'].at(pub);r=ref_month(frag,pub) or (max(v) if v else None)
   off=v[r]-v[shift(r,-1)] if r in v and shift(r,-1) in v else None
   out.append(dict(indicator='payroll_change',measure='1-month change, thousands',claim=f'{ck:.3f}',ref=r,official=off,matched='PAYEMS',tol=1.0))
 for o in out:o.setdefault('why',None);o.update(approx=approx,ineq=ineq)
 return out,'ok' if out else 'no_number'

def main():
 lab=pd.read_csv(ROOT/'labels/ai_corpus_labels.csv')
 items=pd.read_parquet(ROOT/'corpus/items.parquet',columns=['item_id','unit_type','title','text'])
 d=lab[(lab.relevant=='yes')&lab.claim_text.notna()].merge(items,on='item_id',suffixes=('','_c'))
 d['unit']=[unit_text(r) for r in d[['unit_type_c','title','text']].rename(columns={'unit_type_c':'unit_type'}).itertuples(index=False)]
 rows=[];status=[]
 for r in d.itertuples():
  for frag in [f.strip() for f in str(r.claim_text).split(';') if f.strip()]:
   res,st=extract(frag,r.date,r.unit,r.group);status.append(dict(group=r.group,status=st))
   for o in res:
    if o['official'] is None:cat='unverifiable'
    elif o['indicator']=='payroll_change':cat=judge_payroll(float(o['claim']),o['official'],o['approx'],o['ineq'])
    else:cat=judge(o['claim'],o['official'],o['tol'],o['approx'],o['ineq'])
    row=dict(coding_id=r.coding_id,item_id=r.item_id,group=r.group,source=r.source,date=r.date,month=r.month,fragment=frag,indicator=o['indicator'],measure=o['measure'],
     official_series=o['matched'],claim_value=float(o['claim']),inequality=o['ineq'] or '',approx_word=o['approx'],reference_period=o['ref'],official_value_at_pub=o['official'],category=cat,
     unverifiable_reason=o['why'] or ('reference period not in vintage or basis undetermined' if cat=='unverifiable' else ''),
     unnamed_any_reading=('' if 'alts' not in o else 'no official value available' if not o['alts'] else
      'consistent with at least one reading' if any(judge(o['claim'],a,t,o['approx'],o['ineq'])!='wrong' for a,t in o['alts']) else 'inconsistent with every reading'))
    row['category_cpi_tol02']=('correct' if o['official'] is not None and not o['ineq'] and abs(float(o['claim'])-o['official'])<=0.2+1e-9 else cat) if o['matched']=='CPI' and o['measure']=='12-month change' else cat
    rows.append(row)
 C=pd.DataFrame(rows);C.to_csv(OUT/'claims.csv',index=False)
 S=pd.DataFrame(status).value_counts().rename('fragments').reset_index().sort_values(['group','status']);S.to_csv(OUT/'fragment_status.csv',index=False)
 C['period']=pd.cut(C.month.str[:4].astype(int),[2009,2019,2022,2024,2026],labels=['2010-2019','2020-2022','2023-2024','2025-2026']).astype(str)
 C['source_type']=np.where(C.group.isin(['national','mc_national']),'national news',np.where(C.group=='local','local news','social media'))
 tabs=[]
 for cat in ['category','category_cpi_tol02']:
  for by in [['indicator'],['source_type'],['period'],['source_type','period'],['indicator','source_type']]:
   t=C.groupby(by)[cat].value_counts().unstack(fill_value=0)
   for k in ['correct','correct_within_rounding','wrong','unverifiable']:
    if k not in t:t[k]=0
   t['verifiable']=t[['correct','correct_within_rounding','wrong']].sum(axis=1);t['error_rate']=t.wrong/t.verifiable
   t=t.reset_index();t.insert(0,'by','+'.join(by));t.insert(0,'tolerance','CPI 12-month 0.2' if cat!='category' else 'design (0.1)');tabs.append(t)
 T=pd.concat(tabs,ignore_index=True);T.to_csv(OUT/'summary.csv',index=False)
 # 30 scored claims for the manual parse check: proportional by indicator, at least 3 each (seeded).
 k={i:max(3,round(30*n/len(C))) for i,n in C.indicator.value_counts().items()}
 while sum(k.values())>30:k[max(k,key=k.get)]-=1
 R=pd.concat([g.sample(min(len(g),k[i]),random_state=SEED) for i,g in C.groupby('indicator')])
 R=R[['coding_id','date','fragment','indicator','measure','official_series','claim_value','inequality','reference_period','official_value_at_pub','category']].assign(parse_correct_yes_no='',note='')
 if not (OUT/'review_sample_30.csv').exists():R.to_csv(OUT/'review_sample_30.csv',index=False)  # never overwrite the completed manual check
 U=C[C.measure=='unnamed'].groupby(['source_type','unnamed_any_reading']).size().rename('claims').reset_index();U.to_csv(OUT/'unnamed_inflation.csv',index=False);print(U)
 pd.set_option('display.width',250);print(S.to_string());print(T[T.tolerance=='design (0.1)'].to_string());print(len(C))

if __name__=='__main__':main()
