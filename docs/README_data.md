# Data handoff overview (2026-10-16)

Data collection, processing, LLM coding, and the monthly media indices are all complete, and statistical analysis (models 1–3) can begin. Raw files are in `data/raw/` and `corpus/raw/`, and none of them have been modified. Each decision is recorded in `DECISIONS.md`; source and download records are in `provenance/`.

## Handoff files

| File | Contents | Notes |
|---|---|---|
| `data/processed/econ_monthly_realtime.csv` | Real-time monthly economic panel, 2010-01 to 2026-10 (D2 cutoff), 202 rows | `.md` |
| `data/processed/econ_monthly_realtime_prelim_cutoff.csv` | Sensitivity version: cutoff is the Michigan preliminary release date | Same as above |
| `data/processed/survey_monthly.csv` | Michigan subgroups, partisanship, news heard, reasons and expectations, 1978-01 to 2026-09, 585 rows | `.md` |
| `data/processed/youtube_videos.csv` | Snapshot of view counts and comment counts for 7,289 candidate YouTube videos | `.md` |
| `corpus/items.parquet` | Main corpus table, 167,418 items | `items.md`, `corpus_documentation.md` (R2.3) |
| `corpus/source_month_counts.csv` | Retrieved, included, and deduplicated counts by source × month | — |
| `labels/` | Annotation sample, A/B annotations, agreement, adjudication records, gold standard v1 | `labels/README.md` |
| `codebook/codebook.md`, `examples.md` | Codebook v1 (human labeling guide) and gold-standard examples | — |
| `labels/ai_corpus_labels.csv` | LLM labels (frozen v2) for the 11,431 formal coding sample items, plus sampling weights | `labels/ai/run_log.csv` |
| `features/media_monthly.csv`, `media_quarterly.csv` | Monthly and quarterly media indices (national, Media Cloud national, local, Reddit, YouTube) | `features/media_monthly.md` |
| `features/sffed_news_sentiment_monthly.csv` | Monthly mean of the San Francisco Fed News Sentiment Index (comparison) | Same as above |
| `results/ai_validation/` | AI measurement validation on the development set and test set, and repeat-run agreement rates | `README.md` |

## Reproduction

`sh src/process/run_all.sh` rebuilds all of the files above from the raw files in about 5 minutes, without making any network requests. Verified on 2026-10-16: after a rerun, `items.parquet`, `econ_monthly_realtime.csv`, and `adjudicated.csv` are byte-for-byte identical to the original files.

Annotation sampling (`src/annotation/build_sample.py`) is frozen and is not part of the rebuild pipeline.

## Limitations to know before starting the research

- NYT 2026-01-08 to 01-31 is missing, and 2026-10 only runs to 10-04.
- Local news text exists only for 2025–2026.
- Social platforms: YouTube only covers 2023 onward and is a non-probability sample; Reddit sampling starts in 2015 (earlier for personalfinance and inflation).
- Keyword inclusion has a precision of about 0.5–0.6 for NYT and Reddit, so relevance filtering must be done before building indices.
- GDELT and media outlet bias ratings were not obtained.
- Each macro series is empty before its earliest ALFRED vintage. HOAM housing affordability has no historical vintages. The 2026-10 Michigan index is preliminary.
