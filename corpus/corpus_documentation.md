# 语料文档（R2.3、R2.4）

语料主表为 `corpus/items.parquet`，列定义见 `items.md`。本文件逐项记录 task_guide 8.5 要求的内容。所有数字均于 2026-10-16 由 `src/process/build_corpus.py` 的输出核对。采集过程的逐次决策见根目录 `DECISIONS.md`。

## 1. 检索词与日期范围

- 检索词共 26 个，原文为英文，分五组：
  · 通胀与价格：inflation, prices, cost of living, grocery prices, gas prices, affordability, price increases
  · 就业：unemployment, jobless, layoffs, hiring, jobs report, labor market
  · 增长与衰退：GDP, economic growth, recession, economic slowdown
  · 利率与住房：interest rates, mortgage rates, Federal Reserve, housing costs, rent
  · 综合：economy, consumer sentiment, consumer confidence, tariffs
- 规则 `economic_title_regex_v1`：按词边界匹配，不区分大小写。
- 日期范围：2010-01-01 至 2026-10-14（研究截止日）。YouTube 只有 2023-01-01 以后。2010–2022 年的 YouTube 视频按用户决定暂缓。

## 2. 来源、选择理由与样本设计

| 层级 | 来源 | 单位 | 设计 | 覆盖 | 纳入条数 |
|---|---|---|---|---|---:|
| 全国 | NYT Archive API | 标题 + 摘要 + 首段（2025 年起来源不再提供首段） | 全档案 | 2010-01 至 2026-10，202 个月 | 38,468 |
| 全国 | Guardian Open Platform，business/US economy 标签 | 标题 + 导语 + 全文 | 全档案 | 202 个月 | 4,286 |
| 全国 | Media Cloud US National 集合 | 标题 | 固定种子，每个集合月份随机抽 2 个整日 | 2025-09 至 2026-09，13 个月 | 3,854 |
| 地方 | Media Cloud US State & Local 集合 | 标题 | 同上 | 2025-03 至 2026-09，19 个月 | 25,055 |
| 社交 | Reddit：r/economy、r/Economics | 帖子标题 + 正文 | 2015–2024 年每月随机 3 个整日；2025-01 起整月穷尽查询 | 2015-01 至 2026-10 | 29,767 |
| 社交 | Reddit：r/personalfinance | 帖子 | 每月 3 个随机日内的随机圆环时间窗，每月期望约 150 条 | 2010-01 至 2026-10，202 个月 | 3,603 |
| 社交 | Reddit：r/inflation | 帖子 | 整月穷尽查询 | 可得全部月份 | 7,726 |
| 社交 | YouTube：10 个新闻频道视频下的评论 | 顶层评论（发布后 30 天内） | 非概率：按日期覆盖优先选取视频，选中的视频取全部评论 | 2023-01 至 2026-10，46 个月 | 54,659 |

选择理由：
- NYT 和 Guardian 是全国性来源中免费、可回溯到 2010 年、可复现的档案。Media Cloud 提供全国与地方集合，用于对比。
- YouTube 是美国成年人使用率最高的平台（Pew 2025：84%）。Reddit 是辅助平台，用户偏年轻、高学历，只适合做对比，不能代表全国。
- 频道清单及理由见 `provenance/youtube_channels.csv`。没有对频道立场做任何推断。

## 3. 纳入与排除标准及准确率

- 纳入：单位自身文本命中至少一个检索词。
- 排除：广告和赞助内容（`is_ad`，8 条）、讣告（`is_obituary`，170 条）。这两类都只做标记，不删除；分析时排除。
- "纯股市行情""非美国经济"等内容层面的排除，由人工标注和 AI 的相关性判断完成，不靠关键词规则。
- 关键词规则的准确率按金标准估计（`labels/adjudicated.csv`，360 条分层随机样本），准确率 = yes ÷ (yes + no)，unsure 单列；括号内为按抽样权重估计的值：

| 来源 | 标注条数 | yes | no | unsure | 准确率（加权） |
|---|---:|---:|---:|---:|---:|
| NYT | 125 | 70 | 48 | 7 | 0.59（0.61） |
| Guardian | 40 | 39 | 1 | 0 | 0.98（0.94） |
| Media Cloud 全国 | 15 | 10 | 5 | 0 | 0.67（0.67） |
| Media Cloud 地方 | 60 | 40 | 11 | 9 | 0.78（0.78） |
| Reddit | 90 | 37 | 42 | 11 | 0.47（0.49） |
| YouTube | 30 | 24 | 1 | 5 | 0.96（0.97） |

  结论：关键词规则对 NYT 和 Reddit 的精度只有约一半到六成，构建月度指数前必须用经过验证的相关性分类再过滤一次。

