# 数据收集方案

> 版本：v1.0，2026-10-15 编写。
> 上位文档：[task_guide.md](task_guide.md)（总体规划）。本文档只负责“收集什么、去哪里收集、怎么收集、按什么顺序、收完怎么检查”。研究设计、建模和报告不在本文档范围内。若两份文档冲突，以 PDF 原文为准，其次以总体规划为准，并在 `DECISIONS.md` 中记录冲突。
> 标注约定：**【需核实】** 表示编写时未能直接验证，收集前必须核对；**【推断】** 表示判断而非事实；P0 为 PDF 明确要求，P1 为替代解释、机制或验证所需，P2 为可选。

---

## 目录

1. 收集原则与红线
2. 总览：数据集清单
3. 准备工作：账号、密钥、网络与目录
4. 统一的存储、命名与来源登记规范
5. 调查数据（S 组）
6. 宏观经济数据与历史版本（M 组）
7. 新闻数据（N 组）
8. 社交媒体数据（SM 组）
9. 参考与事件数据（R 组）
10. 收集顺序与分工
11. 收集完成后的检查
12. 无法提前收集的数据与后续更新
13. 收集完成清单

---

## 1. 收集原则与红线

1. **只收集真实数据，不编造、不模拟、不凭记忆填写**。拿不到的就记为缺失并写明原因。
2. **原始数据一律原样保存，不可修改**。清洗与变换放到后续步骤，在 `data/interim/` 或 `data/processed/` 中进行。
3. **每一份下载都要登记来源**（第 4.3 节），包括 URL、下载时间、文件校验值和使用条款要点。
4. **宏观数据必须保留历史版本与发布日期**。PDF 要求只用每个预测时点已公开的信息，所以只下载最新值是不够的。
5. **遵守各数据源的使用条款和速率限制**。不得用多个账号或多个 API 项目绕过配额，不得使用来源不明的抓取工具。受版权保护的全文只供内部分析，不放进提交包。
6. **保护隐私**：社交媒体数据不保存用户名、头像、个人主页链接；作者 ID 一律做不可逆哈希。
7. **密钥只存放在环境变量或本地 `.env` 文件中**，不得写入共享文件夹、代码、日志或记忆。
8. **收集范围以“够用”为准**：PDF 要求的控制变量是“可管理的一组”，不要无限扩张。

---

## 2. 总览：数据集清单

| 编号 | 数据集 | 优先级 | 来源 | 需要账号 | 预计耗时【推断】 |
|---|---|---|---|---|---|
| S01 | 密歇根 ICS、ICC、ICE 月度序列 | P0 | 密歇根大学官网 | 否 | 数分钟 |
| S02 | 密歇根分组指数（收入、年龄、教育、地区、党派） | P1 | 同上 | 否 | 数分钟 |
| S03 | 密歇根“听到的新闻” | P1 | 同上 | 否 | 数分钟 |
| S04 | 密歇根原因、预期与购买条件表 | P1 | 同上 | 否 | 数分钟 |
| S05 | 密歇根初值与终值及发布日期、方法文件、党派报告 | P0 | 同上 | 否 | 1 小时（需逐月整理） |
| S06 | 密歇根个体层面数据 | P2 | 同上（Cross-Section Archive） | 视情况 | 先核实可得性 |
| M01–M04 | 失业率、总体 PCE 价格指数、实际 GDP 水平、实际 GDP 环比折年率（全部历史版本） | P0 | ALFRED | FRED API key（免费） | 1 小时 |
| M05–M16 | 核心 PCE、U-6、实际收入、汽油、食品、房贷利率、偿债负担、政策不确定性、住房可负担性、实际消费、房价、股市 | P1 或 P2 | FRED、ALFRED、各机构官网 | 同上 | 1–2 小时 |
| M17 | 费城联储实时数据集（交叉核对） | P2 | 费城联储 | 否 | 30 分钟 |
| N01 | 纽约时报文章元数据（2009-12 至今） | P0 | NYT Archive API | NYT 开发者 key（免费） | 约 1 小时（受速率限制） |
| N02 | Guardian 美国经济报道（含全文） | P1 | Guardian Open Platform | Guardian key（免费） | 1–3 小时 |
| N03 | Media Cloud 全国与地方新闻计数和标题 | P0（地方新闻的主要来源） | Media Cloud | 免费账户 | 1–3 小时 |
| N04 | GDELT 新闻量与语气时间线（2017 年起）及监测窗口文章列表 | P1 | GDELT DOC 2.0 API | 否 | 1 小时 |
| N05 | 旧金山联储每日新闻情绪指数 | P1 | 旧金山联储官网 | 否 | 数分钟 |
| SM01 | YouTube 新闻频道经济类视频及评论 | P0（主社交平台） | YouTube Data API v3 | Google Cloud API key（免费） | 1–3 天（受每日配额限制） |
| SM02 | Reddit 经济类子版块帖子 | P1 | Arctic Shift 存档或 Reddit 官方 API | 视渠道 | 数小时 |
| R01 | 经济数据发布日历（历史与未来） | P0 | ALFRED、BLS、BEA、密歇根 | 否 | 1 小时 |
| R02 | 重大事件时间表 | P1 | 各官方来源 | 否 | 1–2 小时 |
| R03 | 政治日历 | P1 | 官方来源 | 否 | 30 分钟 |
| R04 | 媒体与社交平台使用率 | P1 | Pew Research Center | 否 | 30 分钟 |
| R05 | 专业预测（用于计算数据“意外”） | P2 | 费城联储专业预测者调查（SPF） | 否 | 30 分钟 |
| N06 | 媒体倾向评级 | P2 | AllSides 或 Ad Fontes Media | 视许可 | 先核实许可 |

