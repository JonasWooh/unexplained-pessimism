# 经济叙事人工标注手册 v1（Human Labeling Guide）

适用：annotation_workbook_A.xlsx / annotation_workbook_B.xlsx。两名标注员各用一份，互不交流、互不查看对方表格。本手册即提交包中的"人工标注指南"（R3.1、R6.2）。

> 状态：v0.9 草案。两人完成 30 条校准（calibration 表）并讨论后，只允许澄清措辞、补充边界例子，然后定为 v1；此后不再修改定义。修改记录写在本文件末尾。

---

## 0. 工作流程

1. 先各自独立标完 `calibration` 表的 30 条（C001–C030），记录用时。
2. 两人一起对照差异，讨论分歧，修改本手册中含糊的地方，形成 v1。校准条目不计入 300 条正式样本。
3. 各自独立标完 `main` 表的 360 条（A001–A360）。中途不讨论具体条目；有疑问写在 `notes` 列，并把 `unsure` 用在允许的地方。
4. 每次开始和结束时，在 `time_log` 表记录时间和完成到的编号。
5. 两份表都交回后，由分析者计算一致性（Cohen's κ、Krippendorff's α、原始一致率、混淆矩阵）；不一致的条目再由两人讨论裁决，或请第三人裁决，裁决理由记录在案。裁决结果为金标准。

表格里看不到来源名称、网址和 AI 标签，这是有意的（盲标）。不要上网搜索原文或来源。

预计用时：相关条目每条约 1–1.5 分钟；判为不相关的条目只填第一列，约 15 秒。

---

## 1. 标注单位

每一行是一个单位，只根据 `text` 列里给出的文字判断：

| unit_type | 内容 |
|---|---|
| headline + abstract + lead paragraph | 新闻标题 + 摘要 + 首段 |
| headline + abstract | 新闻标题 + 摘要（2025 年起该来源不再提供首段） |
| headline + standfirst + first 100 body words | 新闻标题 + 导语 + 正文前 100 词 |
| headline only | 只有新闻标题 |
| forum post (title + body, first 1,200 chars) | 论坛帖子标题 + 正文前 1,200 字符 |
| video comment (top-level) | 视频下的一条评论 |

`context` 列只在视频评论时出现（视频标题），帮助理解评论在说什么，但**标注对象是评论本身**，不是视频标题。`[...]` 表示后文被截断，不要猜测截断部分的内容。

---

## 2. 第一步：是否与美国经济相关（`relevant`）

| 值 | 规则 |
|---|---|
| `yes` | 文字传达了关于**美国**经济状况或经济政策的信息、观点或亲身经历：物价与通胀、就业与劳动力市场、增长与衰退、利率与借贷成本、住房成本与房租、关税与贸易、消费者信心，或对这些状况的评价。 |
| `no` | 不满足上面条件。 |
| `unsure` | 读完仍无法判断，并在 `notes` 写原因。尽量少用。 |

**边界规则**
- 个人理财问题（预算、信用分、报税、该不该买某个基金）**只有**在提到经济状况本身时才算 `yes`，例如"现在房租涨得太离谱""这个就业市场根本找不到工作"。只是问个人规划、没有涉及经济状况的，算 `no`。
- 纯股市行情（某只股票涨跌、大盘点位）算 `no`；如果把股市和经济前景、衰退、利率等联系起来，算 `yes`。
- 主要讲其他国家经济的算 `no`；讲外国政策对美国经济的影响（如对美关税）算 `yes`。
- 关键词出现在无关含义中（如"rent a car"、人名、体育），算 `no`。
- 讣告、广告、赞助内容、活动预告，算 `no`。

**`relevant = no` 时，本行其余各列全部留空。**`unsure` 时照常填写其余各列。

---

## 3. 维度 1：语气（Tone）

### 3.1 `tone_overall`：文字本身的整体语气
| 值 | 规则 |
|---|---|
| `negative` | 措辞和表述整体让人感到经济状况坏、令人担忧、批评性 |
| `positive` | 整体让人感到状况好、乐观、肯定 |
| `neutral` | 平铺直叙，没有明显倾向 |
| `mixed` | 正负两面都有，且分量相当 |

### 3.2 `fact_direction`：所报道的**事实本身**对美国家庭是好消息还是坏消息
| 值 | 规则 |
|---|---|
| `bad` | 例：失业率上升、物价上涨、房贷利率上升、裁员 |
| `good` | 例：通胀回落、工资上涨快于物价、招聘增加 |
| `neutral` | 事实对家庭没有明确好坏，例：美联储维持利率不变且无评价 |
| `mixed` | 同时报道好坏两类事实 |
| `no_fact` | 只有观点、情绪或问题，没有陈述经济事实 |

### 3.3 `emotional_intensity`：情绪化措辞的强度
| 值 | 规则 |
|---|---|
| `0` | 没有情绪化措辞 |
| `1` | 轻度，例："worrying""tough""good news" |
| `2` | 强烈，例："skyrocketing""collapse""nightmare""insane"、全大写、多个感叹号 |

**区分事实与情绪（必须分开判断）**：
- "Unemployment rose to 4.3% in July." → `fact_direction = bad`，`emotional_intensity = 0`，`tone_overall = negative` 或 `neutral`（看措辞，单纯陈述数据通常是 `neutral`）。
- "Prices are absolutely insane, I can't afford anything anymore!!!" → `fact_direction = bad`，`emotional_intensity = 2`，`tone_overall = negative`。
- "Inflation cooled again, but economists warn the fight isn't over." → `fact_direction = good`，`tone_overall = mixed`，`emotional_intensity = 0` 或 `1`。

