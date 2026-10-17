# personalfinance reduced sampling proposal (collection rules not yet switched)

This is a collection design proposal; it does not change the existing worker, checkpoints, or raw files. The goal is to reduce new body-text downloads and bring the monthly text volume of each subreddit to a similar order of magnitude. The count-check snapshot is in personalfinance_sampling_proposal_counts.json.

## Basis for the check

In the 13 months already fully obtained, comparing the same months and the same three UTC dates, economy averaged 211.38 items per month, Economics 102.77 items per month, and personalfinance 827 items per month. The months are 2025-01 to 10 and 2026-08 to 10; 2026-10 runs only to the research cutoff. The mean of the two core subreddits is about 157.08 items, so it is proposed to fix in advance a personalfinance target of about 150 expected items per month. This comparison does not prove that all historical years have the same post density.

## Sampling rules

1. Keep the seed 20261015 and the three existing uniform random UTC dates per month; dates are fixed before the text is obtained and are not redrawn because of the number of records on the day, API responses, content, or existing inventory.
2. Obtain the source aggregate total post count N for the month and the number of observable days D (the number of calendar days in a normal month; the cutoff month only runs to the cutoff). When N is missing, fill in the source count first; do not invent a denominator or infer it from other years.
3. Target T=150; set the time window length on each drawn day to L=min(86400, round(86400*D*T/(3*N))) seconds. When N=0, record it as a source count of zero and do not fabricate records. For small historical months where the expected number from three whole days is still below 150, take those three whole days, and do not repeatedly redraw to pad the count.
4. For each drawn day, use a separate, reproducible random stream to draw a start point uniformly from 0 to 86399 seconds. The random stream is Python random.Random('20261015|personalfinance|date|circular_window_v1'). On the day's 24-hour circle, keep the L seconds after the start point; when this crosses midnight, split it into two non-overlapping intervals at the start and end of the drawn day; the part that crosses the boundary must not simply be discarded, nor moved to the next day.
5. Pull only these time windows, and obtain all selected intervals in full; when the API returns a full page, obtain everything using the original exact interval bisection rule; do not truncate to only the first few items in time order, and do not use reaching 150 items as a stopping condition. Existing complete raw files can be used to generate the selection list with the same time predicate, without re-downloading or modifying the raw files.
6. For each subreddit-month, record N, D, T, L, the three dates, the random start points, the actual time intervals, raw file paths, the number of items obtained, and the inclusion probability. The reporting standard becomes "drawn time window complete", which must not be written as "complete whole day". The original whole-day inventory is still kept and listed separately, and must not be mixed with the new sample and counted twice.

## Randomness and boundaries

Given fixed N, D, and L, every source post has the same marginal inclusion probability under this design, p=(3/D)*(L/86400). The expected monthly item count is N*p, about 150; the rounding error is very small, and the cap on L makes the expected count for low-density months fall below 150. The uniform start point on the circle ensures that times near midnight have the same inclusion probability as daytime times. It is still two-stage cluster sampling of random dates plus random time windows, with posts in the same window entering the sample together; it is not simple random sampling of a fixed 150 individual posts. Drift in the source count snapshot will affect the expected item count, and draws should not be quietly changed or padded.

## Volume and speed

Compared with the old three-whole-day design, which averaged 827 items in the checked months, the new target of 150 items reduces the expected text volume by about 82%. The measured totals for 2026-08/09/10 are 6167/5362/2243, corresponding to windows of about 6.03/6.71/7.49 hours per drawn day; it is not assumed that a uniform four hours in all years would achieve the same sample size. Each month usually issues 3 to 6 base time-interval requests, saturated intervals continue to be bisected exactly, and there are also monthly count requests. Request speed is also affected by timeouts and backoff, so the time taken cannot be guaranteed to fall by the same 82%.

## API basis

The official Arctic Shift project API documentation provides time range, ascending/descending order, and field selection, and lists no random ordering option: https://github.com/ArthurHeitmann/arctic_shift/blob/master/api/README.md . Therefore this plan uses time windows selected at random in advance to reduce actual downloads, rather than calling the first page in time order a random sample.

Exclusion of author fields, keeping retrieved_on, never overwriting raw files, a single worker, rate limits, the cap on consecutive failures, and not using hashes all carry over.