---

## 3. 准备工作

### 3.1 账号与密钥（由用户注册，全部免费）

| 用途 | 名称 | 环境变量名【默认】 |
|---|---|---|
| ALFRED 与 FRED | FRED API key（<https://fred.stlouisfed.org/docs/api/api_key.html>） | `FRED_API_KEY` |
| 纽约时报 | NYT Developer key（<https://developer.nytimes.com/>，启用 Archive API） | `NYT_API_KEY` |
| Guardian | Open Platform developer key（<https://open-platform.theguardian.com/>） | `GUARDIAN_API_KEY` |
| Media Cloud | 账户与 API token（<https://search.mediacloud.org/>） | `MEDIACLOUD_API_KEY` |
| YouTube | Google Cloud 项目中启用 YouTube Data API v3 并创建 API key | `YOUTUBE_API_KEY` |
| Reddit（可选） | 已获批的应用的 client ID 与 secret | `REDDIT_CLIENT_ID`、`REDDIT_CLIENT_SECRET` |
| BLS（可选） | BLS API v2 注册 key（<https://data.bls.gov/registrationEngine/>） | `BLS_API_KEY` |
| BEA（可选） | BEA API key（<https://apps.bea.gov/api/signup/>） | `BEA_API_KEY` |

### 3.2 网络

收集必须在能访问以下域名的环境中进行：`sca.isr.umich.edu`、`data.sca.isr.umich.edu`、`api.stlouisfed.org`、`fred.stlouisfed.org`、`alfred.stlouisfed.org`、`api.bls.gov`、`www.bls.gov`、`apps.bea.gov`、`www.bea.gov`、`api.nytimes.com`、`content.guardianapis.com`、`search.mediacloud.org`、`api.gdeltproject.org`、`www.frbsf.org`、`www.googleapis.com`、`arctic-shift.photon-reddit.com`（或 `oauth.reddit.com`）、`www.philadelphiafed.org`、`www.policyuncertainty.com`、`www.atlantafed.org`、`www.pewresearch.org`、`www.federalreserve.gov`。可以在项目设置中添加允许这些域名的云端环境，或在用户自己的电脑上运行收集脚本。开始前先对每个域名发一个简单请求测试连通性，并把结果记入日志。

### 3.3 目录

沿用总体规划第 6.1 节，收集相关的部分如下：

```
/mnt/project-files/final_project/
├── provenance/
│   ├── sources.csv            # 每次下载一行（第 4.3 节）
│   ├── collection_log.md      # 收集过程记录：日期、执行者、问题
│   └── release_calendar.csv   # R01
├── data/raw/<数据集编号>/<下载日期 YYYYMMDD>/   # 原始文件，不可修改
├── corpus/raw/<数据集编号>/<下载日期>/          # 文本类原始数据
└── src/collect/<数据集编号>.py                 # 每个数据集一个收集脚本
```

---

## 4. 统一规范

### 4.1 脚本

- 每个数据集一个脚本 `src/collect/<编号>.py`，可重复运行。
- 支持断点续传：已下载的文件跳过；每个请求的响应原样缓存。
- 遵守速率限制：在两次请求之间等待；遇到 HTTP 429 时按 `Retry-After` 或指数退避重试，最多 5 次。
- 所有时间使用 UTC，并保存时区信息。
- 脚本结束时打印摘要：请求数、成功数、失败数、行数、时间范围。

