# Research Design v1 (pre-registered version)

2026-10-16. Finalized from draft v0: the project lead approved D-A through D-F, all as recommended, at 2026-10-16T18:10Z. Source: Claude Doc "Research Design Draft v0" rev 14. Once frozen, this file will not be modified again; later changes are recorded in DECISIONS.md as deviations.

## Confirmed decisions (approved 2026-10-16T18:10Z)

This draft maps the professor's six research questions onto three groups of falsifiable hypotheses, four models (M1, M1c, M2, M3), and six execution stages. The six items below need your sign-off; everything else follows the defaults in the draft. Once finalized, the full text is written into `DECISIONS.md` as the pre-registration before any model is run, and any later deviation is recorded separately.

| ID | Decision | Recommendation | Rationale |
| --- | --- | --- | --- |
| D-A | Estimation window for the gap model | Keep the fixed 2010–2019 window as the main specification; additionally pre-register two windows, 2000-09–2019 (fully real-time) and 1978–2019 (quasi-real-time), and report the results side by side | In 2010–2019, real-time PCE year-over-year inflation ranged only from 0.2% to 3.0% and the mortgage rate only from 3.3% to 5.0%; in 2022 they reached 6.8% and 7.8%. The main window's coefficients on high inflation and high rates are extrapolations, so the size of the gap must come with a window-sensitivity range |
| D-B | The single primary media hypothesis | The t−1 month value of national news `net_tone` | The cutoff is the 1st of month t, so the current month's media index does not yet exist at the forecast origin; only one primary hypothesis is set, and the other media measures are treated as secondary hypotheses with multiple-testing correction |
| D-C | Coverage of factual calibration | Additionally pull all ALFRED vintages of the two series CPIAUCSL and PAYEMS (using your local FRED key, a few minutes) | The national sample has 1,562 numeric claims, but the existing vintage data can only check the unemployment rate (about 64 claims) and GDP (about 26 claims); the roughly 50 inflation claims mostly cite CPI, and part of the roughly 180 employment claims concern nonfarm payrolls. Without the extra pull, only U-3, GDP, and PCE can be checked, and coverage is very small |
| D-D | Early backfill of non-revised series | For the mortgage rate (Freddie Mac PMMS) and gasoline prices (EIA), fill the months before their earliest ALFRED vintage with the values in the earliest vintage | These two series are never revised after release, so backfilling introduces no look-ahead; series that are revised (EPU, Case-Shiller, U-6, etc.) are not backfilled |
| D-E | Dictionary methods and traditional classifiers | Dictionaries: Loughran–McDonald and VADER (Lexicoder added if licensing allows); traditional classifier: TF-IDF plus logistic regression, trained on the 11,431 LLM labels and evaluated on the 260-item human test set, plus a version trained only on the 100-item human development set | The two training sources answer, respectively, "can the LLM be replicated cheaply" and "are small-sample human labels enough" |
| D-F | Scale of the name-swap test (R3.7) | 120 items × 4 new versions = 480 codings, in 4 batches (the first original-text run reuses the labels from the main coding directly), run by you with Codex in an isolated folder, with the model and prompt unchanged | A second run of the original text must be included to separate the swap effect from Codex's own randomness (tone repeat agreement 0.85) |

Known limitations that need no decision from you but will affect how conclusions are worded: there is no public monthly series on partisan composition, so only a sensitivity range is possible; social platforms and local news enter only the recent descriptive comparison, not the historical models.

## Research questions and hypotheses

The professor asks us to distinguish three explanations: H1, real pressures not captured by headline indicators; H2, information selection, framing, or cognitive bias; H3, measurement, timing, or model problems. The three are not mutually exclusive, and conclusions are given as a combination of evidence; "media bias cannot explain the gap" is an equally acceptable conclusion.

| Research question | Operationalization in this project | Main hypothesis tested | Stage |
| --- | --- | --- | --- |
| RQ1 How to measure bias in news or social media | AI measurement on five dimensions, each paired with an explicit benchmark; human gold-standard validation, dictionary-method comparison, name-swap test | Premise of H2: whether the media side deviates from its benchmarks | 2 |
| RQ2 The effect of this bias in depressing Michigan sentiment | Incremental association after controlling for fundamentals, two-way temporal ordering, the "news heard" pathway, causal design proposal | H2 | 3–4 |
| RQ3 How much of the gap unemployment, inflation, and GDP can explain | M1 out-of-sample gap, explained share, decomposition of each indicator's contribution, with a window-sensitivity range | Benchmark; also tests H1 and H3 | 1 |
| RQ4 Which perception mechanisms the data can measure | Mechanisms classified as "measured", "only compatible evidence", and "not measurable" (table below) | H2, H1 | 5 |
| RQ5 Whether media analysis improves sentiment forecasts | Recursive out-of-sample forecasts, Clark–West test, reported by period | H2 | 3 |
| RQ6 What evidence would refute the media-bias explanation | Pre-registered list of falsification criteria with decision rules, adjudicated one by one after analysis | H2 | 4 |

