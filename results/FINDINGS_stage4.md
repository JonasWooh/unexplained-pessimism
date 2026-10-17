# Stage 4 results: temporal ordering, recall pathway, and falsification list (RQ2, RQ6)

Frozen 2026-10-16. Script `src/analysis/stage4_timing.py`; rerun everything with `sh src/analysis/run_stage4.sh`; implementation details are in the 2026-10-16T19:49Z entry of `DECISIONS.md`. The observational analysis can give only temporal ordering and conditional correlation, so everything below is worded as "associated with..." or "leads". The causal design proposal is in `results/CAUSAL_DESIGN_PROPOSAL.md`.

**Specification**
- Row t is survey month t: tone is taken from month t−1; economic variables are the real-time values on the 1st of month t.
- A "data surprise" is the change in the real-time value between cutoffs t−1 and t. There is no free professional consensus forecast, so "the actual released value minus the previous released value" is used instead.
- Event dummies (`provenance/events.csv`): 1 when a shutdown, tariff announcement, or bank failure occurs in month t−1 or month t; the pandemic is 2020-03 to 12.
- In the local projections, sentiment and tone are both standardized to standard-deviation units.
- Agreed before seeing the results: whether a direction is "significant" is decided by a one-sided 5% test of the average response over horizons 0–6; horizon-by-horizon results are reported alongside.

## 1. Findings

**F1. Tone has a brief leading association with sentiment; sentiment also has a lagged association with later tone; the 0–6 average responses in both directions are not significant.**
The main specification controls for real-time fundamentals, data surprises, events, two lags of sentiment, and lagged tone (`stage4_timing/local_projections.csv`).

- **Forward** (month t−1 tone on sentiment in later months): horizons 0, 1, and 2 are 0.061, 0.065, and 0.070 standard deviations (one-sided p of 0.0002, 0.010, and 0.025), returning to near 0 from horizon 3. The 0–6 average is 0.029 (one-sided p = 0.22).
  - The standard deviation of ICS is about 14.9 points, so 0.06 standard deviations is about 0.9 points.
- **Reverse** (month t−1 sentiment on tone in later months): horizons 0–3 are close to 0, horizons 4 and 5 are 0.34 and 0.38 (one-sided p of 0.037 and 0.019), and the 0–6 average is 0.11 (one-sided p = 0.22).
- The pattern is the same when controlling only for fundamentals, or when excluding the 2020 pandemic months.
- Tone's association is short and small, and sentiment's association with tone appears with a lag of several months; both are significant only at some horizons. This looks more like weak two-way feedback than one-way media leadership.

**F2. Since 2021, tone has not been more negative than fundamentals imply; under the pre-selected fitting window, the residual is in fact positive.**
Regressing monthly tone on real-time U, π, g, and the four household variables, fitted on 2010–2019 (`excess_tone_since_2021.csv`):

| Period | Mean residual | p |
| --- | --- | --- |
| 2021-01 to 2026-10 | +0.18 | 0.011 |
| 2021-07 to 2022-12 | +0.13 | 0.007 |
| 2023-01 to 2024-12 | +0.39 | < 0.001 |
| 2025-01 to 2026-10 | −0.01 | 0.45 |

- High inflation in 2021–2024 should have corresponded to more negative coverage, but actual tone was not that negative.
- When fitted on the full 2010–2026 period, the 2025–2026 residual is −0.15 (p < 0.001). This result depends on the fitting window and must be read together with the table above.
- Fundamentals explain very little of monthly tone, with R² of only 0.06 (0.13 for the full-period fit), so this test itself has limited power.

**F3. Recall pathway: tone is associated with the share who "heard unfavorable news", and topics match one to one; but fundamentals explain recall better.**
Survey months 2010-06 to 2026-08 (`recall_unique_r2.csv`, `recall_regressions.csv`):

- Controlling for fundamentals, each 1-unit increase in last month's tone is associated with a 45 percentage point lower share hearing unfavorable news (p = 0.001). The monthly standard deviation of tone is about 0.2, corresponding to about 9 percentage points.
- After adding the share who "heard unfavorable news", tone's coefficient on ICS goes from significant to −1.5 (p = 0.74), while the share itself remains significant (−0.18, p < 0.001). This fits the ordering "tone → news heard → sentiment", but it is still correlational and cannot be taken as identification of a mediation effect.
- Topic correspondence is very clear:
  - The share of rising-prices coverage corresponds to the share hearing unfavorable price news, with a coefficient of 17.2 (p < 0.001); using layoff coverage as a placebo gives a coefficient of −0.5 (p = 0.85).
  - The share of layoff coverage corresponds to hearing unfavorable employment news, with a coefficient of 62.3 (p = 0.031); price coverage as a placebo gives a coefficient of 0.3.
