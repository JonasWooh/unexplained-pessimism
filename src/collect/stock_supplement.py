"""NASDAQ Composite supplement, with explicit bounded ALFRED query windows.

The API limits JSON real-time queries to 2,000 vintage dates. Response intervals
are clipped to each query window; these are raw windowed records, not distinct
revisions. No substitution for S&P 500 and no synthetic stitching.
"""
from common import *
from macro import LICENSE

def main():
 dates=json.loads((ROOT/'data/raw/M16'/DAY/'NASDAQCOM_vintagedates_0000000.json').read_text())['vintage_dates']
 windows=[];start='1776-07-04'
 for i in range(0,len(dates),1500):
  end=dates[min(i+1499,len(dates)-1)] if i+1500<len(dates) else CUTOFF
  offset=0;rows=0;expected=None
  while True:
   params=dict(series_id='NASDAQCOM',file_type='json',realtime_start=start,realtime_end=end,observation_start='2008-01-01',observation_end=CUTOFF,output_type=1,limit=100000,offset=offset)
   p=fetch('M16','https://api.stlouisfed.org/fred/series/observations',f'NASDAQCOM_window_{i//1500:02}_{offset:07}.json',params,key='fred',license_note=LICENSE+' Query-window validity intervals; boundary clipping is not a new revision.')
   if not p:return
   o=json.loads(p.read_bytes());rows+=len(o['observations']);expected=o['count'];offset=rows
   if rows>=expected:break
   if not o['observations']:raise ValueError('Empty page before total count')
  windows.append(dict(start=start,end=end,rows=rows,expected_rows=expected,complete=rows==expected))
  start=(dt.date.fromisoformat(end)+dt.timedelta(days=1)).isoformat()
 (PROV/'nasdaq_vintage_windows.json').write_text(json.dumps(dict(series='NASDAQCOM',windows=windows,notes='All API vintage dates covered by contiguous query windows. Window boundaries clip validity intervals; not distinct revisions. Separate index from SP500.'),indent=2))

if __name__=='__main__':main()