**Testable hypotheses** (directions stated in advance; gap = actual sentiment − M1 out-of-sample forecast)

- H1a Price level: 36-month cumulative PCE inflation is negative for sentiment after controlling for 12-month inflation, and adding it shrinks the negative gap since 2021.
- H1b Borrowing costs: the 30-year mortgage rate is negative, and adding it shrinks the gap.
- H1c Household income: growth in real per-capita disposable income is positive, and its divergence from GDP growth explains part of the gap.
- H1d Salient prices: gasoline prices remain negative after controlling for overall inflation.
- H2a Media-side negativity asymmetry: tone reacts more to bad news than to good news of the same size.
- H2b Incremental forecasting: national tone in month t−1 improves out-of-sample forecasts over M1, and over M1 plus household and political controls.
- H2c Temporal ordering: tone leads sentiment, and "excess tone" with the fundamentals component removed still has predictive power; the reverse relationship is weaker.
- H2d Recall pathway: tone predicts the share of respondents who "heard unfavorable news", which in turn predicts sentiment, with topics matching one to one (price coverage corresponds to price news heard).
- H3a Survey mode: after the switch to web interviews in April–July 2024, the gap (especially the ICC gap) shows a discrete jump.
- H3b Partisanship: the 2025–2026 gap is concentrated among Democrats and independents, and partisan indices jump at changes of the governing party while fundamentals do not change.
- H3c Model: the size of the gap is highly sensitive to the estimation window and specification, especially extrapolation to high inflation.

**RQ4 prior assessment of mechanism measurability**

| Mechanism | What this project can measure | What gets only compatible evidence or cannot be measured |
| --- | --- | --- |
| Negativity bias | Media-side tone asymmetry between good and bad news; asymmetry of sentiment between improving and worsening fundamentals (aggregate level) | Individual information processing |
| Availability bias | Explanatory power of gasoline and food prices beyond overall inflation; correspondence between the share of price coverage and "price news heard" | Specific instances in personal memory |
| Anchoring on past prices | Competing regressions of 36-month cumulative inflation versus 12-month inflation; share of respondents citing "high prices" as the reason they are worse off financially or that it is a bad time to buy | Personal reference prices |
| Confirmation bias | Not identifiable; only compatible evidence: jumps in partisan indices at changes of administration | Requires individual-level belief, exposure, and experimental data; written into the experiment proposal |

## Data and variables

All variables come from the existing handoff files; only one derived variable (36-month cumulative PCE inflation) and two longer estimation windows are added. The main analysis is monthly, 2010-01 to 2026-10, 202 months in total; the monitoring window is 2026-01 to 2026-10.

