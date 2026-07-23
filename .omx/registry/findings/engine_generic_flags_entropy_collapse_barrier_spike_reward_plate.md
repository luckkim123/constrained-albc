---
title: "engine generic flags (entropy-collapse / barrier-spike / reward-plateau) are benign for a converged teacher"
tags: ["analyze_training", "diagnosis", "entropy", "barrier", "plateau", "clip_fraction", "auto-captured", "trpo_buoyanchor_s30_260722_134743"]
created: 2026-07-12T23:46:27.626318
updated: 2026-07-23T07:32:14.143051
sources: ["diagnose-20260713-081707", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md", "experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md"]
links: []
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# engine generic flags (entropy-collapse / barrier-spike / reward-plateau) are benign for a converged teacher

analyze_training.py emits three generic-heuristic DIAGNOSIS flags that fire on a HEALTHY converged teacher and must NOT be read as defects without a code-exec cross-check: (1) 'entropy collapse -> exploration dead' fires because entropy goes negative at convergence (expected) — cross-check Policy/clip_fraction: if |a|>=1 saturation is low (baseline 0.005) the policy is NOT saturating actions, so exploration is fine (this is also the Lead-2 init_noise_std gate datum). (2) 'reward plateaued last 30% / converged early' fires when reward saturates while DORAEMON keeps hardening DR — cross-check DORAEMON/success_rate (baseline ~0.47, still climbing) + entropy_before rising = curriculum still advancing, not a stall. (3) 'barrier penalty spikes >0.1' fires on Constraint/barrier_penalty magnitude alone — cross-check vs Reward/total (baseline -0.127 = ~1.6% of 7.74) and Constraint/margin/* (all >0 = satisfied); small vs reward + margins satisfied = benign. Rule: an engine generic flag is a HYPOTHESIS; confirm/deny with the paired code-exec metric before writing it as a finding. Evidence: analysis diagnose-20260713-081707.

---

## Merged from the_engine_s_entropy_collapsed_noise_std_low_flags_fire_for_a4_e.md (2026-07-23T07:32:14.143051)

# The engine's `entropy COLLAPSED / noise_std LOW` flags fire for A4 exactly as fo

The engine's `entropy COLLAPSED / noise_std LOW` flags fire for A4 exactly as for the anchor and A3, confirming again that this diagnosis is a constant of the config family and carries no per-run information.

[EVIDENCE: `analyze_training.py --tier 3 --deep` TIER 1, A4 entropy -9.00 / noise 0.09 vs anchor -9.07 / 0.09]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md


---

## Merged from a3_shows_3_barrier_penalty_spikes_max_0_505_against_the_anchor_s.md (2026-07-23T07:32:14.143051)

# A3 shows 3 `barrier_penalty` spikes (max 0.505) against the anchor's 0, but thes

A3 shows 3 `barrier_penalty` spikes (max 0.505) against the anchor's 0, but these are not constraint events — the tag logs the LAST line-search candidate including rejected backtracks, and line search succeeded 100% of the time, so a positive isolated reading is a rejected-candidate artifact.

[EVIDENCE: `analyze_training.py` barrier_penalty last=-0.1268 spikes=3 max=0.505 vs anchor last=-0.1244 spikes=0; Policy/line_search_success = 1.0000 for A3; documented TB-tag trap for Train/barrier_penalty]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md


---

## Merged from the_engine_flags_entropy_collapsed_noise_std_low_for_both_runs_s.md (2026-07-23T07:32:14.143051)

# The engine flags `entropy COLLAPSED / noise_std LOW` for BOTH runs, so that diag

The engine flags `entropy COLLAPSED / noise_std LOW` for BOTH runs, so that diagnosis is a fixed property of this config family (per-dim floors + 0.003 entropy coef) and does not discriminate A3 from the anchor; A3 is in fact the less-collapsed of the two.

[EVIDENCE: `analyze_training.py --tier 3 --deep` TIER 1 block, A3 entropy -7.22 / noise 0.10 vs anchor -9.07 / 0.09, both tagged COLLAPSED/LOW]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md


---

## Merged from the_engine_s_diagnosis_block_reports_reward_plateau_in_every_run.md (2026-07-23T07:32:14.143051)

# The engine's `DIAGNOSIS` block reports reward plateau in every run. "Reward conv

The engine's `DIAGNOSIS` block reports reward plateau in every run. "Reward converged early (Q1-Q2) then plateaued. DORAEMON may be expanding DR too slowly." Additionally on s31 / s32 / Arm N / dgxseed30: "Reward plateaued in last 30% of training." `phase: warmup(1)->plateau(7)`, `plateau: YES since ~5-15%`, `stability cv=0.012`.

[EVIDENCE: engine `DIAGNOSIS` lines, all 7 runs]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md

---

## Update (2026-07-23T06:44:07.820188)

The engine's `DIAGNOSIS` block reports reward plateau in every run. "Reward converged early (Q1-Q2) then plateaued. DORAEMON may be expanding DR too slowly." Additionally on s31 / s32 / Arm N / dgxseed30: "Reward plateaued in last 30% of training." `phase: warmup(1)->plateau(7)`, `plateau: YES since ~5-15%`, `stability cv=0.012`.

[EVIDENCE: engine `DIAGNOSIS` lines, all 7 runs]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md
