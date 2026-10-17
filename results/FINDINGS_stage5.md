# Stage 5 results: mechanisms, group heterogeneity, and methodological issues (RQ4, R5.2–R5.4)

Frozen 2026-10-16. Script `src/analysis/stage5_mechanisms.py`; rerun everything with `sh src/analysis/run_stage5.sh`. Implementation details are in the 2026-10-16T19:53Z entry of `DECISIONS.md`, and the specifications are registered as S136–S150.

**Specification**
- Timing conventions are the same as in earlier stages: fundamentals are the real-time values on the 1st of month t, with monthly dummies added and HAC with 12 lags.
- "Pandemic months" means 2020-03 to 2021-06. Stage 1 already explained that M1's errors in this period cannot be interpreted.
- Full-sample regressions (2010–2026, excluding the pandemic months) also use the gap years for estimation, so they show only in-sample associations and cannot be used to explain the gap.

## 1. Findings

**F1. Sentiment shows no robust asymmetry in its response to good and bad economic news.**
The monthly change in sentiment is regressed separately on the bad-news and good-news parts of last month's data releases (`negativity_confidence.csv`). If negativity bias exists, β_bad + β_good < 0.

| Specification | Sum over the three indicators β_bad + β_good | p |
| --- | --- | --- |
| 1-month change, 2010-02 to 2026-10 | +4.9 | 0.030 |
| Excluding pandemic months | +2.1 | 0.67 |
| 2010–2019 | +7.5 | 0.34 |
| 3-month change, excluding pandemic months | −11.4 | 0.16 |

- The only significant result is the main specification, and its direction is the opposite of negativity bias: the rebound in sentiment when inflation eases is larger than the decline when inflation rises. It depends on the pandemic months and is no longer significant once they are excluded.
- By indicator, the signs of the coefficients are inconsistent across specifications.
- Stage 2 reached the same conclusion on the media side: the negativity asymmetry is not robust.

**F2. Availability: gasoline and food prices have no additional explanatory power within the estimation window; the correspondence between price coverage and "price news heard" is clear.**
(`competition_regressions.csv`, `competition_gap_reduction.csv`)

- Adding gasoline prices and year-over-year food CPI to M1 in 2010–2019: gasoline −0.91 (p = 0.56), food −0.51 (p = 0.46). Recomputing the 2025-01 to 2026-10 gap with this model shrinks it by only 2.2%.
- In-sample association in the full sample (excluding pandemic months): gasoline −11.4 (p = 0.001), food not significant. With 36-month cumulative inflation added at the same time, gasoline falls to −5.0 (p = 0.18).
- Exposure side (stage 4 F3): each 1-unit increase in the share of rising-prices coverage is associated with a 17.2 percentage point higher share hearing unfavorable price news (p < 0.001), and layoff coverage as a placebo is not significant.

**F3. Anchoring on past prices: there is compatible evidence at the aggregate level, but it cannot be identified within the estimation window.**

- **Competing regressions**:
  - In 2010–2019, the coefficient on 36-month cumulative PCE inflation is −0.21 (p = 0.79), the same as in stage 1. The reason is that cumulative inflation changed too little in this period, so identifying power is insufficient.
  - In the full sample, cumulative inflation is −2.2 (p < 0.001), while 12-month inflation is −4.7 (p < 0.001).
  - In the exploratory 2000 window of stage 1, cumulative inflation is significant and shrinks the gap since 2021 by about 24%.
- **Mention rates of "because of high prices" as a reason** (`price_reasons.csv`, `price_reasons_periods.csv`):

| Period | Worse off financially: because of high prices | Bad time to buy durables | Bad time to buy a vehicle | Bad time to buy a home | PCE year-over-year | 36-month cumulative |
| --- | --- | --- | --- | --- | --- | --- |
| 2019 | 7.3 | 11.3 | 19.8 | 24.3 | 1.5 | 5.3 |
| 2022 | 39.8 | 42.4 | 56.0 | 62.5 | 6.2 | 10.9 |
| 2025-01 to 2026-08 | 44.8 | 33.4 | 39.9 | 43.9 | 2.8 | 9.4 |

  - After controlling for 12-month inflation, the coefficients of cumulative inflation on all four mention rates are positive and significant (1.2–2.1, p ≤ 0.001).
  - The inflation rate in 2025–2026 is less than half that of 2022, yet the mention rate of "worse off financially because of high prices" is actually higher. This is compatible with "respondents use the price level rather than the inflation rate as their reference".
