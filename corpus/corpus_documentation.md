# Corpus documentation (R2.3, R2.4)

The main corpus table is `corpus/items.parquet`; column definitions are in `items.md`. This file records, item by item, the content required by task_guide 8.5. All numbers were checked against the output of `src/process/build_corpus.py` on 2026-10-16. Each decision made during collection is recorded in `DECISIONS.md` in the root directory.

## 1. Search terms and date range

- There are 26 search terms, originally in English, in five groups:
  · Inflation and prices: inflation, prices, cost of living, grocery prices, gas prices, affordability, price increases
  · Employment: unemployment, jobless, layoffs, hiring, jobs report, labor market
  · Growth and recession: GDP, economic growth, recession, economic slowdown
  · Interest rates and housing: interest rates, mortgage rates, Federal Reserve, housing costs, rent
  · General: economy, consumer sentiment, consumer confidence, tariffs
- Rule `economic_title_regex_v1`: matched on word boundaries, case-insensitive.
- Date range: 2010-01-01 to 2026-10-14 (research cutoff). YouTube only covers 2023-01-01 onward. YouTube videos from 2010–2022 are deferred by the user's decision.

## 2. Sources, selection rationale, and sample design

| Tier | Source | Unit | Design | Coverage | Items included |
|---|---|---|---|---|---:|
| National | NYT Archive API | Headline + abstract + lead paragraph (from 2025 the source no longer provides the lead paragraph) | Full archive | 2010-01 to 2026-10, 202 months | 38,468 |
| National | Guardian Open Platform, business/US economy tag | Headline + standfirst + full text | Full archive | 202 months | 4,286 |
| National | Media Cloud US National collection | Headline | Fixed seed, 2 whole days randomly drawn per collection-month | 2025-09 to 2026-09, 13 months | 3,854 |
| Local | Media Cloud US State & Local collection | Headline | Same as above | 2025-03 to 2026-09, 19 months | 25,055 |
| Social | Reddit: r/economy, r/Economics | Post title + body | 2015–2024: 3 random whole days per month; from 2025-01: exhaustive full-month queries | 2015-01 to 2026-10 | 29,767 |
| Social | Reddit: r/personalfinance | Posts | Random circular time windows within 3 random days per month, about 150 items expected per month | 2010-01 to 2026-10, 202 months | 3,603 |
| Social | Reddit: r/inflation | Posts | Exhaustive full-month queries | All available months | 7,726 |
| Social | YouTube: comments under videos from 10 news channels | Top-level comments (within 30 days after publication) | Non-probability: videos selected with priority on date coverage, all comments taken from selected videos | 2023-01 to 2026-10, 46 months | 54,659 |

Selection rationale:
- NYT and the Guardian are the national sources with free, reproducible archives that go back to 2010. Media Cloud provides national and local collections for comparison.
- YouTube is the platform with the highest usage among US adults (Pew 2025: 84%). Reddit is a supplementary platform whose users skew younger and more highly educated; it is suitable only for comparison and does not represent the nation.
- The channel list and rationale are in `provenance/youtube_channels.csv`. No inference was made about channel leaning.

## 3. Inclusion and exclusion criteria and precision

- Inclusion: the unit's own text matches at least one search term.
- Exclusion: ads and sponsored content (`is_ad`, 8 items) and obituaries (`is_obituary`, 170 items). Both are only flagged, not deleted; they are excluded during analysis.
- Content-level exclusions such as "stock market quotes only" and "non-US economy" are handled by the relevance judgments of human annotation and AI, not by keyword rules.
- The precision of the keyword rule is estimated against the gold standard (`labels/adjudicated.csv`, a stratified random sample of 360 items), precision = yes ÷ (yes + no), with unsure listed separately; values in parentheses are estimates using sampling weights:

| Source | Items annotated | yes | no | unsure | Precision (weighted) |
|---|---:|---:|---:|---:|---:|
| NYT | 125 | 70 | 48 | 7 | 0.59 (0.61) |
| Guardian | 40 | 39 | 1 | 0 | 0.98 (0.94) |
| Media Cloud national | 15 | 10 | 5 | 0 | 0.67 (0.67) |
| Media Cloud local | 60 | 40 | 11 | 9 | 0.78 (0.78) |
| Reddit | 90 | 37 | 42 | 11 | 0.47 (0.49) |
| YouTube | 30 | 24 | 1 | 5 | 0.96 (0.97) |

  Conclusion: the keyword rule's precision for NYT and Reddit is only about one-half to six-tenths, so before building monthly indices the items must be filtered again with a validated relevance classification.

