"""Generate an explicitly dated collection snapshot from actual saved files."""
from common import *
import pandas as pd,collections

def main():
 inv=list(csv.DictReader((PROV/'inventory.csv').open()));by=collections.defaultdict(list)
 for r in inv:by[r['dataset_id']].append(r)
 rows=[]
 def add(ds,name,status,coverage,count,unit,issues):rows.append(dict(dataset_id=ds,dataset=name,status=status,coverage=coverage,entries=count,unit=unit,issues=issues))
 add('S01','ICS/ICC/ICE','Obtained','ICS from 1952-11, components from 1951-02, all through 2026-09','677 / 677','ICS rows / ICC-ICE rows','Continuous monthly from 1978-01; non-continuous months in early years; all 585 months overlapping with the professor\'s sheet match')
 add('S02','Demographic groups and party','Public data obtained','Groups 1978-01—2026-08; party 1980-06—2026-08','584 / 156','Demographic-group months / party months','39 group indicators; party data sparse in early years; current table 5b is a three-month mean, historical table is monthly')
 add('S03','News heard','Obtained','1978-01—2026-08',584,'Months, 22 statistic columns','Phone and web response modes differ; coding compatibility cannot be treated as established')
 add('S04','Reasons, expectations, buying conditions','Obtained','1978-01—2026-08; inflation expectations through 2026-09','584 / 585','Detailed-table months / inflation-expectation months','Detailed tables have 111 statistic columns; all 12 current tables also saved')
 add('S05','Released values and methodology','Public versions obtained; PDFs lag','2024-01—2026-10 preliminary','65 + 1','PDF reports + preliminary values on the official homepage','October preliminary 46.3 confirmed; September final PDF not obtained, the CSV has the final value; official notice explains the 2025-01 revision differences')
 add('S06','Anonymous microdata survey','Selected fields obtained','2010-01—2026-02',120568,'Cases, 20 columns','Latest available 2026-02; later months not filled in')
 names={'M01':'U-3','M02':'Headline PCE','M03':'Real GDP level','M04':'Real GDP quarter-over-quarter annualized rate','M05':'Core PCE','M06':'U-6','M07':'Real disposable income, two series','M08':'Gasoline','M09':'Food CPI, two series','M10':'30-year mortgage rate','M11':'Debt-service burden','M12':'Policy uncertainty','M14':'Real consumption','M15':'House prices'}
 macro=pd.read_csv(PROV/'macro_completeness.csv')
 for ds,name in names.items():
  a=macro[macro.dataset_id==ds];issues='All vintages available from the API collected; earliest archive vintage dates in macro_completeness.csv'
  if ds in ['M01','M06']:issues+='; official 2025-10 missing value kept'
  if ds=='M04':issues+='; earliest vintage of the q/q series is 2014-09-26; 2026Q3 not yet released'
  if ds=='M12':issues+='; original EPU table also saved, 1521 months, 1900-01—2026-09'
  add(ds,name,'All available vintages downloaded',a.coverage_start.min()+'—'+a.coverage_end.max(),int(a.rows.sum()),'Observation × vintage rows',issues)
 add('M13','Housing affordability HOAM','Latest snapshot obtained','2005-01—2026-07',259,'Months','The source site keeps no archive of historical versions')
 nasdaq=[r for r in by['M16'] if Path(r['file_path']).name=='NASDAQCOM_latest.csv']
 nasdaq_note=('; NASDAQ Composite added for '+nasdaq[0]['coverage_start']+'—'+nasdaq[0]['coverage_end']+', '+nasdaq[0]['rows']+' date rows, with windowed responses for all available vintages saved; a different index, not spliced with the S&P') if nasdaq else ''
 add('M16','Stock market: S&P 500 with NASDAQ supplement','S&P partial; NASDAQ supplement obtained' if nasdaq else 'Partial: latest snapshot only','S&P 2016-10-17—2026-10-14'+nasdaq_note,2608,'S&P date rows; NASDAQ count in the coverage column','ALFRED does not support historical vintages for the S&P, so pre-2016 remains missing; includes gaps on non-trading days')
 add('M17','Philadelphia Fed real-time data','Obtained','Earliest reference period 1947; latest through 2026Q2/2026-07',9,'Workbooks','8 real-time vintage / first-three-estimates workbooks and 1 employment release-date history; PCON is a constructed quarterly price index')
 for ds,name,kind in [('N01','New York Times','nyt_articles'),('N02','Guardian','guardian_articles')]:
  articles=[r for r in by[ds] if r['record_type']==kind];n=sum(int(r['rows']) for r in articles)
  state_file=PROV/(ds+'_archive_state.json');news_state=json.loads(state_file.read_text()) if state_file.exists() else {}
  start=min((r['coverage_start'] for r in articles if r['coverage_start']),default='Not obtained');end=max((r['coverage_end'] for r in articles if r['coverage_end']),default='Not obtained')
  issue='Official key tested successfully; full article metadata saved by month without filtering; current month partial; not news body text' if ds=='N01' else 'Official key tested successfully; business/useconomy tag verified; body text saved as provided, missing bodies not filled in; covers only this tag and does not claim completeness for US economic coverage overall'
  audit_file=PROV/'news_monthly_completeness.csv'
  checks=[r for r in csv.DictReader(audit_file.open()) if r['dataset_id']==ds] if audit_file.exists() else []
  if checks:
   issue+=f'; {sum(int(r["duplicate_ids"]) for r in checks)} duplicate IDs within months; {sum(int(r["dates_outside_month"]) for r in checks)} items with publication dates outside the requested month, kept as returned'
   if ds=='N02':issue+=f'; {sum(int(r["missing_bodyText"]) for r in checks)} items missing body text'
  period=('Requested months 2009-12—2026-10; latest returned publication time '+end+'; contains anomalous dates, so coverage is not inferred from the raw minimum date') if ds=='N01' else start+'—'+end
  add(ds,name,news_state.get('status','not started'),period,n,'Article response items (not the number of de-duplicated articles)',issue)
 story=[r for r in by['N03'] if r['record_type']=='news_stories'];count=sum(int(r['rows']) for r in story)
 state_path=PROV/'mediacloud_collection_state.json';state=json.loads(state_path.read_text()) if state_path.exists() else {}
 complete=bool(state.get('collections')) and all(x['complete'] for x in state['collections']);error=any(x['error'] for x in state.get('collections',[]))
 title_start=min((r['coverage_start'] for r in story if r['coverage_start']),default='Not obtained');title_end=max((r['coverage_end'] for r in story if r['coverage_end']),default='Not obtained')
 collection_status='; '.join(x['name']+(' complete' if x['complete'] else ' paused on error' if x['error'] else ' in progress') for x in state.get('collections',[]))
 daily_path=PROV/'mediacloud_daily_state.json'
 if daily_path.exists():
  daily=json.loads(daily_path.read_text());collection_status='daily rotation '+daily['status']+'; '+str(sum(d['complete'] for d in daily['days']))+'/'+str(len(daily['days']))+' collection-day queries complete'
 add('N03','Media Cloud','Counts obtained; '+collection_status,f'Main counts 2010-01-01—2026-10-14; titles downloaded {title_start}—{title_end} (not continuous full coverage)',f'73572 / {count}','Main daily count rows / raw title response items (batches overlap)','Six daily series each for national and local; 2 requests/minute; currently rotating by day; old windows overlap the daily batches and cannot be added as independent articles; de-duplicated daily coverage in daily_coverage.csv; listing not finished; includes non-economic hits, not labeled or filtered')
 add('N04','GDELT','Not accessible','Not obtained',0,'Records','A recheck request after a 24-hour interval still returned HTTP 429; stopped, not circumvented; actual historical boundary not verified')
 add('N05','San Francisco Fed news sentiment','Obtained','1980-01-01—2026-10-11',17067,'Daily index rows','Excel, 2 CSVs and the replication ZIP all kept; not original news articles')
 add('N06','Media leaning ratings','Numeric ratings not obtained','Not obtained',0,'Ratings','AllSides HTTP 403; Ad Fontes page reachable, but the free educational chart requires a name/email form and joining a mailing list; not registered on the user\'s behalf, and a static chart is not a numeric ratings database')
 sm=collections.Counter()
 for r in by['SM01']:
  if r['rows']:sm[r['record_type']]+=int(r['rows'])
 coverage=list(csv.DictReader((PROV/'youtube_coverage.csv').open()))
 text_path=PROV/'youtube_comment_text_state.json';text_state=json.loads(text_path.read_text()) if text_path.exists() else {}
 text_files=[r for r in by['SM01'] if r['record_type']=='comment_text'];text_start=min((r['coverage_start'] for r in text_files if r['coverage_start']),default='none');text_end=max((r['coverage_end'] for r in text_files if r['coverage_end']),default='none')
 add('SM01','YouTube','Partial; comment-text job '+text_state.get('status','not started'),f'Videos prioritized 2023—2026-10-14; {sum(s["reached_2023_boundary"]=="True" for s in coverage)}/10 channel listings reached the 2023 boundary; comment text {text_start}—{text_end}',f'{sm["video_inventory"]} / {sm["video_statistics"]} / {sm["comment_metadata"]} / {sm["comment_text"]}','Listing / video statistics / comment metadata / comment-text response items',f'Another {sm["video_search_results"]} search results; the two comment batches may overlap and cannot be added as independent comments; comment text collected with the user\'s permission, author fields excluded; comment times can be later than the video cutoff; large channel listings stop at 20000 items; daily searches started to fill listing gaps, actual state in youtube_daily_search_state.json; 2010–2022 not collected')
 reddit_file=PROV/'reddit_collection_state.json';reddit_state=json.loads(reddit_file.read_text()) if reddit_file.exists() else {}
 reddit_records=[r for r in by['SM02'] if r['record_type']=='reddit_posts']
 reddit_start=min((r['coverage_start'] for r in reddit_records if r['coverage_start']),default='Not obtained');reddit_end=max((r['coverage_end'] for r in reddit_records if r['coverage_end']),default='Not obtained')
 add('SM02','Reddit',reddit_state.get('status','not started'),reddit_start+'—'+reddit_end,sum(int(r['rows']) for r in reddit_records),'Post items in non-overlapping time intervals','Collection approved by the user; Arctic Shift community archive, not the official Reddit API; four subreddits; breadth-first by day, first pass 2025 onward, then 2010—2024; author identity fields excluded; saturation probe pages not counted twice; optional comments not collected')
 for ds,name,file,unit,status,issue in [
  ('R01','Release calendar','release_calendar.csv','Calendar rows','Available calendars obtained','Actual releases, ALFRED vintages and future schedules flagged separately; BLS web page 403, FRED calendar obtained'),
  ('R02','Major events','events.csv','Verified events','Partial','FOMC statements and some pandemic/banking/tariff/shutdown events; not claimed to be exhaustive; CBO/GAO sources 403'),
  ('R03','Political calendar','political_elections.csv','Election dates','Obtained','Official tables of presidential terms and party composition of both chambers also saved'),
 ]:
  a=list(csv.DictReader((PROV/file).open()));key='release_date' if ds=='R01' else 'date';add(ds,name,status,min(r[key] for r in a)+'—'+max(r[key] for r in a),len(a),unit,issue)
 add('R04','Pew platform usage rates','Obtained','2025-02-05—2025-06-18',1,'Public report, original survey n=5022','YouTube 84%, Facebook 71%, Instagram 50%, TikTok 37%, Reddit 26% checked; survey microdata not downloaded')
 add('R05','SPF professional forecasts','Obtained','Workbook overall 1968Q4—2026Q3',2,'Complete workbook','Variables start at different times; PCE should not be treated as available since 1968')
 rows.sort(key=lambda r:(['S','M','N','SM','R'].index('SM' if r['dataset_id'].startswith('SM') else r['dataset_id'][0]),int(r['dataset_id'].lstrip('SMNR'))))
 with (PROV/'dataset_status.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
 now=dt.datetime.now(dt.timezone.utc).isoformat();registered_files=len(inv)
 lines=['# Data collection status snapshot','',f'Generated: {now}. Cutoff: 2026-10-14. **Not yet complete**: rate-limited pagination, source restrictions and historical gaps remain; the numbers below describe this snapshot only.','',
 'The **PCE YoY in the professor\'s Excel is core PCE**; 584 months match core PCE. Headline PCE was collected separately. The original Excel and the original downloads were not modified.','',
 '| Dataset | Status | Actual/requested coverage | Entries (unit) | Issues |','|---|---|---|---|---|']
 for r in rows:lines.append(f'| {r["dataset_id"]} {r["dataset"]} | {r["status"]} | {r["coverage"]} | {r["entries"]} ({r["unit"]}) | {r["issues"]} |')
 lines+=['','Registered files: '+str(registered_files)+'; '+str(len(macro))+' usable ALFRED series have complete pagination, with no duplicate vintage keys, future vintages, or observation dates later than vintage dates.','',
 'User decisions implemented: YouTube comment text may be saved, with all author identity fields excluded; the self-imposed per-round request total and per-video comment truncation were removed, stopping only on genuine API errors. NYT/Guardian collection ran through the official APIs with the user\'s keys. Reddit was approved and started; no longer on hold.','',
 'Key checks and limitations: 2025-01 ICS 71.1→71.7 is an official revision; the professor\'s 2026-10 ICS=46.3 is confirmed as preliminary by the official homepage; 2026Q3 GDP=3.7 is still not stored as a verified official value. The 20-link news check found 6 unreadable responses, 7 title differences and 3 readable date differences; see news_url_spotcheck.csv.','',
 'Background progress is given by mediacloud_daily_state.json, youtube_daily_search_state.json, youtube_comment_text_state.json and reddit_collection_state.json; the old supervisor has been replaced; this is not a scheduled task. Coverage is filled by day first; daily snapshots in daily_coverage.csv. Later batches still need the inventory rechecked; this report does not guarantee that future pages will be available.','',
 'Detailed evidence: sources.csv (source, UTC download time, coverage), inventory.csv (per-file entry counts), macro_completeness.csv, release_calendar.csv, excel_reconciliation.md, ../DECISIONS.md. Raw data and copyrighted content are kept locally only and are not packaged for publication.']
 (PROV/'collection_report.md').write_text('\n'.join(lines)+'\n')
 print('Status rows:',len(rows),'registered files:',registered_files)

if __name__=='__main__':main()