| Role | Variable (file · column) | Coverage | Notes |
| --- | --- | --- | --- |
| Dependent variable | `econ_monthly_realtime.csv` · `ics`, `icc`, `ice` | 2010-01–2026-10 | 2026-10 is preliminary; the final is released 2026-10-23 |
| Core economic (M1) | `unrate_rt`, `pce_yoy_rt` (headline PCE), `gdp_qoq_saar_rt` (`gdp_yoy_rt` for robustness), each with `_ref` and `_release_date` | Full period | GDP is a step function of "the latest quarter released before the cutoff", not interpolated |
| Household controls (H1) | New `pce_cum36_rt` (computed from the same PCEPI vintage), `mortgage30_rt`, `rdpi_pc_yoy_rt`, `gas_price_rt`; for robustness add `tdsp_rt`, `u6rate_rt` | Mortgage rate from 2010-07 (backfilled per D-D), real income from 2010-06, U-6 from 2011-04 | `pce_cum_since_2021_01_rt` is empty before 2021, so it cannot enter the 2010–2019 estimation and is descriptive only |
| Political controls | Governing-party dummy (changes in 2017-01, 2021-01, 2025-01); dummy for the 6 months before an election (`political_elections.csv`) | Full period | No public monthly series on partisan composition |
| Measurement and mode (H3) | `mode_web_share`; partisan indices `ics_dem`, `ics_ind`, `ics_rep` (`survey_monthly.csv`) | Partisan indices monthly from 2017-02 to 2026-08; only 18 months in 2010–2016 | Partisan analysis uses only 2017 onward |
| Exposure and recall proxies | `news_f_all`, `news_u_all`, `news_r_all`; unfavorable news categories `newsrn_u_pri_all`, `newsrn_u_emp_all`, etc. | Through 2026-08 | Comparability of open-ended coding before and after the 2024 mode switch is not established |
| Mechanisms and heterogeneity | `pagorn_hp_all` (worse off financially because of high prices), `durrn_hp_all`, `homrn_*`, `vehrn_*`, `px1_*`; ICS/ICC/ICE by income, age, region, and education group | Through 2026-08 | — |
| Main media measures | `media_monthly.csv`, `group = national` | 202 months, 14–37 relevant items per month (median 26) | 2026-01 covers only days 1–7; computed as usual and flagged, not replaced with Guardian; 2026-10 runs only to 10-04 |
| Auxiliary media | `mc_national` (13 months), `local` (2025-03–2026-09, 19 months), `youtube` (from 2023-01, 46 months), Reddit via `media_quarterly.csv` | See left | Used only for recent comparisons and robustness, not in the 2010–2019 estimation |
| External benchmark | `sffed_news_sentiment_monthly.csv` | 202 months | r = 0.37 with our own tone (0.44 for 3-month averages) |
| Events and releases | `provenance/events.csv` (158 entries: FOMC 138, shutdowns, tariffs, bank failures, pandemic), `release_calendar.csv` | Full period | Used for common-shock controls and the dashboard timeline |
| Item level | `labels/ai_corpus_labels.csv` (11,431 items with weights), `corpus/items.parquet` (167,418 items) | — | The latter is used for the full-corpus dictionary index and factual calibration |

**Media measures are used in three tiers according to the AI validation results** (κ between the test set and the gold standard):

- Main measures: tone `net_tone` (0.73), plus volume (0.86) and price framing (0.83), which depend on the relevance judgment.
- Secondary measures (conclusions must note measurement error): factual good/bad `net_fact` (0.57), perspective `household_share` (0.63), actor and attribution `blame_admin_share` (0.67 / 0.56), and topic shares.
- Descriptive only: emotional intensity (0.56), time frame `forecast_share` (0.59), concept error rate (0.47).

The 23 items in the main coding with relevant = unsure do not enter any content measure; only their count is reported.

## Model 1: Economics-only benchmark and the sentiment gap (RQ3, H1, H3)

M1 uses only real-time U-3, headline PCE year-over-year inflation, and annualized quarter-over-quarter GDP growth, is estimated on 2010–2019, and makes out-of-sample forecasts from 2020-01 onward; the gap is the actual value minus the forecast, and a negative gap means only "pessimism the model cannot explain".

```latex
\mathrm{ICS}_t = \alpha + \beta_1 U^{rt}_t + \beta_2 \pi^{rt}_t + \beta_3 g^{rt}_t + \varepsilon_t, \qquad \mathrm{gap}_t = \mathrm{ICS}_t - \widehat{\mathrm{ICS}}_t
```

**Specification**

- No lagged dependent variable and no time trend, otherwise the gap would be absorbed. Seasonal dummies are first jointly tested in the estimation period and added only if significant.
- Standard errors are Newey–West (12 lags). ICS, ICC, and ICE are each estimated once.
- Both kinds of prediction interval are reported: the analytic interval (HAC parameter variance plus residual variance), and a moving-block bootstrap of estimation-period residuals (block length 12 months, 2,000 replications), giving 80% and 95% intervals.

**Estimation windows (corresponding to decision D-A)**

| Window | Real-time status | Role |
| --- | --- | --- |
| 2010-01–2019-12 (main) | Fully real-time | Starting point suggested in the PDF; the already-decided D3 |
| 2000-09–2019-12 | Fully real-time: UNRATE vintages from 1960, PCEPI from 2000-08, GDPC1 from 1991-12 | Adds the 2008 inflation peak and the financial crisis |
| 1978-01–2019-12 | Quasi-real-time: PCE before 2000 uses the earliest vintage (2000-08), GDP uses Philadelphia Fed real-time data (already in `data/raw/M17`); vintages before 1992 are real GNP, which must be noted | The only window containing inflation above 6%, used to test whether the main gap comes from extrapolation |
| Expanding-window recursive | Fully real-time | Robustness for guideline D3; it gradually absorbs the gap, so it serves only as a comparison |

