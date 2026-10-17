# Unexplained Pessimism

**Economic fundamentals, media narratives and U.S. consumer sentiment ahead of the 2026 midterms.**
Final project for *AI Applications in Finance* (Jonas Wu). Data cutoff: 16 October 2026.

| Deliverable | File |
|---|---|
| Report (PDF) | [`report/report_draft_v1.pdf`](report/report_draft_v1.pdf), LaTeX source in [`report/src/`](report/src/) |
| Slides | [`presentation/Unexplained_Pessimism_slides.pptx`](presentation/Unexplained_Pessimism_slides.pptx) (PDF copy alongside), speaker script [`presentation/SCRIPT.md`](presentation/SCRIPT.md) |
| Dashboard | [`dashboard/index.html`](dashboard/index.html) (single offline file), guides [`DASHBOARD_GUIDE_EN.md`](dashboard/DASHBOARD_GUIDE_EN.md) / [`DASHBOARD_GUIDE.md`](dashboard/DASHBOARD_GUIDE.md) |
| Results summary | [`results/RESULTS_OVERVIEW.md`](results/RESULTS_OVERVIEW.md), per stage `results/FINDINGS_stage1-5.md` |
| Research design and decision log | [`research/RESEARCH_DESIGN_v1.md`](research/RESEARCH_DESIGN_v1.md), [`DECISIONS.md`](DECISIONS.md) |

On macOS, double-clicking `启动展示.command` opens the dashboard and the report (type `r` within 5 seconds to rebuild the dashboard first).

## Question and approach

U.S. consumer sentiment has stayed far below what headline economic indicators imply. The project asks how much of that gap fundamentals explain, and whether news and social-media coverage helps explain the rest.

1. **Real-time baseline.** An economic-only model (M1) regresses the University of Michigan Index of Consumer Sentiment (ICS) on unemployment, PCE inflation and real GDP growth, each taken at the ALFRED vintage available before the survey month. It is fit on 2010–2019; the *sentiment gap* is its out-of-sample residual.
2. **Validated LLM measurement.** A frozen prompt codes tone, salience, framing, factual calibration and political attribution for a stratified sample of 11,431 items (NYT, Guardian, Media Cloud national and local news, Reddit, YouTube comments). It is validated against 360 items double-coded by humans and benchmarked against a finance dictionary and a conventional classifier.
3. **Association versus causation.** Chronological forecast comparisons, timing tests and pre-registered falsification criteria. 150 specifications are registered in `results/spec_registry.csv`, adverse results included.

## Main findings

- The gap averages **−35.8 ICS points in 2025 and −39.8 in Jan–Oct 2026**. The three fundamentals explain only 7–11% of the decline since 2019, and the 2025–26 gap stays at least 23 points under every window and robustness variant.
- LLM coding agrees with the human gold standard far better than the dictionary does (tone κ = 0.73, against 0.79 between the two annotators and 0.35 for the Loughran–McDonald dictionary). Swapping political names does not detectably change the coding.
- Lagged national news tone improves on the economic-only forecast (Clark–West p = 0.041) but not once household-pressure and political controls are added (p = 0.23; none of 20 variants significant). Tone-related variation accounts for **at most about 5% of the 2025–26 gap**.
- The gap is similar across income, age, region and education groups and among Republicans. It widens within the web-only survey period, so the change in survey mode does not account for it, and it is already present before the campaign season.
- **Media bias is not the main explanation of the gap.** What remains unexplained is discussed in the report, and `results/CAUSAL_DESIGN_PROPOSAL.md` proposes a randomized framing experiment for causal identification.

## Repository layout

```
.
├── README.md, DECISIONS.md      project overview; timestamped log of every design decision and deviation
├── 启动展示.command               one-click launcher for the dashboard and report (macOS)
├── src/
│   ├── collect/                 data collection from official APIs and archives (needs API keys, see below)
│   ├── process/                 raw → processed panels, corpus, labels, media indices (run_all.sh)
│   ├── annotation/              human annotation sample, workbooks, agreement, gold standard, AI scoring
│   ├── analysis/                research stages 1–5 (run_research.sh); file hashes in results/script_sha256.csv
│   ├── dashboard/               dashboard builder (build.py, template, JS/CSS, vendored D3 7.9.0)
│   └── presentation/            slide figures and deck builder (python-pptx)
├── data/
│   ├── raw/                     original downloads, never modified            [local only]
│   ├── processed/               real-time economic panel, survey panel, research panel
│   └── external/                professor's Excel, used only for a read-only cross-check  [local only]
├── corpus/                      corpus documentation and counts; items.parquet and raw/ are [local only]
├── annotation/, labels/         sampling design, agreement statistics, AI run logs (text-bearing files local only)
├── codebook/, prompts/          coding manual and frozen LLM prompts (v1, v2) with SHA-256
├── codex_runs/                  name-swap (R3.7) run package (inputs local only)
├── features/                    monthly and quarterly media indices
├── provenance/                  release calendar, inventory, collection state and reports (source registry and request log local only)
├── research/                    pre-registered research design
├── results/                     frozen outputs of every stage, findings, spec registry, script hashes
├── report/                      report PDF, plan, LaTeX source, figure/table generators
├── presentation/                deck (.pptx and .pdf), plan, script, slide figure layers
├── dashboard/                   built dashboard and guides
└── docs/
    ├── task_guide.md, data_collection_plan.md      original task checklist and data plan
    ├── README_data.md, README_collection.md         data hand-off notes and collection notes
    ├── audits/                  data collection audit, temporary-file audit
    ├── notes/                   overview of the course files, collection brief
    └── assignment/              course assignment PDF                         [local only]
```

