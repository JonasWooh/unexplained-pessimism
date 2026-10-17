# survey_monthly.csv

- Generating script: `src/process/survey_monthly.py`
- Generated: 2026-10-16
- Rows: 585 (1978-01 to 2026-09, one row per survey month), 184 columns. Values match the official releases, with no transformation.
- Raw data:
  · `data/raw/S02`: response from the subgroup subset service. This is CSV text, saved under the original response name as `monthly_subset_response.html`, plus `table_5b_historical.xls`
  · `data/raw/S03`, `data/raw/S04`: `monthly_all_response_codes.csv`, `tbmpx1px5.csv`

## Column naming

Column names are "variable_group".

- Variables:
  · `ics`, `icc`, `ice`: the three indices
  · `news_*`: economic news heard, `f` favorable, `u` unfavorable, `n` heard none, `r` relative score
  · `newsrn_*`: categories of news heard (government, employment, demand, prices, credit, stock market, trade, energy)
  · `pagorn`: reasons personal finances got better or worse
  · `umex`, `ratex`: unemployment expectations, interest rate expectations
  · `px1`, `px5`: distribution of 1-year and 5–10-year inflation expectations, plus mean, median, etc.
  · `dur`, `veh`, `hom` and the corresponding `*rn`: buying conditions for durables, vehicles, and homes, and reasons
  · `govt`: rating of government economic policy
- Groups:
  · `all`: everyone
  · `a1834`, `a3554`, `a5597`: age groups
  · `y13`, `y23`, `y33`: income terciles
  · `w`, `nc`, `ne`, `s`: West, North Central, Northeast, South
  · `ehs`, `esc`, `ecd`: education of high school or less, some college, college degree
  · `dem`, `ind`, `rep`: Democrat, Independent, Republican
- `px1_median_tb`, `px5_median_tb`: medians from the official monthly table `tbmpx1px5.csv`.

Full definitions are in `data/raw/S05/*/subset_codebook.pdf`.

## Known issues

- Subgroup, news, and reason variables run through 2026-08; the 2026-09 row has only `px1_median_tb` and `px5_median_tb`. This is an official release lag, not missing data.
- The partisan columns (`*_dem`, `*_ind`, `*_rep`) come from the monthly historical table, start in 1980-06, are very sparse early on, and have values in 156 months in total. The current version of yearbook Table 5b is a three-month moving average, so it is not used.
- The share of respondents self-identifying with each party (partisan composition) has no public monthly series.
- From 2024-04 to 2024-07 the survey switched from telephone to web interviews (see `mode_web_share` in `econ_monthly_realtime.csv`), and the comparability of coding for open-ended questions such as "news heard" has not been demonstrated.
