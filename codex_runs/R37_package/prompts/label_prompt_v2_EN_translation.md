> English translation of the frozen prompt `codex_runs/R37_package/prompts/label_prompt_v2.md`, a copy of `prompts/label_prompt_v2.md` (SHA-256 in `prompts/label_prompt_v2.sha256`). The model received the original file, which mixes English and Chinese; this translation is for reading only.

# Labeling prompt v2

You are labeling short texts about the US economy for a research project. Apply the codebook below exactly as written.
The codebook is in Chinese with English label values; the texts are in English.

## Procedure (mandatory)
1. Read each input item yourself and decide every label by applying the codebook to that item's `text`
   (use `context` only to understand a video comment; label the comment itself).
2. Do NOT write or run any code, keyword rules, regular expressions or heuristics that assign labels.
   Do NOT look up the items online. Each label must come from your own reading of the item.
3. Judge each item independently. Do not use any information about the source; none is given.
4. For every non-null label except `relevant`, give a verbatim evidence quote copied exactly from `text`
   (or from `context` for comments, prefixed with "context: "). Use "" only when the label is "none"/"no"/"no_fact"/"0"/"not_applicable".
5. If `relevant` is "no", set every other label to null and `evidence_quotes` to {}.

## Output format
Write exactly one JSON object per input item, one per line (JSONL), in the same order as the input, with these keys:

```json
{
 "item_id": "<copied from input>",
 "relevant": "yes|no|unsure",
 "tone_overall": "...",
 "fact_direction": "...",
 "emotional_intensity": "0|1|2",
 "topics": [
  "T03_prices_rising",
  "..."
 ],
 "price_frame": "...",
 "perspective": "...",
 "time_frame": "...",
 "numeric_claim": "yes|no",
 "claim_text": "verbatim numeric statements separated by \"; \" or \"\"",
 "definition_error": "...",
 "actor_1": "...",
 "direction_1": "...",
 "actor_2": "... or null",
 "direction_2": "... or null",
 "evidence_quotes": {
  "tone_overall": "...",
  "fact_direction": "...",
  "emotional_intensity": "...",
  "topics": "...",
  "price_frame": "...",
  "perspective": "...",
  "time_frame": "...",
  "definition_error": "...",
  "actor_1": "...",
  "actor_2": "..."
 }
}
```

Allowed values:
- relevant: yes, no, unsure
- tone_overall: negative, neutral, positive, mixed
- fact_direction: bad, good, neutral, mixed, no_fact
- emotional_intensity: 0, 1, 2
- topics: list of: T01_layoffs_unemployment_up, T02_hiring_jobs_growth, T03_prices_rising, T04_inflation_easing, T05_economic_growth, T06_recession_risk, T07_interest_rates_borrowing, T08_housing_costs, T09_gas_prices, T10_food_prices, T11_tariffs_trade, T12_stock_market, T13_other (at least one; use T13_other if none fits)
- price_frame: level, rate, both, none
- perspective: national, household, both, none
- time_frame: current, forecast, both, none
- numeric_claim: yes, no
- definition_error: yes, no, not_applicable
- actor_1 / actor_2: president_admin, congress, fed, democrats, republicans, business, foreign_trade, other, none (actor_2 may be null)
- direction_1 / direction_2: credit, blame, neutral_mention (null when the actor is none or null)

## Clarifications added in v2 (from development-set review; definitions in the codebook are unchanged)

- emotional_intensity: use 0 only when the wording is purely factual. Any evaluative, loaded or alarm-carrying word
  (for example "struggle", "pain", "fears", "slump", "surge", "squeeze", "hit hard", "worrying", "tough") makes it at least 1.
  Use 2 only for strong or extreme language, as in the codebook examples.
- time_frame: choose "both" whenever the text describes present or recent conditions AND contains any expectation,
  forecast, plan, warning or "will / could / likely / expected to" statement about the economy. Choose "current" or
  "forecast" only when the other is entirely absent.
- perspective: choose "both" when the text has the aggregate, market or policy level AND any concrete household,
  person or consumer experience (including quoted individuals, or families/consumers described as experiencing the condition).
- fact_direction: an announced or reported economic event (layoffs, a price increase, a tariff taking effect, a rate decision)
  is a fact. Use "no_fact" only when no economic fact is stated at all (pure opinion, a question, a joke).
  Use "mixed" when facts that are good and facts that are bad for households are both reported.
- actors: when the text links an economic condition or outcome to an actor's action (a company cutting jobs or raising prices,
  an agency or official making a decision), record that actor with credit, blame or neutral_mention according to the wording.
  Use "none" only when no actor is connected to the economic content.

