# Read-only check of the professor's Excel file

The original file was not modified. The calculations below are only for confirming the data definitions and completeness; this is not an analysis dataset. Units are percentage points.

| Definition | Alignable months | Mean absolute error | Maximum absolute error | Months with error no greater than 0.01 |
|---|---:|---:|---:|---:|
| headline | 584 | 0.53754305 | 2.25331113 | 4 |
| core | 584 | 0.00000348 | 0.00001351 | 584 |

Comparison formula: 100 × (index for the month in the same latest vintage / index 12 months earlier − 1). The match supports the core PCE definition, with the precision shown in the table above; it cannot be judged to be headline PCE from the column name alone. Historical revisions may affect exact value-by-value matching.

- The consumer sentiment monthly CSV can be matched for 585 months; 585 months agree. The latest month in the CSV is 2026-09. The saved official homepage was also checked; it is explicitly labeled Preliminary Results for October 2026: ICS=46.3, which agrees with the professor's table value 2026-10=46.3. It is a preliminary value and must not be mixed with final values. The official calendar release date is 2026-10-09, and the October final value is scheduled for release on October 23. Evidence: data/raw/S05/20261015/homepage.html, source https://www.sca.isr.umich.edu/ .
- UNRATE 2025-10 has 1 vintage record in total, of which 0 have non-missing values; a missing-value marker is not a usable observation.
- The latest non-missing observation of the GDP quarter-over-quarter annualized rate is 2026-04; the Excel value 2026Q3=3.7 is not recorded as a measured value, and its source cannot be confirmed from it.
- Official website ICS 2022-06=50.0; 2026-05=44.8.