- **Note**: the coefficient on the web-interview dummy in the regressions is also large (+17.9 for the worse-off mention rate). The mode change after 2024-07 coincides in time with events such as tariffs and cannot be separated from them. Tested separately with the stage 1 mode-jump design, the jump in this mention rate is +2.0 (p = 0.21), and +6.5 (p = 0.018) after excluding the transition months; see F6.

**F4. The 2025–2026 gap is present across demographic groups and similar in size; in 2021–2022, by contrast, it differed greatly.**
Each group's gap is computed with its own M1 (fitted on 2010–2019) (`group_gaps.csv`, `group_gap_differences.csv`). The table below is for ICS:

| Dimension | 2021-07 to 2022-12 | 2025-01 to 2026-08 |
| --- | --- | --- |
| Income (low, middle, high tercile) | −16.3, −25.6, −23.5 | −35.2, −39.6, −36.9 |
| Age (18–34, 35–54, 55+) | −0.2, −25.8, −35.2 | −38.8, −42.3, −35.5 |
| Region (West, North Central, Northeast, South) | −19.3, −20.8, −7.8, −33.2 | −39.6, −37.4, −32.0, −38.1 |
| Education (high school or less, some college, college) | −41.7, −36.0, −6.7 | −36.6, −41.2, −35.2 |

- In 2025–2026, the range of gaps across groups within the same dimension is no more than 7.5 points, while the gap itself is 32–42 points. Some between-group differences are statistically significant, for example the Northeast is 5–8 points smaller than the other regions, but the magnitude is far smaller than the gap.
- Each group's M1 explains only 2%–14% of that group's decline in sentiment in 2025.
- The pattern in 2021–2022 is completely different: young people, college graduates, and the Northeast have almost no gap, while older people, those with less education, and the South have large gaps.
- Partisanship (stage 4 F5) is the only dimension that still shows large differences in 2025–2026, and the direction is related to the governing party.

**F5. The 2026 gap is not an election-season phenomenon.**
(`pre_election_years.csv`, `pre_election_regression.csv`)

| Midterm year | January–April gap | May–October gap | Change | Change in tone |
| --- | --- | --- | --- | --- |
| 2010 | 2.1 | 1.9 | −0.2 | +0.02 |
| 2014 | −4.5 | −1.0 | +3.6 | +0.13 |
| 2018 | 1.9 | 2.2 | +0.3 | −0.07 |
| 2022 | −27.4 | −27.1 | +0.3 | −0.07 |
| 2026 | −38.8 | −40.4 | −1.6 | −0.09 |

- The 2010–2018 gaps are in-sample residuals; the 2022 and 2026 gaps are out-of-sample.
- The 2026 gap had already reached −38.8 in January–April and widened by only 1.6 points in the 6 months before the election, slightly below the range of changes in the other midterm years (−0.2 to +3.6), a very small difference.
- Full-sample regression: the monthly change in the gap in the pre-election months May–October does not differ from other months. The coefficient for midterm years is +0.60 (p = 0.22), and for presidential election years +0.73 (p = 0.28).
- Other changes in the same period (R5.4 requires reporting them together): comparing May–October 2026 with January–April, real-time PCE year-over-year inflation rose from 2.8% to 3.7%, gasoline prices rose from $3.15 to $4.18 per gallon, and the 30-year mortgage rate rose from 6.15% to 6.61%. In 2025 there was also the April tariff executive order and the October–November government shutdown. Even if sentiment changed in the months before the election, the change could not be attributed to the election alone.

**F6. Survey mode: the widening of the 2025–2026 gap took place within the web-interview period and was not caused by the mode switch.**
(`mode_gap_changes.csv`, `mode_steps.csv`)

- Comparing only within the web-only period after 2024-07, which is unaffected by level differences between modes:
  - The ICS gap widened from −23.0 in the second half of 2024 to −39.3 in 2026, a change of −16.3. The change through 2025 is −12.8.
  - The change is −10.6 for ICC and −20.0 for ICE.
  - For reference, in the phone-only period from the second half of 2022 to 2024 Q1, the ICS gap narrowed by 6.7 points.
- Jumps at 2024-07 in survey-side mechanism variables (2023–2025 sample, controlling for the M1 variables):

