# media_monthly.csv / media_quarterly.csv

- 生成脚本：`src/process/media_monthly.py`
- 输入：`labels/ai/codex__v2_isolated_r1_corpus/`（冻结提示词 v2，Codex，58 批共 11,431 条）与 `labels/corpus_sample_key.csv`（抽样权重）。合并后的逐条标签见 `labels/ai_corpus_labels.csv`。
- 一行一个"来源组 × 月"（季度版为"来源组 × 季度"）：

| group | 来源 | 覆盖 | 每月编码条数 |
|---|---|---|---|
| national | NYT + Guardian | 2010-01 至 2026-10，202 个月 | 40 |
| mc_national | Media Cloud 全国 | 13 个抽样月 | 20 |
| local | Media Cloud 地方 | 19 个抽样月 | 40 |
| reddit | 四个子版块合并 | 2015-01 至 2026-10，142 个月 | 10 |
| youtube | 10 个频道的评论 | 2023-01 至 2026-10，46 个月 | 20 |

- 没有设"全部来源合并"组：社交平台是非概率样本，与新闻的权重不可比，合并会使含义不清。

## 估计方法

每格内用比率估计量，权重 w = final_weight（第一阶段设计权重 × 层内扩张因子）。YouTube 没有设计权重，w 取月内扩张因子；由于月内恒定，等价于不加权。内容指标只在 relevant = yes 的条目上计算；unsure 只计数，不进入指标。

## 列定义

| 列 | 含义 |
|---|---|
| `n_coded`、`n_relevant`、`n_unsure`、`n_not_relevant` | 该格编码条数及相关性分布（未加权条数） |
| `relevant_share` | 加权相关比例：yes ÷ (yes + no) |
| `est_relevant_items` | 抽样框中相关条目的加权估计数。新闻组可作为供给量；YouTube 的值只针对所选视频的评论 |
| `net_tone` | 正面占比 − 负面占比 |
| `share_negative`、`share_positive`、`share_mixed` | 各类语气占比 |
| `net_fact` | 好消息占比 − 坏消息占比 |
| `share_no_fact` | 只有观点、没有事实的条目占比 |
| `emotional_intensity_mean` | 情绪强度均值，0–2 |
| `price_frame_share` | 涉及价格的条目占比 |
| `price_level_share_of_priced` | 涉及价格的条目中，用价格水平表述（level 或 both）的占比 |
| `household_share` | 家庭视角（household 或 both）占比 |
| `forecast_share` | 预测框架（forecast 或 both）占比 |
| `numeric_claim_share` | 含数字陈述的占比 |
| `definition_error_rate` | 概念错误 ÷ 适用条目 |
| `blame_admin_share`、`credit_admin_share` | 把经济状况归咎或归功于总统/行政当局的占比（actor_1 或 actor_2） |
| `fed_mention_share` | 提及美联储的占比 |
| `business_blame_share` | 归咎企业的占比 |
| `topic_*` | 13 个主题各自的占比 |
| `low_n_flag` | 相关条目少于 10 条，估计不稳定 |
| `source_gap` | 来源端缺口说明：NYT 2026-01 只有 1–7 日，2026-10 只到 4 日 |
| `weighting` | 加权方式说明 |

## 质量与已知问题

- AI 测量的验证见 `results/ai_validation/README.md`。测试集与金标准的 κ：
  · relevant 0.86、语气 0.73、价格框架 0.83、数字陈述 0.79
  · 事实好坏 0.57、情绪强度 0.56、时间框架 0.59、视角 0.63、行动者 0.67、归因方向 0.56
  · 概念错误 0.47，偏弱，相应指标只宜描述性使用
- Reddit 每月只编码 10 条，142 个月中有 140 个月 low_n，应使用 `media_quarterly.csv`：48 个季度中只有 7 个 low_n。
- 全国组每月相关条目为 14–37 条，中位数 26，月度指标有抽样噪声，可用 3 个月移动平均做稳健性检验。
- 与旧金山联储每日新闻情绪指数的月均值比较（`sffed_news_sentiment_monthly.csv`，202 个月）：net_tone 的 Pearson r = 0.37，3 个月平均后 r = 0.44；net_fact 的 r = 0.39。两者测量对象不同（旧金山联储基于 24 家报纸的文章情绪模型），中等相关属于预期范围。
- 模型为 GPT 6 luna，推理强度 high（项目负责人声明，`labels/ai/model_declaration.json`）；运行日志中模型名称记为"不可见"；Codex 无法设定温度。测试集 26 条重复运行的一致率：relevant 0.92、语气 0.85、情绪强度 0.69、时间框架 0.73。
- 运行日志显示，部分批次在结构核验后修复过证据摘录和 claim_text 字段（`labels/ai/job_logs/`）。测试集也经过同一流程，因此测试集表现反映的就是实际使用的流程。