**Reporting conventions for RQ3**

- Estimation-period R², out-of-sample RMSE, and out-of-sample R².
- Explained share: for period P, using average 2019 sentiment as the reference, S = 1 − mean gap ÷ mean (ICS − 2019 mean). The periods are 2021-07–2022-12, 2023–2024, 2025, and 2026-01–2026-10.
- Contribution decomposition: each indicator's contribution is β × (current value − 2019 mean).
- Results for the four windows are shown side by side, and the explained share is reported as a range.

**H1 test (M1 plus household controls)**: first add 36-month cumulative inflation, the mortgage rate, real per-capita disposable income growth, and gasoline prices one at a time, then add all four at once; the criteria are the change in the mean gap since 2021 and the out-of-sample RMSE. Debt-service burden and U-6 are added only in robustness checks. EPU is itself built from newspaper text, so it is classed as a media robustness check, not an H1 control.

**H3 tests**

1. Survey mode: on the 2023-01–2025-12 gap series, regress on a step dummy starting 2024-07 and the web-interview share, separately for ICC and ICE; also run a version excluding 2024-04–06.
2. Partisanship: from 2017, the change in each partisan index relative to its own 2017-02–2019-12 mean, focusing on the jumps at 2021-01 and 2025-01.
3. Sensitivity range for partisan composition: ICS is a linear weighting of the groups, so if the Republican share falls by Δs, the total index is affected by Δs × (ICS\_Rep − ICS\_others). Δs takes values of 2, 4, and 6 percentage points; the range of effects on the gap is reported, with a note that the composition itself is not observable.

Identification note: M1 is a reduced-form mapping, not a structural model. The gap can come from omitted variables (H1), measurement changes (H3), changes in the relationship itself, or perception factors (H2); the gap alone cannot distinguish among them.

## Model 2: Economic indicators plus media measures (RQ5, associational evidence for RQ2)

M2 adds the single primary media variable to M1: national news net tone in month t−1. It answers "does media add incremental predictive power", not "does media cause changes in sentiment".

```latex
\mathrm{ICS}_t = \alpha + \beta' X^{rt}_t + \gamma\, \mathrm{Tone}_{t-1} + [\rho\, \mathrm{ICS}_{t-1}] + \varepsilon_t
```

**Timing alignment**: under D2, the forecast origin for month t is the 1st of month t, so only media indices for month t−1 and earlier can be used. Current-month tone is used only in a separately labeled "contemporaneous association" analysis and does not count as forecasting.

**Out-of-sample evaluation**

- Expanding-window recursive one-step forecasts: the first training window is 2010-01–2016-12 (84 months), and the evaluation period is 2017-01–2026-10; also run 3-month-ahead direct forecasts.
- Every model is reported in one version with the same AR(1) term and one without an AR term.
- Metrics: RMSE, MAE, RMSE ratio relative to M1; nested comparisons use the one-sided Clark–West test (HAC), with bootstrap confidence intervals for the errors.
- Reported by period: 2017–2019, 2020–2022, 2023–2024, 2025–2026; reported once with and once without the pandemic months 2020-03–12.

**Secondary media hypotheses** (each added separately, with Benjamini–Hochberg control of the false discovery rate, q = 0.10): `net_fact`, `price_level_share_of_priced`, `household_share`, `topic_prices_rising`, `topic_layoffs_unemployment_up`, `blame_admin_share`; also report a version with the first principal component of these six. Lags of 1–3 months are chosen by BIC within each training window.

**Measurement noise**: the national group has only about 26 relevant items per month, so monthly tone carries considerable sampling error, which is also one candidate reason for its correlation of only 0.37 with the San Francisco Fed index. Treatment:

1. Use a within-cell bootstrap to estimate each month's sampling variance, report the reliability ratio (signal variance ÷ observed variance), and use it to state the direction of attenuation in γ.
2. Pre-register three alternative media measures: a 3-month moving average; the San Francisco Fed index (external, large sample); a full-corpus dictionary index (a by-product of R3.5).

