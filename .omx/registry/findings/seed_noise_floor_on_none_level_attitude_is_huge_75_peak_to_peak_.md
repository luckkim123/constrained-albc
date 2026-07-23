---
title: "Seed-noise floor on none-level attitude is HUGE (~75% peak-to-peak on roll ss_error): the +/-5% adoption band is undecidable at n=1"
tags: ["seed-floor", "none-band", "methodology", "variance", "adoption-criterion", "albc", "teacher", "seed", "floor", "paired-seed", "scoping", "audit", "auto-captured", "trpo_buoyanchor_s30_260722_134743"]
created: 2026-07-22T04:04:07.570011
updated: 2026-07-23T07:32:14.143051
sources: ["diagnose-20260723-134359", "teacher-campaign-plan.md#11", "experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md"]
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

---

## Update (2026-07-23T04:55:41.753704)

UPDATE 2026-07-23 -- the 75% figure is the OLD plant; the corrected plant measures 56.0%. The headline 74.8% was measured on seed_floor_dgx (main@9de2da1, PRE-buoyancy-recentre plant, DGX-trained): none roll ss_error 0.4499 / 0.3074 / 0.2090, mean 0.3221, p2p 74.8%. The same three seeds retrained on the CORRECTED plant (teacher_baseline_buoyfix, workstation) measure 0.4967 / 0.2786 / 0.3934, mean 0.3896, CV 22.9%, p2p 56.0%. The DESIGN CONCLUSION IS UNCHANGED -- 56% is still ~11x the +/-5% adoption band, so single-seed verdicts stay undecidable and paired-seed (same seeds for anchor and intervention, within-seed delta) remains mandatory. Only the quoted number moves. Planning documents that say '~75% on the current plant' are wrong: quote 56.0% for the post-buoyfix plant and keep 74.8% attributed to the old one. Other none-level floors on the corrected plant, same 3 seeds: pitch ss_error 89.8% p2p, roll os_env_mean 26.2%, roll n_gt20 24.8%, roll rise_time 39.3%, yaw os_env_mean 187.0%. Re-visit: analysis diagnose-20260723-134359 section 'tracking'.

---

## Update (2026-07-23T07:08:18.136272)

SCOPE CORRECTION from the 2026-07-23 validity audit (SSOT section 11.4 D3): this page's floor is UNPAIRED (cross-seed) and must NOT be used to judge PAIRED same-seed same-machine comparisons. The Stage-A runs were already paired (all 10 posttam runs carry seed: 30, verified in every train/params/agent.yaml), so the earlier sentence on this page calling "EVERY single-seed Stage-A tracking verdict undecidable by construction" over-reaches: under the paired analysis A4's +73.6% (+0.158 deg, 3.5-4x the paired scatter bound, coherent across roll+pitch+CV) is a DECIDABLE FAIL, and A5's +16.8% (+0.036 deg) is NULL by the PAIRED floor, not by this unpaired one. What remains true and unchanged: the +/-5% band is dead under every floor; paired-seed design is the correct screening method; this floor governs UNPAIRED designs and seed-generalization claims. Two hard limits the paired design keeps: (a) pairing survives only WITHIN one machine (same config + same seed cross-machine measured +109% on roll ss_error: dgxseed30 vs biasema); (b) the same-machine paired repeatability floor is unmeasured (n=3 scatter bound 16.8%; a repeat run is proposed, human-gated). Screening/adoption/paper protocol now lives in the eval-metric-units-and-decision-floors convention page and SSOT section 11.6.

---

## Merged from the_seed_noise_floor_on_the_corrected_plant_is_56_0_peak_to_peak.md (2026-07-23T07:32:14.143051)

# The seed-noise floor on the corrected plant is 56.0% peak-to-peak on `none` `rol

The seed-noise floor on the corrected plant is 56.0% peak-to-peak on `none` `roll.ss_error` — not the 74.8% figure carried in the planning documents, which is the OLD-plant `seed_floor_dgx` measurement. - NEW plant (anchor): 0.4967 / 0.2786 / 0.3934 — mean 0.3896, CV 22.9%, p2p 56.0% - OLD plant (`seed_floor_dgx`): 0.4499 / 0.3074 / 0.2090 — mean 0.3221, p2p 74.8%

[EVIDENCE: `summary.json` none/roll/ss_error]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md

---

## Update (2026-07-23T06:44:07.820188)

The seed-noise floor on the corrected plant is 56.0% peak-to-peak on `none` `roll.ss_error` — not the 74.8% figure carried in the planning documents, which is the OLD-plant `seed_floor_dgx` measurement. - NEW plant (anchor): 0.4967 / 0.2786 / 0.3934 — mean 0.3896, CV 22.9%, p2p 56.0% - OLD plant (`seed_floor_dgx`): 0.4499 / 0.3074 / 0.2090 — mean 0.3221, p2p 74.8%

[EVIDENCE: `summary.json` none/roll/ss_error]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md
