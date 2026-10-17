# econ_monthly_realtime.csv

- 生成脚本：`src/process/econ_realtime.py`（同一脚本生成敏感性版本 `econ_monthly_realtime_prelim_cutoff.csv`）
- 生成时间：2026-10-16
- 行数：202（2010-01 至 2026-10，一行一个调查月份），63 列
- 原始数据：`data/raw/M01–M16`（ALFRED 全部版本）、`data/raw/S01`（密歇根月度 CSV）、`data/raw/S05`（官网首页初值、历史发布日历 PDF）

## 信息截止日规则

- 主文件（`cutoff_rule = D2`）：第 t 月的截止日 τ = 第 t 月 1 日的前一天。只使用 ALFRED `realtime_start ≤ τ ≤ realtime_end` 的数值，即截止日当时公开的版本。
- 敏感性文件（`cutoff_rule = mich_prelim`）：τ = 第 t 月密歇根初值发布日的前一天，发布日取自官方历史发布日历。
- 每个指标在该版本内取**最新的非缺失观测期**。官方缺失值（ALFRED 中的 `.`，例如 2025-10 的失业率）会被跳过，所以截止日 2025-10-31 时最新可得的失业率是 8 月数据，因为 9 月数据到 2025-11-20 才发布。
- 同比、环比、累计涨幅的分子和分母都取自**同一版本**。

## 列定义

| 列 | 含义 |
|---|---|
| `month` | 调查月份 YYYY-MM |
| `origin_date` | 截止日 τ |
| `cutoff_rule` | `D2` 或 `mich_prelim` |
| `ics`、`icc`、`ice` | 密歇根三项指数：2026-09 及以前为月度 CSV 的终值；2026-10 为官网首页的初值 |
| `ics_status` | `final` 或 `prelim` |
| `mich_prelim_release_date`、`mich_final_release_date` | 官方初值和终值发布日 |
| `mode_web_share` | 网络访谈比例：2024-04 为 0.25，05 为 0.5，06 为 0.75，07 起为 1，此前为 0 |
| `<x>_rt` | 截止日的实时值 |
| `<x>_ref` | 该值对应的观测期（周度或日度序列为观测日期） |
| `<x>_release_date` | 该值所在版本的 `realtime_start`，即该数值的发布日 |
| `unrate` / `u6rate` | U-3（UNRATE）、U-6（U6RATE），% |
| `pce_yoy_rt`、`core_pce_yoy_rt` | 总体 PCE（PCEPI）、核心 PCE（PCEPILFE）同比，% |
| `pce_cum_since_2021_01_rt`、`food_cpi_cum_since_2021_01_rt` | 相对 2021-01 的累计涨幅，%；观测期早于 2021-02 时为空 |
| `rdpi_pc_yoy_rt`、`rdpi_yoy_rt`、`real_pce_yoy_rt` | 人均实际可支配收入（A229RX0）、实际可支配收入（DSPIC96）、实际消费（PCEC96）同比，% |
| `food_cpi_yoy_rt`、`food_home_cpi_yoy_rt` | 食品 CPI（CPIUFDSL）、家庭食品 CPI（CUSR0000SAF11）同比，% |
| `case_shiller_yoy_rt` | Case-Shiller 全国房价（CSUSHPISA）同比，% |
| `mortgage30_rt` | 30 年期房贷利率（MORTGAGE30US，周度），% |
| `gas_price_rt` | 普通汽油零售价（GASREGW，周度），美元/加仑 |
| `tdsp_rt` | 家庭偿债负担（TDSP，季度），% |
| `epu_rt` | 政策不确定性指数（USEPUINDXM） |
| `gdp_qoq_saar_rt` | 实际 GDP（GDPC1）环比折年率 = 100×((G_q/G_{q-1})^4 − 1) |
| `gdp_yoy_rt` | 实际 GDP 同比 = 100×(G_q/G_{q-4} − 1) |
| `gdp_ref_quarter` | 观测季度 |
| `gdp_release_number` | 截至截止日，该季度已出现的发布次数：1 为首次估计（advance），2 为第二次，3 为第三次，≥4 为后续修订 |
| `sp500_close`、`nasdaq_close` 及 `_ref` | 截止日前最后一个交易日的收盘价，取自当前数据；市场数据不修订 |

## 已知问题

- 各序列在其 ALFRED 最早版本之前为空，不用后来的版本回填，否则会造成前视偏差：U-6 从 2011-04 起有值，家庭食品 CPI 从 2011-05 起，人均实际可支配收入从 2010-06 起，房贷利率从 2010-07 起，EPU 从 2013-07 起，Case-Shiller 从 2014-12 起，S&P 500 从 2016-11 起（FRED 只提供 2016-10-17 以后的数据）。
- GDP 是"截止日前最新已发布季度"的阶梯函数，不是插值，不违反 R1.7。环比和同比都由 GDPC1 的同一版本计算；A191RL1Q225SBEA 的版本从 2014-09 才开始，因此未使用。
- HOAM 住房可负担性只有当前快照，没有历史版本，不能做实时变量，因此不在本文件中；原件在 `data/raw/M13`。
- 2026-10 的 ICS/ICC/ICE 是初值（46.3/44.7/47.3），终值将于 2026-10-23 发布。
- 党派构成（自认共和党比例）没有可用的月度序列；各党派的信心指数见 `survey_monthly.csv`。
