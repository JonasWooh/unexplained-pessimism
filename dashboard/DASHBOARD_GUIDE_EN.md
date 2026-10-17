# Perception Gap Monitor: walkthrough by tab

This guide covers dashboard v2 (17 October 2026), with data up to 16 October 2026. Every number below matches what the page shows, and all of them come from the frozen result files.

## The essentials

- **Question.** In 2025–26, consumer sentiment is far below the level that economic fundamentals imply. Can news coverage explain that gap?
- **Method.**
  - A model is fit on 2010–2019 using only three fundamentals: unemployment, inflation and GDP growth.
  - The model only uses data that had already been published before each survey month (real-time vintages).
  - Its prediction is compared with the actual University of Michigan Index of Consumer Sentiment (ICS). The difference is the **gap**.
- **Main result.** The gap averaged −35.8 points in 2025 and −39.8 points so far in 2026. We tested survey mode, partisan composition and news tone, and each accounts for only a small part of it.
- **Colours.** These are the same on every page.
  - Black: actual sentiment.
  - Blue line and light-blue band: the model prediction and its prediction interval.
  - Orange: the gap.
  - Grey band: the pandemic months (March 2020 to June 2021). The frozen design does not apply the model to these months, so the model and gap lines stop there on purpose.
- **Controls.**
  - Hover over a chart to read the values for a month.
  - Click a month to open the side drawer, which shows that month's data and news headlines. Use ←/→ to move between months and Esc to close it.
  - The button at the top right switches between light and dark themes.

---

## 1. Overview

This tab gives the conclusion in one sentence, plus one main chart.

**Headline.** "Consumers are about 36 to 40 points gloomier than the economy predicts, and the news does not explain why."

**Status board (right)**

| Shown | Meaning |
| --- | --- |
| Michigan ICS, Oct 2026 **46.3** (Preliminary) | Preliminary October reading, released 9 October. The final reading is due 23 October and may be revised slightly. |
| Fundamentals model **89.7**, 95% interval 81.6 to 97.6 | The model's prediction from the fundamentals available that month, with its 95% prediction interval. |
| Gap this month **−43.4** | Actual minus predicted (46.3 − 89.7). The line below gives the 2025 average gap (−35.8) and the 2026 average so far (−39.8). |
| Share of the fall since 2019 explained **7%–11%** | Of the drop in sentiment since 2019, the three fundamentals explain 7% in 2025 and 11% in 2026. |
| Election Day, Nov 3, in N days | Days until the midterms, counted from the day the page is opened. Election Day falls 18 days after the data cutoff. |

**Main chart: "Michigan sentiment and what the fundamentals predict"**

- The black line is the actual ICS.
- The dashed blue line is the model's fit inside the 2010–2019 estimation window.
- The solid blue line is the out-of-sample prediction after that window.
- The orange area between them is the gap. It has stayed large since mid-2021.
- The two short horizontal segments on the right mark the average gap in 2025 (−35.8) and 2026 (−39.8).
- The grey band marks the pandemic months, where the model is not applied.

**Four takeaway cards.** The link at the bottom of each card opens the matching tab.

| Card | Number | Meaning |
| --- | --- | --- |
| 01 The gap | −35.8 / −39.8 | Average gap in 2025 and in 2026 so far, in index points. |
| 02 Survey and party | ≤ 2.7 | A plausible shift in the partisan mix of respondents moves the index by at most 2.7 points. The switch from phone to web interviews is associated with about −5.7 points in the headline index (p = 0.072, not significant). |
| 03 News tone | p = 0.23 | Once household and political controls are included, news tone adds no forecasting power (Clark–West p = 0.23; 0 of 20 specifications significant). At most about 5% of the 2025–26 gap is associated with tone. |
| 04 AI measurement | κ 0.73 | LLM coding of tone agrees with the human gold standard at κ 0.73; two human annotators agree with each other at 0.79. For relevance the figures are 0.86 and 0.81. Dictionary and keyword methods reach at most 0.39 on tone. |

**Chips at the bottom (data vintage)**

- For each source, the chips show the latest release used in this build and when it was published:
  - Data cutoff: 16 October.
  - Michigan: October preliminary, released 9 October.
  - Unemployment: August, released 4 September.
  - PCE prices: August, released 30 September.
  - GDP: 2026Q2, released 30 September.