---

# Codebook (verbatim)

## 1. Annotation unit

Each row is one unit. Judge it only from the text given in the `text` column:

| unit_type | Content |
|---|---|
| headline + abstract + lead paragraph | News headline + abstract + lead paragraph |
| headline + abstract | News headline + abstract (from 2025 on, this source no longer provides the lead paragraph) |
| headline + standfirst + first 100 body words | News headline + standfirst + first 100 words of the body |
| headline only | News headline only |
| forum post (title + body, first 1,200 chars) | Forum post title + first 1,200 characters of the body |
| video comment (top-level) | A single comment under a video |

The `context` column appears only for video comments (it holds the video title). It helps you understand what the comment is about, but **the object of annotation is the comment itself**, not the video title. `[...]` means the rest of the text was truncated; do not guess what the truncated part says.

---

## 2. Step 1: Is it related to the US economy (`relevant`)

| Value | Rule |
|---|---|
| `yes` | The text conveys information, opinions, or first-hand experience about **US** economic conditions or economic policy: prices and inflation, employment and the labor market, growth and recession, interest rates and borrowing costs, housing costs and rent, tariffs and trade, consumer sentiment, or evaluations of these conditions. |
| `no` | Does not meet the condition above. |
| `unsure` | You still cannot decide after reading; write the reason in `notes`. Use as rarely as possible. |

**Boundary rules**
- Personal finance questions (budgeting, credit scores, filing taxes, whether to buy a particular fund) count as `yes` **only** when they mention economic conditions themselves, for example "rent has gotten absurdly high these days" or "you just can't find a job in this job market". Questions that only ask about personal planning and do not touch on economic conditions count as `no`.
- Pure stock market moves (a particular stock rising or falling, index levels) count as `no`; if the text links the stock market to the economic outlook, recession, interest rates, etc., it counts as `yes`.
- Text mainly about another country's economy counts as `no`; text about the effect of foreign policy on the US economy (e.g., tariffs on the US) counts as `yes`.
- Keywords that appear with an unrelated meaning (e.g., "rent a car", personal names, sports) count as `no`.
- Obituaries, advertisements, sponsored content, and event announcements count as `no`.

**When `relevant = no`, leave all other columns in the row blank.** When `unsure`, fill in the other columns as usual.

---

## 3. Dimension 1: Tone

### 3.1 `tone_overall`: overall tone of the text itself
| Value | Rule |
|---|---|
| `negative` | Overall, the wording and presentation make economic conditions seem bad or worrying, or are critical |
| `positive` | Overall, makes conditions seem good; optimistic, approving |
| `neutral` | Plain, matter-of-fact statement with no clear leaning |
| `mixed` | Both positive and negative sides are present, with comparable weight |

### 3.2 `fact_direction`: whether the **reported facts themselves** are good or bad news for US households
| Value | Rule |
|---|---|
| `bad` | E.g., the unemployment rate rising, prices rising, mortgage rates rising, layoffs |
| `good` | E.g., inflation easing, wages rising faster than prices, more hiring |
| `neutral` | The facts are not clearly good or bad for households, e.g., the Fed holds rates unchanged, with no evaluation |
| `mixed` | Both good and bad facts are reported |
| `no_fact` | Only opinions, emotions, or questions; no economic facts are stated |

### 3.3 `emotional_intensity`: strength of emotional wording
| Value | Rule |
|---|---|
| `0` | No emotional wording |
| `1` | Mild, e.g., "worrying", "tough", "good news" |
| `2` | Strong, e.g., "skyrocketing", "collapse", "nightmare", "insane", all caps, multiple exclamation marks |

**Separate facts from emotion (they must be judged separately)**:
- "Unemployment rose to 4.3% in July." → `fact_direction = bad`, `emotional_intensity = 0`, `tone_overall = negative` or `neutral` (depending on the wording; a plain statement of data is usually `neutral`).
- "Prices are absolutely insane, I can't afford anything anymore!!!" → `fact_direction = bad`, `emotional_intensity = 2`, `tone_overall = negative`.
- "Inflation cooled again, but economists warn the fight isn't over." → `fact_direction = good`, `tone_overall = mixed`, `emotional_intensity = 0` or `1`.

---

## 4. Dimension 2: Selection and salience (Topics, multiple selection allowed)

Among the 13 columns below, enter `1` for each topic the text **explicitly addresses**, and leave the others blank. Select at least one; if none fits, enter `1` in `T13_other`.

