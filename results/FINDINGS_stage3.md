# Stage 3 results: forecast comparison (RQ5, H2b)

Frozen 2026-10-16. The design is in the Model 2, Model 3, and robustness sections of `research/RESEARCH_DESIGN_v1.md`; implementation details are in the 2026-10-16T19:35Z entry of `DECISIONS.md`. Specifications are registered in `results/spec_registry.csv` (from S083); rerun everything with `sh src/analysis/run_stage3.sh`.

**Specification**
- The forecast origin is the 1st of month t: use the real-time economic values on that date and the media measures for month t−1, with ICS_{t−1} added in the AR version.
- All four models share an expanding window starting 2010-06 (real per-capita disposable income is available only from that month). The first training window runs to 2016-12, and the evaluation period is 2017-01 to 2026-10, 118 months in total.
- Fixed in writing before seeing the results: item 2 of the falsification list uses the AR version as the main version, because it controls for the persistence of sentiment itself and is the stricter test; the version without AR is reported alongside.
- RMSE ratio = larger model ÷ smaller model; below 1 means forecasts are more accurate after adding the variables. Clark–West is a one-sided test.

## 1. Findings

**F1. Adding media tone to the model with only the three fundamentals gives a small but significant improvement in forecasts.**
1-step forecasts, AR version (`stage3_forecast/comparisons.csv`):

| Period | M1 RMSE | M2 RMSE | Ratio [95% interval] | Clark–West p |
| --- | --- | --- | --- | --- |
| 2017-01 to 2026-10 | 4.93 | 4.89 | 0.991 [0.949, 1.022] | 0.041 |
| Same, excluding 2020-03 to 12 | 4.23 | 4.13 | 0.976 [0.931, 1.010] | 0.005 |
| 2017–2019 | 3.04 | 2.85 | 0.937 | 0.017 |
| 2020–2022 | 6.54 | 6.69 | 1.023 | 0.48 |
| 2023–2024 | 4.30 | 4.31 | 1.004 | 0.36 |
| 2025–2026 | 5.00 | 4.60 | 0.920 | 0.005 |

Without AR, M1 itself is poor (RMSE 14.1), and the ratio after adding tone is 0.946 (p = 0.006). 3-month direct forecasts show no improvement in the AR version (p = 0.88).

**F2. After controlling for household pressures and political variables, media tone has no out-of-sample increment in the main specification.**
M1c vs. M3, AR version:

- RMSE ratio 1.001 [0.964, 1.046], Clark–West p = 0.23; p = 0.42 after excluding the pandemic months.
- By period, only 2017–2019 is significant (p = 0.007); for 2025–2026, p = 0.34.
- None of the 20 robustness variants is significant at the 5% level, with p between 0.065 and 0.85. The closest to significance are the full-frame dictionary index (p = 0.065) and the Michigan preliminary-release cutoff (p = 0.095). See `stage3_robustness/variants.csv` and `fig_spec_curve_cw.png`.
- Without AR, 18 of the 20 variants are significant (main specification p = 0.004, ratio 0.926). But the models without AR miss the persistence of sentiment itself, and their RMSE is more than twice that of the AR versions; here tone very likely stands in for the persistent part of the gap rather than providing independent information.

**F3. In sample, the tone coefficient is stably positive and significant, but small when converted into points.**
M3, AR version, 2010-06 to 2026-10: γ = 5.03 (HAC 12-lag standard error 1.40, p < 0.001). The conclusion is the same with HAC 6 and 18 lags, and the 2010–2019 window gives 5.93 (`media_coefficients.csv`).

- The monthly standard deviation of national tone is about 0.20, so a one-standard-deviation change in tone moves same-month ICS by about 1.0 point, and about 1.8 points cumulatively in the long run (γ ÷ (1 − ρ), ρ = 0.45).
- Magnitude conversion (`magnitude.csv`, using M3 fitted on 2010–2019): national tone in 2025 is 0.15 below its 2019 mean, corresponding to about 1.6 points; the mean 2025 gap in stage 1 is −35.8, so this part accounts for about 4.5%. In 2026 it accounts for about 3.6%. Tone in 2021–2022 and 2023–2024 is not more negative than in 2019, and the corresponding shares are below 0.
- These are upper bounds on the association, not causal effects.

