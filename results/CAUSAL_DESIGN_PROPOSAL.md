# Causal Design Proposal (report appendix, not implemented)

2026-10-16. Based on the "Causal inference" section of `research/RESEARCH_DESIGN_v1.md` (D5: observational analysis + causal design proposal). The project's observational results (stages 3 and 4) can give only temporal ordering and conditional correlation. The three designs below set out what data and assumptions are needed to turn "the way media report affects consumer sentiment" into an identifiable causal question. None of the three is implemented in this project.

## Constraints that the observational results place on the design

- Stage 3: after controlling for household pressures and political variables, tone has no out-of-sample increment. The share of the gap associated with tone is at most about 5%, which is an upper bound on the association.
- Stage 4: in terms of temporal ordering, both directions are significant only at some horizons. Topic correspondence in the recall pathway is very clear, but fundamentals explain "heard unfavorable news" better. Tone coefficients do not differ between Democrats and Republicans.
- Stage 2: after inflation eased, price-level wording declined, but the weight of price coverage stayed high; during Trump's second term, 40% of items blame the administration. The name-swap test detected no AI coding bias.

The experiment therefore should not answer a question that already has a large literature, such as "does negative news lower sentiment", but rather: given the same set of real data, does the **wording** (price level or inflation rate, household perspective or national aggregate) change how respondents answer the Michigan questions? This is exactly what the project's observational data cannot distinguish.

## 1. Randomized framing experiment (main proposal)

**Treatment groups** (five groups; all groups are shown the same set of real official data for the same month, with no deception):

| Group | Wording | Example key point |
| --- | --- | --- |
| A Balanced summary (control) | Inflation rate, unemployment rate, and GDP side by side, without evaluation | "Over the past 12 months prices rose [π]%, the unemployment rate is [U]%, and GDP grew at an annualized [g]%" |
| B Price level | Emphasizes the cumulative increase relative to before the pandemic | "Compared with early 2020, prices have risen a cumulative [P]%" |
| C Inflation rate | Emphasizes the year-over-year increase and the direction of its change | "Inflation has fallen from its 2022 peak of [π_peak]% to [π]%" |
| D Household perspective | The same numbers converted into household spending | "A typical household spends [$X] more per month on food and housing than in 2020" |
| E National aggregate | The same numbers placed in a national-aggregate narrative | "The U.S. economy has grown for [k] consecutive quarters, and employment stands at [N] million" |

The numbers in square brackets are filled in at implementation with the latest official releases for the month of the experiment. The factual content of the five groups must be identical and checked by someone not involved in setting the hypotheses.

**Outcome variables**
- The five index questions of the Michigan Surveys of Consumers, with original wording and order, scored using the official relative-score method.
- One-year inflation expectations (original question).
- Pre-registered secondary outcomes: "whether the respondent recently heard unfavorable news about the economy", and a manipulation check (whether the respondent can restate the key points of the material read).

**Sample size**
- With d = 0.2, two-sided α = 0.05, and power 0.8, each group needs 394 people (two-sample independent t-test, 393.4 rounded up). The five groups total 1,970 people.
- With a Bonferroni correction for 10 pairwise comparisons (α = 0.005), each group needs 668 people, 3,340 in total.
- There are only 4 pre-registered main comparisons (B, C, D, and E each against A). With a Holm correction, the required sample falls between the two.
- d = 0.2 is the conventional "small effect". The observational association in stage 3 is very small, and the actual effect may be smaller still: if the true effect is d = 0.15, each group needs about 700 people.

**Analysis plan**
- Main estimate: OLS of the outcome on treatment dummies, with HC2 robust standard errors. Covariates (partisanship, age, income, education, region, baseline economic assessment) are pre-specified and used only to improve precision.
- Pre-registered heterogeneity: partisanship (corresponding to H3b), and self-reported frequency of news exposure.
- Exclusion rule: respondents who fail the attention check are excluded by a rule fixed in advance, and results without exclusion are reported as well.

**Ethics and procedure**
- Pre-register on OSF or AsPredicted before the experiment.
- Obtain informed consent and IRB approval.
- After completion, tell respondents the full official data sources.
- All materials are truthful wordings of real data, so no deception is needed and no partisan figures are involved.

**Limits to external validity**
- A one-time reading differs from long-term news exposure, and the effect may decay. A follow-up measurement one week later can be added for part of the sample to estimate the retained share, which corresponds exactly to ρ in section 3.
- An online sample, even with quota sampling, still needs CPS weighting.

## 2. Quasi-experimental ideas

**A. Local newspaper closures**
- Treatment: an area's only daily newspaper closes or stops printing. The treatment date is the closure date, and the controls are comparable areas without closures over the same period.
- Estimation: staggered difference-in-differences, using an estimator robust to staggered treatment, such as Callaway–Sant'Anna. Outcome variables are area-level consumer sentiment and inflation expectations.
- Assumptions and threats:
  - Closures often happen in areas whose economies are already declining, so pre-trends must be tested.
  - Spillovers: readers may shift to national media or social platforms.
  - Stage 2 of this project found local news less negative than national news (net tone difference +0.37), so the expected sign is: after a closure, local sentiment moves closer to the level under the national news environment.

**B. Sinclair acquisitions of local TV stations**
- Treatment: after a Sinclair acquisition, local stations raise the weight of national political and economic coverage and their content converges toward nationally uniform scripts. This is documented in the literature; see Martin & McCrain (2019, APSR).
- Estimation: also staggered difference-in-differences, with treatment as completion of the acquisition and the unit as the television market (DMA).

**Data gaps common to both**
- Michigan public data cover only the four census regions, with no state or market identifiers. One must apply for restricted geographic variables, or switch to another survey with state or county identifiers and a large enough sample.
- A matchable dataset of local coverage content is needed to demonstrate the "first stage", that is, that the treatment actually changed the coverage that local audiences were exposed to. The project's local news corpus covers only 2025-03 to 2026-09, which is not enough for this.

## 3. From sample effects to the national index (R4.6)

Even if the experiment identifies a single-exposure wording effect τ, it cannot be converted directly into points on the national index. The approximate relationship is:

ΔICS_national ≈ Σ_g w_g × e_g × τ_g × ρ_g

- w_g: the weight of group g in the national population, using CPS weighting.
- e_g: the share of group g actually exposed to this kind of wording during a period before the survey. This needs population-level exposure estimates, for example a panel with media-use logs; content analysis alone cannot provide it.
- τ_g: the single-exposure effect for group g, that is, the heterogeneity estimate from the experiment, which must be converted to index points.
- ρ_g: the share of the effect still retained from exposure to the time of the interview, from the experiment's follow-up measurement.

**Required assumptions**
- The wording in the experiment is comparable to real coverage.
- The effect transfers from the experimental sample to the population.
- The effects of repeated exposures can be summed. The last is the hardest to sustain, so the report should give sensitivity ranges for ρ and for the aggregation method.

**Example** (only to illustrate the magnitude conversion, not an estimate): with e = 0.5, τ = 0.1 standard deviations, and ρ = 0.3, the national effect is about 0.015 standard deviations, or about 0.2 points given an ICS standard deviation of about 15 points. Only when both the exposure share and the retained share are very high could a wording effect reach an appreciable share of the gap (about 36–40 points). This is consistent in magnitude with the stage 3 finding that "the share associated with tone is at most about 5%".
