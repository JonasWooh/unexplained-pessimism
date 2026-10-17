# media_monthly.csv / media_quarterly.csv

- Generating script: `src/process/media_monthly.py`
- Inputs: `labels/ai/codex__v2_isolated_r1_corpus/` (frozen prompt v2, Codex, 58 batches totaling 11,431 items) and `labels/corpus_sample_key.csv` (sampling weights). The merged per-item labels are in `labels/ai_corpus_labels.csv`.
- One row per "source group × month" (the quarterly version is "source group × quarter"):

| group | Source | Coverage | Items coded per month |
|---|---|---|---|
| national | NYT + Guardian | 2010-01 to 2026-10, 202 months | 40 |
| mc_national | Media Cloud national | 13 sampled months | 20 |
| local | Media Cloud local | 19 sampled months | 40 |
| reddit | Four subreddits combined | 2015-01 to 2026-10, 142 months | 10 |
| youtube | Comments from 10 channels | 2023-01 to 2026-10, 46 months | 20 |

- There is no "all sources combined" group: social platforms are non-probability samples whose weights are not comparable with those of news, and combining them would make the meaning unclear.

## Estimation method

Within each cell a ratio estimator is used, with weight w = final_weight (first-stage design weight × within-stratum expansion factor). YouTube has no design weight, so w is the within-month expansion factor; since it is constant within a month, this is equivalent to no weighting. Content indicators are computed only on items with relevant = yes; unsure is only counted and does not enter the indicators.

## Column definitions

| Column | Meaning |
|---|---|
| `n_coded`, `n_relevant`, `n_unsure`, `n_not_relevant` | Number of items coded in the cell and the relevance distribution (unweighted counts) |
| `relevant_share` | Weighted relevant share: yes ÷ (yes + no) |
| `est_relevant_items` | Weighted estimated number of relevant items in the sampling frame. For news groups it can serve as supply volume; for YouTube the value applies only to comments on the selected videos |
| `net_tone` | Positive share − negative share |
| `share_negative`, `share_positive`, `share_mixed` | Share of each tone category |
| `net_fact` | Good-news share − bad-news share |
| `share_no_fact` | Share of items with only opinion and no facts |
| `emotional_intensity_mean` | Mean emotional intensity, 0–2 |
| `price_frame_share` | Share of items that involve prices |
| `price_level_share_of_priced` | Among items that involve prices, the share framed in terms of price level (level or both) |
| `household_share` | Share with a household perspective (household or both) |
| `forecast_share` | Share with a forecast framing (forecast or both) |
| `numeric_claim_share` | Share containing numeric claims |
| `definition_error_rate` | Conceptual errors ÷ applicable items |
| `blame_admin_share`, `credit_admin_share` | Share that blames or credits the president/administration for economic conditions (actor_1 or actor_2) |
| `fed_mention_share` | Share mentioning the Federal Reserve |
| `business_blame_share` | Share blaming businesses |
| `topic_*` | Share for each of the 13 topics |
| `low_n_flag` | Fewer than 10 relevant items; the estimate is unstable |
| `source_gap` | Note on source-side gaps: NYT 2026-01 has only days 1–7, and 2026-10 only runs to day 4 |
| `weighting` | Note on the weighting method |

## Quality and known issues

- Validation of the AI measurement is in `results/ai_validation/README.md`. κ between the test set and the gold standard:
  · relevant 0.86, tone 0.73, price framing 0.83, numeric claims 0.79
  · factual good/bad 0.57, emotional intensity 0.56, time framing 0.59, perspective 0.63, actor 0.67, attribution direction 0.56
  · conceptual errors 0.47, which is weak; the corresponding indicator should only be used descriptively
- Reddit codes only 10 items per month, and 140 of 142 months are low_n, so `media_quarterly.csv` should be used: only 7 of 48 quarters are low_n.
- The national group has 14–37 relevant items per month, median 26; monthly indicators have sampling noise, and a 3-month moving average can be used as a robustness check.
- Comparison with the monthly mean of the San Francisco Fed daily News Sentiment Index (`sffed_news_sentiment_monthly.csv`, 202 months): Pearson r for net_tone = 0.37, r = 0.44 after 3-month averaging; r for net_fact = 0.39. The two measure different things (the San Francisco Fed index is based on an article sentiment model over 24 newspapers), so a moderate correlation is within the expected range.
- The model is GPT 6 luna, reasoning effort high (declared by the project lead, `labels/ai/model_declaration.json`); in the run logs the model name is recorded as "not visible"; Codex cannot set temperature. Agreement rates for repeat runs on 26 test-set items: relevant 0.92, tone 0.85, emotional intensity 0.69, time framing 0.73.
- The run logs show that in some batches the evidence excerpt and claim_text fields were repaired after structural validation (`labels/ai/job_logs/`). The test set went through the same process, so test-set performance reflects the process actually used.