### 4.2 文件命名

`data/raw/<编号>/<YYYYMMDD>/<来源原始文件名或查询描述>.<扩展名>`。分页结果按页码编号。不要重命名官方下载的文件，以便追溯。

### 4.3 来源登记 `provenance/sources.csv`

| 列 | 含义 |
|---|---|
| `dataset_id` | 例如 M02 |
| `file_path` | 相对路径 |
| `source_name` | 例如 ALFRED |
| `url_or_endpoint` | 完整 URL 或接口及参数（去掉密钥） |
| `downloaded_at_utc` | 下载时间 |
| `sha256` | 文件校验值 |
| `rows` | 行数或条目数 |
| `coverage_start`、`coverage_end` | 覆盖期 |
| `vintage_or_release` | 数据版本或发布日期 |
| `license_note` | 使用条款要点，例如“仅供非商业研究，不得再分发全文” |
| `collector` | 执行者 |
| `notes` | 其他问题 |

---

## 5. 调查数据（S 组）

来源：密歇根大学 Surveys of Consumers。数据表页：<https://data.sca.isr.umich.edu/tables.php>。时间序列文件：<https://www.sca.isr.umich.edu/tables.html>。使用前阅读站点页脚的使用协议，并把要点写入 `license_note`【需核实】。

### S01 消费者信心三项指数（P0）

- **文件**：月度 ICS `https://www.sca.isr.umich.edu/files/tbmics.csv`；月度分项 `https://www.sca.isr.umich.edu/files/tbmiccice.csv`（同名 `.xls` 和 `.pdf` 也可用；文件名格式已核实，内容为 ICC 与 ICE【推断】，下载后确认列名）。另下载数据表页的表 1a、1b 的 Excel 版本作为核对。
- **覆盖**：全部历史（1978 年起），主分析用 2010 年起。
- **检查**：2026-05 的 ICS 应为 44.8，2022-06 应为 50.0（来源：密歇根 2026 年 7 月党派报告）；与教授 Excel 的信心列逐月比对。

### S02 分组指数（P1）

- **内容**：表 2n（收入三分位）、3n（年龄）、4n（教育）、5a（地区）、5b（政治党派）的 ICS、ICC、ICE。
- **方法**：从数据表页下载各表的 Excel 版本；若只有 PDF，用表格抽取工具转换后逐行核对。另查看网站的 “Time Series Demographics” 页面是否有更完整的分组时间序列【需核实】。
- **注意**：党派自 2017 年 2 月起每月询问（来源：密歇根党派报告）；党派报告中的图使用三个月移动平均，而表 5b 可能是月度值，下载后确认。

### S03 听到的新闻（P1）

- **内容**：表 23（听到的商业状况变化新闻，有利、不利）、表 24（具体新闻条目）。
- **用途**：消费者端的“回忆”代理变量，用于回应 PDF 中“认知偏差的主张需要接触或回忆证据”的要求。
- **检查**：确认问题措辞与编码在 2024 年方法转换前后是否一致。

### S04 原因、预期与购买条件（P1）

- 表 7（对个人财务状况看法的原因，包括提到高物价的比例）。
- 表 32、33（一年和五年通胀预期）；或时间序列文件 `tbmpx1px5.csv`。
- 表 35–38（耐用品与汽车购买条件及原因）、41、42（住房购买条件及原因）。
- P2：表 30（失业预期）、31（利率预期）、34（对政府经济政策的评价）。

### S05 发布信息与方法文件（P0）

- **初值与终值**：从 <https://data.sca.isr.umich.edu/reports.php?year=2026> 及其他年份的报告页，记录每月初值与终值的数值和发布日期，写入 `data/raw/S05/release_values.csv`（列：`month, prelim_value, prelim_release_date, final_value, final_release_date, source_url`）。至少覆盖 2024 年以来；更早的月份若无法逐月整理，以终值为准并在日志中说明。
- **方法文件**：方法转换公告 <https://www.sca.isr.umich.edu/files/methodtransitionannouncement2024.pdf>、2026 年的方法与党派报告（如 `partisaneconomy202607_revised.pdf`、`partisaneconomy202504.pdf`、`partisaneconomy202402.pdf`）、调查说明页与技术文档。全部 PDF 存档。
- **已知事实**（已核实，可用于检查）：2024 年 4、5、6 月网络访谈比例分别为 25%、50%、75%，7 月起全部为网络访谈；每月约 900–1,000 份访谈。