**Excess tone**: within each training window, regress tone on real-time fundamentals and take the residual as "excess tone", then put it into M2. If raw tone has predictive power but excess tone does not, media is only another reading of the fundamentals.

## Model 3: Adding household and political controls (joint test of H1 and H2)

M3 = M2 + household controls + political controls. The key comparison is not M3 against M1 but M3 against "M3 without media" (denoted M1c): only this comparison can answer "after controlling for real pressures, does media still add anything".

```latex
\mathrm{ICS}_t = \alpha + \beta' X^{rt}_t + \delta' H^{rt}_t + \theta' P_t + \gamma\, \mathrm{Tone}_{t-1} + [\rho\, \mathrm{ICS}_{t-1}] + \varepsilon_t
```

- H (household): 36-month cumulative PCE inflation, the mortgage rate, real per-capita disposable income growth, and gasoline prices, exactly the same as in the H1 test of M1.
- P (political): governing-party dummy, dummy for the 6 months before an election. Partisan group indices are available monthly only from 2017 onward, so they do not enter M3 and are placed in stages 4–5.

| Comparison | What it tests |
| --- | --- |
| M1 vs. M1c | Predictive power of the household and political controls themselves (H1, H3) |
| M1 vs. M2 | Increment from media alone (first part of H2b) |
| M1c vs. M3 | Increment from media after controlling for real pressures and political factors (main test of H2b) |

**Coefficient stability**: 60-month rolling-window coefficient plots; break tests at the known dates 2020-03, 2024-07, and 2025-01.

**Degrees of freedom and collinearity**: the first training window has 84 months and M3 has about 10 regressors, which can be estimated but leaves little room; variance inflation factors are reported. The mortgage rate moved within a narrow range in 2010–2019, so for its coefficient the long-window results are the main reference. No variable selection or regularization is done; the variable set is fixed here.

**Magnitude conversion**: multiply M3's γ by the deviation of tone from its 2019 mean to get "the share of the gap associated with media tone", reported only as an upper bound on the association and not called a causal effect of media.

## Causal inference: observational analysis, design proposal, and falsification list (RQ2, RQ6)

We adopt "observational analysis + causal design proposal" (D5). The observational part can provide only evidence on temporal ordering and conditional correlation; reports are always worded as "associated with" or "leads", never "causes".

**Observational analysis (stage 4)**

1. Two-way local projections (0–6 months): use month t−1 tone to predict future changes in sentiment, controlling for real-time fundamentals, lagged sentiment, and lagged tone; in reverse, use month t−1 sentiment to predict future tone. Only a significant forward direction alone is compatible with "media leads"; significance in both directions indicates feedback or audience demand; significance only in the reverse direction does not support the media explanation.
2. Common shocks: add data surprises (the actual released value minus the previous released value, because there is no free source of professional consensus forecasts) and dummies for shutdowns, tariffs, the pandemic, and bank failures from `events.csv`; and test whether excess tone still has predictive power.
3. Recall pathway: tone's prediction of the share who "heard unfavorable news", the latter's prediction of sentiment, and topic correspondence: the share of price coverage corresponds to unfavorable price news heard, and the share of layoff coverage corresponds to unfavorable employment news heard. This is the project's only evidence on the exposure side, and it is still correlational.
4. Partisan heterogeneity (from 2017-02, about 115 months): New York Times readers lean Democratic, so if tone works through exposure, its association with the Democratic index should be stronger; this is compatible evidence only.

**Causal design proposal (written into the report appendix, not implemented)**

- Randomized framing experiment: the same set of real data presented in five truthful wordings (balanced summary, price level, inflation rate, household perspective, national aggregate); outcome variables are the five Michigan questions and one-year inflation expectations; with d = 0.2, α = 0.05, and power 0.8, pairwise comparisons need about 394 people per group; pre-registered, with informed consent, and subject to IRB approval.
- Quasi-experimental ideas: changes in local coverage caused by local newspaper closures or Sinclair acquisitions; this needs state-level sentiment microdata (public tables have only the four census regions), and must spell out treatment assignment, pre-trends, and spillovers.
- From sample effects to the national index (R4.6): national effect ≈ exposure share × per-exposure effect × share still retained at the time of the interview; this needs population-level exposure estimates, representative sampling or CPS weighting, and an assumption that effects transfer.

**Falsification list (RQ6, pre-registered, adjudicated one by one after analysis)**

