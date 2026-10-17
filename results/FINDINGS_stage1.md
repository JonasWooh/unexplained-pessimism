# Stage 1 results: economic baseline (RQ3, H1, H3)

Frozen 2026-10-16. The design is in `research/RESEARCH_DESIGN_v1.md`, deviations and implementation details are in the 2026-10-16T18:40Z entry of `DECISIONS.md`, and all specifications are registered in `results/spec_registry.csv`. Scripts are in `src/analysis/`; rerun everything with `sh src/analysis/run_stage1.sh`.

Findings come first below, followed by the adjudication of the hypotheses, with the two parts kept separate. Parentheses after numbers give the source file. Gap = actual value − M1 forecast; a negative number means sentiment is below the level that fundamentals can explain. Intervals are 95% intervals for period means from the moving-block bootstrap (block length 12, 2,000 replications).

## 1. Findings

**F1. M1 fits well in 2010–2019; during the pandemic its monthly errors are extremely large, so that period cannot be used to validate the model.**
Regressing ICS on the real-time unemployment rate, PCE year-over-year inflation, and annualized quarter-over-quarter GDP growth gives R² of 0.90, n = 120. The coefficients are: unemployment rate −4.84 (HAC standard error 0.29), inflation −2.31 (1.00), GDP growth 1.09 (0.28). The seasonal dummies are jointly significant (p = 0.001) and are kept under the pre-registered rule (`stage1_m1/m1_fit.csv`). The Engle–Granger test shows that the residuals are stationary (p < 0.001), indicating that the levels regression is not spurious (`unit_roots_main_window.csv`). The mean gap from 2020-01 to 2021-06 is +1.1, but this results from positive and negative errors offsetting each other and does not mean the model explains the pandemic. The root mean square of monthly errors from 2020-03 to 2021-06 is 30.3. The reason is that the unemployment rate (14.7%) and annualized GDP growth (−32.9% and +33.1%) are far outside the range of values in the estimation period: the gap is +52.0 in 2020-09 and −39.6 in 2021-01 (`m1_gap_monthly.csv`).

The explained shares below therefore use only the periods from 2021-07 onward, and the pandemic period is not interpreted.

**F2. From the second half of 2021, a large and persistent negative gap appears and widens period by period.** The table below gives the by-period results for ICS, from `stage1_m1/m1_periods.csv` and `fig_m1_gap_ics.png`.

| Period | Change in actual value relative to 2019 | Mean gap | 95% interval | Explained share S |
| --- | --- | --- | --- | --- |
| 2021-07 to 2022-12 | −32.6 | −22.9 | [−7.7, 7.9] | 0.30 |
| 2023-01 to 2024-12 | −27.0 | −25.2 | [−4.4, 4.7] | 0.07 |
| 2025-01 to 2025-12 | −38.4 | −35.8 | [−4.2, 3.9] | 0.07 |
| 2026-01 to 2026-10 | −44.8 | −39.8 | [−5.3, 5.1] | 0.11 |

- The gap in every period is far outside the interval, bootstrap p < 0.001.
- After 2023, the three fundamentals explain only 7%–11% of the decline in sentiment.
- Contribution decomposition: in 2021–2022, inflation pulls sentiment down by 9.4 points and the unemployment rate by 2.6 points. In 2025–2026, no contribution exceeds 4.2 points.
- The ICC gap is larger (−55.2 in 2026), and the ICE gap smaller (−29.9).
- The 2026-10 ICS is preliminary.

**F3. The 2025–2026 gap is robust to specification; the 2021–2022 gap is sensitive to the estimation window.**
In the main window, the 2025 gap lies between −35.5 and −36.3 under each of the following variants: HAC with 6 or 18 lags, dropping the seasonal terms, using GDP year-over-year instead, and using the Michigan preliminary release date as the cutoff. The first-difference specification gives a larger gap, −41.1 without a constant (`m1_robustness.csv`).

With other estimation windows, the 2025 gap is −31.7 in the 2000-09–2019 window and −35.9 in the 1978–2019 window. The 2021–2022 gap, by contrast, ranges from −10.1 (2000 window) to −25.1 (1978 window), versus −22.9 in the main window (`stage1_windows/m1_windows.csv`). The reason is that the inflation coefficient changes with the window: −5.4 in the 2000 window and −2.3 in the main window. In the main window, PCE year-over-year inflation varies only between 0.2% and 2.9%, and 53% of the months since 2021 are outside this range (`h1_support.csv`).

Expanding-window recursive estimation gradually absorbs the gap into the coefficients, but the 2025 gap is still −25.2.

