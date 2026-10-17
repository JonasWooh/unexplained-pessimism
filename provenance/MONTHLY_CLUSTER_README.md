# 月度文本采集状态表

当前主表为 `monthly_cluster_status.csv`，汇总及运行状态为 `monthly_cluster_summary.json`。固定清单为 `monthly_cluster_plan.json`。每完成一个抽样日及 worker 退出时刷新报告；这不是定时任务。报告只读取本地数据。

- Media Cloud：地方 38379429，2025-03 至 2026-09；全国 34412234，2025-09 至 2026-09。每集合每月抽 2 日，抽中日完整分页后才计完成。此前完整月份、完整日期及十月截至 14 日的部分另列。数量指标用已有每日检索计数，快照可随来源更新。
- Reddit：economy、Economics 的 2015–2024 年每月 3 个 UTC 日期；personalfinance 延续 2010 年以来每月 3 日。优先近期 personalfinance 9 日，再补核心版块 2017–2024、2015–2016，最后其余历史 personalfinance。半日区间可复用，但未补齐全天不算完整日。
- 每个来源独立使用 Python `random.Random(20261015)`，按月份升序无放回抽日期；当月只在截止日之前抽。日期在下载前固定，不因库存、速度或当天记录数重抽。
- 这是按日整群抽样，同日记录共同入样，不是报道/帖子逐条简单随机抽样。已有非随机库存单列，不自动混入随机样本。
- `planned_sample_days` / `completed_sample_days` 是当前抽样日计划；`sample_days_reused` 是抽中且原来已完整的日期；`sample_days_newly_completed` 是本轮补齐的日期。
- `sample_unique_records` 只计完整抽样日内的唯一 ID；正在分页的日期不计入。`sample_plan_completion` 是抽样日计划完成率。
- `retained_other_full_days` / `retained_other_full_day_records` 是旧库存中未被抽中的完整日期和记录，包括新补采范围之外的日期，与抽样记录分列。
- Media Cloud 的 `retained_prior_month_inventory_records` 是此前原始库存审计的月度去重数；完整月份依据用户提供的独立审计。它可能包含其他完整日记录，不能重复相加，也不保证与较新计数快照吻合。
- `source_query_count` 是来源实际返回的月度计数，Reddit 未查询时留空。`count_snapshot_days` 是 Media Cloud 分母含有的日期数；2026-10 只至 14 日。
- `observed_sample_fraction` 是完整抽样日记录数除以月度检索数，**不是全月采集完整率**。额外库存和未完成日期不计入该分子。
- Reddit 不收作者字段，保留 `retrieved_on`；得分和评论数是存档抓取时的快照，不同年份之间不可比。
- 旧 `sampling_monthly_status.csv` / `sampling_summary.json` 属于已停止的每日/半日计划。原件和旧报告保留，不做哈希校验。

Media Cloud 用已有日检索数估计剩余页数。Reddit 未取得所有月度计数前只能报告请求数下限及明确假设下的耗时情景，不能保证全项目几小时内完成。连续 5 次瞬时错误后停止并标记需用户解决，不无限重试。

## Economics 2021-09 月度计数

用户选择将该月拆为互不重叠的UTC区间后求和。范围为09-01至09-08、09-08至09-15、09-15至09-22、09-22至09-29、09-29至10-01（左闭右开）。只有五段全部成功才发布月度分母；每段原始响应保留，来源路径及总和见 `monthly_count_partitions/Economics_2021-09.json`。分段响应为顺序取得的来源计数快照；不是抽样外推，也不代表同一瞬间的原子快照。

## 已实施的personalfinance时间窗规则（取代上述全天采样说明）

用户已批准实施 personalfinance_window_design.json：每月仍保留原先三个随机日期，但仅完整拉取各日期上随机起点的圆环时间窗。依据实际月度计数N计算时长，使每月期望记录约150条；缺计数不设假分母。随机流、选中区间、概率及计数快照均冻结存档。原来的全天完整日清单和原件仍保留，不变成新的窗口样本。

sample_unit=circular_time_window 的行使用 planned_sample_windows / completed_sample_windows / sample_windows_reused / sample_windows_newly_completed。这些行的 planned_sample_days / completed_sample_days 均为0，表示新方案没有“全天完整”的目标；不是旧全天库存消失。通用 planned_sample_dates / completed_sample_dates 表示相应日期的采样单位完成。target_expected_monthly_records、window_length_seconds、marginal_inclusion_probability、selected_time_intervals记录设计参数。

retained_full_days_including_selected_dates / retained_full_day_records_including_selected_dates 单列该来源原有全天库存，包含被新时间窗抽中的日期；这些库存与sample_unique_records有重叠，不可相加。personalfinance原完整31日及本轮较早补齐9日均留存。部分日期只有完整的选中窗口时，不增加全天库存数。

在实际计数快照稳定且来源区间接口穷尽的前提下，每条帖子边际入样概率相同，为(3/D)*(L/86400)。同一时间窗记录一起入样，仍非逐帖简单随机抽样。实际每月条数可以高于或低于150，不通过截断、重抽或凑数改变随机性。报告自动刷新逻辑及故障后停止规则不变。

## 优先使用personalfinance完整库存

已验证2025-01至2025-10全月库存区间完整，标记reuse_inventory_priority，先补来源aggregate月计数，再按既定日期、随机起点和时长规则直接生成窗口样本。这些月份无需新增文本请求。其余不完整月份仍只复用已穷尽的叶区间并补所选窗口缺口；不因库存在哪些日期存在而改抽。复核证据见 personalfinance_inventory_reuse_audit.json。来源新计数与旧库存的去重计数可能有快照差异，分别保留，不修改原件或伪造分母。

## 统一月度计数超时规则（用户已批准）

整月aggregate连续5次超时（包括来源422 Timeout、读取/连接超时、网关504）后，自动建立不重叠、最多7天一段的UTC分区；月末尾段不足7天，截止月不越过研究截止日。只在全部分段取得后求和发布月度分母，已取得的分段从断点复用，不重新请求整月。某分段仍连续失败5次则停止并询问，不能继续无限细分。403访问拒绝和429限速不触发这一规则，仍遵守原访问与限速处理。

规则在reddit_monthly_count_timeout_policy.json和状态文件中保存；分段的来源原件、计数与区间见monthly_count_partitions。该规则已解决personalfinance 2012-11的计数阻塞；它不会改变随机日期、时间窗、每月期望150条或作者字段边界。