| # | Falsification criterion | Operational decision rule |
| --- | --- | --- |
| 1 | Media tone can be explained by fundamentals | After regressing tone on fundamentals, the mean residual since 2021 is not significantly different from 0 |
| 2 | No out-of-sample increment | The Clark–West test of M1c vs. M3 is not significant at the 5% level |
| 3 | Sentiment leads media | In the local projections, the reverse response is significant and the forward response is not |
| 4 | Real pressures explain the gap | After adding household controls, the mean gap since 2021 shrinks by more than half and falls within the 95% prediction interval |
| 5 | The gap comes from measurement or partisanship | The mode jump or the partisan sensitivity range can cover more than half of the mean 2025–2026 gap |
| 6 | Recall follows the economy rather than media | Fundamentals explain "heard unfavorable news" better than tone does |
| 7 | No differences across groups | Groups with different media use (partisanship, age) have the same gap pattern |
| 8 | The measurement itself is unstable | The excess flip rate under name or source swaps is significantly greater than 0, or the three tone measures give opposite conclusions |

The "half" in items 4 and 5 is a reporting threshold fixed in advance; the actual numbers are always reported as they are.

## Robustness checks

Each item recomputes the M1 gap and the γ and Clark–West statistics of M2 and M3, and all results are collected into one specification curve plot; every specification run (including unfavorable results) is registered in `results/spec_registry.csv`.

| Dimension | Main specification | Alternative specifications |
| --- | --- | --- |
| Dependent variable | ICS | ICC, ICE |
| Information cutoff | 1st of month t (D2) | Michigan preliminary release date (`econ_monthly_realtime_prelim_cutoff.csv`) |
| Gap estimation window | Fixed 2010–2019 | 2000-09–2019; 1978–2019; expanding window |
| GDP | Annualized quarter-over-quarter | Year-over-year |
| Form | Levels | First differences (ADF and KPSS reported first) |
| Pandemic | Included | Exclude 2020-03–12 |
| Survey mode | No treatment | Web-interview dummy; exclude 2024-04–06 |
| Media measure | National `net_tone`, t−1 | 3-month average; `net_fact`; `share_negative`; San Francisco Fed index; full-corpus dictionary index; EPU |
| Media sources | NYT + Guardian | NYT only (Guardian is not U.S.-based); exclude the two incomplete months 2026-01 and 2026-10 |
| Lag | 1 month | BIC selection among 1–3 months |
| Inference | HAC 12 lags | HAC 6 and 18 lags; moving-block bootstrap |
| Seasonality | Depends on the estimation-period test | Monthly dummies forced in |

Social platforms and local news do not enter the table above and get a separate recent comparison: differences in tone and framing between YouTube (from 2023-01) and national news in overlapping months, and their descriptive association with the gap; Reddit uses quarterly data (from 2015); local versus national news in 2025-03–2026-09. All conclusions are restricted to the respective periods and samples.

## Measurement validation and bias benchmarks (RQ1; including R3.5, R3.7, factual calibration)

R3.5 and R3.7 are both placed in stage 2 and must be finished before models 2 and 3, because they determine whether the media measures can serve as credible explanatory variables. R3.7 needs you to run Codex once and can run in parallel with stage 1.

**R3.5 Dictionary methods and traditional classifiers**

- Item level: on the same 260-item human test set, compare the LLM, dictionary methods (tone), keyword rules (topics and price framing), and TF-IDF plus logistic regression. Dictionary thresholds are set only on the development set. When the classifier is trained on LLM labels, items overlapping the gold standard are removed. Report per-class precision, recall, and F1, macro-average F1, and κ with the gold standard, grouped by source, with bootstrap confidence intervals. The 32 items with relevance = unsure follow the already-decided convention.
- Index level: use the classifier for relevance filtering and the dictionary for tone to build a monthly index from all keyword-matched NYT and Guardian items in `items.parquet`, and compare it with the LLM index and the San Francisco Fed index. The trade-off here: the LLM is accurate per item but has only about 26 items per month, while the dictionary is crude per item but has several hundred items per month.

**R3.7 Name and source-label swap test**