## 4. 文本单位类型

见第 2 节和 `items.md` 的 `unit_type`。不同单位所含信息量不同：Media Cloud 只有标题，Guardian 是全文。分析时按来源分组或加来源固定效应，不能直接混在一起比较。

## 5. 地理相关性与受众信息

- NYT、Guardian、Media Cloud 全国集合属于全国层级；Media Cloud 州与地方集合覆盖 1,713 家媒体。没有取得媒体所在州的元数据，`geo_state` 为空。
- Guardian 是英国媒体，只取其美国经济标签。
- 受众信息：
  · 子版块订阅数（存档快照）：r/personalfinance 20,444,068，r/Economics 5,240,534，r/economy 1,028,494，r/inflation 96,189
  · YouTube 频道统计见 `data/raw` 下 SM01 的 channel 文件
  · 视频播放量见 `data/processed/youtube_videos.csv`
  · 美国成年人平台使用率见 R04（Pew 2025）

## 6. 去重、转载、广告、疑似自动化

- 规则见 `items.md` 的"重复识别"。
- 结果：重复 2,484 条，转载 21,188 条，近似重复合并 666 对。
- 地方媒体转载集中：Media Cloud 地方纳入 25,055 条，去掉重复和转载后剩 7,264 条。通讯社稿件被大量地方站点转载，转载数记为供给放大度量。
- Reddit 的周期性模板帖（如每周价格讨论帖）会被识别为近似重复。
- 疑似自动化：按隐私设计没有保存作者和账号字段，无法使用发帖频率、账号创建时间等规则，`is_suspected_automated` 留空；这一点作为局限写入报告。内容层面的完全重复已由去重规则标出。

## 7. 按来源和月份的条目数与缺失

`source_month_counts.csv` 逐来源×月给出：已取得条数、纳入条数、去重后条数、去重和转载后条数。

已知缺口：
- NYT 2026-01-08 至 01-31 缺失（当月只有 16 条纳入），2026-10 只到 10-04。重新请求后来源仍只返回这些，属于来源端缺口，不能当成零报道。
- Media Cloud 的文本只有上述抽样月份，更早年份只有每日计数（`data/raw` 的 N03 计数文件）。
- YouTube 有 308 天没有可用视频。8 个大频道的上传列表只覆盖近期，2023–2024 年主要依靠旧搜索补充，是非随机样本，`video_search_only_supplement` 标为 True 的评论有 18,525 条。PBS NewsHour 关闭了评论。
- GDELT 不可得（HTTP 429）。数值化的媒体立场评级没有取得（AllSides 返回 403）。

## 8. 访问限制与使用条款

- NYT、Guardian：官方 API 和密钥；NYT 只有摘要和首段（snippet_only）。
- Media Cloud：官方 API，只用标题。
- Reddit：Arctic Shift 社区存档，不是 Reddit 官方接口，不能宣称是完整的实时 Reddit 数据。score 和 num_comments 是存档抓取时的快照。
- YouTube：官方 Data API v3。API 政策要求非授权数据在 30 天内刷新或删除，不能作为无限期档案。
- 所有来源：不保存作者和账号字段，仅供内部研究使用，不对外分发原文。提交包只给 ID 和重新抓取脚本（task_guide 8.6）。

## 9. 抽样局限及对结论的影响

- 地方新闻的文本只覆盖 2025–2026 年，所以 2017–2024 年在模型中只能用关注量（计数）。地方与全国的语气对比只能在 2025–2026 年做。
- 社交平台的覆盖期较短，用户也不代表全国：Reddit 的抽样从 2015 年开始（personalfinance 和 inflation 更早），YouTube 从 2023 年开始。社交指数只用于敏感性分析和近期对比，不进入 2010–2019 年的估计期。
- YouTube 是非概率样本，没有抽样权重；只能做描述和组内比较，不能外推到平台总体。
- 关键词纳入的精度因来源而异（第 3 节），月度指数必须先用经过验证的相关性分类过滤。
