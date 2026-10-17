# econ_monthly_realtime.csv

- Generating script: `src/process/econ_realtime.py` (the same script generates the sensitivity version `econ_monthly_realtime_prelim_cutoff.csv`)
- Generated: 2026-10-16
- Rows: 202 (2010-01 to 2026-10, one row per survey month), 63 columns
- Raw data: `data/raw/M01–M16` (all ALFRED vintages), `data/raw/S01` (Michigan monthly CSV), `data/raw/S05` (preliminary values from the official homepage, historical release calendar PDF)

## Information cutoff rule

- Main file (`cutoff_rule = D2`): the cutoff for month t is τ = the day before the 1st of month t. Only ALFRED values with `realtime_start ≤ τ ≤ realtime_end` are used, i.e. the vintage that was public on the cutoff date.
- Sensitivity file (`cutoff_rule = mich_prelim`): τ = the day before the Michigan preliminary release date for month t, with release dates taken from the official historical release calendar.
- For each indicator, the **latest non-missing observation period** within that vintage is taken. Official missing values (`.` in ALFRED, e.g. the unemployment rate for 2025-10) are skipped, so at the 2025-10-31 cutoff the latest available unemployment rate is the August figure, because the September figure was not released until 2025-11-20.
- The numerator and denominator of year-over-year, period-over-period, and cumulative changes are all taken from the **same vintage**.

## Column definitions

| Column | Meaning |
|---|---|
| `month` | Survey month YYYY-MM |
| `origin_date` | Cutoff τ |
| `cutoff_rule` | `D2` or `mich_prelim` |
| `ics`, `icc`, `ice` | The three Michigan indices: for 2026-09 and earlier, final values from the monthly CSV; for 2026-10, the preliminary value from the official homepage |
| `ics_status` | `final` or `prelim` |
| `mich_prelim_release_date`, `mich_final_release_date` | Official preliminary and final release dates |
| `mode_web_share` | Share of web interviews: 0.25 in 2024-04, 0.5 in 05, 0.75 in 06, 1 from 07 onward, 0 before that |
| `<x>_rt` | Real-time value at the cutoff |
| `<x>_ref` | The observation period the value refers to (the observation date for weekly or daily series) |
| `<x>_release_date` | `realtime_start` of the vintage containing the value, i.e. the release date of that value |
| `unrate` / `u6rate` | U-3 (UNRATE), U-6 (U6RATE), % |
| `pce_yoy_rt`, `core_pce_yoy_rt` | Headline PCE (PCEPI), core PCE (PCEPILFE), year over year, % |
| `pce_cum_since_2021_01_rt`, `food_cpi_cum_since_2021_01_rt` | Cumulative increase relative to 2021-01, %; empty when the observation period is earlier than 2021-02 |
| `rdpi_pc_yoy_rt`, `rdpi_yoy_rt`, `real_pce_yoy_rt` | Real disposable income per capita (A229RX0), real disposable income (DSPIC96), real consumption (PCEC96), year over year, % |
| `food_cpi_yoy_rt`, `food_home_cpi_yoy_rt` | Food CPI (CPIUFDSL), food at home CPI (CUSR0000SAF11), year over year, % |
| `case_shiller_yoy_rt` | Case-Shiller national home price index (CSUSHPISA), year over year, % |
| `mortgage30_rt` | 30-year mortgage rate (MORTGAGE30US, weekly), % |
| `gas_price_rt` | Regular gasoline retail price (GASREGW, weekly), dollars/gallon |
| `tdsp_rt` | Household debt service burden (TDSP, quarterly), % |
| `epu_rt` | Policy uncertainty index (USEPUINDXM) |
| `gdp_qoq_saar_rt` | Real GDP (GDPC1) quarter-over-quarter annualized rate = 100×((G_q/G_{q-1})^4 − 1) |
| `gdp_yoy_rt` | Real GDP year over year = 100×(G_q/G_{q-4} − 1) |
| `gdp_ref_quarter` | Observation quarter |
| `gdp_release_number` | Number of releases for that quarter as of the cutoff: 1 is the first estimate (advance), 2 the second, 3 the third, ≥4 later revisions |
| `sp500_close`, `nasdaq_close` and `_ref` | Closing price on the last trading day before the cutoff, taken from current data; market data are not revised |

## Known issues

- Each series is empty before its earliest ALFRED vintage and is not backfilled with later vintages, since that would create look-ahead bias: U-6 has values from 2011-04, food at home CPI from 2011-05, real disposable income per capita from 2010-06, the mortgage rate from 2010-07, EPU from 2013-07, Case-Shiller from 2014-12, S&P 500 from 2016-11 (FRED only provides data after 2016-10-17).
- GDP is a step function of "the latest quarter released before the cutoff", not an interpolation, and does not violate R1.7. Both the quarter-over-quarter and year-over-year rates are computed from the same vintage of GDPC1; vintages of A191RL1Q225SBEA only start in 2014-09, so it is not used.
- HOAM housing affordability has only a current snapshot and no historical vintages, so it cannot be a real-time variable and is not in this file; the raw file is in `data/raw/M13`.
- The 2026-10 ICS/ICC/ICE are preliminary (46.3/44.7/47.3); the final values will be released on 2026-10-23.
- Partisan composition (share self-identifying as Republican) has no available monthly series; consumer sentiment indices by party are in `survey_monthly.csv`.
