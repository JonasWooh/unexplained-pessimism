# AI 测量验证（R3.4–R3.6）

- 模型：项目负责人声明为 Codex 中的 GPT 6 luna，推理强度 high（默认），全程固定（`labels/ai/model_declaration.json`）。运行日志 `labels/ai/run_log.csv` 中模型名称和设置记为"不可见"，原样保留。温度不可设定。
- 提示词：`prompts/label_prompt_v1.md`（SHA256 26365ac8…）；`prompts/label_prompt_v2.md`（SHA256 9f95f20a…）冻结。所有运行用的提示词副本均已核对哈希一致。
- 金标准：`labels/adjudicated.csv`。relevant = unsure 的金标准条目不计入 relevant 指标。
- 评分脚本：`src/annotation/score_ai.py`。逐维度、逐类别、按来源的结果见 `*_metrics.csv` 和 `*_per_class.csv`。

## 开发集（100 条，用于选择提示词版本）

v1 与 v2 的逐维度对比见 `dev_v1_vs_v2.csv`。10 个编码维度的平均 κ：v1 0.652，v2 0.670。按"开发集平均 κ"规则冻结 v2。

## 测试集（260 条，冻结 v2 后只运行一次）

| 维度 | n | 准确率 | κ | 宏 F1 | 人工 A–B 的 κ |
|---|---:|---:|---:|---:|---:|
| relevant | 236 | 0.94 | 0.86 | 0.93 | 0.81 |
| tone_overall | 174 | 0.85 | 0.73 | 0.81 | 0.79 |
| fact_direction | 174 | 0.70 | 0.57 | 0.63 | 0.72 |
| emotional_intensity | 174 | 0.74 | 0.56 | 0.72 | 0.59 |
| price_frame | 174 | 0.90 | 0.83 | 0.82 | 0.93 |
| perspective | 174 | 0.85 | 0.63 | 0.54 | 0.78 |
| time_frame | 174 | 0.74 | 0.59 | 0.70 | 0.82 |
| numeric_claim | 174 | 0.91 | 0.79 | 0.89 | 0.86 |
| definition_error | 174 | 0.74 | 0.47 | 0.48 | 0.77 |
| actor_1 | 174 | 0.75 | 0.67 | 0.56 | 0.83 |
| direction_1 | 174 | 0.68 | 0.56 | 0.67 | 0.78 |

（人工 A–B 的 κ 取自全部 360 条，见 `labels/agreement_summary.csv`。）

- 主题：13 个中 10 个 κ ≥ 0.70；汽油价格 0.60、经济增长 0.63、其他 0.54。
- 按来源的结果见 `codex__v2_isolated_r1_test_metrics.csv`。relevant 的 κ：NYT 0.90、Reddit 0.83、地方 0.72、Media Cloud 全国 0.54（n = 11）。tone 的 κ 在 0.63–0.76 之间。
- 格式：260 条全部返回，没有非法取值，1,315 条证据摘录全部能在原文中逐字找到。
- 自身一致性：测试集随机 26 条，在独立上下文中重复运行（`codex__v2_isolated_r2`）。一致率：relevant 0.92、语气 0.85、事实好坏 0.85、情绪强度 0.69、价格框架 0.88、视角 0.81、时间框架 0.73、数字陈述 0.92、概念错误 0.85、行动者 0.77、方向 0.88。

## 尚未完成（属于研究阶段）

- 与词典法、TF-IDF + 逻辑回归的比较（R3.5）
- 政治人物名字和来源标签的替换测试（R3.7）
