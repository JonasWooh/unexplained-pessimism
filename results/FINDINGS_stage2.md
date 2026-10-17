# Stage 2 results: measurement validation and bias benchmarks (RQ1; R3.3, R3.5, R3.7, factual calibration)

Frozen 2026-10-16. The design is in `research/RESEARCH_DESIGN_v1.md`, implementation details and deviations are in the 2026-10-16T19:23Z entry of `DECISIONS.md`, and all specifications are registered in `results/spec_registry.csv` (from S066). Scripts are in `src/analysis/`; rerun everything with `sh src/analysis/run_stage2.sh`.

Findings come first, then the adjudication of the hypotheses. All intervals are 95% bootstrap intervals. "National news" means NYT + Guardian, the source of the main media measures.

## 1. Findings

**F1. At the item level, LLM coding is clearly better than every low-cost method; the dictionary method's tone judgments are barely usable, and only on national news.**
On the 260-item human test set, tone and price framing use group A (items that both the gold standard and the LLM judge relevant, 174 items), and relevance uses the 236 items with gold-standard yes/no (`stage2_r35/item_metrics.csv`).

| Dimension | LLM | Loughran–McDonald | VADER | Keyword rules | TF-IDF (trained on LLM labels) | TF-IDF (trained on the 100-item human development set) |
| --- | --- | --- | --- | --- | --- | --- |
| Relevance κ | 0.86 [0.79, 0.93] | — | — | 0 (all judged relevant) | 0.75 [0.64, 0.83] | 0.41 |
| Tone κ | 0.73 [0.63, 0.81] | 0.35 [0.23, 0.46] | 0.27 [0.18, 0.35] | — | 0.39 [0.28, 0.50] | 0.14 |
| Price framing κ | 0.83 [0.75, 0.90] | — | — | 0.48 | 0.64 | 0.39 |
| Mean κ over 13 topics | 0.79 | — | — | 0.58 | 0.69 | 0.23 |

- For the paired difference in macro-average F1 between the LLM and each method, no bootstrap interval contains 0. For example, LLM − LM on tone is 0.30 [0.18, 0.40], and LLM − TF-IDF on relevance is 0.06 [0.01, 0.11].
- LM tone κ by source group: national news 0.51, local news 0.19, social platforms 0.10. VADER is below 0.33 in all three groups.
- Keyword rules almost fail on the two topics most central to the inflation narrative: rising prices κ 0.10, easing inflation −0.01. TF-IDF gets 0.72 and 0.41, and the LLM 0.79 and 0.79 (`item_metrics.csv`, group A).
- The classifier trained only on the 100 human labels is the worst on every dimension, showing that small-scale human annotation is not enough to train a substitute coder.
- Dictionary thresholds were set only on the development set: LM cutoff 0.0, development-set macro F1 0.44; VADER compound-score cutoff 0.15, mixed-judgment cutoff 0.10, macro F1 0.43 (`dictionary_thresholds.json`).
- Group B is the 186 items the gold standard judges relevant, with items the LLM judges not relevant counted as errors. LLM tone κ drops to 0.66 [0.56, 0.74] and price framing to 0.74 [0.65, 0.82], still higher than every other method: LM 0.36, VADER 0.26, TF-IDF 0.40 and 0.66 (`item_metrics.csv`).

**F2. At the index level, with the same sample size the dictionary method correlates with the San Francisco Fed index as strongly as the LLM does; expanding the sample to the full frame raises the correlation clearly.**
The full frame is 42,472 NYT and Guardian units, of which 26,758 are judged relevant by TF-IDF, a median of 120 per month. Items in the training set are predicted with 5-fold cross-fitting (`stage2_dictindex/info.json`).

| Correlation with the San Francisco Fed index | Monthly level | 3-month average | First difference |
| --- | --- | --- | --- |
| LLM index (about 26 items per month) | 0.37 | 0.44 | 0.18 |
| LM dictionary, only the same units sampled for the LLM | 0.37 | 0.57 | 0.12 |
| LM dictionary, full frame | 0.54 | 0.67 | 0.23 |
| VADER, full frame | 0.50 | 0.60 | 0.23 |

- The correlation between the full-frame dictionary index and the LLM index is 0.42 (0.46 for 3-month averages).
- On the same units, the two methods correlate equally with the external index, showing that the main reason for the LLM index's low correlation is the small number of items per month, not the coding method.
- First-difference correlations are low in all combinations (0.12–0.25); the shared component is mainly the slow-moving part.
- The full-frame dictionary index (`features/media_dict_monthly.csv`) serves, by design, as an alternative media measure in stage 3.