### S06 个体层面数据（P2）

网站有 Cross-Section Archive。先核实访问条件、更新时滞和许可；如果可以获得近年数据，可用于按党派、收入的更细分析。不可得就跳过并记录。

---

## 6. 宏观经济数据与历史版本（M 组）

### 6.1 通用方法：ALFRED 全部历史版本

- **接口**：`https://api.stlouisfed.org/fred/series/observations`，参数 `series_id=<ID>`、`realtime_start=1776-07-04`、`realtime_end=9999-12-31`、`observation_start=<起始>`、`file_type=json`、`api_key=<FRED_API_KEY>`。返回的每条观测都带 `realtime_start` 和 `realtime_end`，表示该数值有效的时间段；`realtime_start` 即发布日期。单次请求有条数上限，超过时用 `offset` 翻页【需核实上限数值】。
- **发布日期列表**：`https://api.stlouisfed.org/fred/series/vintagedates?series_id=<ID>`，用于 R01。
- **无 key 的备选**：ALFRED 网页的 “Download Data”，选择版本日期，导出压缩的 Excel 或制表符文本（已核实）。
- **观测起点**：【默认】`observation_start=2008-01-01`，保证 2010 年起的同比计算有 12 个月或 4 个季度的前置数据。若要做 1978 年起的长样本稳健性检验，再下载 1977 年起的数据。
- **当前最新值**：同时保存一份 `https://fred.stlouisfed.org/graph/fredgraph.csv?id=<ID>`，方便与教授 Excel 对比。
- **重要**：BEA 的全面修订会改变价格指数和实际 GDP 的基期（例如从 2012 = 100 改为 2017 = 100），所以同比只能在**同一版本内部**计算，绝不能跨版本拼接水平值。

### 6.2 数据集明细

| 编号 | 指标 | 序列 ID | 频率 | 下载方式 | 优先级 | 说明 |
|---|---|---|---|---|---|---|
| M01 | U-3 失业率（季调） | `UNRATE`（BLS `LNS14000000`） | 月 | ALFRED 全部版本 | P0 | 2025-10 官方无数据（BLS 因政府停摆未收集，已核实）；每年 1 月修订季节因子 |
| M02 | 总体 PCE 价格指数 | `PCEPI` | 月 | ALFRED 全部版本 | P0 | 用于按 PDF 公式计算同比 |
| M03 | 实际 GDP 水平 | `GDPC1` | 季 | ALFRED 全部版本 | P0 | 用于计算同比 |
| M04 | 实际 GDP 环比折年率 | `A191RL1Q225SBEA` | 季 | ALFRED 全部版本 | P0 | 记录估计类型（初值、第二次、第三次、年度修订），可由发布日期与 BEA 日程对应 |
| M05 | 核心 PCE 价格指数 | `PCEPILFE` | 月 | ALFRED | P1 | 用于确认教授 Excel 的口径 |
| M06 | U-6 | `U6RATE`（BLS `LNS13327709`） | 月 | ALFRED | P1 | 劳动力未充分利用 |
| M07 | 实际可支配收入（总量与人均） | `DSPIC96`、`A229RX0` | 月 | ALFRED | P1 | 实际家庭收入的代理 |
| M08 | 汽油零售价 | `GASREGW` | 周 | FRED 最新值 | P1 | 每周一发布，一般不修订；按发布日对齐 |
| M09 | 食品价格（CPI） | `CPIUFDSL`、家庭食品 `CUSR0000SAF11` | 月 | ALFRED | P1 | 可得性机制 |
| M10 | 30 年期房贷利率 | `MORTGAGE30US` | 周 | FRED 最新值 | P1 | 每周四发布，不修订 |
| M11 | 家庭偿债负担 | `TDSP` | 季 | ALFRED | P1 | 季度，按发布时间对齐，不插值 |
| M12 | 经济政策不确定性 | `USEPUINDXM`；原始文件 <https://www.policyuncertainty.com/us_monthly.html> | 月 | 两处都下载 | P1 | 记录下载日期（数值可能随新报纸样本更新）；它本身来自报纸文本，与媒体测量有重叠 |
| M13 | 住房可负担性 | 亚特兰大联储 Home Ownership Affordability Monitor【需核实网址、格式与覆盖期】；备选 NAR 住房可负担指数【需核实许可】 | 月 | 官网下载 | P1 | 不可得时用房价与房贷利率组合代替，并记录 |
| M14 | 实际个人消费支出 | `PCEC96` | 月 | ALFRED | P2 | 用于演示中“对消费预测的启示” |
| M15 | 房价 | `CSUSHPISA` | 月 | FRED | P2 | 财富效应 |
| M16 | 股票市场 | 例如 `SP500` | 日 | FRED | P2 | FRED 上的标普 500 可能只有近 10 年【需核实】，需要时另找来源 |
| M17 | 费城联储实时数据集 | <https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/real-time-data-set-for-macroeconomists> | 月、季 | 直接下载 Excel | P2 | 交叉核对 ALFRED；是否包含 PCE 价格指数【需核实】 |

