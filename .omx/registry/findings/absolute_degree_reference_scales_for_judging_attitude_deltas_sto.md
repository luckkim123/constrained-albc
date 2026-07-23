---
title: "Absolute-degree reference scales for judging attitude deltas (stop reading percentages on a small base)"
tags: ["methodology", "significance", "attitude", "threshold", "auto-captured", "trpo_buoyanchor_s30_260722_134743"]
created: 2026-07-23T04:55:17.458948
updated: 2026-07-23T07:32:14.143051
sources: ["diagnose-20260723-134359", "experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md"]
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Absolute-degree reference scales for judging attitude deltas (stop reading percentages on a small base)

REFERENCE: this repo has no accuracy specification, so attitude deltas must be judged against the three degree-valued scales that DO exist in the source, not against percentages on a small base. (1) actor's own euler OBSERVATION noise sigma: _OBS_NOISE_STD euler = 0.02 rad = 1.146 deg (envs/main/config.py:271). (2) euler observation BIAS band the policy must tolerate: _OBS_BIAS_MAG = +/-0.02 rad = +/-1.146 deg (config.py:292). (3) the only degree-valued THRESHOLD in the codebase: rp_vel_settling activation gate 0.087 rad = 5.0 deg (mdp/constraints.py:222) -- note this is a cost ACTIVATION gate, not an accuracy spec. WORKED EXAMPLE (2026-07-23): the buoyfix retrain 'deficit' of +0.110 deg on none roll ss_error, adverse on 3/3 seeds, is 9.6% of one sigma of (1) -- statistically consistent, physically negligible. The same run's plant gain of -3.934 deg on roll os_env_mean is 78.7% of (3) -- large. Reading only the percentages (+28% vs -20%) inverts the importance. This generalises the CORRECTION already applied to tam_plant_correctness_fix, whose 'robustness-for-accuracy' framing was a percentage-on-small-base artifact (~20:1 in the fix's favour once restated in degrees). Re-visit: analysis diagnose-20260723-134359 section 'tracking'.

---

## Merged from restated_in_absolute_degrees_against_this_repo_s_own_reference_s.md (2026-07-23T07:32:14.143051)

# Restated in absolute degrees against this repo's own reference scales, the retra

Restated in absolute degrees against this repo's own reference scales, the retrain cost is negligible and the plant gain is large. This is the correction the `tam_plant_correctness_fix` wiki page already applied once to a percentage-framed claim on a small base. - retrain `roll.ss_error` +0.110 deg = **9.6%** of one obs-noise sigma - retrain `pitch.ss_error` +0.117 deg = 10.2% of one sigma - plant `roll.os_env_mean` -3.934 deg = **78.7%** of the 5-deg settling gate

[EVIDENCE: `config.py:271` `_OBS_NOISE_STD` euler = 0.02 rad = 1.146 deg; `config.py:292` `_OBS_BIAS_MAG` euler = +-0.02 rad; `constraints.py:222` `rp_vel_settling` gate = 0.087 rad = 5 deg]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md

---

## Update (2026-07-23T06:44:07.820188)

Restated in absolute degrees against this repo's own reference scales, the retrain cost is negligible and the plant gain is large. This is the correction the `tam_plant_correctness_fix` wiki page already applied once to a percentage-framed claim on a small base. - retrain `roll.ss_error` +0.110 deg = **9.6%** of one obs-noise sigma - retrain `pitch.ss_error` +0.117 deg = 10.2% of one sigma - plant `roll.os_env_mean` -3.934 deg = **78.7%** of the 5-deg settling gate

[EVIDENCE: `config.py:271` `_OBS_NOISE_STD` euler = 0.02 rad = 1.146 deg; `config.py:292` `_OBS_BIAS_MAG` euler = +-0.02 rad; `constraints.py:222` `rp_vel_settling` gate = 0.087 rad = 5 deg]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md
