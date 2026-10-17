"""Channel x natural-month acquisition status; never equates hits with completeness."""
from common import *
from youtube_monthly_search import used_today,estimate
import calendar

def main():
 registry=list(csv.DictReader((PROV/'youtube_video_acquisition_registry.csv').open()))
 channels=json.loads((PROV/'youtube_inventory_state.json').read_text());coverage={r['channel_id']:r for r in csv.DictReader((PROV/'youtube_coverage.csv').open())}
 cp=PROV/'youtube_classified_state.json';classified=json.loads(cp.read_text())['playlists'] if cp.exists() else []
 sp=PROV/'youtube_monthly_search_state.json';state=json.loads(sp.read_text())
 query={(d['channel'],d['month']):d for d in state['queries']};rows=[]
 for ch in channels:
  cid=ch['channel'];original=coverage[cid];long=next((d for d in classified if d['channel']==cid and d['kind']=='UULF'),{})
  for year in range(2023,2027):
   for month in range(1,13):
    label=f'{year:04}-{month:02}'
    if label>CUTOFF[:7]:continue
    start=label+'-01';members=[r for r in registry if r['channel']==cid and r['published'][:7]==label];q=query.get((cid,label),{})
    complete=False;route='legacy_partial_not_eligible';reason='Legacy quarterly search is nonrandom and incomplete; raw retained.';scope_ids=None
    if original['earliest'][:10]<=start:
     route='uploads';complete=True;reason='Available upload list paginated through this calendar month.'
    if long.get('earliest') and long['earliest'][:10]<=start:
     route='classified_UULF';complete=True;reason='Long-video playlist only; excludes shorts; convention undocumented; not an all-video census.'
     members=[r for r in members if 'classified_UULF' in r['routes']]
    if q.get('status')=='complete_pagination':
     route='monthly_economic_OR_search';complete=True;reason='Monthly result pagination complete; API search coverage is not a platform-wide census.';scope_ids=set(q['ids']);members=[r for r in members if r['video_id'] in scope_ids]
    elif q.get('page'):
     route='monthly_economic_OR_search_partial';complete=False;reason=q.get('status','pending');scope_ids=set(q['ids']);members=[r for r in members if r['video_id'] in scope_ids]
    rows.append(dict(channel_id=cid,channel=ch['title'],month=label,acquisition_route=route,obtained_unique=len({r['video_id'] for r in members}),title_match_unique=sum(r['title_rule_match']=='True' for r in members),pagination_complete=complete,query_estimate=q.get('query_estimate',''),search_pages=q.get('page',0),notes=reason))
 path=PROV/'youtube_channel_month_status.csv';tmp=path.with_suffix('.tmp')
 with tmp.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 tmp.replace(path);estimate(state)
 summary=dict(as_of_utc=dt.datetime.now(dt.timezone.utc).isoformat(),channel_months=len(rows),complete_inventory_or_query_months=sum(r['pagination_complete'] for r in rows),search_calls_current_pacific_day=used_today(),search_status=state['status'],search_error=state.get('error'),classified_status=json.loads(cp.read_text()).get('status') if cp.exists() else None)
 (PROV/'youtube_daily_status.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