- Unique explanatory power: fundamentals R² 0.21, tone 0.14. Before web interviews, in 2010-06 to 2024-03, the two are 0.28 and 0.13.

**F4. Democrats' sentiment is not more strongly associated with tone than Republicans'.**
2017-02 to 2026-08 (`partisan_gamma.csv`):

- Tone coefficients: Democrats 4.5 (p = 0.14), independents 5.5 (p = 0.005), Republicans 6.8 (p = 0.009).
- Democrats minus Republicans is −2.3 (p = 0.57).
- NYT readers lean Democratic, so if tone works through exposure, the Democratic coefficient should be larger. The results show no such sign, so this exposure channel receives no compatible evidence.

**F5. Gap patterns differ clearly across groups, but the differences come mainly from partisanship and cannot be distinguished from media exposure.**
(`group_gap_differences.csv`)

- By party (relative to each group's own 2017-02 to 2019-12 mean):
  - 2021-07 to 2022-12: Democrats +2.9, Republicans −75.2.
  - 2025-01 to 2026-08: Democrats −38.7, Republicans −29.8, a difference of −8.9 (p = 0.001).
  - The monthly correlation between the two parties' gap paths in 2021–2026 is −0.72.
- By age (each group's own M1 gap):
  - 2021–2022: ages 18–34 −0.2, ages 55 and over −35.2.
  - 2025–2026: −38.8 and −35.5 respectively, a difference of −3.3 (p = 0.033).

## 2. Item-by-item adjudication of the falsification list (RQ6)

Adjudication follows the pre-registered operational rules; "half" is a reporting threshold fixed in advance, and actual numbers are reported as they are.

| # | Falsification criterion | Result | Verdict |
| --- | --- | --- | --- |
| 1 | Media tone can be explained by fundamentals | Residual since 2021 is +0.18 (p = 0.011), significantly different from 0, but in the direction of being more positive than fundamentals imply; −0.01 in 2025–2026 (p = 0.45) | Not triggered under the literal rule. The direction of the deviation is the opposite of "media too negative", and 2025–2026 does not differ from 0, so this likewise does not support the media-bias explanation |
| 2 | No out-of-sample increment | M1c vs. M3, AR main version p = 0.23, none of the 20 variants significant; p = 0.004 without AR | **Triggered** (main version) |
| 3 | Sentiment leads media | 0–6 average: forward p = 0.22, reverse p = 0.22; horizon by horizon, forward is significant at horizons 0–2 and reverse at horizons 4–5 | Not triggered. There is also no evidence of one-way media leadership; the pattern is a weak two-way association |
| 4 | Real pressures explain the gap | Stage 1: adding household variables in the main window barely changes the gap (−27.4 to −27.2), but these variables are not identifiable in the main window | Not triggered (lack of power, see stage 1 F4) |
| 5 | The gap comes from measurement or partisanship | Stage 1: survey mode affects only ICC, by about 5–8 points; partisan composition is no more than 2.7 points, both far less than half the gap | Not triggered |
| 6 | Recall follows the economy rather than media | Unique R² of fundamentals 0.21, tone 0.14 (0.28 and 0.13 before web interviews) | **Triggered**. But tone still has an independent association, and topic correspondence is clear (F3) |
| 7 | No differences across groups | The gaps of partisan and age groups differ significantly in 2025–2026, with large differences in pattern | Not triggered. The differences overlap heavily with partisanship and cannot be attributed to media exposure (F4, F5) |
| 8 | The measurement itself is unstable | None of the 39 excess flip rates in the swap test is significant (stage 2); the three measures, LLM tone, full-frame dictionary, and negative share, have coefficients of the same sign in M3 (stage 3) | Not triggered |

## 3. Synthesis

- Two falsification criteria are triggered: item 2, no out-of-sample increment after controlling for real pressures; and item 6, recall follows economic fundamentals more.
- Items 1 and 3 are not triggered literally, but the direction of the evidence also does not support the media-bias explanation: since 2021 tone has not been more negative than fundamentals imply, and in temporal ordering there is no one-way media leadership.
- The media side still has measurable, directional associations: the short-run positive association, the topic correspondence in recall, and the very high share blaming the administration during the Trump term (stage 2). But none of these is enough to explain the 2025–2026 gap of about 36–40 points; the part associated with tone is at most about 5% (stage 3 F3).
