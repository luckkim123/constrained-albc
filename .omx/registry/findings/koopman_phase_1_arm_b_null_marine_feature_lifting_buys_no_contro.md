---
title: "Koopman Phase 1 arm B NULL: marine-feature lifting buys no control quality and costs transient overshoot"
tags: []
created: 2026-08-04T17:21:41.875932
updated: 2026-08-04T17:55:05.321505
sources: []
links: ["roll_transient_is_worst_at_none_dr_and_improves_monotonically_as.md"]
category: decision
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: resolved
---

# Koopman Phase 1 arm B NULL: marine-feature lifting buys no control quality and costs transient overshoot

[FINDING] Koopman Phase 1 arm B (marine-feature observation lifting, obs 72->79) is NULL against
its pre-registration and the Koopman line is CLOSED. It is not a flat null: it is a DR-level-dependent
trade whose heavy tail gets monotonically WORSE as the exam gets EASIER.

Run `trpo_koopmanB_260804_202709` (4096 env, 5000 iter, seed 30, branch `exp/koopman-marine-obs`
e865f0b), eval `static_260805_020809`, against the E-int teacher `trpo_eint_s30_rs2350_260727_195102`
model_4999.

PAIRING: 24/24 dr+fault keys elementwise identical at all four DR levels, against BOTH the
pre-registered GPU0 baseline `static_260804_143234` and the same-device GPU1 reproduction
`static_260804_203719`. The two baselines return the same verdict with deltas differing by less than
0.001, so the cross-device concern raised by the floors' own "paired same-machine" protocol string is
empirically moot here. Survival is 100.00 pct at every level in both runs, so no accuracy delta is
survivorship-contaminated.

PRE-REGISTERED VERDICT (fixed 2026-08-04 before any code existed): ADOPT iff ss_error improves past
the 0.10 deg floor on >=2 of 4 DR levels AND os_env_mean stays within 10.0 pp AND n_gt20 within 15.

- Condition 1 FAILS. att_norm ss_error improves at `hard` only (1.0120 -> 0.8017) and REGRESSES at
  `medium` (0.4664 -> 0.5671). One level, not two, and the wrong sign elsewhere.
- Condition 2 FAILS. roll n_gt20 at `none` goes 0.00 -> 20.33 envs against a floor of 15.

=> NULL. Do not adopt. Close the line per `koopman-lifting/PLAN.md` section 8 exit clause 2.

THE SHAPE IS THE INTERESTING PART. roll n_gt20 baseline -> armB by level:
none 0.00 -> 20.33, soft 0.33 -> 8.33, medium 1.00 -> 5.00, hard 5.00 -> 6.67. The regression is
LARGEST at nominal physics, where the baseline was perfect, and smallest at hard. A policy that fails
most at the easiest condition is not trading nominal precision for robustness; something about its
transient is wrong.

MECHANISM: transient, not steady-state. At `none` the steady-state error is unchanged
(0.4037 -> 0.4003) while overshoot `os_env_mean` rises 7.96 -> 13.74 pp and pitch `rise_time` slows
0.441 -> 0.544 s (+23 pct). The 20 offending envs peak between 20 and 40 deg (n_gt40 = 0.00
everywhere), i.e. large overshoot on the way to a correct steady state.

[EVIDENCE: os_env_mean is worse in 8 of 8 (level x axis) cells -- roll none 7.96->13.74, soft
8.00->12.80, medium 8.98->11.87, hard 9.39->11.97; pitch none 9.45->10.82, soft 8.48->10.30, medium
8.22->10.20, hard 8.32->9.76. Largest single delta +5.78 pp, all UNDER the 10.0 pp per-cell floor.
Consistent in sign across every cell while no cell clears its own floor -- the decision floors are a
per-cell noise test and do not aggregate, so a systematic regression of this shape passes them
silently. Read the sign pattern, not only the flags. Code-exec 2026-08-05 from the two summary.json
files named above.]
[CONFIDENCE: HIGH]

WHY THIS IS A RESULT AND NOT A NON-EVENT: the pre-registered expectation was null-to-small, on the
argument that a 2-layer MLP can already represent these pointwise functions. That expectation is MET.
Handing the network sin/cos of roll and pitch plus the three quadratic rate terms p|p|, q|q|, r|r| --
functions it can already build internally -- bought no control quality and cost transient behaviour.
This is evidence about THIS dictionary at 5000 iters, single seed, on the current plant. It is not
evidence about Koopman lifting in general, and the page should not be cited as if it were.

RETRY COST, so a future session does not re-derive it: arm C (the control-set arm) was estimated at
>=15 GPU-h and is not scheduled. Phase 2 does not open.

---

## Update (2026-08-04T17:55:05.321505)

## 2026-08-05 -- this transient shape is a KNOWN pattern, and that makes the arm B result sharper

Cross-referenced after the verdict was recorded. The inverted roll transient described above --
worst at `none`, improving as DR hardens -- is not new to arm B. It is already on the wiki as
[[roll_transient_is_worst_at_none_dr_and_improves_monotonically_as]] (2026-07-21, HIGH confidence,
observed in two runs, mechanism still UNEXPLAINED), which concluded it is "a property of the policy
family, not of any one intervention."

That page's numbers are `roll os_env_mean`: A3 none 21.486 -> hard 14.730, anchor none 17.022 ->
hard 14.172. Both inverted.

The current plant does NOT show it. E-int's own `roll os_env_mean` runs none 7.96 / soft 8.00 /
medium 8.98 / hard 9.39 -- the ordinary direction, harder plant = worse transient -- while arm B
reads 13.74 / 12.80 / 11.87 / 11.97, inverted, and at a magnitude close to the 2026-07-21 runs.

So the correct statement about arm B is NOT "it has a strange transient". It is that **arm B
re-acquired a transient shape the current policy family had lost**, against a same-plant,
24/24-paired baseline that does not have it. The 2026-07-21 pattern was observed on posttam-era
runs, so the "the current baseline lost it" half is a cross-plant observation and is weaker; the
"arm B has it and its paired baseline does not" half is controlled and is the claim that matters.

This strengthens the NULL rather than softening it: the marine-feature lifting did not merely fail
to help, it moved the policy back toward a transient regime this project has been trying to explain
since July. That page's own follow-up -- nominal-corner exposure via a DORAEMON nominal sampling
floor -- remains a deferred training-side experiment and is not unblocked by this.