- News is coded through October 2026. October is only half a month, so it is marked as a partial month.
- The chips also show the prompt version (label_prompt_v2 with its hash) and the coder: GPT 6 luna (Codex) with reasoning effort set to high.

---

## 2. Findings (five steps)

The orange box at the top is the key point for this tab. The gap is large, it persists, and every demographic group shows it. None of the explanations tested (survey mode, partisan mix, news tone) accounts for more than a small part of it.

The text card is on the left and the chart on the right. Move between steps with the buttons, the numbered step labels, or the ←/→ keys.

**Step 1: Sentiment vs model**

- This is the same chart as on the Overview, with the blue 95% prediction interval added. The interval comes from a moving-block bootstrap.
- Numbers to note:
  - 2025: actual ICS averaged 57.6; the model predicts 93.4.
  - 2026 so far: actual ICS averaged 51.2; the model predicts 90.9.

**Step 2: Size of the gap**

- This chart plots the gap itself.
  - The model sits on the zero line.
  - The orange line shows how far the actual value falls below the model.
  - The blue band is the prediction interval, centred on zero.
- The black segments are period averages:
  - 2021–22: −22.9.
  - 2023–24: −25.2.
  - 2025: −35.8.
  - 2026: −39.8.
- The 95% interval for a period average is roughly ±4 points, so −35.8 is far outside model error.
- Robustness across three estimation windows (2010–19, 2000–19 and 1978–19):
  - The 2025 gap ranges from −31.7 to −35.9.
  - The 2026 gap ranges from −33.0 to −40.3.
  - The 2021–22 gap depends heavily on the window (−10.1 to −25.1), so it is reported as a range.

**Step 3: Survey and party**

- The darker grey area is the web-interview period. April–June 2024 mixed phone and web interviews, and from July 2024 all interviews were on the web.
- The switch is associated with a drop of 8.0 points in the Index of Current Conditions (ICC, p < 0.001) and 5.7 points in the headline ICS (p = 0.072). The gap kept widening after interviews were fully on the web.
- A plausible change in the partisan mix of respondents moves the index by at most 2.7 points.
- In 2025, Republicans were 29 points below their own 2017–19 level, so the gap is not confined to one party.

**Step 4: News tone**

- The orange line is the gap.
- The purple line is national news tone: NYT and Guardian, about 26 relevant items a month, shown as a 3-month mean.
- Both series are standardised, so the axis is in standard deviations.
- Added to the three fundamentals alone, tone slightly improves one-month forecasts (p = 0.041).
- Once household-stress and political controls are in the model, tone adds nothing (p = 0.23; 0 of 20 specifications significant).
- At most about 5% of the 2025–26 gap is associated with tone.

**Step 5: By group**

- Each row of the dumbbell chart is one group, by income third, age, region or education. Each group's gap is measured against its own model.
- The hollow blue dot is the gap in July 2021 to December 2022. The solid orange dot is the gap in January 2025 to August 2026.
- In 2025–26, every group sits between 32.0 and 42.3 points below its own model, a spread of only 10.3 points.
- In 2021–22 the gaps were smaller and more uneven. For example, the 18–34 age group had almost no gap then.
- Conclusion: the remaining gap is broad and unexplained. Price levels, policy uncertainty and how individuals process information remain hypotheses for further work.

---

## 3. Sentiment

The orange box at the top is the key point for this tab. Compare the black line with the blue band: since July 2021 the headline index has been below the 95% band in 63 of 64 months. All three partisan groups are also below their own 2017–19 levels.

**Control bar (shared by the Sentiment and News tabs)**

| Control | What it does |
| --- | --- |
| Index: ICS / ICC / ICE | Switches between the headline index, current conditions and expectations. |
| Interval: 80% / 95% | Sets the width of the prediction interval. |
| News series: Monthly / 3-month mean | Shows news series as monthly values or as 3-month means. Monthly values are noisy. |
| Events | Chooses which events appear as small ticks under the time axis: survey-mode changes, elections, shutdowns, tariffs and trade, and FOMC statements. |
| Period: All / 2017– / 2021– / 2024– | Quick period presets. The default is 2017–. |
| Brush strip (thin chart with the orange gap) | Drag across it to pick any period. Every chart and number below updates to match. |

**KPI row.** Values are for the default period, January 2017 to October 2026, and change with the selected period.

