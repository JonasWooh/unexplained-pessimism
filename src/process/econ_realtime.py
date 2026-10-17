"""Real-time monthly economic panel (task_guide 6.2, 7.1 step 3).

For survey month t the information cutoff tau_t is the last day before the 1st of month t (D2): a value
is usable only if its ALFRED realtime_start <= tau_t <= realtime_end. Within that vintage the latest
non-missing observation is taken; growth rates use numerator and denominator from the same vintage.
A sensitivity file uses tau_t = day before the Michigan preliminary release of month t.
Series without ALFRED vintages before some date are left missing before their first vintage.
"""
import csv,glob,json,re,datetime as dt
from pathlib import Path
import pandas as pd
import pypdf
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2];RAW=ROOT/'data/raw';OUT=ROOT/'data/processed'
START,END='2010-01','2026-10'

def alfred(sid):
 recs=[];vint=[]
 for f in sorted(RAW.glob(f'M*/*/{sid}_observations_*.json')):recs+=json.loads(f.read_text())['observations']
 for f in sorted(RAW.glob(f'M*/*/{sid}_vintagedates_*.json')):vint+=json.loads(f.read_text())['vintage_dates']
 if not recs:raise FileNotFoundError(sid)
 return recs,sorted(set(vint))

class Series:
 def __init__(self,sid):
  self.sid=sid;self.recs,self.vintages=alfred(sid)
  self.first_seen={}
  for r in self.recs:self.first_seen[r['date']]=min(self.first_seen.get(r['date'],r['realtime_start']),r['realtime_start'])
 def vintage(self,tau):
  """{obs_date: (value or None, realtime_start)} valid at tau."""
  return {r['date']:(None if r['value']=='.' else float(r['value']),r['realtime_start']) for r in self.recs if r['realtime_start']<=tau<=r['realtime_end']}
 def latest(self,tau):
  v=self.vintage(tau);obs=[d for d,(x,_) in v.items() if x is not None]
  if not obs:return None,None,None,v
  d=max(obs);return v[d][0],d,v[d][1],v

def shift(date,months):
 y,m=int(date[:4]),int(date[5:7]);k=y*12+m-1+months;return f'{k//12:04}-{k%12+1:02}-01'

def pct(a,b):return None if a is None or b is None or b==0 else 100*(a/b-1)

def michigan():
 s=next(RAW.glob('S01/*/tbmics.csv'));c=next(RAW.glob('S01/*/tbmiccice.csv'))
 mon={m:i for i,m in enumerate(['January','February','March','April','May','June','July','August','September','October','November','December'],1)}
 out={}
 for r in csv.DictReader(open(s)):out.setdefault(f"{int(r['YYYY']):04}-{mon[r['Month']]:02}",{})['ics']=float(r['ICS_ALL'])
 for r in csv.DictReader(open(c)):
  d=out.setdefault(f"{int(r['YYYY']):04}-{mon[r['Month']]:02}",{})
  for k in ['ICC','ICE']:
   if r[k].strip():d[k.lower()]=float(r[k])
 for d in out.values():d['ics_status']='final'
 # Preliminary values for months after the CSV, from the saved official homepage only.
 t=BeautifulSoup(next(RAW.glob('S05/*/homepage.html')).read_bytes(),'html.parser').get_text(' ',strip=True)
 m=re.search(r'Preliminary Results for (\w+) (\d{4}).*?Index of Consumer Sentiment ([\d.]+).*?Current Economic Conditions ([\d.]+).*?Index of Consumer Expectations ([\d.]+)',t)
 month=f"{int(m.group(2)):04}-{mon[m.group(1)]:02}"
 if month not in out:out[month]=dict(ics=float(m.group(3)),icc=float(m.group(4)),ice=float(m.group(5)),ics_status='prelim')
 # Official preliminary/final release dates.
 text='\n'.join(p.extract_text() for p in pypdf.PdfReader(next(RAW.glob('S05/*/historical_release_dates.pdf'))).pages)
 rel={}
 for a,y,p,f in re.findall(r'^(\w{3}) (\d{4}) (\d+/\d+/\d{4}) (\d+/\d+/\d{4})',text,re.M):
  k=f"{y}-{['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'].index(a)+1:02}"
  rel[k]=tuple(dt.datetime.strptime(x,'%m/%d/%Y').date().isoformat() for x in (p,f))
 return out,rel

