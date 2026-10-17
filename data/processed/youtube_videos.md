# youtube_videos.csv

- 生成脚本：`src/process/export_labels.py`
- 来源：`provenance/youtube_freeze_v1_20261015T2310Z/`；videos.list 统计快照取于 2026-10-15
- 行数：7,289 个候选视频，范围是 2023-01-01 至 2026-10-14、标题命中经济词表的视频

## 列定义

| 列 | 含义 |
|---|---|
| `routes` | 取得途径：uploads 列表、长视频（UULF）或直播（UULV）分类列表、旧搜索补充 |
| `search_only_supplement` | True 表示只经旧搜索取得，属于非随机样本 |
| `view_count`、`comment_count_snapshot` | 2026-10-15 的快照，不是发布当时的数值。可作为接触量的粗略代理（R2.4）；不同发布时间的视频之间，累计时长不同，不能直接比较 |
| `comments_collected`、`window_comments` | 是否已完整采集评论；发布后 30 天内的顶层评论数 |

## 已知问题

- 8 个大频道的上传列表只覆盖近期，2023–2024 年主要依靠搜索补充；Shorts 未纳入。
- PBS NewsHour 关闭了评论。
- YouTube API 政策要求，非授权数据须在 30 天内刷新或删除。本数据仅供内部研究使用，不对外分发。