| Shown | Meaning |
| --- | --- |
| ICS, Oct 2026 (preliminary) **46.3**; −43.4 vs model, model 89.7 | Sentiment, gap and model prediction for the last month in the period. |
| Mean ICS gap **−27.9** points; 66 out-of-sample months | Average gap over the out-of-sample months in the period. 2017–2019 is inside the estimation window, and pandemic months are excluded, so only January–February 2020 and July 2021 onward (66 months) count. That includes the smaller gaps of 2021–24, which is why this number is smaller than the 2025–26 gaps. |
| Months below the 95% band **63** of 66; first in view: Aug 2021 | Number of months in which sentiment was below the lower edge of the 95% interval, and the first such month in the period. |
| National news tone in view **−0.45** net tone; −0.07 vs 2010–19 mean −0.38 | Average net tone of national news in the period (share positive minus share negative). It is 0.07 below the 2010–19 average. |
| News items coded in view **7,831** items; 5,615 judged relevant | Number of items the LLM coded in the period, and how many it judged relevant to the economy. |

**Charts**

- **Michigan sentiment against the fundamentals model.** This is the main chart.
  - The black line is the selected index.
  - The blue line and band are the model and its interval.
  - The grey area at the right marks the web-interview period.
  - Coloured ticks below the axis are the selected events.
  - The card's key line says that since July 2021 the index has been below the 95% band in 63 of 64 months.
- **Gap: actual minus model.** This chart shows the gap only.
  - The orange line is the gap.
  - The blue band is the interval, centred on zero.
  - The thin grey line shows the 2010–19 fit residuals, so you can see how large normal model error is.
  - Key line: the gap averaged −22.9 in 2021–22 and −39.8 so far in 2026.
- **Partisans against their own 2017–19 level.**
  - Democrats, Independents and Republicans each have a line, showing sentiment relative to that group's own 2017–19 mean.
  - The top right shows the last month in the period. In August 2026: Democrats −39, Independents −49, Republicans −38.
  - The two parties swap places when the presidency changes hands. By 2025–26 all three groups are very low.
- **Events and elections in view.** Events of the selected types within the period, most recent first. Clickable items link to the original source, such as USTR, OPM or House records.

---

## 4. News

The orange box at the top is the key point for this tab. Look at tone and blame. After January 2025, coverage became more negative and more critical of the administration. But tone adds no forecasting power once household and political conditions are controlled for (see Tests).

The control bar and KPI row are the same as on the Sentiment tab.

**Tone of economic news and posts, by source**

- Net tone is the share of positive items minus the share of negative items, among items the LLM judged relevant, weighted by sampling design.
- Five sources can be switched on and off: national news (NYT and Guardian), other national outlets, local news, Reddit and YouTube comments.
- Hollow points mark thin months.
- The top right shows the month's value and sample size, for example −0.73 with n = 28 for national news in October 2026.
- Key line: coverage turned more negative in 2025–26, but no more than economic conditions predict (Tests, criterion 1).
- Local news text covers only 2025–26, and social media covers only recent years. Both are used for recent comparison only, not for estimation on 2010–19.

**Blame and credit for the administration**

- The orange line is the share of relevant national news items that blame the president or administration for economic conditions. The blue line is the share that gives them credit.
- The black horizontal lines show the average blame share in each administration:
  - Obama: 3% (2010–16).
  - Trump, first term: 19% (2017–20).
  - Biden: 6% (2021–24).
  - Trump, second term: 40% (2025–).
- Grey bands mark the Trump terms.
- The name-swap test found no coder bias, so this difference is not an artefact of the AI coding.

**Framing: which topics the coverage is about**

- Each row of the heat map is a topic, such as layoffs, rising prices or tariffs. Each column is a month. Darker cells mean a larger share of relevant items mention that topic, and an item can mention several topics.
- The selector at the top right switches the source.
- The key line lists the three largest topics for the month. In October 2026 these were rising prices 36%, gas prices 21%, and tariffs and trade 21%.

**Salience: estimated volume of relevant items**

- The number of relevant items in the full collection, estimated from the relevance rate in the coded sample. It measures how prominent the topic is.
- It uses the source chosen in the Framing chart.

**Factual calibration of quoted numbers**

- Each point is one numeric claim in national news about inflation, jobs, unemployment or GDP. Each claim is checked against the official value available on the publication date.
- The three rows are correct, wrong and unverifiable.
- The table below gives the totals:
  - National news: 68 claims checked, 66 correct and 2 wrong (2.9% error rate). Another 10 could not be verified.
  - Social media: 9 checked, all correct. Another 16 could not be verified.
