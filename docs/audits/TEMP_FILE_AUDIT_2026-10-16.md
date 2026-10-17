# 临时文件清点（2026-10-16）

核查时间：2026-10-16T16:57:56-04:00。范围：`/Users/jonasw/Documents/NLP/Final Project`。本次只新增本报告与逐文件 CSV，未删除、移动或改写任何既有项目文件。

## 结论

严格可清理候选 **51 个文件，758,981 bytes（约 0.759 MB）**。其中 10 个锁文件只能在相关程序停止后清理。

| 类别 | 文件数 | 逻辑大小（bytes） |
|---|---:|---:|
| Python 缓存 | 36 | 502,721 |
| PDF 检查截图 | 2 | 256,260 |
| 空日志 | 3 | 0 |
| 空锁文件 | 10 | 0 |

完整路径、逐文件大小、理由和清理条件见 `TEMP_FILE_INVENTORY_2026-10-16.csv`。大小按文件内容计算，不代表磁盘实际可回收空间。

## A：纯临时文件

- `src/collect/__pycache__/`：34 个 `.pyc`，479,564 bytes。
- `src/analysis/__pycache__/build_r37_package.cpython-311.pyc`：14,860 bytes。
- `src/annotation/__pycache__/build_workbooks.cpython-311.pyc`：8,297 bytes。
- `provenance/previews/preliminary_report.png`、`release_dates_last_page.png`：分别为 2024 年 1 月密歇根初值报告页面、历史发布日期 PDF 最后一页的阅读截图。已查看图片；原始 `2024_January_Preliminary_Results.pdf` 和 `historical_release_dates.pdf` 均在 `data/raw/S05/20261015/`，源码和说明文档未发现对截图的引用。
- 空日志：`provenance/news_supervisor.log`、`remaining_supervisor.log`、`youtube_public_web_progress.log`。
- `provenance/` 下 10 个零字节 `.lock`：`arctic_shift_api`、`mediacloud_api`、`monthly_cluster_report`、`nyt_archive`、`official_event_pages`、`youtube_claude`、`youtube_commentThreads`、`youtube_playlistItems`、`youtube_public_browser`、`youtube_search`（均加 `.lock` 后缀）。`src/collect/audit_runtime.py:7` 和 `month_cluster_report.py:44` 表明它们只用于同步并自动创建。

进程名扫描未发现相关 Python 采集或分析进程；`lsof` 显示一个 `com.apple` 进程以只读方式打开这些锁文件，这不等于确认它们正被 flock 持锁，也不能据此保证之后无人启动采集。本次不移除锁文件。

## B：仅属运行历史，建议归档

5 个文件共 2,355 bytes：

- `provenance/collection_eta_snapshot.json`：旧的采集剩余时间估计。
- `provenance/monthly_cluster_eta_snapshot.json`：旧的分簇采集时间情景，被 `DECISIONS.md` 和报告代码文字引用。
- `provenance/running_collection.json`、`youtube_running_collection.json`：已标记 `superseded_by_daily_coverage_workers`。
- `provenance/news_running_collection.json`：已标记 `workers_finished_check_dataset_states`，记录退出码和结束时间。

这些文件不影响当前 `src/process/run_all.sh` 和 `src/analysis/run_research.sh` 的计算，但仍是过程记录。移出后会影响既有说明中的引用，因此没有归入“与项目完全无关”。

## C：不要当作临时垃圾清理

- `corpus/raw/`、`data/raw/`：原始输入和官方证据。即使某些页面未进入最终语料，也不能仅凭名称、空响应、未被主入口直接读取便判为无用。
- `provenance/sources.csv`：`src/process/build_corpus.py:152` 读取下载时间，影响语料输出。
- `provenance/monthly_cluster_selections/`：语料构建及人工抽样直接读取 ID、原始文件路径、日期和纳入概率。
- `provenance/youtube_freeze_v1_20261015T2310Z/`：`build_corpus.py:96` 和 `build_sample.py:85` 使用的冻结输入，不能因名称带 freeze 或存在同名工作表而删除。
- `provenance/*state*.json`、抽样方案、`personalfinance_window_month_plans/`、`monthly_count_partitions/`、`sampling_selections/`：用于恢复采集、解释纳入范围与抽样设计。其中 `month_cluster_common.py`、`month_cluster_report.py` 直接读取多份旧状态。当前主分析未读取不等于没有复现价值。
- `provenance/*before*.json`、`monthly_cluster_retained_baseline*.json`：设计迁移快照或基线。`retained_baseline_v2` 当前仍被读取；`DECISIONS.md` 明确保留 personalfinance 迁移前断点。其他旧版本未逐一证明可替代，保留。
- 非空 `provenance/*.log`：40 个，共 2,148,733 bytes。抽查发现 HTTP 422、连接失败、退避和成功请求等信息，属于采集审计；可以集中归档，但不能统称纯临时。没有逐行评估全部日志的信息冗余。
- `provenance/requests.jsonl`、`inventory.csv`：采集请求和完整性依据；请求日志也被 `audit_runtime.last_event()` 读取。
- `labels/ai/job_logs/`、`labels/ai/run_log.csv`、所有原始模型输出：模型标注不可依靠确定性脚本重新生成，运行日志是独立性、尝试次数和设置的证据。
- `codex_runs/R37_package/`、`labels/ai_inputs/`、`prompts/`：实验输入、批次和冻结提示词。打包副本可重复生成，但与实验复现直接有关，不归入纯临时。
- `results/`、`features/`、`annotation/`、`codebook/`、`research/`、`DECISIONS.md` 及项目说明：研究产物、人工核验或方法依据。尤其 `results/stage2_factcal/review_sample_30.csv` 有人工核验意见，不应覆盖或删除。
- `API_KEY.txt`：联网采集读取的本地配置，已被 `.gitignore` 忽略；未读取其中内容。它不属于临时垃圾。

## 核查范围与限制

清点前项目共有 36,281 个文件，逻辑大小 5,128,257,915 bytes（约 5.128 GB）。大头为原始语料；清理 A 类主要改善整洁度，几乎不释放空间。

已检查全部文件路径及大小、复现入口、数据构建脚本、相关文档引用、同步文件实现、运行状态内容和截图。没有运行会覆盖冻结成果的全流程，没有发起采集，也没有逐一验证所有原始响应能否排除。未发现 `.tmp`、`.bak`、编辑器交换文件或 `.DS_Store`；未把“可重新生成”直接等同于“与复现无关”。

Git 实际根目录是 `/Users/jonasw/Documents`，本项目在该上层仓库中整体为未跟踪目录，没有独立 `.git`。以上是工作目录文件清点，不能依赖现有 Git 历史恢复其内容。
