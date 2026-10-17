# 当前采集方式

用户已批准并实施 personalfinance 每月期望约150条的随机日期＋圆环时间窗采样。主报告为 monthly_cluster_status.csv 和 monthly_cluster_summary.json；以实时状态文件为准。

- Media Cloud：已完成当前全部64个抽样日、32个集合月份。全国39464条，地方185150条。原有完整月份和其他完整日期另列保留；数量指标来自已有每日检索计数。
- Reddit economy / Economics：各2015–2024年、每月3个完整UTC随机日期，各360日；继续优先2017–2024年。两核心版块原计划和断点未改变。
- personalfinance：仍是2010-01至2026-10既有每月3个随机日期，共606个日期窗口。用真实月度总数N和可观察日数D确定窗口时长，期望月度条数约150；随机起点在当天24小时圆环上均匀抽取，跨午夜拆为当日首尾两段。抽中窗口取全，不因达到150条而截断。完成窗口不等于完成全天。
- 新设计 personalfinance_window_design.json，月度冻结参数 personalfinance_window_month_plans，选择清单 monthly_cluster_selections/reddit_personalfinance_window_v1_*。旧完整日状态快照与选择清单保留，全天库存与新窗口样本分开，不相加重复计数。
- 报告字段 sample_unit 区分 UTC_full_day / circular_time_window；personalfinance 用 planned/completed_sample_windows，完整全天计数字段为0。通用 planned/completed_sample_dates 表示对应日期的采样单位完成，不保证全天完整。
- 旧月度/半日主表与历史方案草稿保留；personalfinance_sampling_proposal.md 的“未实施”仅为历史草案状态，已由本次用户授权的实际设计取代。
- 每接口单worker、原速率和连续失败上限、作者字段排除、retrieved_on保留、原件不覆盖、无哈希校验均保持。YouTube不属于本任务，不调用或管理其接口。

库存优先安排：personalfinance 2025-01至2025-10完整旧库存可直接生成30个新规则窗口，现已提到队列前部；只补真实月度aggregate计数，不新增正文下载。固定随机日期及窗口生成规则不变，证据见personalfinance_inventory_reuse_audit.json。

已实施统一计数超时分段规则：整月aggregate五次超时后自动按UTC最多7天分段求和，分段五次失败才停并询问。personalfinance 2012-11阻塞已解决（月度计数1046），worker已从断点继续；当前具体进度以状态文件及monthly_cluster_status.csv为准。