- Rule: an inflation figure that does not say whether it is CPI or PCE counts as unverifiable. Claims from Reddit and YouTube are reported only as counts, and their text is not shown.

---

## 5. Measurement

The orange box at the top is the key point for this tab.

- The LLM agrees with the human gold standard about as well as two humans agree with each other: tone κ 0.73 vs 0.79, relevance 0.86 vs 0.81.
- No label changes significantly when names, parties or outlets are swapped (0 of 39 tests).
- Monthly series are noisy, so the analysis uses 3-month means.

**Corpus and coded sample (table)**

- For each source the table gives four numbers: items in the keyword-filtered collection, items the LLM coded, items it judged relevant, and the relevant share.
- Totals: 167,418 items collected, 11,431 coded and 7,681 relevant.
- 2,484 duplicates were removed and 21,188 syndicated copies were flagged.
- Reddit (55%) and the NYT (63%) have the lowest relevant shares. Keyword filtering alone is unreliable, which is why LLM coding first decides whether an item is relevant.

**National tone against the San Francisco Fed news index**

- Both lines are 3-month means, standardised: LLM-coded national news tone, and the San Francisco Fed Daily News Sentiment index.
- Three numbers on the right:
  - **Monthly reliability 0.61**, or 0.78 for 3-month means. This measures how stable the monthly index is.
  - **Correlation with the SF Fed index 0.37**, or 0.44 for 3-month means.
  - **Full-volume dictionary 0.54**: the correlation with the SF Fed index when a dictionary scores every item.
- The correlation is modest mainly because there are only about 26 relevant items a month. Small samples, not wrong judgements by the LLM, are the main cause.

**Coded items per month, by source**

- Each cell is the number of items coded for one source in one month. Darker cells hold more items.
- Hatched cells are months flagged as thin. Blank cells mean the source was not collected that month.
- Local news and social media cover only recent years. January 2026 is thin because only 1–7 January was collected for the NYT, and October 2026 is thin because it is a partial month.

**Agreement with the human gold standard (κ chart)**

- Each row is one coding dimension.
  - The solid black dot is the LLM's Cohen's κ on the 260-item test set. The prompt was tuned on the development set, then frozen, and the test set was scored once.
  - The hollow dot is the κ between the two human annotators.
  - The small grey ticks are the low-cost baselines: dictionaries, keyword rules and TF-IDF.
- Reference lines mark 0.6 ("substantial") and 0.8 ("almost perfect").
- LLM results:
  - Stronger dimensions: relevance 0.86, price framing 0.83, topics (mean of 13) 0.79, numeric claim 0.79, tone 0.73.
  - Weaker dimensions: political actor 0.67, perspective 0.63, time frame 0.59, factual direction 0.57, emotional intensity 0.56, attribution direction 0.56, definition error 0.47.
- For this reason the monthly index relies on tone and factual direction, and emotional intensity is used only as an auxiliary measure.

**Name and outlet swap test**

- The test swaps names or parties in the text, or labels the outlet as Fox News or MSNBC, then codes the item again. It measures how much more often a label changes than when the same text is simply coded again. That difference is the **excess flip rate**.
- There are three panels: names swapped, labelled as Fox News, and labelled as MSNBC. Each panel has 13 dimensions, and the bars are 95% intervals.
- Result: all 39 intervals include zero, so no bias was detected. Each group has only 30–40 items, so the test has limited power. The correct wording is "not detected", not "no bias".

---

## 6. Tests

The orange box at the top is the key point for this tab. Two of eight pre-registered criteria are triggered: criterion 2 (no out-of-sample gain) and criterion 6 (the news people recall follows the economy). Both count against news coverage as the explanation for the gap.

**Does lagged news tone improve one-month forecasts? (specification curve)**

- Each row is one specification: the main one plus 19 robustness variants. Examples of variants: ICC or ICE instead of ICS, the preliminary-release cutoff, dropping 2020, NYT only, the SF Fed index, and the policy uncertainty index (EPU).
- The horizontal axis is the Clark–West test p-value on a log scale. The grey area left of the 0.05 line is significant at 5%.
- Each row has two points:
  - **Hollow blue:** tone added to the three fundamentals only (M2 vs M1). The main specification has p = 0.041, and 9 of the 20 rows are significant.
  - **Solid orange:** tone added after household and political controls (M3 vs M1c). The main specification has p = 0.23, and none of the 20 rows are significant.