| Variable | Jump | p | After excluding 2024-04 to 06 | p |
| --- | --- | --- | --- | --- |
| Heard unfavorable news | +7.1 | 0.41 | −15.9 | 0.10 |
| Heard unfavorable price news | −2.3 | < 0.001 | −1.5 | 0.27 |
| Worse off financially because of high prices | +2.0 | 0.21 | +6.5 | 0.018 |
| Median 1-year inflation expectation | +0.2 | 0.68 | −1.1 | 0.012 |

  - None of the four variables shows a jump that is significant under both samples. But the results are very sensitive to whether the transition months are excluded, so the levels of these open-ended items and of inflation expectations before and after 2024 should not be compared directly.
  - The stage 4 recall pathway therefore also reports a sample ending 2024-03.

**F7. In the recent period, tone on social platforms and in local news moves with the gap less closely than national news does.**
Correlation of last month's tone with the current month's ICS gap (`recent_sources.csv`), descriptive only:

| Source | Period | Months or quarters | Correlation (levels) | National news, same period | Correlation (first differences) | National news, same period |
| --- | --- | --- | --- | --- | --- | --- |
| YouTube comments | 2023-02 to 2026-10 | 45 months | 0.16 | 0.62 | 0.05 | 0.01 |
| Local news | 2025-04 to 2026-10 | 19 months | 0.44 | 0.09 | 0.41 | 0.12 |
| Media Cloud national | 2025-10 to 2026-10 | 13 months | 0.30 | 0.25 | 0.13 | 0.07 |
| Reddit (quarterly) | 2015Q2 to 2026Q3 | 45 quarters | 0.10 | 0.23 | −0.06 | 0.13 |

- YouTube comments are on average more negative than national news (−0.67 vs. −0.48, already reported in stage 2), but their monthly fluctuations are almost unrelated to the gap.
- Local news has a higher correlation, but only 19 months, and the levels correlation is affected by common trends.
- Conclusions are limited to these periods and samples. Neither social platforms nor local news enter the historical models.

## 2. Three-way classification of mechanisms (RQ4)

| Mechanism | Measured (aggregate level) | Only compatible evidence | Not measurable |
| --- | --- | --- | --- |
| Negativity bias | Media-side good/bad news asymmetry: not robust (stage 2 F6); sentiment side: not robust (F1) | — | Individual information processing |
| Availability | Topic correspondence between price coverage and "price news heard": holds (stage 4 F3); additional explanatory power of gasoline and food within the estimation window: does not hold (F2) | The full-sample association of gasoline prices (F2, includes gap years) | Specific instances in personal memory |
| Anchoring on past prices | Competing regressions of cumulative inflation and the inflation rate: not identifiable within the estimation window (F3, stage 1 F4) | Cumulative inflation significant in the full sample and the 2000 window; the mention rate of "because of high prices" stays high after inflation eased (F3) | Personal reference prices |
| Confirmation bias | Not identifiable | Opposite-direction jumps in partisan indices at changes of administration (stage 1 F6); negative correlation of partisan gap paths (−0.72, stage 4 F5) | Individual beliefs, exposure, and processing; written into the experiment proposal |

## 3. Adjudication against the design requirements

| Item | Verdict | Basis |
| --- | --- | --- |
| RQ4 Mechanism measurability | Two mechanisms are tested at the aggregate level, both with the result "not robust or not identifiable"; anchoring and confirmation bias have only compatible evidence | Section 2 |
| R5.2 Group heterogeneity | The 2025–2026 gap is widespread and similar across income, age, region, and education groups; only partisan differences are large | F4; stage 4 F5 |
| R5.3 Survey mode comparability | The widening of the 2025–2026 gap took place within the web period; level comparisons of open-ended items and inflation expectations across the break are unreliable | F6; stage 1 F5 |
| R5.4 Approaching election | No evidence that the change in the gap in the months before the election is unusual; inflation, gasoline prices, and interest rates rose over the same period | F5 |
| Falsification list item 7 (supplement) | The stage 4 verdict of "not triggered" stands. But note: in 2025–2026 the gaps of the demographic groups are similar, and between-group differences show up mainly in 2021–2022 and along the partisan dimension | F4 |

## 4. Limitations

- Each group's M1 is fitted on 2010–2019 and has the same extrapolation problem as in stage 1, so the between-group comparisons are of relative sizes under the same kind of extrapolation.
- The group indices are published by Michigan by group without sample sizes or standard errors, so tests of between-group differences use only the HAC variance of the monthly series.
- The mention rates of "because of high prices" as a reason come from coding of open-ended questions, and their comparability before and after the mode switch has not been established. Part of the rise in these mention rates in F3 may come from the mode switch.
- There is no monthly series on partisan composition, so composition adjustment can only use the stage 1 sensitivity range (no more than 2.7 points).