**F4. After adding household pressure variables, these channels cannot be identified in the main window.**
Adding 36-month cumulative inflation, the 30-year mortgage rate, real per-capita disposable income growth, and gasoline prices, separately or together, none is significant in the ICS equation (p between 0.24 and 0.89). The mean gap since 2021 changes only from −27.4 to −27.2 (`stage1_h1/h1_models.csv`).

The reason is that these variables changed too little in the estimation period: 89% of out-of-sample cumulative inflation values and 96% of mortgage rate values fall outside their 2010–2019 ranges (`h1_support.csv`). This is therefore a lack of power and cannot be taken as evidence that these channels do not exist.

Exploratory analysis (not pre-registered): in the 2000-09–2019 window, where variation is larger, cumulative inflation is significant (ICS −1.68, p = 0.008; ICC −2.35, p = 0.001). It shrinks the ICS gap since 2021 from −20.4 to −15.5, about 24%, and the 2025 gap from −31.7 to −26.2 (`h1_models_with_exploratory.csv`).

**F5. After the switch to web interviews, the current conditions index ICC shifts down by about 5–8 points, while ICS and ICE show no stable jump.**
Regressing the 2023–2025 gap on a step variable starting 2024-07 (`stage1_h3/h3a_mode.csv`):

| Index | Coefficient | p-value | After excluding the 2024-04 to 06 transition months |
| --- | --- | --- | --- |
| ICC | −8.0 | < 0.001 | −8.4 |
| ICS | −5.7 | 0.07 | — |
| ICE | −4.1 | 0.32 | — |

Using the web-interview share instead of the step variable gives the same results. To rule out interference from the April 2025 tariff shock, an exploratory regression through 2025-03 was also run: ICC is still −5.1 (p < 0.001), and ICS is +0.3.

**F6. Partisan reactions are sharp but go in opposite directions; after they offset, the overall gap is still large, and it does not come only from the out-party.**
Jumps in the 3 months before and after changes of administration (`h3b_party_jumps.csv`):

| Change | Democrats | Republicans | Independents | All |
| --- | --- | --- | --- | --- |
| 2021-01 | +17.8 | −19.7 | — | +0.4 |
| 2025-01 | −28.2 | +17.6 | −4.2 | −7.6 |

Deviation of each partisan index in 2025 from its own 2017–2019 mean (`h3b_party_periods.csv`): Democrats −37.3, independents −42.4, and Republicans also −29.3.

Sensitivity range for partisan composition: assuming the Republican share falls by 2, 4, or 6 percentage points, ICS would fall by only 0.8–2.7 points, no more than 7% of the 2025–2026 gap (`h3b_composition_bound.csv`). The partisan shares used in the calculation are estimated by least squares under the constraint that overall ICS equals the weighted average of the three groups with weights summing to 1: Democrats 0.26, independents 0.54, Republicans 0.20, with a fitting error of 1.0 point.

## 2. Adjudication of hypotheses

| Hypothesis | Verdict | Basis |
| --- | --- | --- |
| H1a Cumulative inflation | Not supported in the main window, because of insufficient identification; the exploratory 2000 window supports the direction but explains only about a quarter | F4 |
| H1b Mortgage rate | Not supported; the coefficient is negative but not significant in the ICS equation, and positive in the ICC equation | F4 |
| H1c Real income | Not supported; the coefficient has the right sign but is not significant | F4 |
| H1d Gasoline prices | Not supported; the coefficient has the right sign but is not significant | F4 |
| H3a Survey mode | Partly supported: only ICC shows a stable jump, about 5–8 points, less than a fifth of the ICC gap | F5 |
| H3b Partisanship | Partly supported: the jumps are clear, but the 2025–2026 gap is not concentrated only among Democrats and independents, as Republicans are also far below their own baseline; the composition effect is negligible | F6 |
| H3c Model and window | Supported, but only for 2021–2022; the 2025–2026 gap is at least 23 points in absolute value under all three windows and all robustness specifications | F3 |

**Falsification list**
- Item 4 (real pressures explain the gap) is not triggered: no combination of household controls shrinks the gap since 2021 by half: ICS shrinks by at most 4%, ICC by at most 10%, and the exploratory model by 24%.
- Item 5 (the gap comes from measurement or partisanship) is not triggered: the upper bound on the absolute value of the mode-jump range is 11.9 for ICS and 12.6 for ICC, both smaller than half of their respective mean 2025–2026 gaps (ICS about 18–20, ICC about 24–28); the partisan composition effect is no more than 2.7.

**Questions left for later stages**: the 2025–2026 gap of −36 to −40 points cannot be explained by economic fundamentals, household pressure variables, survey mode, or partisan composition. This residual is the object of the stage 3 test of the media increment (H2). Because of the window sensitivity in F3, conclusions about 2021–2022 must be reported with the window range.