### 6.3 宏观数据的特别检查

1. 用 M02 最新版本按 100 ×（P_t / P_{t−12} − 1）计算总体 PCE 同比，再用 M05 计算核心 PCE 同比，分别与教授 Excel 的 “PCE YoY” 列对比，确认 Excel 是哪个口径，结果写入 `provenance/excel_reconciliation.md`。
2. 确认 M01 中没有 2025-10 的任何版本。
3. 确认 M04 最新版本中是否已有 2026Q3。若没有，说明教授 Excel 中的 3.7 不是 BEA 官方值，需继续追查来源。
4. 抽查几个版本：例如某季度 GDP 的初值、第二次、第三次估计，与 BEA 当时的新闻稿数值一致。

---

## 7. 新闻数据（N 组）

文本单位、检索词和纳入标准见总体规划第 8.2 节。本节只写获取方法。所有新闻原始响应都只供内部分析，提交包中只保留 ID、URL、标题和派生标签。

### N01 纽约时报（P0，全国性，2010 年起历史主来源）

- **接口**：Archive API `https://api.nytimes.com/svc/archive/v1/{year}/{month}.json?api-key=<NYT_API_KEY>`。每个请求返回该月全部文章的元数据（包括标题、摘要、署名、栏目、关键词和 URL，不含正文）。覆盖 1851 年至今。
- **范围**：2009-12 至最新月份，约 203 次请求。
- **速率**：开发者层级约每分钟 5 次、每天 500 次【需核实】。【默认】每次请求间隔 13 秒。全部历史一次即可完成。
- **存储**：每月响应原样保存为 `corpus/raw/N01/<下载日期>/<YYYY>-<MM>.json`。
- **字段**：下载第一个月后，列出实际字段（如 `headline.main`、`abstract`、`lead_paragraph`、`snippet`、`pub_date`、`section_name`、`news_desk`、`type_of_material`、`keywords`、`web_url`、`word_count`）并写入日志【需核实，接口字段可能已调整】。若首段字段缺失，文本单位改为“标题 + 摘要”，并修改总体规划的 D10。
- **初筛**：收集阶段不做筛选，保存全部文章；筛选在清洗步骤进行。
- **检查**：每月文章数不为零；画出每月文章数的走势，检查异常的缺口或跳变。

### N02 Guardian（P1，全国性报道，有全文）

- **接口**：`https://content.guardianapis.com/search`，主要参数：`q`（经济检索词，可用 AND、OR）、`section`（如 `business`、`us-news`）或 `tag`（美国经济相关标签，例如 `business/useconomy`【需核实标签 ID】）、`from-date`、`to-date`、`show-fields=headline,trailText,bodyText,byline,wordcount`、`page-size`、`page`、`order-by=oldest`、`api-key`。
- **范围**：2010-01 至今，按月分片查询以便断点续传。
- **速率**：以注册时页面说明为准【需核实】。
- **注意**：Guardian 是英国媒体的美国版，报告中需说明；全文受版权保护，只作内部分析。

### N03 Media Cloud（P0，地方新闻的主要来源）

- **工具**：Python 包 `mediacloud`（PyPI），使用其搜索 API（`SearchApi`），需要 API token。
- **集合**：在 Source Manager 中查找“United States - National”与“United States - State & Local”两个集合的 ID【需核实名称和 ID】，以及各州的 State & Local 集合（如需按州分析）。
- **获取内容**：
  1. 按主题组检索词，获取两个集合的每日报道数（关注度时间序列），以及每日全部报道数（用作分母）。
  2. 获取监测窗口（2025-01 至今）的报道列表（标题、URL、媒体名称、发布日期）。
- **覆盖期**：先查询并记录两个集合的最早可用日期【需核实】。若覆盖期短于 2010 年起，地方新闻只用于监测窗口与近年对比，结论相应收窄。
- **全文**：是否提供正文【需核实】；若只有标题，地方新闻的文本单位为标题。

