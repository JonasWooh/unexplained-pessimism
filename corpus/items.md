# items.parquet

- Generating script: `src/process/build_corpus.py`, runs in about 5 minutes
- Generated: 2026-10-16
- Rows: 167,418, one row per corpus unit (in scope). By source:

| Source | Items |
|---|---:|
| YouTube | 54,659 |
| Reddit | 41,096 |
| NYT | 38,468 |
| Media Cloud local | 25,055 |
| Guardian | 4,286 |
| Media Cloud national | 3,854 |

- Inclusion rule: the unit's own text (title + text) matches at least one economic search term (the 26 terms in task_guide 8.2, i.e. `youtube_details.TERMS`), and the publication date is between 2010-01-01 and 2026-10-14. This is the same rule as for the human annotation sampling frame.
- Retrieved, included, and deduplicated counts by source × month are in `source_month_counts.csv`; summary statistics are in `items_stats.json`.

## Column definitions

| Column | Meaning |
|---|---|
| `item_id` | `source:ID within source`, unique across the table |
| `source` | NYT, Guardian, MediaCloud_National, MediaCloud_Local, Reddit, YouTube |
| `outlet_name` | Outlet name, subreddit (r/…), or YouTube channel name |
| `source_level` | national, local, social |
| `platform` | news_api, media_cloud, reddit, youtube |
| `unit_type` | headline_abstract_lead, headline_abstract (NYT has no lead paragraph from 2025 on), full_text (Guardian), headline (Media Cloud), post, comment |
| `pub_datetime_utc` | Publication time. Media Cloud has the date only |
| `month` | Publication month YYYY-MM |
| `url` | Link to the original; for YouTube comments, the video link |
| `title`, `text` | Title, body, or excerpt. When a Reddit body is `[removed]`/`[deleted]`, text is empty and the original status is recorded in `body_status` |
| `text_license` | full (Guardian, Reddit, YouTube), snippet_only (NYT abstract/lead paragraph, Media Cloud headline) |
| `query_terms_matched` | Matched search terms, separated by `|` |
| `geo_state` | Empty: metadata on the state where the outlet is located was not obtained |
| `audience_info` | Subreddit subscriber count (archive snapshot); empty for other sources |
| `dedup_cluster_id`, `cluster_size` | Duplicate cluster and its size |
| `is_duplicate` | A duplicate within the same outlet or account space, and not the earliest item in its cluster |
| `is_repost` | A syndicated copy across different outlets, and not the earliest item in its cluster; syndication count = number of distinct outlets in the cluster − 1, usable as a measure of supply amplification |
| `is_ad` | Guardian isHosted (advertiser-hosted content), NYT paid content, or URL path containing sponsored / sponsor-content / paid-content / advertorial |
| `is_obituary` | NYT type_of_material is Obituary or Paid Death Notice, or URL contains /obituar |
| `is_suspected_automated` | Empty: by privacy design, account fields were not collected, so it is not possible to judge by account whether an account is automated |
| `engagement_likes`, `engagement_replies` | Reddit score and num_comments (snapshots at the time the archive crawled them, not comparable across years); like counts and reply counts for YouTube comments |
| `engagement_reposts` | Empty: neither platform provides it |
| `collected_at_utc` | Download time of the corresponding raw file (from `provenance/sources.csv`) |
| `design` | full_archive, random_day_cluster, random_circular_window, exhaustive_month, non_probability_video_selection |
| `sample_weight` | Inverse of the inclusion probability within source × month: 1 for the full archive; for day clusters, observable days in the month ÷ days drawn; 1/p for circular time windows; empty for YouTube (non-probability sample) |
| `sample_date` | The date drawn, for cluster and time-window designs only |
| `section`, `type_of_material` | News section, article type |
| `video_id`, `video_title`, `video_channel_group`, `video_search_only_supplement` | YouTube comments only |
| `source_item_id`, `raw_file` | ID within the source and raw file path, for traceability |

## Duplicate identification

Union-find is used to merge three kinds of relations:

1. Same normalized URL, news only: hostname and path lowercased, fragment and tracking parameters (utm_*, fbclid, gclid, etc.) removed, other query parameters kept.
2. Same normalized text: lowercased, keeping only letters, digits, and spaces.
3. Near-duplicates: only for texts of more than 8 words. MinHash on word-level 3-grams (128 permutations, 32 bands × 4 rows, seed 20261015), then verified with exact Jaccard ≥ 0.8.

Identified: 2,484 duplicates, 21,188 syndicated copies (mainly wire-service stories in Media Cloud local outlets), 666 near-duplicate pairs merged, 8 ads, 170 obituaries.

**Do not delete these items during analysis**; choose according to the question:
- For supply volume, use all items;
- For content units, use `~is_duplicate & ~is_repost`;
- Exclude ads and obituaries per Section 8.2.
