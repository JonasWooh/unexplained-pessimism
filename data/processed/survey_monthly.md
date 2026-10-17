# survey_monthly.csv

- 生成脚本：`src/process/survey_monthly.py`
- 生成时间：2026-10-16
- 行数：585（1978-01 至 2026-09，一行一个调查月份），184 列。数值与官方发布一致，未做任何变换。
- 原始数据：
  · `data/raw/S02`：分组子集服务的返回。这是 CSV 文本，按原响应名保存为 `monthly_subset_response.html`，另有 `table_5b_historical.xls`
  · `data/raw/S03`、`data/raw/S04`：`monthly_all_response_codes.csv`、`tbmpx1px5.csv`

## 列命名

列名为"变量_组别"。

- 变量：
  · `ics`、`icc`、`ice`：三项指数
  · `news_*`：听到的经济新闻，`f` 有利、`u` 不利、`n` 没听到、`r` 相对分值
  · `newsrn_*`：所听到新闻的类别（政府、就业、需求、价格、信贷、股市、贸易、能源）
  · `pagorn`：个人财务好转或变差的原因
  · `umex`、`ratex`：失业预期、利率预期
  · `px1`、`px5`：1 年、5–10 年通胀预期的分布，以及均值、中位数等
  · `dur`、`veh`、`hom` 及对应的 `*rn`：耐用品、汽车、住房购买条件及原因
  · `govt`：对政府经济政策的评价
- 组别：
  · `all`：全体
  · `a1834`、`a3554`、`a5597`：年龄组
  · `y13`、`y23`、`y33`：收入三分位
  · `w`、`nc`、`ne`、`s`：西部、中北部、东北部、南部
  · `ehs`、`esc`、`ecd`：教育程度为高中及以下、部分大学、大学学位
  · `dem`、`ind`、`rep`：民主党、独立人士、共和党
- `px1_median_tb`、`px5_median_tb`：官方月度表 `tbmpx1px5.csv` 的中位数。

完整定义见 `data/raw/S05/*/subset_codebook.pdf`。

## 已知问题

- 分组、新闻和原因类变量到 2026-08 为止，2026-09 行只有 `px1_median_tb`、`px5_median_tb`。这是官方发布滞后，不是缺失。
- 党派列（`*_dem`、`*_ind`、`*_rep`）来自月度历史表，从 1980-06 起，早期很稀疏，共 156 个月有值。年鉴表 5b 当前版本是三个月移动平均，因此未使用。
- 自认各党派受访者的比例（党派构成）没有月度公开序列。
- 2024-04 至 2024-07 调查从电话改为网络访谈（见 `econ_monthly_realtime.csv` 的 `mode_web_share`），"听到的新闻"等开放题的编码可比性没有得到证明。