### N04 GDELT DOC 2.0（P1，2017 年起的量与机器语气）

- **接口**：`https://api.gdeltproject.org/api/v2/doc/doc`，无需 key。参数：`query`（检索词，加 `sourcecountry:US`、`sourcelang:english`）、`mode`（`timelinevolraw` 为原始数量，`timelinetone` 为平均语气，`artlist` 为文章列表）、`startdatetime` 与 `enddatetime`（格式 YYYYMMDDHHMMSS）、`format=json`、`maxrecords`（文章列表最多 250）。
- **覆盖**：2017-01-01 至今。时间线模式覆盖全期；文章列表模式只返回所选窗口最后三个月的结果（已核实）。
- **获取内容**：各主题组 2017 年至今的每日数量与语气时间线；监测窗口按天分片抓取文章列表（标题、URL、域名、日期）。
- **用途**：只作外部对比，不作为主要的自建测量。

### N05 旧金山联储每日新闻情绪指数（P1，外部基准）

- **页面**：<https://www.frbsf.org/research-and-insights/data-and-indicators/daily-news-sentiment-index/>。
- **下载**：完整数据 Excel、两份 CSV 和复现代码 ZIP 全部保存（已核实可下载）。
- **说明**：基于 24 家美国主要报纸，1980 年起，每周更新。用于验证自建语气指数。

### N06 媒体倾向评级（P2）

若需要按来源立场分组，可使用 AllSides 或 Ad Fontes Media 的评级。先核实许可条款，许可不允许时跳过。

---

## 8. 社交媒体数据（SM 组）

### SM01 YouTube（P0，主社交平台）

**配额（以官方页面为准，编写时的说明）**：默认每天 100 次 `search.list` 调用，加上其他接口合计 10,000 单位；列表类读取通常每次 1 单位。可通过官方表格申请提高配额。不得用多个项目绕过配额。

**步骤**：

1. **确定频道清单**（写入 `data/raw/SM01/channels.csv`，列：频道名称、频道 ID、类型（全国或地方）、所在州、立场备注、选择理由）。【默认】全国：CNN、Fox News、NBC News、ABC News、CBS News、CNBC、Bloomberg Television、PBS NewsHour。地方：若干个大城市或摇摆州的地方电视台频道。用 `channels.list`（参数 `forHandle` 或 `id`，`part=snippet,contentDetails,statistics`）获取频道 ID、订阅数和 uploads 播放列表 ID。
2. **获取视频清单**：用 `playlistItems.list`（`playlistId=<uploads 播放列表>`、`part=snippet,contentDetails`、`maxResults=50`）翻页获取全部视频。大型频道视频很多，需要较多请求。uploads 播放列表能否返回全部历史视频【需核实】：若最早只能取到某个日期，则对更早的年份改用 `search.list`（`channelId`、`publishedAfter`、`publishedBefore`、`q=<经济检索词>`、`type=video`），每天最多 100 次，按年份和频道分配，优先保证每个季度都有样本。
3. **筛选经济类视频**：按标题和描述匹配经济检索词（总体规划第 8.2 节），筛选规则写入文档，抽查 100 条计算准确率。
4. **获取视频统计**：`videos.list`（`part=snippet,statistics,contentDetails`，每次最多 50 个 ID）获取播放量、点赞数、评论数、时长。注意这些统计是抓取当天的累计值，不是视频发布时的值，必须记录抓取时间。
5. **获取评论**：`commentThreads.list`（`videoId`、`part=snippet`、`maxResults=100`、`textFormat=plainText`）。接口只能按时间倒序或相关性排序，无法直接取“最早的评论”，因此【默认】对每个视频翻页取全部顶层评论，单个视频上限 2,000 条；分析时按评论自己的时间戳，只保留视频发布后 30 天内的评论。达到上限的视频要记录，因为它们的早期评论可能没有取全。评论被关闭的视频记录为缺失。
6. **隐私处理**：保存时丢弃作者显示名、头像和频道链接，作者频道 ID 做加盐哈希（盐值存放在环境变量中）。
7. **存储**：`corpus/raw/SM01/<下载日期>/videos.jsonl`、`comments/<videoId>.jsonl`。
8. **配额计划**：先估计各频道视频数与评论页数，按天分批，写入 `collection_log.md`。若配额不够，优先保证：2023 年至今全覆盖；2010–2022 年按季度抽样。