**F3. The monthly reliability of the national LLM tone index is about 0.62, and about 0.78 for 3-month averages; the low correlation with the San Francisco Fed index can be explained mainly by sampling noise, and the other two candidate reasons are not supported.**
A within-cell bootstrap (2,000 replications) on the 40 coding units per month, with a finite-population correction (`stage2_reliability/reliability.csv`):

- The monthly sampling standard deviation is 0.12, against a standard deviation of 0.20 for the index itself.
- Reliability is 0.62 (0.50 without the finite-population correction); for 3-month averages it is 0.78 (0.72). `net_fact` is similar, at 0.63.
- Under classical measurement error, the tone coefficient in M2 is attenuated toward 0 by a factor of about 0.62. This is the reason stage 3 pre-registers two alternative measures, the 3-month average and the full-frame dictionary.
- After correcting for attenuation, the correlation with the San Francisco Fed index is 0.47 (0.50 for 3-month averages). This assumes the external index has no measurement error, so it is an upper-bound-type correction.

Three pre-registered comparisons (`stage2_reliability/sffed_checks.csv`):

1. Sampling noise: the 3-month average raises the correlation from 0.37 to 0.44, and the full-frame dictionary reaches 0.54. **Supported.**
2. Headline plus abstract versus full text: using Guardian only (about 17 items per month), the LM dictionary correlates at 0.34 on coding-unit text and 0.25 on full text. Full text does not raise the correlation. **Not supported.** The Guardian is a British outlet with few items, so this test has limited power.
3. Topic scope: using only items on macro topics (T01–T06), the LLM index correlates at 0.34 and the full-frame dictionary at 0.43, neither higher than with all items. **Not supported.**

A gap remains after removing sampling noise; a reasonable explanation is the difference in construction: the San Francisco Fed index uses a dictionary to score all economics articles from 24 newspapers, while this project uses keyword screening of NYT and Guardian. This is only an inference and was not tested separately.

**F4. Among numeric claims that name the indicator, the national news error rate is about 3% (2 of 68), and social platforms have no errors among 9. Extreme inflation figures on social platforms never name the indicator and are uncheckable under the rules; but they match no official measure.**
Rules extract the indicator, value, and observation period from `claim_text`, and these are compared with the ALFRED vintage in effect on the publication date (`stage2_factcal/claims.csv`, `summary.csv`).

- Of 3,569 claim fragments, 103 fall within the four indicators. Most of the rest cite stock indexes, commodity prices, wages, or state or local data, or are forecasts, and are excluded under the pre-set rules (`fragment_status.csv`).
- **Manual spot check**: you checked 30 parsing results (`review_sample_30.csv`): 26 correct, 4 wrong. Following your comments, three rules were revised and all 103 were rerun:
  - A figure that says only "inflation" without naming CPI or PCE is no longer assigned a series by closeness of value, and is reclassified as uncheckable (K01583, K00987).
  - Comparison-period months such as "compared to March" are no longer treated as the reference month (K07821; the reference month becomes 2023-04, verdict unchanged).
  - Statements without "to", such as "unemployment rate fell 4%", are reclassified as having an unclear measure and as uncheckable (K06427).
  - Once this rule is applied uniformly, the three national news items you had judged correct ("US inflation falls to 2.1%", "cools to 3.2%", "rose to 3.7% in September") also do not name the indicator and are likewise changed to uncheckable. Otherwise K00987 and K00058, which are the same kind of case, would be treated differently.
  - After the revision, 23 verdicts changed in total: 15 from correct to uncheckable, and 8 from incorrect to uncheckable (`claims.csv` gains an `unverifiable_reason` column).
- **National news**: among the 68 checkable claims that name the indicator, 2 are incorrect (2.9%); using the ±0.2 sensitivity tolerance for 12-month CPI changes gives the same result.
  - One is the Guardian on 2026-07-14 writing that June CPI fell −0.8% month over month, when the seasonally adjusted value was −0.42%.
  - One, on 2020-08-18, writes an unemployment rate of 11%, when the latest value at the time was 10.2% (July).
  - The two "inflation of 9.1% in June 2022" items previously judged incorrect do not name the indicator and are now uncheckable. The official not-seasonally-adjusted CPI value is exactly 9.1%, and the seasonally adjusted value is 8.9–9.0%.
  - By period: 2010–2019 0/29, 2020–2022 1/14, 2023–2024 0/14, 2025–2026 1/11. The samples are too small to test for a trend.