## 4. Text unit types

See Section 2 and `unit_type` in `items.md`. Different units carry different amounts of information: Media Cloud has only headlines, while the Guardian is full text. In analysis, group by source or add source fixed effects; they cannot be mixed together and compared directly.

## 5. Geographic relevance and audience information

- NYT, the Guardian, and the Media Cloud national collection are at the national tier; the Media Cloud state and local collection covers 1,713 outlets. Metadata on the state where each outlet is located was not obtained, so `geo_state` is empty.
- The Guardian is a UK outlet; only its US economy tag is used.
- Audience information:
  · Subreddit subscriber counts (archive snapshot): r/personalfinance 20,444,068, r/Economics 5,240,534, r/economy 1,028,494, r/inflation 96,189
  · YouTube channel statistics are in the SM01 channel files under `data/raw`
  · Video view counts are in `data/processed/youtube_videos.csv`
  · Platform usage among US adults is in R04 (Pew 2025)

## 6. Deduplication, syndication, ads, suspected automation

- The rules are in "Duplicate identification" in `items.md`.
- Results: 2,484 duplicates, 21,188 syndicated copies, 666 near-duplicate pairs merged.
- Syndication is concentrated in local media: 25,055 Media Cloud local items were included, and 7,264 remain after removing duplicates and syndicated copies. Wire-service stories are widely republished by local sites, and the syndication count is recorded as a measure of supply amplification.
- Periodic template posts on Reddit (such as weekly price discussion threads) are identified as near-duplicates.
- Suspected automation: by privacy design, author and account fields were not saved, so rules based on posting frequency, account creation time, and so on cannot be used, and `is_suspected_automated` is left empty; this is written into the report as a limitation. Exact content-level duplicates have already been flagged by the deduplication rules.

## 7. Item counts and missingness by source and month

`source_month_counts.csv` gives, by source × month: items retrieved, items included, items after deduplication, and items after deduplication and syndication removal.

Known gaps:
- NYT 2026-01-08 to 01-31 is missing (only 16 items included that month), and 2026-10 only runs to 10-04. After re-requesting, the source still returns only these, so this is a source-side gap and cannot be treated as zero coverage.
- Media Cloud text exists only for the sampled months above; earlier years have only daily counts (the N03 count files in `data/raw`).
- YouTube has 308 days with no usable video. The upload lists of 8 large channels only cover recent periods, and 2023–2024 relies mainly on supplementary older searches, which is a non-random sample; 18,525 comments have `video_search_only_supplement` marked True. PBS NewsHour has comments turned off.
- GDELT is not available (HTTP 429). Numeric media outlet bias ratings were not obtained (AllSides returned 403).

## 8. Access restrictions and terms of use

- NYT, Guardian: official APIs and keys; NYT has only the abstract and lead paragraph (snippet_only).
- Media Cloud: official API, headlines only.
- Reddit: Arctic Shift community archive, not the official Reddit interface; it cannot be claimed to be complete real-time Reddit data. score and num_comments are snapshots at the time the archive crawled them.
- YouTube: official Data API v3. The API policy requires unauthorized data to be refreshed or deleted within 30 days, so it cannot serve as an indefinite archive.
- All sources: author and account fields are not saved; for internal research use only; original text is not distributed externally. The submission package provides only IDs and re-crawl scripts (task_guide 8.6).

## 9. Sampling limitations and their effect on conclusions

- Local news text only covers 2025–2026, so for 2017–2024 only attention volume (counts) can be used in the models. Comparisons of local vs. national tone can only be made for 2025–2026.
- Social platform coverage periods are short, and their users do not represent the nation: Reddit sampling starts in 2015 (earlier for personalfinance and inflation), and YouTube starts in 2023. Social indices are used only for sensitivity analysis and recent comparisons, and do not enter the 2010–2019 estimation period.
- YouTube is a non-probability sample with no sampling weights; it can only be used for description and within-group comparisons, and cannot be extrapolated to the platform as a whole.
- The precision of keyword inclusion varies by source (Section 3), so the monthly indices must first be filtered with a validated relevance classification.