- Interpretation: the information in tone is largely already contained in the household and political variables.

**Which moves first, tone or sentiment? (local projections)**

- **Left panel (purple):** the response of sentiment over the next 0–6 months to a one-standard-deviation change in tone. It is about +0.06 to +0.07 SD in months 0–2, roughly one index point, then returns to near zero.
- **Right panel (black):** the response of tone to a change in sentiment. It is about +0.34 to +0.38 SD in months 4–5.
- Shaded areas are 95% intervals.
- "Avg" at the far right is the 0–6 month average response, which is the pre-registered test statistic. The one-sided p is 0.22 in both directions.
- Conclusion: both directions show only weak associations. Media do not lead sentiment in one direction only.

**Pre-registered falsification criteria (eight cards)**

The two triggered cards have a darker background and a black "Triggered" label.

| # | Criterion | Result | Verdict |
| --- | --- | --- | --- |
| 1 | Tone is explained by fundamentals | Residual tone since 2021 is +0.18 (p = 0.011), so coverage was less negative than fundamentals predict. In 2025–26 it is −0.01 (p = 0.45). | Not triggered. The sign runs against media bias. |
| 2 | No out-of-sample gain | M3 vs M1c: p = 0.23; 0 of 20 specifications significant. | **Triggered** |
| 3 | Sentiment leads media | Average 0–6 month response, one-sided: p = 0.22 forward and p = 0.22 reverse. | Not triggered. Media do not lead either. |
| 4 | Real pressures explain the gap | Adding household-stress variables leaves the gap almost unchanged, but these variables are not identified in 2010–19. | Not triggered (low power). |
| 5 | The gap is measurement or partisanship | Survey mode shifts ICC by about 8 points; partisan composition by at most 2.7 points. | Not triggered. |
| 6 | Recall follows the economy | For the share of respondents who heard unfavourable news, the unique R² is 0.21 for fundamentals and 0.14 for tone. | **Triggered** |
| 7 | No difference across groups | Party and age gaps do differ, but the differences closely follow party lines. | Not triggered. |
| 8 | Measurement is unstable | None of the 39 excess flip rates in the swap test is significant. | Not triggered. |

---

## 7. Update plan

The orange box at the top is the key point for this tab.

- Three releases come before Election Day: the final Michigan reading on 23 October, and GDP and personal income and outlays (PCE prices) on 29 October.
- The first Michigan reading after the election is on 6 November.
- Changes around the election cannot be attributed to the election alone.

**Release calendar, October to December 2026**

- Releases are listed by date: BLS employment reports and CPI, Michigan preliminary and final readings, and BEA GDP and PCE.
- Each release has a status tag. "In this build" means it is already included. "Scheduled" means it has not been released yet.
- Three marker rows are included: the data cutoff (16 October), today, and Election Day (3 November).

**How to update (five steps)**

1. Pull the new data on your own machine. The API keys are stored locally, and FRED/ALFRED cannot be reached from the cloud environment.
2. Run `sh src/process/run_all.sh` to rebuild the real-time panel, the corpus and the monthly media measures.
3. Code the new items with the frozen label_prompt_v2, using the same model and settings, in an isolated folder that holds only the prompt and the inputs.
4. Run `sh src/analysis/run_research.sh` to re-run the analysis with the pre-registered specifications. New months are reported as observations after the cutoff and are not used to re-tune anything.
5. Run `python3 src/dashboard/build.py` to rebuild the dashboard. The data vintage in the header updates automatically.

**Post-election review (grey box)**

- After the November and December Michigan readings, compare the gap and the news measures with two sets of months:
  - The months before the election.
  - The same months around the 2010, 2014, 2018 and 2022 midterms.
- Tariffs, prices, interest rates and the end of the 2025 shutdown all overlap with Election Day. Any change around it therefore cannot be attributed to the election alone.

---

## Footer

- The footer has a project description, the list of data sources and two reading notes:
  - The results are associations in observational data. The page does not claim that news coverage causes changes in sentiment.
  - Reddit and YouTube appear only as counts and averages, and their text is never shown. Headlines link to the publishers.
- The repository link is still the placeholder `[GitHub repository URL]`. It will be replaced once you send the address.