**F4. The tone coefficient becomes larger after the 2024-07 survey mode switch.**
Results from `gamma_breaks.csv`:

- In the AR version, γ increases by 11.7 after 2024-07 (p = 0.010); without AR it increases by 41.3 (p < 0.001).
- At 2020-03 and 2025-01 only the intercept changes; γ itself shows no significant change.
- 60-month rolling coefficients are in `fig_rolling_gamma.png`.
- This echoes the stage 1 finding that ICC shifted down after web interviews. Sentiment in the web sample may be more sensitive to the news environment, but there are only 28 months of data, so this is an exploratory observation.

**F5. Adding household and political controls by itself makes out-of-sample forecasts worse.**
In the AR version, the RMSE ratio of M1c to M1 is 1.16 [1.01, 1.37], worst in 2020–2022 (1.26). The reason is the same as in stage 1: cumulative inflation and the mortgage rate varied little in the training period, so extrapolation is unstable. In addition, the governing-party dummy is constantly 0 in the first training window (2010–2016 is all the same administration), so its coefficient can only be estimated gradually after 2017.

The highest variance inflation factor is 4.5 in the first window (cumulative inflation) and 5.5 over the full period, which does not amount to serious collinearity (`vif.csv`).

**F6. None of the secondary media variables survives the false discovery rate correction (AR version).**
The six variables are added to M1 one at a time, with lags of 1–3 chosen by BIC in each window, plus the first principal component of the six (`secondary.csv`).

- In the AR version, all BH-corrected p-values are at least 0.43.
- Without AR, only `net_fact` passes (corrected p = 0.082, q = 0.10).

**F7. Results for the alternative media measures: excess tone keeps the same information as raw tone; the San Francisco Fed index and EPU add nothing.**

- **Excess tone**: following the design literally, regressing tone on U, π, and g, which are already in the model, and taking the residual gives forecasts identical to raw tone by the Frisch–Waugh–Lovell theorem, so the test is uninformative. The residual was therefore taken instead from a regression on U, π, g, the household variables, and the data releases of month t−1 (recorded as a deviation). Results: M1 vs. M2, AR version, p = 0.024; M1c vs. M3, p = 0.12. With the fundamentals component removed, tone's increment over M1 remains, so it is not merely another reading of the fundamentals; but after controlling for household variables it is likewise not significant.
- **3-month average tone**: no increment in the AR version (p = 0.73), and γ is not significant. The information in monthly tone lies mainly in short-run changes, which are absorbed by the AR term after smoothing.
- **San Francisco Fed index**: AR version γ = 0.68 (p = 0.86).
- **EPU**: AR version γ close to 0 (p = 0.54).
- **Full-frame dictionary index**: γ = 9.2 (p = 0.017), and M1c vs. M3 p = 0.065, the variant closest to significance in the AR version.

## 2. Adjudication of hypotheses and the falsification list

| Item | Verdict | Basis |
| --- | --- | --- |
| H2b first part: tone adds to M1 | Supported, small effect | F1: AR version p = 0.041, RMSE down 0.9%; 9 of the 20 variants significant |
| H2b main test: tone still adds after controlling for real pressures and politics | Not supported (main specification) | F2: none of the 20 variants significant in the AR version; only the specifications without AR support it |
| RQ5 Whether media analysis improves sentiment forecasts | Only a small improvement over the fundamentals model, which disappears after adding household and political controls | F1, F2 |
| Falsification list item 2 (no out-of-sample increment) | **Triggered** (AR main version p = 0.23); not triggered in the version without AR | F2 |
| Secondary media hypotheses | All not significant in the AR version | F6 |
| Share of the gap associated with tone | No more than about 5% in 2025–2026 | F3 |

## 3. Limitations

- The evaluation period has only 118 months, and 2025–2026 only 22 months, so the by-period tests have limited power.
- The design did not state whether the AR version should be the main version. Here the AR version was chosen before seeing the results and recorded in DECISIONS.md, and both versions are reported in full.
- The monthly reliability of the media measures is about 0.62 (stage 2), so γ is underestimated. The conclusions from the two alternative measures, the 3-month average and the full-frame dictionary, agree with the main measure or are weaker; measurement noise did not change the direction.