**局限（写进语料文档）**：评论者是自选的少数人；已删除的视频与评论无法获得；推荐算法影响曝光；统计值是抓取时的累计值。

### SM02 Reddit（P1，辅助对比）

- **渠道一：官方 API**。2025 年 11 月起不再自助开通，需按 Reddit 的 Responsible Builder Policy 申请并等待人工审批（来源：n8n 文档）。若用户已有获批应用，可用 OAuth 访问；官方接口的列表只能回溯有限条数，不适合取历史数据。
- **渠道二：Arctic Shift 社区存档**（<https://arctic-shift.photon-reddit.com>）。提供 API、按子版块的下载工具，以及 Academic Torrents 上的完整存档。API 没有可用性保证，有速率限制；大规模数据建议用存档文件。该站未声明数据许可【需核实 README】，与 Reddit 用户协议的关系不明确。**使用前须征得授课教授同意**，并在报告中披露。
- **子版块**【默认】：r/economy、r/Economics、r/personalfinance、r/inflation。记录每个子版块的订阅数与选择理由。
- **单位**：帖子（标题 + 正文）；评论可选，只在监测窗口抓取。
- **范围**：2010-01 至今（若用存档）；只用官方 API 时仅限近期。
- **隐私**：丢弃用户名，作者 ID 做加盐哈希。

---

## 9. 参考与事件数据（R 组）

### R01 经济数据发布日历（P0）

- **历史发布日期**：由 ALFRED 的 `vintagedates` 接口得到各序列的每次发布日期；密歇根的初值与终值发布日期来自 S05。
- **未来发布日期**：BLS 发布日程 <https://www.bls.gov/schedule/>；BEA 发布日程 <https://www.bea.gov/news/schedule>；密歇根报告页。
- **输出**：`provenance/release_calendar.csv`，列：`indicator, reference_period, release_date, release_type（advance、second、third、annual、prelim、final 等）, source_url`。
- **用途**：构造实时数据集、标注仪表盘上的发布事件、做“发布后 0–2 天”的报道分析。

### R02 重大事件时间表（P1）

- **内容**：FOMC 会议与决议日期（<https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm>）、政府停摆起止日期、重大关税公告、疫情关键日期、重大金融事件。
- **方法**：人工整理，每个事件必须有官方或权威来源 URL。只收录与经济相关、且能明确定日的事件。
- **输出**：`data/raw/R02/events.csv`，列：`date, event, category, source_url`。

### R03 政治日历（P1）

- **内容**：历任总统及任期、国会两院多数党、2010 年以来的选举日（2010、2012、2014、2016、2018、2020、2022、2024、2026 年；2026 年中期选举为 11 月 3 日）。
- **用途**：执政党虚拟变量、选举前同期比较。

### R04 媒体与社交平台使用率（P1）

- **内容**：Pew Research Center 的社交媒体使用调查（<https://www.pewresearch.org/internet/2025/11/20/americans-social-media-use-2025>）、新闻平台与新闻来源使用的相关报告。
- **用途**：说明各平台的代表性、讨论接触与可迁移性。
- **已核实的数值**：美国成年人使用率 YouTube 84%、Facebook 71%、Instagram 50%、TikTok 37%、Reddit 26%（2025 年 2 月 5 日至 6 月 18 日调查，5,022 名成年人）。

### R05 专业预测（P2）

- **内容**：费城联储专业预测者调查（SPF）对失业率、实际 GDP 增长和 PCE 通胀的预测。
- **用途**：计算数据发布的“意外”。月度数据的市场一致预期通常不免费；不可得时用“实际值 − 上期值”或简单模型预测作为替代，并在报告中说明。

---

## 10. 收集顺序与分工

### 10.1 阶段

| 阶段 | 内容 | 依赖 | 说明 |
|---|---|---|---|
| 0 准备 | 账号与密钥、网络连通性测试、目录与 `sources.csv` | 无 | 必须最先完成 |
| 1 快速、小体量 | S01–S05、M01–M17、N05、R01、R03、R04 | 阶段 0 | 数据量小，几小时内可完成；完成后可立即开始经济基线分析 |
| 2 新闻 | N01、N03、N04、N02 | 阶段 0 | 受速率限制；N01 优先，它是历史媒体指数的主来源 |
| 3 社交 | SM01、SM02 | 阶段 0；SM02 需等教授答复 | SM01 受每日配额约束，**应在第一天就开始**，与阶段 1、2 并行 |
| 4 补充 | R02、R05、M13 的替代方案、N06、S06 | 阶段 1 | 人工整理较多 |
| 5 检查 | 第 11 节的全部检查；与教授 Excel 对账 | 阶段 1–4 | 检查通过后才交给分析工作流 |

