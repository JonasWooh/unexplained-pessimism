# items.parquet

- 生成脚本：`src/process/build_corpus.py`，运行约 5 分钟
- 生成时间：2026-10-16
- 行数：167,418，一行一个语料单位（in scope）。按来源：

| 来源 | 条数 |
|---|---:|
| YouTube | 54,659 |
| Reddit | 41,096 |
| NYT | 38,468 |
| Media Cloud 地方 | 25,055 |
| Guardian | 4,286 |
| Media Cloud 全国 | 3,854 |

- 纳入规则：单位自身文本（title + text）至少命中一个经济检索词（task_guide 8.2 的 26 个词，即 `youtube_details.TERMS`），且发布日在 2010-01-01 至 2026-10-14 之间。与人工标注抽样框的规则相同。
- 按来源×月的已取得数、纳入数、去重后数量见 `source_month_counts.csv`；汇总统计见 `items_stats.json`。

## 列定义

| 列 | 含义 |
|---|---|
| `item_id` | `来源:来源内ID`，全表唯一 |
| `source` | NYT、Guardian、MediaCloud_National、MediaCloud_Local、Reddit、YouTube |
| `outlet_name` | 媒体名、子版块（r/…）或 YouTube 频道名 |
| `source_level` | national、local、social |
| `platform` | news_api、media_cloud、reddit、youtube |
| `unit_type` | headline_abstract_lead、headline_abstract（NYT 2025 年起没有首段）、full_text（Guardian）、headline（Media Cloud）、post、comment |
| `pub_datetime_utc` | 发布时间。Media Cloud 只有日期 |
| `month` | 发布月份 YYYY-MM |
| `url` | 原文链接；YouTube 评论为视频链接 |
| `title`、`text` | 标题、正文或摘录。Reddit 正文为 `[removed]`/`[deleted]` 时，text 为空，原状态记在 `body_status` |
| `text_license` | full（Guardian、Reddit、YouTube）、snippet_only（NYT 摘要/首段、Media Cloud 标题） |
| `query_terms_matched` | 命中的检索词，以 `|` 分隔 |
| `geo_state` | 空：未取得媒体所在州的元数据 |
| `audience_info` | 子版块订阅数（存档快照）；其他来源为空 |
| `dedup_cluster_id`、`cluster_size` | 重复聚类及其规模 |
| `is_duplicate` | 同一媒体或账号空间内的重复，且不是该聚类中最早的一条 |
| `is_repost` | 不同媒体之间的转载，且不是该聚类中最早的一条；转载数 = 聚类中不同媒体数 − 1，可作为供给放大的度量 |
| `is_ad` | Guardian isHosted（广告主托管内容）、NYT 付费内容，或 URL 路径含 sponsored / sponsor-content / paid-content / advertorial |
| `is_obituary` | NYT type_of_material 为 Obituary 或 Paid Death Notice，或 URL 含 /obituar |
| `is_suspected_automated` | 空：按隐私设计没有采集账号字段，无法按账号判断是否为自动化账号 |
| `engagement_likes`、`engagement_replies` | Reddit 的 score 和 num_comments（存档抓取时的快照，不同年份不可比）；YouTube 评论的点赞数和回复数 |
| `engagement_reposts` | 空：两个平台都不提供 |
| `collected_at_utc` | 对应原始文件的下载时间（来自 `provenance/sources.csv`） |
| `design` | full_archive、random_day_cluster、random_circular_window、exhaustive_month、non_probability_video_selection |
| `sample_weight` | 来源×月内入样概率的倒数：全档案为 1；日整群为月内可观测天数 ÷ 抽中天数；圆环时间窗为 1/p；YouTube 为空（非概率样本） |
| `sample_date` | 抽中的日期，仅整群和时间窗设计 |
| `section`、`type_of_material` | 新闻栏目、文章类型 |
| `video_id`、`video_title`、`video_channel_group`、`video_search_only_supplement` | 仅 YouTube 评论 |
| `source_item_id`、`raw_file` | 来源内 ID 和原始文件路径，可追溯 |

## 重复识别

用并查集合并三类关系：

1. 规范化 URL 相同，仅新闻：主机名和路径转小写，去掉 fragment 和跟踪参数（utm_*、fbclid、gclid 等），保留其他查询参数。
2. 规范化文本相同：小写，只保留字母、数字和空格。
3. 近似重复：只对 8 个词以上的文本做。用词级 3-gram 的 MinHash（128 个排列，32 个分带 × 4 行，种子 20261015），再以精确 Jaccard ≥ 0.8 核实。

已识别：重复 2,484 条，转载 21,188 条（主要是 Media Cloud 地方媒体的通讯社稿件），近似重复合并 666 对，广告 8 条，讣告 170 条。

**分析时不要删除这些条目**，按问题选择：
- 供给量用全部条目；
- 内容单位用 `~is_duplicate & ~is_repost`；
- 广告和讣告按 8.2 节排除。
