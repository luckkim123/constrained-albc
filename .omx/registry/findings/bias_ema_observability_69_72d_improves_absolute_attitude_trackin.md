---
title: "bias_ema observability (69->72D) improves absolute attitude tracking + CV but does NOT shrink the hard-DR heavy-tail ratio -- the DC-bias tail is authority-limited (p7_tail e2)"
tags: ["bias_ema", "observability", "use_bias_ema_obs", "heavy-tail", "authority-limited", "dc-bias", "cv", "absolute-tracking", "p7_tail", "e2"]
created: 2026-07-13T13:47:17.565874
updated: 2026-07-13T13:47:17.565874
sources: ["experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e2_biasobs_260713_173456/analysis/diagnose-20260713-223534/report.md"]
links: ["bias_reward_bias_ema_penalty_theory_review_conditionally_sound_h.md", "teacher_hard_dr_cv_explodes_without_heavy_tail_dc_bias_dispersio.md", "eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr.md"]
category: decision
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# bias_ema observability (69->72D) improves absolute attitude tracking + CV but does NOT shrink the hard-DR heavy-tail ratio -- the DC-bias tail is authority-limited (p7_tail e2)

Probe result for the "make the penalized bias_ema state observable" hypothesis
([[bias reward bias_ema penalty theory review]] flagged bias_ema is penalized in reward
but not in obs -- punished for an unseen quantity). e2 (use_bias_ema_obs=True, appends 3
bias_ema components -> 69D->72D) vs consolidated baseline, run trpo_e2_biasobs_260713_173456.

OUTCOME split by metric family:
- ABSOLUTE tracking: large gain. att_norm hard ss_error 0.723->0.398 (-45%), roll hard
  0.529->0.305, pitch 0.379->0.187; matched-none 0.532->0.249 (2.1x); jitter ~-40% all levels;
  hard att_norm CV 2.13->1.40. Delivered on a HARDER exam (e2 curriculum inertia_scale Beta-std
  0.396 vs baseline 0.268, 1.47x wider) -- so the gain is understated, not a confound artifact.
- HEAVY-TAIL RATIO: unchanged. per-env median|error_roll| max/median 25.8x (bl 23.2x), top-6/64
  45.8% (bl 48.7%) -- both in the proposal's H2 authority-limited band (>=18x, >=45%), NOT H1's
  (<=12x, <=38%). So observability did NOT close the DC-bias heavy-tail.

VERDICT: H2 on the literal discriminating criterion -- the DC-bias hard-DR tail is a
capability/authority (or DR-shaping) limit, NOT a credit-assignment gap observation can close.
BUT H1's MECHANISM is validated: making the penalized state observable clearly helped absolute
tracking + dispersion. The max/median ratio is a weak lens here (roll is DC-bias dispersion, not
a fat-tail per [[teacher hard-DR: CV explodes without heavy-tail]]; the ratio is inflated by a
tiny median -- e2 absolute max 3.785 < baseline 4.802).

CAVEAT: transient per-env peak|error_roll|>20deg count rose 3->6 (all in first 0.2-0.7% of the
trajectory = startup overshoot, not steady-state) -- confirm it is not a new oscillation before
adopting bias_ema obs into the baseline.

IMPLICATION: bias_ema obs is a keeper for absolute tracking/CV, but does NOT deliver the p7_tail
tail-shrink goal -- point the remaining tail probes at DR-shaping (xyprune) / actuation-side
levers / more curriculum pressure, NOT at more observability. Cross-run hard is run-relative
(see [[eval.py static --doraemon-dr grades each run on its OWN learned DR]]); e2's wider
curriculum makes its wins a lower bound.
Source: report experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e2_biasobs_260713_173456/analysis/diagnose-20260713-223534/report.md
