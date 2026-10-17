# 当前采集进度与缺口

现场核对：2026-10-16T02:54:51.644955+00:00。当前随机样本包含复用，旧原始库存另行保留。

| 来源 | 完整月份／计划 | 完整日期或窗口／计划 | 当前样本条数 |
|---|---:|---:|---:|
| MediaCloud/34412234 | 13/13 | 26/26 (UTC_full_day) | 39464 |
| MediaCloud/38379429 | 19/19 | 38/38 (UTC_full_day) | 185150 |
| Reddit/Economics | 120/120 | 360/360 (UTC_full_day) | 17857 |
| Reddit/economy | 120/120 | 360/360 (UTC_full_day) | 19831 |
| Reddit/personalfinance | 50/202 | 150/606 (circular_time_window) | 3453 |

Media Cloud及两个核心Reddit板块的当前抽样计划均已完成。personalfinance已按用户批准的统一计数超时规则恢复：整月五次超时后，自动按最多7天一段覆盖整月并求和；分段五次仍失败才停下询问。2012-11五段原始计数合计1046，三个窗口108条，已完成。

Reddit当前状态：waiting_retry；PID 12709。以状态文件为准。原件不覆盖、不执行哈希校验、不保存作者字段。其他来源缺口沿用current_collection_source_limits.csv，未重新请求受限站点。YouTube不属于本任务。

逐月待完成项：monthly_sampling_pending_months.csv；时间窗与概率详见personalfinance_window_month_plans及monthly_cluster_status.csv。