### 10.2 并行分工【默认】

| 执行者 | 负责 | 交付 |
|---|---|---|
| 收集者甲 | S 组、M 组、R01、R03、R05 | `data/raw/S*`、`data/raw/M*`、`release_calendar.csv`、`excel_reconciliation.md` |
| 收集者乙 | N 组、R02、R04 | `corpus/raw/N*`、`events.csv` |
| 收集者丙 | SM 组 | `corpus/raw/SM*`、`channels.csv`、配额与抽样记录 |

每个执行者只写自己负责的目录；`sources.csv` 和 `collection_log.md` 是共享文件，追加写入，写入前重新读取，写入后约十秒再读一次确认没有被覆盖。

---

## 11. 收集完成后的检查

每个数据集完成后填写检查结果（写入 `collection_log.md`）：

**通用检查**
- [ ] `sources.csv` 中有对应记录，校验值正确
- [ ] 覆盖期与预期一致，记录实际起止日期
- [ ] 按月统计条目数或观测数，没有无法解释的缺口或重复
- [ ] 缺失的期间写明原因（官方未发布、接口限制、配额不足等）
- [ ] 原始文件未被修改

**宏观与调查**
- [ ] 第 6.3 节的四项检查
- [ ] 每个版本的发布日期都不晚于其下载日期，且观测期早于发布日期
- [ ] S01 与 S05 的终值一致；2026-10 等最新月份标注为初值或终值
- [ ] 2024-04 至 2024-06 方法转换期在数据中有标记

**文本**
- [ ] 抽查 20 条记录的 URL 可打开，标题与日期正确
- [ ] 检索词命中率与纳入准确率的抽查结果已记录
- [ ] 社交媒体数据中没有用户名或可识别个人的信息
- [ ] 达到上限或抽样的部分有记录

---

## 12. 无法提前收集的数据与后续更新

以下数据不能在收集阶段完成，需要在分析过程中产生或在之后更新：

| 内容 | 原因 | 处理 |
|---|---|---|
| 人工标注 | 需要在语料清洗、抽样后由两名真人完成 | 用户自行安排 |
| LLM 标注 | 需要先有编码手册和抽样 | 工作流 C |
| 事实校准所需的“发布时官方值” | 不需要另外收集：由 M 组的历史版本提供 | 按文章发布日期查询当时最新版本 |
| 选举前后新发布的数据 | 尚未发布 | 按 R01 的未来发布日期更新；预计包括：密歇根 10 月终值、第三季度 GDP 初值、9 月 PCE、10 月就业报告、选举后的密歇根 11 月初值【需核实具体日期】 |
| 新的新闻与社交媒体内容 | 持续产生 | 更新脚本按增量抓取，从上次截止时间开始 |

更新时运行同一套收集脚本，新下载放入新的日期目录，不覆盖旧文件，并在 `sources.csv` 中追加记录。

---

## 13. 收集完成清单

| 编号 | 状态 | 实际覆盖期 | 条目数 | 执行者 | 完成日期 | 备注 |
|---|---|---|---|---|---|---|
| S01 | 未开始 | | | | | |
| S02 | 未开始 | | | | | |
| S03 | 未开始 | | | | | |
| S04 | 未开始 | | | | | |
| S05 | 未开始 | | | | | |
| S06 | 未开始 | | | | | P2 |
| M01 | 未开始 | | | | | |
| M02 | 未开始 | | | | | |
| M03 | 未开始 | | | | | |
| M04 | 未开始 | | | | | |
| M05–M12 | 未开始 | | | | | |
| M13 | 未开始 | | | | | 需核实来源 |
| M14–M17 | 未开始 | | | | | P2 |
| N01 | 未开始 | | | | | |
| N02 | 未开始 | | | | | |
| N03 | 未开始 | | | | | |
| N04 | 未开始 | | | | | |
| N05 | 未开始 | | | | | |
| N06 | 未开始 | | | | | P2 |
| SM01 | 未开始 | | | | | |
| SM02 | 未开始 | | | | | 待教授同意 |
| R01 | 未开始 | | | | | |
| R02 | 未开始 | | | | | |
| R03 | 未开始 | | | | | |
| R04 | 未开始 | | | | | |
| R05 | 未开始 | | | | | P2 |

执行者完成一个数据集后更新本表对应行（只改自己的行，改前重新读取文件）。
