# 逐日覆盖优先（2026-10-15 用户要求）

目标：先补全规定研究期内尚未查询的日期，再继续同一天的分页；条目总量不再作为覆盖完整性的替代指标。研究期截止仍为 2026-10-14，下载时间另记。

- Reddit：只对尚未完成的区间按 UTC 午夜分割；每天轮转。达到接口 100 条返回上限的区间二分后放到队尾，继续取完，不设总请求或条目上限。2025 年以来监测窗口首轮优先。已完成区间和原始文件不动。社区存档查询完整不等于 Reddit 本站完整。
- Media Cloud：2025-01-01 至截止日，两个集合分别按发布日期逐日查询。每个日期先取一页，随后轮转后续页；优先尚无已下载报道的日期。start=end 的同日请求已实际成功，程序验证每条返回记录发布日期均匹配。官方服务代码的整个窗口分页按 indexed_date 排序，因此此前总条数不能证明发布日期覆盖。旧窗口查询暂停，由 daily 状态文件记录新任务。旧批次与新日批次可能重叠，完整性表按 story ID 去重计数，原始数据不修改。
- YouTube：2023 年以来，被 uploads 截断的频道范围新增逐日官方 search 查询，先让不同日期获得查询机会，再加深某日或频道。搜索成功且无结果仅代表该查询无命中，不保证平台当天不存在相关视频。评论下载按视频发布日期累计取得页数调度，先补较少覆盖日期；每分钟接入新增发现的视频。评论真实日期单独统计；视频日期覆盖绝不等于评论日期覆盖。评论无按日期过滤接口，必须继续翻页，不能承诺全平台每日评论完整。2010–2022 的原方案季度样本尚未完成。
- NYT、Guardian：保留已取得的月批次，并按文章发布日期检查日分布；月批次完成不等于每天都有报道，也不等于当前月提供方已更新到截止日。
- 调查、宏观：按官方发布频率、应有观察期、发布日期和历史版本检查；不把月/季度值复制为每日值。休市、官方停发、源站无数据和未下载分开记录。
- GDELT 和媒体评级既有访问障碍未因本次调度调整而消失。评级属于非日频数据。

逐日状态表：daily_coverage.csv；摘要：daily_coverage_summary.json。这是带时间戳的快照，可用 src/collect/daily_coverage.py 刷新。只进行计数、日期与查询完成性检查，不进行内容分析、标注或哈希校验。

运行状态：reddit_collection_state.json、youtube_comment_text_state.json、youtube_daily_search_state.json、mediacloud_daily_state.json。旧 supervisor 状态已标记 superseded_by_daily_coverage_workers。实际 API 配额、禁用评论、访问错误等照实记录，不绕过限制。

核实依据：Media Cloud 官方客户端 https://github.com/mediacloud/api-client/blob/main/mediacloud/api.py 和官方服务 https://github.com/mediacloud/web-search/blob/main/mcweb/backend/search/views.py 。
