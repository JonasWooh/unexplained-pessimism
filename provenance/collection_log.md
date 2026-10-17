# Collection process record

Snapshot generated at 2026-10-15T01:59:04.143385+00:00. Data retrieval cutoff 2026-10-14.

The plan and the task guide were first read in full, and then the sites listed in the plan were tested. Next, survey, macro, and vintage materials were collected; YouTube was started the same day, and news and reference sources continued. All raw files were created exclusively, and the actual sources and UTC times are recorded in sources.csv.

This round ran in the local conda base. Recorded parameter errors, 404s, 403s, 429s, and timeouts are all kept. Access denials were not circumvented with proxies, changed identities, or non-public interfaces. Reddit was not accessed directly. Permission and personal information boundaries are still handled according to the user's answers.

The survey/macro/reference data snapshot has been checked: 4578 raw files completed hash checks at 2026-10-15T01:57:30Z, with 0 failures and 0 unregistered raw files. The 16 ALFRED series have 37086 observation-vintage rows in total, with complete pagination. S01 has no missing months from 1978 onward, and S06 has 194 months in total with no duplicate CASEID.

The YouTube directory has been traversed to the boundary returned by the source: 8 channels were truncated at 20000 entries, and 2 channels go back to the 2023 boundary. After 96 successful pages, the official search received 429/rateLimitExceeded, and subsequent YouTube requests stopped. There are 35959 comment metadata records; comment text was not collected; this metadata is not called an NLP comment corpus.

The topic unions for Media Cloud national and local are 1015455 and 3015899 items respectively (API statistics, possibly duplicated across collections). At 1000 items per page and a rate limit of 2 requests per minute, the waiting time alone is about 35 hours, well above the plan's estimate. This single background download continues over the original monitoring range, with progress written to mediacloud_collection_state.json; the date range was not shortened, and it is not treated as a full-population sample. When the process ends/errors, the local snapshot will be regenerated.

Check of 20 news links: 14 succeeded, 4 refused, 1 not found, 1 rate-limited; title and date differences are in news_url_spotcheck.csv. Precision of the economic topic was not annotated, and no modeling or analysis was done. Preliminary/final values were only checked against real sources; the official 2025-01 revision was found and the raw file kept; 2026-10 ICS 46.3 has been confirmed as a preliminary value.

Files downloaded later are newer than the snapshot above, so the report item counts carry the generation time; the complete list is in collection_report.md and dataset_status.csv. Restricted sources and pending items are detailed in DECISIONS.md.

## Actual request results (including recorded failures, excluding cache hits)

| Dataset | Status code or exception type: count |
|---|---|
| M01 | 200: 7, 400: 1 |
| M02 | 200: 4, 400: 1 |
| M03 | 200: 4, 400: 1 |
| M04 | 200: 7, 400: 1 |
| M05 | 200: 4, 400: 1 |
| M06 | 200: 4, 400: 1 |
| M07 | 200: 8, 400: 2 |
| M08 | 200: 4, 400: 1 |
| M09 | 200: 8, 400: 2 |
| M10 | 200: 4, 400: 1 |
| M11 | 200: 4, 400: 1 |
| M12 | 200: 6, 400: 1 |
| M13 | 200: 3 |
| M14 | 200: 4, 400: 1 |
| M15 | 200: 4, 400: 1 |
| M16 | 200: 2, 400: 4 |
| M17 | 200: 15 |
| N01 | 200: 8 |
| N02 | 200: 2 |
| N03 | 200: 52, ReadTimeout: 1 |
| N04 | 200: 1, 429: 1 |
| N05 | 200: 5 |
| N06 | 403: 1 |
| R01 | 200: 31 |
| R02 | 200: 20, 403: 3, 404: 1 |
| R03 | 200: 14, 404: 1 |
| R04 | 200: 1 |
| R05 | 200: 4 |
| S01 | 200: 4 |
| S02 | 200: 8 |
| S03 | 200: 4 |
| S04 | 200: 15 |
| S05 | 200: 89 |
| S06 | 200: 16 |
| SM01 | 200: 4213, 403: 22, 429: 1 |
