# AI Measurement Validation (R3.4–R3.6)

- Model: declared by the project lead as GPT 6 luna in Codex, reasoning effort high (default), fixed throughout (`labels/ai/model_declaration.json`). In the run log `labels/ai/run_log.csv`, the model name and settings are recorded as "not visible" and are kept as is. Temperature cannot be set.
- Prompts: `prompts/label_prompt_v1.md` (SHA256 26365ac8…); `prompts/label_prompt_v2.md` (SHA256 9f95f20a…) frozen. The hashes of all prompt copies used in runs have been checked and match.
- Gold standard: `labels/adjudicated.csv`. Gold-standard items with relevant = unsure are not counted in the relevant metrics.
- Scoring script: `src/annotation/score_ai.py`. Results by dimension, by class, and by source are in `*_metrics.csv` and `*_per_class.csv`.

## Development set (100 items, used to choose the prompt version)

The dimension-by-dimension comparison of v1 and v2 is in `dev_v1_vs_v2.csv`. Mean κ across the 10 coding dimensions: v1 0.652, v2 0.670. v2 was frozen under the "development-set mean κ" rule.

## Test set (260 items, run only once after freezing v2)

| Dimension | n | Accuracy | κ | Macro F1 | Human A–B κ |
|---|---:|---:|---:|---:|---:|
| relevant | 236 | 0.94 | 0.86 | 0.93 | 0.81 |
| tone_overall | 174 | 0.85 | 0.73 | 0.81 | 0.79 |
| fact_direction | 174 | 0.70 | 0.57 | 0.63 | 0.72 |
| emotional_intensity | 174 | 0.74 | 0.56 | 0.72 | 0.59 |
| price_frame | 174 | 0.90 | 0.83 | 0.82 | 0.93 |
| perspective | 174 | 0.85 | 0.63 | 0.54 | 0.78 |
| time_frame | 174 | 0.74 | 0.59 | 0.70 | 0.82 |
| numeric_claim | 174 | 0.91 | 0.79 | 0.89 | 0.86 |
| definition_error | 174 | 0.74 | 0.47 | 0.48 | 0.77 |
| actor_1 | 174 | 0.75 | 0.67 | 0.56 | 0.83 |
| direction_1 | 174 | 0.68 | 0.56 | 0.67 | 0.78 |

(Human A–B κ is computed on all 360 items; see `labels/agreement_summary.csv`.)

- Topics: 10 of 13 have κ ≥ 0.70; gasoline prices 0.60, economic growth 0.63, other 0.54.
- Results by source are in `codex__v2_isolated_r1_test_metrics.csv`. κ for relevant: NYT 0.90, Reddit 0.83, local 0.72, Media Cloud national 0.54 (n = 11). κ for tone ranges from 0.63 to 0.76.
- Format: all 260 items were returned, with no invalid values, and all 1,315 evidence excerpts can be found verbatim in the original text.
- Self-consistency: 26 random test-set items were rerun in an independent context (`codex__v2_isolated_r2`). Agreement rates: relevant 0.92, tone 0.85, factual good/bad 0.85, emotional intensity 0.69, price framing 0.88, perspective 0.81, time frame 0.73, numeric claim 0.92, concept error 0.85, actor 0.77, direction 0.88.

## Not yet completed (belongs to the research stage)

- Comparison with dictionary methods and TF-IDF + logistic regression (R3.5)
- Swap test of political figures' names and source labels (R3.7)