## Data not in git

Everything marked *local only* is excluded by `.gitignore`. Raw downloads are bulky, and the corpus contains third-party text (news articles, Reddit posts, YouTube comments) that may not be redistributed; YouTube API data must also be refreshed or deleted within 30 days. Sizes at the time of the first commit:

| Excluded | Size | How to obtain |
|---|---:|---|
| `corpus/raw/` (NYT, Guardian, Media Cloud, Reddit, YouTube responses) | 4.5 GB | `src/collect/` with your own API keys |
| `data/raw/` (ALFRED/FRED, Michigan survey, BLS, BEA, release calendars) | 91 MB | `src/collect/` (public sources) |
| `corpus/items.parquet` (corpus main table with text) | 61 MB | `sh src/process/run_all.sh` after collection |
| YouTube per-video metadata in `provenance/` and `data/processed/youtube_videos.csv` | 172 MB | `src/collect/youtube_*.py` |
| Annotation sample, workbooks, annotator files, gold standard, adjudication (contain item text) | 1.7 MB | `src/annotation/` and `src/process/run_all.sh` from the corpus; human labels themselves cannot be regenerated |
| LLM inputs and raw outputs (`labels/ai_inputs/`, `labels/ai/**/*.jsonl`, `labels/ai_corpus_labels.csv`, R3.7 inputs, `results/stage2_r35/test_predictions.csv`) | 19 MB | rerun the frozen prompts in `prompts/`; run logs and prompt hashes are committed |
| Source registry and request log (`provenance/sources.csv`, `provenance/requests.jsonl`) | 47 MB | written by `src/collect/` during collection |
| Course PDF and Excel | 0.1 MB | course materials |

Because of this, a fresh clone contains every frozen result, the report, the deck and the dashboard, but the full rebuild needs the local-only files.

## How to reproduce

Environment used: Python 3.11 (conda base) with pandas 1.5, numpy 1.24, statsmodels 0.14, scipy 1.10, scikit-learn 1.3, matplotlib 3.7, pyarrow 11, plus requests, beautifulsoup4, lxml, openpyxl, xlrd, PyMuPDF, pypdf and vaderSentiment. The deck needs python-pptx. The report needs XeLaTeX with the TeX Gyre fonts (a full TeX Live; BasicTeX lacks them). All commands run from the repository root.

1. **Collect** (network; only if raw data are missing). Put a local `API_KEY.txt` at the root with one labelled line per service (FRED, NYT, Guardian, Media Cloud, YouTube). It is git-ignored and read only at run time. Collection order, quotas and resumable state are described in `docs/README_collection.md` and `provenance/collection_report.md`.
2. **Process** (no network, about 5 minutes): `sh src/process/run_all.sh` rebuilds `data/processed/`, `corpus/items.parquet`, `labels/` and `features/` from the raw files. Set `PY=/path/to/python` if your interpreter is not `~/anaconda3/bin/python`. The annotation sample is frozen and deliberately not redrawn.
3. **Analyse**: `sh src/analysis/run_research.sh` runs stages 1–5 in order (uses `python3` on `PATH`) and rewrites `results/`, including the spec registry and script hashes.
4. **Report**: `python report/src/make_figures.py && python report/src/make_tables.py`, then in `report/src/` run `xelatex report && bibtex report && xelatex report && xelatex report`.
5. **Slides**: `python src/presentation/make_slide_figures.py && python src/presentation/build_deck.py`.
6. **Dashboard**: `python src/dashboard/build.py` writes `dashboard/index.html` (D3 inlined, works offline).

Known data limitations (NYT gap in January 2026, local news text only for 2025–26, YouTube only from 2023, preliminary October ICS) are listed in `docs/README_data.md` and in the report.