---

## 4. 维度 2：选择与显著性（Topics，可多选）

在下列 13 列中，文字**明确涉及**的主题填 `1`，否则留空。至少选一个；都不符合就在 `T13_other` 填 `1`。

| 列 | 主题 |
|---|---|
| T01_layoffs_unemployment_up | 裁员、失业上升 |
| T02_hiring_jobs_growth | 招聘、就业增长 |
| T03_prices_rising | 物价上涨、生活成本高 |
| T04_inflation_easing | 通胀回落、涨价放缓 |
| T05_economic_growth | 经济增长、GDP |
| T06_recession_risk | 衰退、经济放缓风险 |
| T07_interest_rates_borrowing | 利率、借贷成本、美联储利率决策 |
| T08_housing_costs | 房价、房租、住房可负担性 |
| T09_gas_prices | 汽油价格 |
| T10_food_prices | 食品、杂货价格 |
| T11_tariffs_trade | 关税、贸易政策 |
| T12_stock_market | 股市 |
| T13_other | 其他经济主题 |

只是顺带出现一个词不算"涉及"，要是文字确实在讨论这个主题。

---

## 5. 维度 3：框架（Framing，三个独立的轴）

### 5.1 `price_frame`：讲价格时用哪种表述
| 值 | 规则 |
|---|---|
| `level` | 价格水平："比以前贵多少""groceries cost twice what they did" |
| `rate` | 通胀率或涨价速度："inflation slowed to 3%""prices rising faster" |
| `both` | 两种都有 |
| `none` | 没有讲价格 |

注意："inflation is down" 是 `rate`；"prices are still way higher than 2020" 是 `level`。通胀率下降不等于价格下降。

### 5.2 `perspective`：视角
| 值 | 规则 |
|---|---|
| `national` | 全国总量、宏观数据、市场或政策层面 |
| `household` | 家庭或个人的亲身经历、具体人的处境 |
| `both` | 两者都有 |
| `none` | 都不是 |

### 5.3 `time_frame`：时间
| 值 | 规则 |
|---|---|
| `current` | 当前或刚发生的状况 |
| `forecast` | 预测、预期、对未来的担忧或判断 |
| `both` | 两者都有 |
| `none` | 都不是（例如纯历史回顾） |

---

## 6. 维度 4：事实校准（Factual calibration）

人工只做两件事；与当时官方数据的逐项核对由分析者用发布时的数据版本（ALFRED）完成。

### 6.1 `numeric_claim` 与 `claim_text`
- `numeric_claim = yes`：文字中有关于美国经济指标的数字陈述（失业率、通胀率、GDP 增速、利率、房价、油价、新增就业等）。
- 是 `yes` 时，在 `claim_text` 逐字摘抄每一条数字陈述，用 `;` 分隔。例：`unemployment rose to 4.3% in July; 114,000 jobs added`。
- 个人收入、个人账单的数字（"I make $50k"）不算，填 `no`。

### 6.2 `definition_error`：概念或定义错误
| 值 | 规则 |
|---|---|
| `yes` | 有明显概念错误，例：把"通胀下降"说成"价格下降"；混淆同比和环比；把其他失业指标当成 U-3；把初值当作确定值且与文意矛盾 |
| `no` | 提到经济统计概念，但没有发现错误 |
| `not_applicable` | 没有提到任何经济统计概念 |

不确定时填 `no`，并在 `notes` 说明。

---

## 7. 维度 5：政治归因（Political attribution）

是否把经济状况（好或坏）归因于某个行动者。最多记录两个：`actor_1` / `direction_1`，`actor_2` / `direction_2`。没有归因时 `actor_1 = none`，其余留空。

| actor 值 | 含义 |
|---|---|
| `president_admin` | 总统或行政当局（含点名的总统、白宫、内阁） |
| `congress` | 国会 |
| `fed` | 美联储 |
| `democrats` | 民主党或民主党人 |
| `republicans` | 共和党或共和党人 |
| `business` | 企业、公司、行业 |
| `foreign_trade` | 外国政府或贸易伙伴、外国政策 |
| `other` | 其他（工会、州政府等，在 notes 写明） |
| `none` | 没有归因 |

| direction 值 | 含义 |
|---|---|
| `credit` | 归功：把好的经济结果归于该行动者 |
| `blame` | 归咎：把坏的经济结果归于该行动者 |
| `neutral_mention` | 提到该行动者与经济状况有关，但没有归功或归咎 |

**批评不等于偏差。**这里只记录文字说了什么；是否构成偏差，由分析阶段与基准比较后判断，标注时不要考虑来源立场。

例："Trump's tariffs are driving up grocery prices" → `actor_1 = president_admin`，`direction_1 = blame`。
例："The Fed held rates steady on Wednesday." → `actor_1 = fed`，`direction_1 = neutral_mention`。

---

## 8. 其他列

- `notes`：疑问、`unsure` 的原因、`other` 的说明。不要写对来源的猜测。
- 不要修改 `item_id`、`date`、`unit_type`、`context`、`text` 列，不要排序或删除行。

---

## 9. 修改记录

| 日期 | 版本 | 修改内容 | 依据（校准条目编号） |
|---|---|---|---|
| 2026-10-16 | v0.9 | 初稿 | — |
| 2026-10-16 | v0.9 | 校准后未修改 | C001–C030 |
