"""Deterministic temporal cluster design; no text content is used in selection."""
import datetime as dt,random
SEED=20261015
FRACTION=.5

def halfday(source,day):
 start=int(dt.datetime.fromisoformat(day).replace(tzinfo=dt.timezone.utc).timestamp())
 half=random.Random(f'{SEED}|{source}|{day}').randrange(2)
 return start+half*43200,start+(half+1)*43200

def intersect_pending(source,pending):
 selected=[]
 for lo,hi,label in pending:
  while lo<hi:
   end=min(hi,(lo//86400+1)*86400);day=dt.datetime.fromtimestamp(lo,dt.timezone.utc).date().isoformat();a,b=halfday(source,day)
   if max(lo,a)<min(end,b):selected.append([max(lo,a),min(end,b),label])
   lo=end
 return selected

from functools import lru_cache
import calendar
@lru_cache(maxsize=None)
def day_ranks(month):
 y,m=map(int,month.split('-'));days=list(range(1,calendar.monthrange(y,m)[1]+1))
 random.Random(f'{SEED}|month-date-order|{month}').shuffle(days)
 return {d:i for i,d in enumerate(days)}

def interval_priority(source,interval):
 lo,hi,month=interval;date=dt.datetime.fromtimestamp(lo,dt.timezone.utc)
 phase=0 if source in ['economy','Economics'] and '2017-01'<=month<='2024-12' else 1
 return phase,day_ranks(month)[date.day],month,source,lo
