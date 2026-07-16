---
title: "constraint margin must be normalized (J_C/d_k) -- absolute margin flips binding/slack"
tags: ["constraint", "margin", "binding", "J_C_d_k", "normalization", "ConstraintTRPO", "analysis-pitfall", "doc-sync"]
created: 2026-06-07T08:12:41.839480
updated: 2026-07-16T05:55:47.479346
sources: ["diagnose-20260606-194621", "diagnose-20260713-081707", "diagnose-20260714-084409"]
links: ["constrainttrpo_slack_tail_9_of_10_constraints_deep_slack_is_plau.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# constraint margin must be normalized (J_C/d_k) -- absolute margin flips binding/slack

NEVER read `Constraint/margin/<name>` absolute values to judge which constraint is binding vs slack. The 10 ConstraintTRPO constraints have budgets spanning 40x (attitude budget=0.01 -> d_k=1.0, thruster_util budget=0.40 -> d_k=40.0; d_k=budget/(1-cost_gamma), cost_gamma=0.99). A large absolute margin means a large BUDGET, not large headroom. You MUST normalize: J_C/d_k = 1 - margin/d_k (valid in the slack regime where `Constraint/viol/<name> == -Constraint/margin/<name>` exactly, i.e. adaptive floor not engaged; constraint_trpo.py:447/449). J_C/d_k near 1 = binding, near 0 = deep slack.

VERIFIED teacher (trpo_main_teacher_260525_232805, raw TB final-window w200, budgets from config.py:56-68):

| constraint | budget | d_k | margin | J_C/d_k | state |
|:--|--:|--:|--:|--:|:--|
| thruster_util | 0.40 | 40.0 | 5.208 | 0.870 | BINDING (only one near budget, slack 13%) |
| rp_vel_settling | 0.20 | 20.0 | 10.893 | 0.455 | mid |
| arm_torque | 0.08 | 8.0 | 4.742 | 0.407 | mid |
| rp_rate | 0.10 | 10.0 | 6.815 | 0.319 | mid |
| yaw_rate | 0.10 | 10.0 | 8.621 | 0.138 | slack |
| manipulability | 0.05 | 5.0 | 4.811 | 0.038 | slack |
| arm_joint_vel | 0.02 | 2.0 | 1.938 | 0.031 | slack |
| joint1_pos | 0.01 | 1.0 | 0.995 | 0.005 | deep slack |
| attitude | 0.01 | 1.0 | 0.997 | 0.003 | DEEPEST slack |
| cumul_yaw | 0.01 | 1.0 | 1.000 | 0.000 | fully inert |

THE TRAP (real incident, 2026-06-07 baseline co-review): teacher report.md:174,180 wrote "attitude/cumul_yaw sit near the 0 budget line (binding family)". This is BACKWARDS. attitude margin=0.997 looked small in absolute terms, but its d_k is also 1.0, so J_C/d_k=0.003 = DEEPEST slack, not binding. The actually-binding constraint is thruster_util (J_C/d_k=0.870). Root cause: margin read without dividing by d_k. The same pitfall is in the yaw finding page (cited yaw_rate margin=8.62 "largest of 10" as if it meant most slack -- it is mid at J_C/d_k=0.138).

CONSISTENCY: matches E6 (constraint_budget_x0_5_binds_only_thruster_util_authority_starva) which computed teacher thruster_util J_C/d_k=0.869 ~ 0.870 here. CMDP structure across runs = "1 dominant channel (thruster_util) + 9-long slack tail". teacher: thruster_util already binding-adjacent at budget=0.40 but still 0 violation, barrier penalty per-step 1.5% -> policy barely perturbed. E6 halved thruster budget -> over-bind -> authority starvation -> destructive.

IMPLICATION for "is the constraint inert?" questions: "all margins satisfied" (true: 10/10 viol<0) does NOT mean "all have headroom to spare". 9 do; thruster_util does not. The correct claim is "9 deep-slack inert + 1 binding-adjacent that holds 0-violation", NOT "all satisfied with room". This distinction governs constraint-rebalance experiment design: tightening a deep-slack channel (attitude) to shape attitude is the lever; tightening thruster (authority) is destructive (E6 proven).

ENGINE GAP: analyze_training.py `_constraint_margin()` (lines 370-379) returns absolute margin with NO d_k normalization. Fix delegated -- engine should emit J_C/d_k alongside margin. Until fixed, every report+wiki note hand-reads absolute margin and risks re-committing this flip.

---

## Update (2026-07-12T09:44:01.646060)

## UPDATE (2026-07-12): ENGINE GAP closed -- engine now normalizes

The "ENGINE GAP" recorded above ("analyze_training.py `_constraint_margin()` returns absolute margin with NO d_k normalization; fix delegated") is CLOSED. The delegated fix landed the same afternoon this page was created: commit `4ff9ea1` ("feat(engine): normalize constraint margin to J_C/d_k in TIER2 this-repo branch", 2026-06-07 17:27:21 +0900, ancestor of current HEAD).

Verified in the working tree (`.omx/profile/analyze_training.py`):
- `_constraint_binding_ratio` (`:416-430`) returns `1.0 - margin / d_k`.
- TIER2 output prints a `JC/dk=` column (`:809`) and flags the binding channel by max ratio (`:820-824`: "binding (max JC/dk): <name>; deepest slack: <name>").
- The low-level `_constraint_margin()` helper (`:370-379`) still returns the RAW absolute margin, but its consumer (`:803`) normalizes it before display -- so the engine output is normalized, only the helper is raw.
- Pinned by regression test `.omx/profile/test_constraint_margin_norm.py` (teacher ground truth thruster_util margin=5.208, attitude margin=0.997 -- matches the VERIFIED table above).

SHARED CAVEAT (manual formula AND engine `JC/dk` column): both consume the logged margin, which in the BINDING regime is frozen at alpha*d_k (adaptive floor engaged, alpha=0.05). So J_C/d_k is exact only in the slack regime and saturates at 1-alpha=0.95 for a genuinely-violating channel: a channel with true J_C/d_k>1 displays 0.95, not its real ratio. thruster_util at 0.870 < 0.95 is unaffected; the whole slack tail is exact. This limit was implicit before and is now stated.

DO NOT tell readers the engine lacks normalization -- it has since 4ff9ea1 (2026-06-07). The mirror doc `constrained-albc/docs/reference/constraints.md` §5 carried the same stale claim; its correction is delegated 2026-07-12.

---

## Update (2026-07-12T09:55:15.010878)

## UPDATE (2026-07-12, doc fix LANDED)

The mirror-doc correction that the prior update logged as "its correction is delegated 2026-07-12" is now DONE, not pending. `constrained-albc/docs/reference/constraints.md` §5 and its Korean mirror `constraints.ko.md` had the stale "the analysis engine still has this gap" sentence replaced with the normalized-engine description (commit `3a8a9bb`, branch `exp/latency-dr`). The new paragraph cites `_constraint_binding_ratio` (`:416-430`), the `JC/dk=` column (`:809`), the max-ratio binding flag (`:820`), the regression test, and the `1-alpha=0.95` saturation caveat -- consistent with this page. No pending delegation remains; doc and wiki now agree.

---

## Update (2026-07-16T05:55:47.479346)

## Update (2026-07-16): the trap RECURRED a 3rd time; the ENGINE GAP is now CLOSED

Two corrections to this page, found while re-reading the `teacher_baseline_opt` campaign for
next-experiment planning (2026-07-16 Q&A session).

### 1. Third recurrence — `teacher_baseline_opt` baseline report + campaign README

This page's THE TRAP section records the 2026-06-07 incident. It happened AGAIN, after this page
existed, in the last pre-fix report:

[FINDING] `teacher_baseline_opt/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md`
section 6 wrote "attitude / joint1_pos / cumul_yaw are the binding trio (margin ~1.0), the rest carry
large slack" -- BACKWARDS, the identical flip this page warns about. The campaign index
`teacher_baseline_opt/README.md` section 1a then propagated it verbatim
("최타이트 margin = attitude 0.994 / joint1_pos 0.997 / cumul_yaw 1.000, 나머지 slack 1.98-9.64").
The report even writes "every normalized margin > 0" while listing ABSOLUTE margins.
[EVIDENCE: diagnose-20260713-081707/report.md section 6 FINDING line; teacher_baseline_opt/README.md:46]
[CONFIDENCE: HIGH]

Recomputed for THAT run (budgets verified from its own `config/env.yaml`:533-580, cost_gamma=0.99
at env.yaml:582 -- identical to the config.py budgets this page already tabulates):

| constraint | budget | d_k | margin | J_C/d_k | state |
|:--|--:|--:|--:|--:|:--|
| thruster_util | 0.40 | 40.0 | 7.79 | 0.805 | BINDING (the only one) |
| rp_vel_settling | 0.20 | 20.0 | 9.64 | 0.518 | mid |
| rp_rate | 0.10 | 10.0 | 6.29 | 0.371 | mid |
| arm_torque | 0.08 | 8.0 | 7.29 | 0.089 | slack |
| manipulability | 0.05 | 5.0 | 4.64 | 0.072 | slack |
| yaw_rate | 0.10 | 10.0 | 9.44 | 0.056 | slack |
| arm_joint_vel | 0.02 | 2.0 | 1.98 | 0.010 | slack |
| attitude | 0.01 | 1.0 | 0.994 | 0.006 | deep slack (README called this "tightest") |
| joint1_pos | 0.01 | 1.0 | 0.997 | 0.003 | deep slack |
| cumul_yaw | 0.01 | 1.0 | 1.000 | 0.000 | fully inert |

Same CMDP structure this page documents for the 260525 teacher: 1 dominant channel (thruster_util)
+ a 9-long slack tail. The three the README calls "tightest" are the three LOOSEST.

CONSEQUENCE for readers of that campaign: `teacher_baseline_opt/README.md` section 1a's constraint row
is WRONG and the campaign is internally inconsistent -- e3's report (diagnose-20260714-084409 section 8)
has it RIGHT ("the binding constraint shifted to thruster_util (J_C/d_k 0.881, the closest to its
budget)") because the engine fix landed BETWEEN the two reports (07-13 -> 07-14). Do not cite the
baseline report's or the campaign README's "binding trio" claim.

### 2. ENGINE GAP is CLOSED (this page's last section is now stale)

[FINDING] The "ENGINE GAP: analyze_training.py `_constraint_margin()` returns absolute margin with NO
d_k normalization. Fix delegated" note is resolved. The engine now normalizes and the behaviour is
pinned by tests: `.omx/profile/test_constraint_margin_norm.py` asserts
`J_C/d_k = 1 - margin/(budget/(1-cost_gamma))` against the verified teacher table, requires a loud
failure when budgets cannot be resolved, and its docstring names the exact flip
("attitude margin=0.997 was misread as BINDING when it is the DEEPEST slack (J_C/d_k=0.003); the truly
binding channel is thruster_util (J_C/d_k=0.870)"). First report to consume the fix:
diagnose-20260714-084409 (e3).
[EVIDENCE: .omx/profile/test_constraint_margin_norm.py:1-12 docstring + _TEACHER table :29-41;
e3 report diagnose-20260714-084409 section 8 prints "J_C/d_k 0.881 binding"]
[CONFIDENCE: HIGH]

So the residual risk is no longer the engine -- it is HAND-READ margins in prose (campaign READMEs,
planning notes, wiki pages) and PRE-2026-07-14 reports, which still carry absolute values. When
reading any report dated on/before 2026-07-13, re-normalize before trusting any binding/slack claim.

### Cross-link

Snapshot normalization fixes WHO is binding; it does not fix WHEN. A deep-slack J_C/d_k at convergence
still does not mean the constraint never shaped training -- see
[[constrainttrpo_slack_tail_9_of_10_constraints_deep_slack_is_plau]], whose free TB-trajectory check on
this very run found 8/10 constraints near-binding during early exploration and only rp_vel_settling +
manipulability genuinely inert.

