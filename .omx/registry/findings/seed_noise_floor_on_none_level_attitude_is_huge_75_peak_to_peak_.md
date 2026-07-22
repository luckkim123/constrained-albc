---
title: "Seed-noise floor on none-level attitude is HUGE (~75% peak-to-peak on roll ss_error): the +/-5% adoption band is undecidable at n=1"
tags: ["seed-floor", "none-band", "methodology", "variance", "adoption-criterion", "albc", "teacher"]
created: 2026-07-22T04:04:07.570011
updated: 2026-07-22T04:04:07.570011
sources: []
links: []
category: convention
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# Seed-noise floor on none-level attitude is HUGE (~75% peak-to-peak on roll ss_error): the +/-5% adoption band is undecidable at n=1

MEASURED 2026-07-22 from 3 DGX seeds (30/31/32, group seed_floor_dgx, main@9de2da1, IDENTICAL config, ONLY --seed differs -- verified). All eval.py static, none DR level, canonical eval/static_*/summary.json. Do NOT compare to the workstation anchor (different GPU).

none-level spread = (max-min)/mean across the 3 seeds:
| metric           | seed30 | seed31 | seed32 | mean   | spread% |
|------------------|--------|--------|--------|--------|---------|
| roll ss_error    | 0.4499 | 0.3074 | 0.2090 | 0.3221 | 74.8%   |
| pitch ss_error   | 0.2791 | 0.1993 | 0.1703 | 0.2162 | 50.3%   |
| roll os_env_mean | 23.40  | 19.52  | 16.31  | 19.74  | 35.9%   |
| roll CV          | 61.4   | 55.4   | 27.2   | 48.0   | 71.3%   |
| pitch CV         | 29.9   | 40.5   | 18.6   | 29.7   | 73.6%   |
| yaw CV           | 11.1   | 15.9   | 25.6   | 17.5   | 82.6%   |

THE SEED-NOISE FLOOR on none-level attitude is ~75% peak-to-peak on roll ss_error (+/-37% as a half-range), 50% on pitch. roll ss_error alone spans 0.209->0.450, a 2.15x range, from seed ALONE.

CONSEQUENCE (this is the finding, not a failure): the campaign's '+/-5% of anchor' adoption band has NO measured provenance (confirmed: no wiki page ever derived it) and is DESTROYED by this measurement -- the floor is ~15x the band. EVERY single-seed vs single-seed Stage-A tracking verdict (A1-A5) read at +/-5% is UNDECIDABLE by construction: the intervention deltas (A3 +26%, A4 +74%, A5 +17% on none roll) are all INSIDE one seed's noise band. A4's +73.6% 'catastrophic' roll regression is within seed-to-seed range; A5's +16.8% is trivially inside -> A5 resolves NULL.

The band MUST be re-derived before any future adopt/discard call. Options: (a) multi-seed cells (>=3 seeds/arm, compare means with the measured floor as the error bar), or (b) a paired-seed design (same seed for anchor+intervention, compare within-seed deltas which cancel the seed term). n=3 and (max-min)/mean is a crude high-biased spread estimator, but even conservatively a 2.15x roll range obliterates a +/-5% band. Caveat: this floor is at the workstation eval GPU on these DGX-trained checkpoints; the mechanism (RL seed variance in a heavy-tail-at-hard policy family) is plant-independent.
