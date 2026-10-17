"""Keyword-rule baseline for topics and price framing (R3.5), written from the codebook definitions
(annotation/codebook_v1.md sections 4 and 5.1) before any rule was scored. Rules are case-insensitive
regular expressions on the unit text; no rule is tuned on the test set.

Topics: a topic is 1 if any of its patterns matches; T13_other is 1 when no other topic matches.
price_frame: `rate` patterns talk about inflation or the speed of price increases; `level` patterns talk
about prices being high/expensive/costing more than before. both if both match, none if neither.
"""
import re

TOPIC_PATTERNS={
 'T01_layoffs_unemployment_up':[r'\blay ?offs?\b',r'\blaid off\b',r'\bjob (cuts?|losses)\b',r'\bunemployment (rate )?(rose|rises|rising|climb\w*|jump\w*|up|increas\w*|hit|surg\w*)',r'\bjobless claims\b',r'\bfired\b',r'\blost (my|their|his|her) jobs?\b',r'\bcut(ting)? (\d[\d,]* )?jobs\b'],
 'T02_hiring_jobs_growth':[r'\bhir(ing|ed|es)\b',r'\b(added|adds|adding|created|creating|gained?|gains) (\d[\d,.]* )?(million |thousand )?jobs\b',r'\bjob (growth|gains|openings)\b',r'\bpayrolls? (rose|grew|increased|jump\w*|gain\w*)',r'\blabor market (is )?(strong|tight|robust|solid)',r'\bunemployment (rate )?(fell|falls|dropped|drops|declin\w*|low)'],
 'T03_prices_rising':[r'\bprices? (are |were |have |has |keep |kept )?(ris\w*|rose|soar\w*|climb\w*|jump\w*|surg\w*|up|higher|increas\w*|skyrocket\w*)',r'\bcost of living\b',r'\b(inflation|cpi) (rose|rises|rising|jump\w*|accelerat\w*|surg\w*|climb\w*|hit|high|picked up)',r'\b(high|higher|rising|soaring|persistent|hot) inflation\b',r'\bexpensive\b',r'\bcan\'?t afford\b',r'\bunaffordable\b',r'\bprice (hikes?|increases?)\b'],
 'T04_inflation_easing':[r'\b(inflation|cpi|price (growth|increases?)) (cool\w*|eas\w*|slow\w*|fell|falls|declin\w*|moderat\w*|dropped|drops|retreat\w*)',r'\bdisinflation\b',r'\b(cooling|easing|slowing|lower|falling) inflation\b',r'\bprices? (fell|falls|dropped|drops|declin\w*|eas\w*)'],
 'T05_economic_growth':[r'\bgdp\b',r'\bgross domestic product\b',r'\beconom(y|ic) (grew|grows|growing|expand\w*)',r'\beconomic (growth|expansion|output)\b',r'\brecovery\b'],
 'T06_recession_risk':[r'\brecession\w*\b',r'\bdownturn\b',r'\bslowdown\b',r'\beconom(y|ic) (slow\w*|contract\w*|shrink\w*|shrank|weak\w*)',r'\bcontraction\b',r'\bdepression\b',r'\bstagflation\b'],
 'T07_interest_rates_borrowing':[r'\binterest rates?\b',r'\bfed(eral reserve)?\b.{0,40}\brates?\b',r'\brate (cuts?|hikes?|increases?)\b',r'\bborrowing costs?\b',r'\bmortgage rates?\b',r'\bfed funds\b',r'\bcredit card (rates?|debt|interest)\b'],
 'T08_housing_costs':[r'\bhous(e|ing) (prices?|costs?|market|affordability)\b',r'\bhome (prices?|values?|sales)\b',r'\brents?\b',r'\brental\b',r'\bmortgages?\b',r'\baffordable housing\b',r'\blandlords?\b'],
 'T09_gas_prices':[r'\bgas(oline)? (prices?|costs?)\b',r'\bprices? (at|of) the pump\b',r'\bat the pump\b',r'\bfuel (prices?|costs?)\b',r'\b(oil|crude) prices?\b'],
 'T10_food_prices':[r'\bgrocer(y|ies)\b',r'\bfood (prices?|costs?|inflation)\b',r'\beggs?\b',r'\bbeef\b',r'\bsupermarkets?\b'],
 'T11_tariffs_trade':[r'\btariffs?\b',r'\btrade (war|deal|deficit|policy|agreement|talks|barriers?)\b',r'\bimports?\b',r'\bexports?\b',r'\bnafta\b',r'\busmca\b'],
 'T12_stock_market':[r'\bstocks?\b',r'\bstock market\b',r'\bwall street\b',r'\bdow\b',r'\bs&p\b',r'\bnasdaq\b',r'\bshares\b',r'\bequit(y|ies)\b'],
}
RATE=[r'\binflation\b',r'\bcpi\b',r'\bconsumer price index\b',r'\bprices? (rose|rising|rises|grew|increased|climbed|fell|slowed|cooled)\b.{0,40}\d+(\.\d+)? ?(%|percent)',r'\d+(\.\d+)? ?(%|percent)\b.{0,30}\b(from|over) (a|the) year (earlier|ago|before)',r'\bannual (rate|pace)\b',r'\bprices? (are )?(rising|growing) (faster|slower|more slowly)\b',r'\bpace of (price|inflation)\b']
LEVEL=[r'\bexpensive\b',r'\bcost(s|ing)? (more|twice|double|\$)',r'\b(twice|double) (as much|what)\b',r'\bcan\'?t afford\b',r'\bunaffordable\b',r'\baffordab\w*\b',r'\bprices? (are|remain|stay|stayed|is) (still |so |too )?(high|elevated|insane|crazy|ridiculous)',r'\bhigher prices\b',r'\bhigh prices\b',r'\bprices? (are |were )?(way |much |far )?(higher|more) than\b',r'\bcost of living\b',r'\bsticker shock\b',r'\bprice tags?\b']

_T={k:re.compile('|'.join(v),re.I) for k,v in TOPIC_PATTERNS.items()}
_R=re.compile('|'.join(RATE),re.I);_L=re.compile('|'.join(LEVEL),re.I)

def topics(text):
 hit={k:int(bool(rx.search(text))) for k,rx in _T.items()}
 hit['T13_other']=int(not any(hit.values()));return hit

def price_frame(text):
 r,l=bool(_R.search(text)),bool(_L.search(text))
 return 'both' if r and l else 'rate' if r else 'level' if l else 'none'
