# youtube_videos.csv

- Generating script: `src/process/export_labels.py`
- Source: `provenance/youtube_freeze_v1_20261015T2310Z/`; videos.list statistics snapshot taken on 2026-10-15
- Rows: 7,289 candidate videos, covering videos from 2023-01-01 to 2026-10-14 whose titles match the economic term list

## Column definitions

| Column | Meaning |
|---|---|
| `routes` | How the video was obtained: uploads list, long-video (UULF) or live-stream (UULV) category list, older search supplement |
| `search_only_supplement` | True means obtained only through the older search, which is a non-random sample |
| `view_count`, `comment_count_snapshot` | Snapshot from 2026-10-15, not values at the time of publication. Can serve as a rough proxy for exposure (R2.4); videos with different publication times have accumulated over different lengths of time, so they cannot be compared directly |
| `comments_collected`, `window_comments` | Whether comments have been fully collected; number of top-level comments within 30 days after publication |

## Known issues

- The upload lists of 8 large channels only cover recent periods, and 2023–2024 relies mainly on the search supplement; Shorts are not included.
- PBS NewsHour has comments turned off.
- YouTube API policy requires unauthorized data to be refreshed or deleted within 30 days. This data is for internal research use only and is not distributed externally.