| Column | Topic |
|---|---|
| T01_layoffs_unemployment_up | Layoffs, rising unemployment |
| T02_hiring_jobs_growth | Hiring, job growth |
| T03_prices_rising | Rising prices, high cost of living |
| T04_inflation_easing | Inflation easing, price increases slowing |
| T05_economic_growth | Economic growth, GDP |
| T06_recession_risk | Recession, risk of an economic slowdown |
| T07_interest_rates_borrowing | Interest rates, borrowing costs, Fed rate decisions |
| T08_housing_costs | Home prices, rent, housing affordability |
| T09_gas_prices | Gasoline prices |
| T10_food_prices | Food and grocery prices |
| T11_tariffs_trade | Tariffs, trade policy |
| T12_stock_market | Stock market |
| T13_other | Other economic topics |

A word that only appears in passing does not count as "addressing" a topic; the text must actually be discussing that topic.

---

## 5. Dimension 3: Framing (three independent axes)

### 5.1 `price_frame`: which kind of description is used when the text talks about prices
| Value | Rule |
|---|---|
| `level` | Price level: "how much more expensive than before", "groceries cost twice what they did" |
| `rate` | Inflation rate or speed of price increases: "inflation slowed to 3%", "prices rising faster" |
| `both` | Both are present |
| `none` | Does not talk about prices |

Note: "inflation is down" is `rate`; "prices are still way higher than 2020" is `level`. A falling inflation rate does not mean falling prices.

### 5.2 `perspective`: perspective
| Value | Rule |
|---|---|
| `national` | National aggregates, macro data, the market or policy level |
| `household` | First-hand experience of households or individuals, the situation of specific people |
| `both` | Both are present |
| `none` | Neither |

### 5.3 `time_frame`: time
| Value | Rule |
|---|---|
| `current` | Current or just-occurred conditions |
| `forecast` | Forecasts, expectations, worries or judgments about the future |
| `both` | Both are present |
| `none` | Neither (e.g., a purely historical review) |

---

## 6. Dimension 4: Factual calibration

Annotators do only two things here; the item-by-item check against the official data of the time is done by the analyst, using the data vintage available at release (ALFRED).

### 6.1 `numeric_claim` and `claim_text`
- `numeric_claim = yes`: the text contains a numeric statement about a US economic indicator (unemployment rate, inflation rate, GDP growth, interest rates, home prices, gas prices, jobs added, etc.).
- When it is `yes`, copy every numeric statement verbatim into `claim_text`, separated by `;`. Example: `unemployment rose to 4.3% in July; 114,000 jobs added`.
- Numbers about personal income or personal bills ("I make $50k") do not count; enter `no`.

### 6.2 `definition_error`: conceptual or definitional error
| Value | Rule |
|---|---|
| `yes` | There is a clear conceptual error, e.g., describing "inflation falling" as "prices falling"; confusing year-over-year and month-over-month changes; treating another unemployment measure as U-3; treating a preliminary figure as final in a way that contradicts the meaning of the text |
| `no` | Economic statistical concepts are mentioned, but no error was found |
| `not_applicable` | No economic statistical concept is mentioned |

When unsure, enter `no` and explain in `notes`.

---

## 7. Dimension 5: Political attribution

Whether economic conditions (good or bad) are attributed to an actor. Record at most two: `actor_1` / `direction_1`, `actor_2` / `direction_2`. When there is no attribution, set `actor_1 = none` and leave the rest blank.

| actor value | Meaning |
|---|---|
| `president_admin` | The president or the administration (including a named president, the White House, the cabinet) |
| `congress` | Congress |
| `fed` | The Federal Reserve |
| `democrats` | The Democratic Party or Democrats |
| `republicans` | The Republican Party or Republicans |
| `business` | Businesses, companies, industries |
| `foreign_trade` | Foreign governments or trading partners, foreign policies |
| `other` | Other (unions, state governments, etc.; specify in notes) |
| `none` | No attribution |

| direction value | Meaning |
|---|---|
| `credit` | Credit: attributes a good economic outcome to the actor |
| `blame` | Blame: attributes a bad economic outcome to the actor |
| `neutral_mention` | Mentions the actor as connected to economic conditions, without giving credit or blame |

**Criticism is not bias.** Record only what the text says; whether it amounts to bias is judged at the analysis stage by comparison with a benchmark. Do not take the source's leaning into account when labeling.

Example: "Trump's tariffs are driving up grocery prices" → `actor_1 = president_admin`, `direction_1 = blame`.
Example: "The Fed held rates steady on Wednesday." → `actor_1 = fed`, `direction_1 = neutral_mention`.

---