- Sample: take about 120 texts mentioning a president or a party from the test set and the main coding sample, stratified by the entity mentioned.
- Five versions: the original text twice (the first is the label already in the main coding, the second a new run); swapped names and parties (Trump and Biden, Obama and Trump, Republicans and Democrats, with pronouns changed accordingly); "Source: Fox News" prepended to the text; "Source: MSNBC" prepended to the text. Each version goes in a different batch, with shuffled IDs and isolated context, and the prompt and model are exactly the same as in the main coding.
- Metrics: excess flip rate = share of swapped versions that differ from the original − share differing between the two original runs, reported by dimension with bootstrap intervals; the directional test checks whether tone scores shift in the same direction when Trump is replaced with Biden and under the reverse swap.
- If the excess flip in tone or attribution is significant, it is written into the report as an AI measurement bias and counted toward item 8 of the falsification list.

**Factual calibration (the fourth measurement dimension)**: use rules to extract the indicator, value, and observation period from `claim_text`, and compare them with the ALFRED vintage in effect on the publication date. Rates have a tolerance of ±0.1 percentage points; outcomes are classified as correct, correct within rounding, incorrect, or unverifiable. Which indicators are covered depends on D-C. You spot-check 30 extraction results to confirm the parsing is correct. The concept error rate (κ 0.47) is descriptive only.

**Bias benchmark for each dimension (R3.3)**

| Dimension | Benchmark | Test |
| --- | --- | --- |
| Tone (negativity bias) | Good and bad news of equal size | Regress tone separately on the positive and negative parts of changes in unemployment, inflation, and GDP, and test whether the coefficients are equal in absolute value |
| Selection and salience | The size of actual economic changes | Whether the elasticity of the rising-prices topic to rising inflation is symmetric with the elasticity of the easing-inflation topic to falling inflation; likewise for layoff and hiring topics |
| Framing | The inflation path | After inflation eases, whether the share of price-level wording stays high; changes in the share of household perspective |
| Factual calibration | The official vintage public at the time of publication | Error rate by period and source |
| Political attribution | Similar economic conditions under different administrations | Regress the share blaming the administration on fundamentals and four administration dummies; criticism by itself is not bias |
| Cross-source | Different sources in the same period | Differences among national, local, YouTube, and Reddit in overlapping periods; these show only differences in supply and are not called bias |

In addition, estimate the reliability of the monthly index and explain the 0.37 correlation with the San Francisco Fed index: sampling noise, the difference between headline-plus-abstract and full text, and different topic scope. Each of the three reasons gets one testable comparison: a 3-month average, the Guardian full-text subsample, and items on macro topics only.

## Execution order and locking results

There are six stages in total, with the stage 2 Codex run in parallel with stage 1; results are locked at the end of each stage before the next one begins. Code goes in `src/analysis/`, results in `results/stage<N>_*/`, and everything is included in `run_all.sh` for one-command rebuilding.

0. **Finalization and pre-registration**: after you confirm D-A through D-F, this design is written into `DECISIONS.md`. From then on, any new or modified specification is recorded as a deviation.
1. **Economic baseline (RQ3, H1, H3)**: extend `econ_realtime.py` (adding 36-month cumulative inflation, the D-D backfill, and the two long windows); estimate M1, the gap and prediction intervals, explained shares and contribution decomposition, and the H1 and H3 tests.
2. **Measurement validation and bias benchmarks (RQ1)**: generate the R3.7 run package and hand it to you; R3.5 item-level and index-level comparisons; factual calibration; five-dimension benchmark tests; index reliability; compute the R3.7 metrics once the Codex output is received.
3. **Forecast comparison (RQ5)**: recursive forecasts for M1, M1c, M2, and M3, Clark–West, false-discovery-rate correction for the secondary hypotheses, coefficient stability, specification curve.
4. **Temporal ordering and causality (RQ2, RQ6)**: two-way local projections, common shocks, recall pathway, partisan heterogeneity; adjudicating the falsification list item by item; drafting the causal design proposal.
5. **Mechanisms, heterogeneity, and methods (RQ4, R5.2–R5.4)**: the three-way mechanism classification table; gaps by income, age, region, and partisan group; survey-mode comparability; comparison with the same pre-election period of the 2010, 2014, 2018, and 2022 midterms; recent comparison of social and local media.
6. **Freezing results**: one `FINDINGS.md` per stage, with findings and hypotheses written separately and each conclusion citing its table or figure number; locked together with `spec_registry.csv` and the script SHA256 hashes. The dashboard and report are done after that.

**Data cutoff**: this round of research uses 2026-10-16 as the cutoff (the Michigan October value is preliminary). Before the report, the October final value (10-23) and the preliminary Q3 GDP estimate may be added; the November preliminary value is released after Election Day (11-03) and goes into the plan for later updates.