def mode_web_share(month):
 return {'2024-04':0.25,'2024-05':0.5,'2024-06':0.75}.get(month,1.0 if month>='2024-07' else 0.0)

def market(sid,tau):
 f=next(RAW.glob(f'M16/*/{sid}_latest.csv'));rows=[(r['observation_date'],r[sid]) for r in csv.DictReader(open(f)) if r[sid] not in ('','.')]
 rows=[x for x in rows if x[0]<=tau]
 return (float(rows[-1][1]),rows[-1][0]) if rows else (None,None)

def build(cutoff_rule):
 S={k:Series(k) for k in ['UNRATE','U6RATE','PCEPI','PCEPILFE','GDPC1','A229RX0','DSPIC96','PCEC96','GASREGW','CPIUFDSL','CUSR0000SAF11','MORTGAGE30US','TDSP','USEPUINDXM','CSUSHPISA']}
 mich,rel=michigan();rows=[]
 month=START+'-01'
 while month[:7]<=END:
  m=month[:7]
  tau=(dt.date.fromisoformat(month)-dt.timedelta(days=1)).isoformat() if cutoff_rule=='D2' else (dt.date.fromisoformat(rel[m][0])-dt.timedelta(days=1)).isoformat()
  r=dict(month=m,origin_date=tau,cutoff_rule=cutoff_rule,**{k:mich.get(m,{}).get(k) for k in ['ics','icc','ice','ics_status']},
   mich_prelim_release_date=rel.get(m,(None,None))[0],mich_final_release_date=rel.get(m,(None,None))[1],mode_web_share=mode_web_share(m))
  for sid,col in [('UNRATE','unrate'),('U6RATE','u6rate'),('MORTGAGE30US','mortgage30'),('TDSP','tdsp'),('USEPUINDXM','epu'),('GASREGW','gas_price')]:
   x,d,rs,_=S[sid].latest(tau);r.update({f'{col}_rt':x,f'{col}_ref':d,f'{col}_release_date':rs})
  for sid,col in [('PCEPI','pce'),('PCEPILFE','core_pce'),('A229RX0','rdpi_pc'),('DSPIC96','rdpi'),('PCEC96','real_pce'),('CPIUFDSL','food_cpi'),('CUSR0000SAF11','food_home_cpi'),('CSUSHPISA','case_shiller')]:
   x,d,rs,v=S[sid].latest(tau)
   prev=v.get(shift(d,-12),(None,))[0] if d else None
   r.update({f'{col}_yoy_rt':pct(x,prev),f'{col}_ref':d,f'{col}_release_date':rs})
   if sid in ('PCEPI','CPIUFDSL'):
    base=v.get('2021-01-01',(None,))[0] if d and d>='2021-01-01' else None
    r[f'{col}_cum_since_2021_01_rt']=pct(x,base)
  x,d,rs,v=S['GDPC1'].latest(tau)
  if d:
   q1=v.get(shift(d,-3),(None,))[0];q4=v.get(shift(d,-12),(None,))[0]
   r.update(gdp_qoq_saar_rt=None if q1 is None else 100*((x/q1)**4-1),gdp_yoy_rt=pct(x,q4),gdp_ref_quarter=f"{d[:4]}Q{(int(d[5:7])-1)//3+1}",gdp_release_date=rs,
    gdp_release_number=sum(1 for t in S['GDPC1'].vintages if S['GDPC1'].first_seen[d]<=t<=tau))
  else:r.update(gdp_qoq_saar_rt=None,gdp_yoy_rt=None,gdp_ref_quarter=None,gdp_release_date=None,gdp_release_number=None)
  for sid,col in [('SP500','sp500'),('NASDAQCOM','nasdaq')]:
   x,d=market(sid,tau);r.update({f'{col}_close':x,f'{col}_ref':d})
  rows.append(r);month=shift(month,1)
 return pd.DataFrame(rows)

if __name__=='__main__':
 OUT.mkdir(parents=True,exist_ok=True)
 for rule,name in [('D2','econ_monthly_realtime.csv'),('mich_prelim','econ_monthly_realtime_prelim_cutoff.csv')]:
  df=build(rule);df.to_csv(OUT/name,index=False);print(name,df.shape)
