# Current collection progress and gaps

On-site check: 2026-10-16T02:54:51.644955+00:00. The current random sample includes reused items; the old raw inventory is kept separately.

| Source | Complete months/planned | Complete dates or windows/planned | Current sample items |
|---|---:|---:|---:|
| MediaCloud/34412234 | 13/13 | 26/26 (UTC_full_day) | 39464 |
| MediaCloud/38379429 | 19/19 | 38/38 (UTC_full_day) | 185150 |
| Reddit/Economics | 120/120 | 360/360 (UTC_full_day) | 17857 |
| Reddit/economy | 120/120 | 360/360 (UTC_full_day) | 19831 |
| Reddit/personalfinance | 50/202 | 150/606 (circular_time_window) | 3453 |

The current sampling plans for Media Cloud and the two core Reddit subreddits are all complete. personalfinance has resumed under the unified count timeout rule approved by the user: after five timeouts on a full month, the whole month is automatically covered in segments of at most 7 days and summed; the process stops and asks only if a segment still fails five times. For 2012-11, the five segments' raw counts total 1046, and the three windows have 108 items; this month is complete.

Current Reddit status: waiting_retry; PID 12709. The state file is authoritative. Raw files are not overwritten, no hash verification is performed, and author fields are not saved. Gaps for other sources follow current_collection_source_limits.csv, and restricted sites were not requested again. YouTube is not part of this task.

Pending items by month: monthly_sampling_pending_months.csv; time windows and probabilities are detailed in personalfinance_window_month_plans and monthly_cluster_status.csv.
