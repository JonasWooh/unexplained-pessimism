# Results Overview (frozen version)

Frozen 2026-10-16. The data cutoff is 2026-10-16, and the Michigan October data are preliminary. This file only summarizes the frozen conclusions of each stage; details, tables, and sources are in each stage's `FINDINGS_stage<N>.md`.

- Design: `research/RESEARCH_DESIGN_v1.md`.
- Deviations and implementation details: `DECISIONS.md`.
- Specification registry: `results/spec_registry.csv`, 150 specifications in total, including all unfavorable results.
- Script hashes: `results/script_sha256.csv`.
- One-command rebuild: `sh src/analysis/run_research.sh`, which runs stages 1–5 in order.

## One-sentence conclusion

In 2025–2026, Michigan sentiment is about 36–40 points below the level that unemployment, inflation, and GDP can explain. This gap is robust to specification, window, and survey mode, is present across demographic groups, and had already formed before the election season. National news tone has a small but stable association with sentiment, but after controlling for household pressures and political variables it adds no out-of-sample forecasting increment; the part associated with tone accounts for at most about 5% of the gap. Media bias is not the main explanation of this gap.

## Six research questions

| Question | Conclusion | Main evidence |
| --- | --- | --- |
| RQ1 How to measure media bias | LLM coding is clearly better at the item level than dictionary methods and traditional classifiers (tone κ 0.73, LM dictionary 0.35). Name and source swaps detected no coder bias. Monthly index reliability is 0.62, with noise mainly due to the small number of items per month. Neither the media-side negativity asymmetry nor the selection asymmetry is robust; during Trump's second term, 40% of items blame the administration, but this cannot be directly identified as bias. National news cites official figures mostly accurately (2 errors among the 68 claims that name the indicator). | Stage 2 |
| RQ2 The effect of bias on sentiment | Tone has a brief positive association with sentiment (horizons 0–2), and sentiment also has a lagged association with later tone; the average responses in both directions are not significant. Topic correspondence in the recall pathway is clear, but fundamentals explain "heard unfavorable news" better. Tone coefficients do not differ between Democrats and Republicans. | Stages 3–4 |
| RQ3 How much fundamentals can explain | After 2023, they explain only 7%–11% of the decline in sentiment. The 2025–2026 gap is at least 23 points in absolute value under all three estimation windows and all robustness specifications; the 2021–2022 gap, by contrast, is sensitive to the window. | Stage 1 |
| RQ4 Measurable perception mechanisms | Negativity bias: not robust on either the media side or the sentiment side. Availability: the correspondence between price coverage and "price news heard" holds; gasoline and food have no additional explanatory power within the estimation window. Anchoring: not identifiable within the estimation window, with only compatible evidence, such as the mention rate of "worse off financially because of high prices" staying high after inflation eased. Confirmation bias: only compatible evidence (partisan jumps). | Stage 5, section 2 |
| RQ5 Whether media improves forecasts | Only a small improvement over the three-fundamentals model (RMSE down 0.9%, p = 0.041); after adding household and political controls, none of the 20 variants is significant. | Stage 3 |
| RQ6 Evidence refuting the media explanation | Item 2 (no out-of-sample increment) and item 6 (recall follows the economy more) are triggered. Items 1 and 3 are not triggered literally, but the direction of the evidence also does not support the media-bias explanation. | Stage 4, section 2 |

## Three groups of hypotheses

- **H1 Real pressures**: not identifiable in the main window, because cumulative inflation and the mortgage rate changed too little in 2010–2019; this is a lack of power and cannot be taken as evidence that these channels do not exist. In the exploratory 2000 window, cumulative inflation explains about a quarter of the gap; the mention rate of "because of high prices" remained very high in 2025–2026. H1 is an explanation that is not ruled out but that these data cannot confirm.
- **H2 Media selection, framing, and bias**: there are measurable media-side features, but their association with the gap is very weak; see RQ2 and RQ5 above. The main evidence does not support treating it as the main explanation.
- **H3 Measurement, timing, and model**:
  - Survey mode affects only ICC, by about 5–8 points, and the widening of the 2025–2026 gap took place within the web-only period.
  - The effect of partisan composition is no more than 2.7 points.
  - Window sensitivity affects only 2021–2022.
  - The bulk of the 2025–2026 gap cannot be attributed to these factors.

## What remains unexplained

The 2025–2026 gap has three features: it is not explained by any of the factors above; it is similar in size across income, age, region, and education groups; and Republicans are also far below their own baseline.

The project's data can rule out or bound several explanations: fundamentals, survey mode, partisan composition, the election season, and the increment from media tone. But they cannot determine the source of the remainder. Possible directions include:
- the price level itself (H1a);
- policy uncertainty such as tariffs;
- individual-level information processing.

These can only serve as discussion and directions for future research and cannot be written as conclusions. The causal design proposal is in `results/CAUSAL_DESIGN_PROPOSAL.md`.

## Limitations that must be stated in the report

- The observational analysis gives only temporal ordering and conditional correlation; the word "causes" is not used anywhere in the text.
- The national media measures come only from NYT and Guardian, with about 26 relevant items per month and a monthly reliability of 0.62. 2026-01 covers only days 1–7; 2026-10 runs only to 10-04.
- Social platforms and local news are described only for the recent period and do not enter the historical models.
- Factual calibration, the name-swap test, and the 2025–2026 by-period tests all have very small samples.
- The Michigan October final value (10-23) and the preliminary Q3 GDP estimate are not in this round's data. The November preliminary value is released after Election Day (11-03) and is listed in the plan for later updates.
