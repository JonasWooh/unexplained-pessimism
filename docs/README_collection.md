# 本轮数据收集

原始请求：只收集真实数据及核查完整性；不分析、不标注。检索截止日期为 **2026-10-14**；文件夹日期使用本批次开始的 UTC 日期 20261015，实际逐文件下载时刻以来源登记为准。

结果入口：

- `provenance/collection_report.md`：带时间戳的状态汇报，明确区分完成、进行中、等待许可与缺失。
- `provenance/dataset_status.csv`：每一个方案数据集的状态、覆盖、条目数和问题。
- `provenance/sources.csv`：来源 URL/公开参数、UTC 下载时间、覆盖和条目数。认证参数不入表。
- `provenance/inventory.csv`：逐文件检查；版本行、月、案例、标题、评论元数据不是同一种计数单位。
- `DECISIONS.md`：方案中需核实项及实际调整、许可限制。
- `provenance/excel_reconciliation.md`：教授 Excel 的 PCE 口径证据。
- `provenance/release_calendar.csv`：发布日、ALFRED 版本日、未来计划分别标记，不能混用。

`data/raw/` 和 `corpus/raw/` 保存下载响应原件，独占创建而不覆盖。原方案、指导清单和教授 Excel 均未修改。部分原站响应实际是 CSV/PDF，但请求保存名以 `.html` 结尾；文件内容保持原样，inventory 和请求日志记录实际用途/Content-Type。没有把任何 API key 复制到这里、脚本或日志。

运行环境为本地 conda base：`/Users/jonasw/anaconda3/bin/python`。依赖 requests、pandas、openpyxl、xlrd、beautifulsoup4、PyMuPDF；本轮补装了 xlrd 以读取原始 `.xls`。各脚本从原 `API_KEY.txt` 按本地标签运行时读取密钥，完整值不输出。不要共享该文件或原始受版权语料。

已下载同名原件会跳过。当前批次的 Media Cloud 继续操作为 `src/collect/N03.py`；它先读取保存的分页 token，再以单个 worker 按 31 秒以上的请求间隔交替两集合，直到分页结束或某集合出现错误。不能同时启动第二个 Media Cloud worker；否则账户总速率会超限。计数总量不等于本地文章数，最早出版日期也不等于可靠连续历史起点。

YouTube `youtube_inventory.py` 只完成目录能返回的范围；`youtube_search.py` 补查目录缺失季度，每天最多 100 次官方搜索，已存在的响应可继续读取。用户已允许评论正文，`youtube_comment_text.py` 请求 API 的 plainText/textDisplay，服务器端排除所有作者身份字段，另存 `comment_text_*.json`，不改原元数据文件。`youtube_comment_text_state.json` 保存逐视频分页状态；按用户要求已取消自行设置的单轮请求数、预留配额和单视频2000条截断，直到顶层分页结束或 API 实际错误，未收回复正文。`run_youtube_remaining.py` 单次后台继续正文及缺失视频详情，停止后重建状态报告；不能同时启动第二个 YouTube worker。`youtube_inventory_state.json` 的 done 不是覆盖完整标记，应看 `youtube_coverage.csv`。所有统计都是采集时累计值，不是发布时数值。

`src/collect/finalize_snapshot.py` 重跑本地完整性与状态表，不分析数据、不改 raw。运行中新增原件可能晚于报告快照，后续应再次生成快照。`running_collection.json` 和 progress 日志记录本地长请求的状态；这是本次采集的单次后台进程，不是定时自动化。电脑休眠、断网或 API 限制可能中断，错误会保留，不自动切换网络或身份。

NYT/Guardian 已使用用户提供的官方密钥实测成功，并启动 `run_news_remaining.py` 单次后台采集；`news_archives.py` 负责每月原响应、分页和配额。NYT 2009-12 起全部文章元数据；Guardian 2010-01 起已核实的 US economy 标签及可得正文。查看 `news_running_collection.json` 和 `N01_archive_state.json` / `N02_archive_state.json`；不可同时启动重复 worker。

Reddit 已获用户明确授权并启动 `reddit_posts.py`，通过 Arctic Shift 社区存档采集四个子版块的帖子，排除所有作者身份字段。单次 API 返回上限100条不代表总量截断；满页递归拆分时间区间，保留原响应，只将非重叠叶区间计入帖子数。`reddit_collection_state.json` 和 `reddit_progress.log` 记录断点、数量和实际错误；不是 Reddit 官方 API，也不保证存档本身完整。先收2025年以来，再补2010—2024；未采可选评论。

后续仍缺：各源未完成分页、截断历史的未完搜索页、未公开的调查报告和未来宏观发布、部分重大事件。正文与旧评论元数据可能重叠，不能将两批行数相加当作独立评论数。评论发布时间保留实际值，可晚于视频检索截止日。YouTube 非授权数据需在 30 天内刷新/删除；不要把此目录作为永久不刷新的档案。未创建自动提醒或删除任务。