- **Social platforms**: all 9 checkable claims are correct. In addition, 13 inflation figures do not name the indicator, 1 unemployment statement has an unclear measure, and 2 GDP growth figures lack a measure.
- **Inflation figures that do not name the indicator** (`unnamed_inflation.csv`, descriptive only, not counted in the error rate): each is compared against the 12-month and 1-month changes in CPI and PCE, and counts as matching if any one measure matches (±0.2 for 12-month CPI changes, for the same reason as above).
  - All 9 national news items match at least one measure.
  - Of the 13 social platform items, 6 match no measure. Of these, 4 are exaggerated claims of 15%–50% ("50 percent inflation", "18% inflation", "inflation is like 15% easy", "more than 20%"), and 2 are close but do not match (2.9% vs. 2.7%, "2.5% in January 2025").
  - If this looser measure is counted, national news has 2 errors in 77 (2.6%), and social platforms 6 errors in 22 (27%).
- Conclusion: national news cites official figures mostly accurately. The problem on social platforms is mainly not citing the wrong series, but giving figures far from any official measure with no source stated. The sample is very small (25 social items), so this is descriptive only.

**F5. Name and source-label swaps detected no AI coding bias.**
120 items mentioning a president or a party, 5 versions each (`stage2_r37/`). All 480 new codings were returned, with no invalid values, and all 3,551 evidence excerpts can be found verbatim (`qa.json`).

- Excess flip rate = share of swapped versions whose label differs from the first original label − share of second original runs that differ from the first. Flip rates between the two original runs: tone 18%, blaming the administration 26%, factual good/bad 30% (`flip_rates.csv`).

| Dimension | Swapped names and parties | Labeled Fox News | Labeled MSNBC |
| --- | --- | --- | --- |
| Tone | +4.2 [−2.5, +11.7] | −1.7 [−7.5, +4.2] | +0.8 [−5.8, +7.5] |
| Blaming the administration | +0.8 [−5.9, +8.3] | −8.3 [−16.7, 0.0] | −0.8 [−8.3, +6.7] |
| Emotional intensity | +6.7 [−0.8, +14.2] | +1.7 | +5.8 [−1.7, +14.2] |

(Units: percentage points.) Of the 39 excess flip rates across 13 dimensions and 3 versions, none is significantly greater than 0.

- Directional test (`directional.csv`):
  - The change in tone is −0.08 when Trump is replaced with Biden and 0.00 when Biden is replaced with Trump; the difference between the two is −0.08 [−0.32, +0.16].
  - The corresponding difference for blaming the administration is +0.15 [−0.03, +0.35]. The direction of the point estimate is that when the main figure in the text becomes Trump, the share of items the coder codes as blaming the administration falls slightly rather than rising.
  - The tone difference between the Fox and MSNBC versions is −0.02 [−0.10, +0.07].
- Each swap direction has only 25–40 items, so only fairly large biases can be ruled out. The accurate statement is "not detected".

**F6. Bias benchmarks: neither negativity asymmetry nor "still emphasizing the price level after inflation eased" receives robust support; the share blaming the administration changes greatly with changes of administration; NYT and Guardian are more negative than other news sources.**
National news monthly measures, 2010-01 to 2026-09, 201 months; "news of the month" = the real-time value at cutoff t+1 − the real-time value at cutoff t (`stage2_bias/`).

1. **Tone asymmetry** (`tone_asymmetry.csv`): in the main specification, the coefficient on rising unemployment is −0.026 (p = 0.002), and on falling unemployment −0.054 (sign opposite to expectations, p = 0.48); neither inflation part is significant. The coefficients on good and bad GDP news are both negative, which is caused by the large swings in GDP in 2020. The joint test of the three "bad + good = 0" restrictions has p < 0.001, but it is driven by exactly this pair of opposite-signed GDP coefficients. The conclusions differ across variants:
   - Adding lagged tone: p = 0.20.
   - Excluding 2020-03 to 12: p = 0.015, but driven by the coefficient on falling unemployment, +0.35, which is a positivity asymmetry.
   - Using 3-month changes: p = 0.08.
   Monthly tone mainly follows the level of the economy and the period, not the month-by-month news from releases.
2. **Selection and salience** (`topic_selection.csv`):
   - For each 1 percentage point rise in inflation, the share of the rising-prices topic increases by 0.13 (p = 0.08); for each 1 percentage point fall, the easing-inflation topic increases by 0.12 (p = 0.008). The difference is 0.02 [−0.17, +0.26].
   - For each 1 percentage point rise in unemployment, the layoffs topic increases by 0.029 (p < 0.001); when unemployment falls, the hiring topic increases by only 0.007 (p = 0.76). The difference, 0.02 [−0.16, +0.17], is not significant.
   - Results with 3-month changes are the same.
