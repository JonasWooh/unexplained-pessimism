"""Generate an explicitly dated collection snapshot from actual saved files."""
from common import *
import pandas as pd,collections

def main():
 inv=list(csv.DictReader((PROV/'inventory.csv').open()));by=collections.defaultdict(list)
 for r in inv:by[r['dataset_id']].append(r)
 rows=[]
 def add(ds,name,status,coverage,count,unit,issues):rows.append(dict(dataset_id=ds,dataset=name,status=status,coverage=coverage,entries=count,unit=unit,issues=issues))
 add('S01','ICS/ICC/ICE','已取得','ICS 1952-11、分项 1951-02 起，均至 2026-09','677 / 677','ICS 行 / ICC-ICE 行','1978-01 起连续月度；早年非连续月度；教授表重叠 585 月全匹配')
 add('S02','人口分组与党派','已取得公开数据','分组 1978-01—2026-08；党派 1980-06—2026-08','584 / 156','人口分组月 / 党派月','39 分组指标；党派早期稀疏；当前 5b 是三月均值，历史表是月度')
 add('S03','听到的新闻','已取得','1978-01—2026-08',584,'月，22 统计列','电话/网页回答方式不同，编码兼容性不能视为已证明')
 add('S04','原因、预期、购买条件','已取得','1978-01—2026-08；通胀预期至 2026-09','584 / 585','详细表月 / 通胀预期月','详细表 111 统计列；另存全部 12 份当前表')
 add('S05','发布值与方法','已取得公开版本，PDF有滞后','2024-01—2026-10 初值','65 + 1','PDF报告 + 官网首页初值','10月初值46.3已确认；9月终值PDF未取得，CSV有终值；2025-01修订差异有官方公告')
 add('S06','匿名微观调查','已取得所选字段','2010-01—2026-02',120568,'案例，20 列','最新可得 2026-02，未自行补齐后续月份')
 names={'M01':'U-3','M02':'总体 PCE','M03':'实际 GDP 水平','M04':'实际 GDP 环比年率','M05':'核心 PCE','M06':'U-6','M07':'实际可支配收入两序列','M08':'汽油','M09':'食品 CPI 两序列','M10':'30 年房贷利率','M11':'偿债负担','M12':'政策不确定性','M14':'实际消费','M15':'房价'}
 macro=pd.read_csv(PROV/'macro_completeness.csv')
 for ds,name in names.items():
  a=macro[macro.dataset_id==ds];issues='已收 API 全部可得版本；档案最早版本日详见 macro_completeness.csv'
  if ds in ['M01','M06']:issues+='；2025-10 官方缺失保留'
  if ds=='M04':issues+='；环比序列最早版本为 2014-09-26；2026Q3 未发布'
  if ds=='M12':issues+='；另存 EPU 原表 1521 月，1900-01—2026-09'
  add(ds,name,'可得版本下载完整',a.coverage_start.min()+'—'+a.coverage_end.max(),int(a.rows.sum()),'观测×版本行',issues)
 add('M13','住房可负担性 HOAM','最新快照已取得','2005-01—2026-07',259,'月','原站文件没有历史版本档案')
 nasdaq=[r for r in by['M16'] if Path(r['file_path']).name=='NASDAQCOM_latest.csv']
 nasdaq_note=('；另补 NASDAQ Composite '+nasdaq[0]['coverage_start']+'—'+nasdaq[0]['coverage_end']+'，'+nasdaq[0]['rows']+' 日期行，另存全部可得版本的分窗口响应；是不同指数，不与标普拼接') if nasdaq else ''
 add('M16','股票市场：S&P 500 与 NASDAQ 补充','标普部分；NASDAQ补充已取得' if nasdaq else '部分：仅最新快照','S&P 2016-10-17—2026-10-14'+nasdaq_note,2608,'S&P 日期行；NASDAQ 数量见覆盖栏','标普 ALFRED 不支持历史版本，早于2016年仍缺；含非交易日缺失')
 add('M17','费城实时数据','已取得','参考期最早 1947；最新至 2026Q2/2026-07',9,'工作簿','8 份实时版本/首次三次估计工作簿及 1 份就业历史发布日；PCON 为构造的季度价格指数')
 for ds,name,kind in [('N01','纽约时报','nyt_articles'),('N02','Guardian','guardian_articles')]:
  articles=[r for r in by[ds] if r['record_type']==kind];n=sum(int(r['rows']) for r in articles)
  state_file=PROV/(ds+'_archive_state.json');news_state=json.loads(state_file.read_text()) if state_file.exists() else {}
  start=min((r['coverage_start'] for r in articles if r['coverage_start']),default='未取得');end=max((r['coverage_end'] for r in articles if r['coverage_end']),default='未取得')
  issue='官方密钥实测成功；按月保存全量文章元数据，不筛选；当前月部分，非新闻正文' if ds=='N01' else '官方密钥实测成功；business/useconomy 标签已核实；正文按实际字段保存，缺正文不补写；只覆盖该标签，不宣称美国经济报道总体完整'
  audit_file=PROV/'news_monthly_completeness.csv'
  checks=[r for r in csv.DictReader(audit_file.open()) if r['dataset_id']==ds] if audit_file.exists() else []
  if checks:
   issue+=f'；月内重复ID {sum(int(r["duplicate_ids"]) for r in checks)} 条；出版日期不在请求月份 {sum(int(r["dates_outside_month"]) for r in checks)} 条，原样保留'
   if ds=='N02':issue+=f'；缺正文 {sum(int(r["missing_bodyText"]) for r in checks)} 条'
  period=('请求月份 2009-12—2026-10；返回最晚出版时间 '+end+'；含异常日期，不以原始最小日期解释覆盖') if ds=='N01' else start+'—'+end
  add(ds,name,news_state.get('status','未启动'),period,n,'文章响应条目（不等于去重文章数）',issue)
 story=[r for r in by['N03'] if r['record_type']=='news_stories'];count=sum(int(r['rows']) for r in story)
 state_path=PROV/'mediacloud_collection_state.json';state=json.loads(state_path.read_text()) if state_path.exists() else {}
 complete=bool(state.get('collections')) and all(x['complete'] for x in state['collections']);error=any(x['error'] for x in state.get('collections',[]))
 title_start=min((r['coverage_start'] for r in story if r['coverage_start']),default='未取得');title_end=max((r['coverage_end'] for r in story if r['coverage_end']),default='未取得')
 collection_status='；'.join(x['name']+(' 完成' if x['complete'] else ' 错误暂停' if x['error'] else ' 进行中') for x in state.get('collections',[]))
 daily_path=PROV/'mediacloud_daily_state.json'
 if daily_path.exists():
  daily=json.loads(daily_path.read_text());collection_status='逐日轮转 '+daily['status']+'；'+str(sum(d['complete'] for d in daily['days']))+'/'+str(len(daily['days']))+' 集合日查询完成'
 add('N03','Media Cloud','计数已取得；'+collection_status,f'主计数 2010-01-01—2026-10-14；已下载标题 {title_start}—{title_end}（不连续全覆盖）',f'73572 / {count}','主日计数行 / 原始标题响应条目（批次重叠）','全国+地方各6条日序列；2请求/分钟；当前按天轮转；旧窗口与日批次重叠，不可相加为独立文章；逐日去重覆盖见 daily_coverage.csv；列表未完成；含非经济命中，未标注筛除')
 add('N04','GDELT','不可访问','未取得',0,'记录','间隔后以24小时请求复查仍 HTTP 429；停止，未绕过；实际历史边界未核实')
 add('N05','旧金山联储新闻情绪','已取得','1980-01-01—2026-10-11',17067,'每日指数行','Excel、2 CSV、复现 ZIP 均保留；不是原始新闻文章')
 add('N06','媒体倾向评级','数值评级未取得','未取得',0,'评级','AllSides HTTP 403；Ad Fontes 页面可达，免费教育图表要求姓名/邮箱表单并加入邮件列表；未替用户注册，静态图表也不等于数值评级数据库')
 sm=collections.Counter()
 for r in by['SM01']:
  if r['rows']:sm[r['record_type']]+=int(r['rows'])
 coverage=list(csv.DictReader((PROV/'youtube_coverage.csv').open()))
 text_path=PROV/'youtube_comment_text_state.json';text_state=json.loads(text_path.read_text()) if text_path.exists() else {}
 text_files=[r for r in by['SM01'] if r['record_type']=='comment_text'];text_start=min((r['coverage_start'] for r in text_files if r['coverage_start']),default='无');text_end=max((r['coverage_end'] for r in text_files if r['coverage_end']),default='无')
 add('SM01','YouTube','部分；评论正文任务 '+text_state.get('status','未启动'),f'视频优先 2023—2026-10-14；{sum(s["reached_2023_boundary"]=="True" for s in coverage)}/10 频道目录到达 2023 边界；评论正文 {text_start}—{text_end}',f'{sm["video_inventory"]} / {sm["video_statistics"]} / {sm["comment_metadata"]} / {sm["comment_text"]}','目录 / 视频统计 / 评论元数据 / 评论正文响应条目',f'另有 {sm["video_search_results"]} 条搜索结果；评论两批可能重叠，不能相加视为独立评论；正文获用户允许，排除作者字段；评论时间可晚于视频截止日；大频道目录止于20000条；已启动按天搜索补目录缺口，实际状态见 youtube_daily_search_state.json；2010–2022未采')
 reddit_file=PROV/'reddit_collection_state.json';reddit_state=json.loads(reddit_file.read_text()) if reddit_file.exists() else {}
 reddit_records=[r for r in by['SM02'] if r['record_type']=='reddit_posts']
 reddit_start=min((r['coverage_start'] for r in reddit_records if r['coverage_start']),default='未取得');reddit_end=max((r['coverage_end'] for r in reddit_records if r['coverage_end']),default='未取得')
 add('SM02','Reddit',reddit_state.get('status','未启动'),reddit_start+'—'+reddit_end,sum(int(r['rows']) for r in reddit_records),'非重叠时间区间帖子条目','用户已批准采集；Arctic Shift 社区存档，非 Reddit 官方 API；四子版块；按天广度优先，先2025年以来首轮，再2010—2024；排除作者身份字段；饱和探测页不重复计数；未采可选评论')
 for ds,name,file,unit,status,issue in [
  ('R01','发布日历','release_calendar.csv','日历行','已取得可得日历','实际发布、ALFRED版本、未来计划分别标识；BLS网页403，FRED日历已取得'),
  ('R02','重大事件','events.csv','已核实事件','部分','FOMC声明及部分疫情/银行/关税/停摆；未宣称穷尽；CBO/GAO源403'),
  ('R03','政治日历','political_elections.csv','选举日期','已取得','另保存总统任期与两院党派构成官方表'),
 ]:
  a=list(csv.DictReader((PROV/file).open()));key='release_date' if ds=='R01' else 'date';add(ds,name,status,min(r[key] for r in a)+'—'+max(r[key] for r in a),len(a),unit,issue)
 add('R04','Pew 平台使用率','已取得','2025-02-05—2025-06-18',1,'公开报告，原调查 n=5022','YouTube84%、Facebook71%、Instagram50%、TikTok37%、Reddit26%核对；未下载调查个体数据')
 add('R05','SPF 专业预测','已取得','工作簿总体 1968Q4—2026Q3',2,'完整工作簿','各变量开始时间不同；PCE 不能当成自1968年都有')
 rows.sort(key=lambda r:(['S','M','N','SM','R'].index('SM' if r['dataset_id'].startswith('SM') else r['dataset_id'][0]),int(r['dataset_id'].lstrip('SMNR'))))
 with (PROV/'dataset_status.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
 now=dt.datetime.now(dt.timezone.utc).isoformat();registered_files=len(inv)
 lines=['# 数据收集状态快照','',f'生成时间：{now}。截止日：2026-10-14。**尚未全部完成**：存在限速分页、来源限制和历史缺口；下列数字仅为此快照。','',
 '教授 Excel 的 **PCE YoY 是核心 PCE**；584 个月与核心 PCE 匹配。总体 PCE 已单独收集。原 Excel 和原下载文件没有改写。','',
 '| 数据集 | 状态 | 实际/请求覆盖期 | 条目数（单位） | 问题 |','|---|---|---|---|---|']
 for r in rows:lines.append(f'| {r["dataset_id"]} {r["dataset"]} | {r["status"]} | {r["coverage"]} | {r["entries"]}（{r["unit"]}） | {r["issues"]} |')
 lines+=['','登记文件：'+str(registered_files)+' 份；'+str(len(macro))+' 条可用 ALFRED 序列分页完整，无重复版本键、未来版本或观测日晚于版本日。','',
 '用户决定已落实：YouTube 可保存评论正文，排除全部作者身份字段；取消自设单轮请求总数和单视频评论截断，遇接口真实错误才停止。NYT/Guardian 已使用用户密钥执行官方 API 采集。Reddit 已批准并启动；不再暂缓。','',
 '关键核对及局限：2025-01 ICS 71.1→71.7 是官方修订；教授表2026-10 ICS=46.3 已由官网首页确认为初值；2026Q3 GDP=3.7仍未作为已核实官方值入库。新闻20链接检查有6个不可读响应、7个标题差异及3个可读日期差异，详见 news_url_spotcheck.csv。','',
 '后台进度以 mediacloud_daily_state.json、youtube_daily_search_state.json、youtube_comment_text_state.json、reddit_collection_state.json 为准，旧 supervisor 已替代；不是定时任务。按天优先补覆盖，逐日快照见 daily_coverage.csv。后续批次仍需再次核对库存；本报告不保证未来页面可得。','',
 '详细证据：sources.csv（来源、UTC下载时刻、覆盖）、inventory.csv（逐文件条目数）、macro_completeness.csv、release_calendar.csv、excel_reconciliation.md、../DECISIONS.md。原始数据与受版权内容仅保留在本地，不打包公开。']
 (PROV/'collection_report.md').write_text('\n'.join(lines)+'\n')
 print('Status rows:',len(rows),'registered files:',registered_files)

if __name__=='__main__':main()
