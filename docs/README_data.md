# 数据交接总览（2026-10-16）

数据收集、处理、LLM 编码和月度媒体指数均已完成，可以开始统计分析（模型 1–3）。原始文件在 `data/raw/`、`corpus/raw/`，均未修改。逐次决策见 `DECISIONS.md`，来源与下载记录见 `provenance/`。

## 交接文件

| 文件 | 内容 | 说明 |
|---|---|---|
| `data/processed/econ_monthly_realtime.csv` | 2010-01 至 2026-10 的实时月度经济面板（D2 截止日），202 行 | `.md` |
| `data/processed/econ_monthly_realtime_prelim_cutoff.csv` | 敏感性版本：截止日为密歇根初值发布日 | 同上 |
| `data/processed/survey_monthly.csv` | 密歇根分组、党派、听到的新闻、原因与预期，1978-01 至 2026-09，585 行 | `.md` |
| `data/processed/youtube_videos.csv` | 7,289 个 YouTube 候选视频的播放量和评论数快照 | `.md` |
| `corpus/items.parquet` | 语料主表，167,418 条 | `items.md`、`corpus_documentation.md`（R2.3） |
| `corpus/source_month_counts.csv` | 来源×月的已取得数、纳入数、去重后数量 | — |
| `labels/` | 标注样本、A/B 标注、一致性、裁决记录、金标准 v1 | `labels/README.md` |
| `codebook/codebook.md`、`examples.md` | 编码手册 v1（人工标注指南）及金标准示例 | — |
| `labels/ai_corpus_labels.csv` | 11,431 条正式编码样本的 LLM 标签（冻结 v2）加抽样权重 | `labels/ai/run_log.csv` |
| `features/media_monthly.csv`、`media_quarterly.csv` | 月度和季度媒体指数（全国、Media Cloud 全国、地方、Reddit、YouTube） | `features/media_monthly.md` |
| `features/sffed_news_sentiment_monthly.csv` | 旧金山联储新闻情绪指数月均值（对照） | 同上 |
| `results/ai_validation/` | AI 测量的开发集、测试集验证和重复运行一致率 | `README.md` |

## 复现

`sh src/process/run_all.sh` 会从原始文件重建以上全部文件，约 5 分钟，不发起任何网络请求。2026-10-16 已验证：重跑后 `items.parquet`、`econ_monthly_realtime.csv`、`adjudicated.csv` 与原文件逐字节相同。

标注抽样（`src/annotation/build_sample.py`）已冻结，不在重建流程内。

## 研究开始前必须知道的局限

- NYT 2026-01-08 至 01-31 缺失，2026-10 只到 10-04。
- 地方新闻的文本只有 2025–2026 年。
- 社交平台：YouTube 只有 2023 年以后，且是非概率样本；Reddit 的抽样从 2015 年开始（personalfinance 和 inflation 更早）。
- 关键词纳入对 NYT 和 Reddit 的精度约为 0.5–0.6，构建指数前必须先做相关性过滤。
- GDELT 和媒体立场评级没有取得。
- 各宏观序列在其最早的 ALFRED 版本之前为空。HOAM 住房可负担性没有历史版本。2026-10 的密歇根指数是初值。