3. **Framing** (`framing.csv`, `framing_periods.csv`): real-time PCE inflation peaked in 2022-07.
   - Among items with a price frame, the share of "price level" wording is 0.76 in 2010–2019, 0.68 before the peak, and 0.60 after the peak. Controlling for the level of inflation, the post-peak coefficient is −0.09 (p = 0.035); controlling for 36-month cumulative inflation, it is not significant.
   - After inflation eased, the price topic itself was still more frequent: the share of items with a price frame rose from 0.25 to 0.47, with a post-peak coefficient of +0.09 (p = 0.06).
   - The share of household perspective shows no significant change.
   - So the issue with national news is not "still emphasizing the price level" but that the weight of price coverage stays high.
4. **Factual calibration**: see F4.
5. **Political attribution** (`attribution.csv`, `attribution_means.csv`):
   - Share of items blaming the administration: Obama period 0.03, Trump first term 0.19, Biden 0.06, Trump second term 0.40.
   - Controlling for unemployment, inflation, and GDP, relative to the Obama period: Trump first term +0.14 (p < 0.001), Biden +0.02 (p = 0.68), Trump second term +0.35 (p < 0.001). The Wald test that the four administrations are equal has p < 0.001.
   - The share crediting the administration is below 0.07 in all periods.
   - This cannot be directly called bias: tariffs and similar measures are direct presidential decisions, and criticism aimed at the administration may be accurate. Together with F5, this difference is not caused by the coder seeing Trump's name.
6. **Cross-source comparison** (`cross_source.csv`, each group compared with national news in the same months):
   - **Local news** (2025-03 to 2026-09): net tone −0.27 versus national −0.63, a difference of +0.37 [+0.30, +0.44]. Blaming the administration 0.14, versus national 0.40.
   - **Media Cloud national group** (13 months): also less negative than NYT and Guardian (+0.17 [+0.06, +0.28]), and less blame of the administration (−0.22).
   - **YouTube comments** (from 2023-01): more negative (−0.19 [−0.24, −0.13]), with 0.14 more household perspective, 0.12 more price-level wording, and 0.18 more of the rising-prices topic.
   - **Reddit** (quarterly): tone close to national news; more household perspective and price framing, and less blame of the administration. Design weights for Reddit items vary greatly and the bootstrap distribution is skewed, so the differences for this group are for reference only.
   - These differences show only that different sources supply different content and are not called bias. But they imply that in 2025–2026 the main measure built from NYT and Guardian is very likely more negative than U.S. news as a whole.

## 2. Adjudication of hypotheses and premises

| Item | Verdict | Basis |
| --- | --- | --- |
| RQ1 premise: AI measurement can serve as an explanatory variable | Supported, but monthly noise is large | F1: the LLM beats the benchmarks on every dimension; F3: monthly reliability 0.62, so stage 3 must report the 3-month average and full-frame dictionary versions |
| H2a Media-side negativity asymmetry | Not supported (no robust evidence) | F6-1: the conclusion flips with the specification, and significance in the main specification comes from opposite-signed GDP coefficients |
| Selection asymmetry (R3.3) | Not supported | F6-2: the interval for the slope difference between the rising and easing topics contains 0 |
| Price-level framing after inflation eased (R3.3) | Not supported; the weight of price coverage stays high | F6-3 |
| Political attribution changes with the administration (R3.3) | A difference exists but cannot be identified as bias | F6-5; F5 rules out a coder reaction to names |
| Cross-source differences | The main measure is more negative than other news sources | F6-6 |
| Falsification list item 8 (unstable measurement) | The name and source swap part is not triggered; "the three tone measures give opposite conclusions" awaits adjudication in stage 3 | F5; F2 |
| Three candidate reasons for the 0.37 correlation | Sampling noise supported; full text and topic scope not supported | F3 |

## 3. Limitations

- The factual calibration sample is small: 68 checkable national news claims that name the indicator, and 9 from social platforms. CPI is checked against the seasonally adjusted series, which differs systematically from the not-seasonally-adjusted figures media cite; this is reported with the ±0.2 sensitivity tolerance. The parsing rules were revised after a manual spot check of 30 items (26/30 correct, the 4 errors fixed), and no second spot check was done after the revision.
- The name-swap test has only 25–40 items per direction, so power is limited; replacing Obama with Trump creates anachronisms. Remaining swap issues are in `labels/r37/r37_swap_review.md`.
- The bias benchmarks are aggregate associations at the monthly level, with about 26 relevant items per month; out-of-sample inference is left to stage 3.
- Local news and the Media Cloud national group cover only some months of 2025–2026, so the cross-source conclusions apply only to those months.
