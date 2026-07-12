---
title: "Session state 2026-07-12: constraint deep-dive (Q&A) -- covered structure/prob-avg/reward-cost-parallel/classification/thresholds; 2 wiki pages + constraints.md 3.2/3.4/4.3/4.6 + 1 PROMPT; pending 5/9"
tags: ["session-log", "constraint", "deep-dive", "resume-marker", "2026-07-12"]
created: 2026-07-12T08:29:32.109454
updated: 2026-07-12T08:29:32.109454
sources: []
links: ["reward_md_deep_dive_session_2026_07_11_4_review_fix_prompts_queu.md", "reward_cost_parallel_structure_mostly_mirroring_two_real_couplin.md", "constraint_threshold_budget_tuning_thresholds_split_into_hard_ph.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Session state 2026-07-12: constraint deep-dive (Q&A) -- covered structure/prob-avg/reward-cost-parallel/classification/thresholds; 2 wiki pages + constraints.md 3.2/3.4/4.3/4.6 + 1 PROMPT; pending 5/9

Interactive constraint deep-dive (Q&A mode, user asks / assistant explains from code; fixes go
to .sp/plans PROMPTs, knowledge goes to docs + omx wiki). Sister to the 2026-07-11 reward.md
deep-dive [[reward_md_deep_dive_session_2026_07_11_4_review_fix_prompts_queu]]. This page is the
resume marker so a post-compaction session knows what was covered and what remains.

## Covered (constraints.md walked section by section)

- §1 structure: 3-layer (definitions / IPO optimization / wiring), optimizer has ZERO prob-vs-avg
  branches.
- §2 prob/avg taxonomy: theoretically a correct CMDP reduction (prob = average constraint on a
  {0,1} indicator). "No distinction" true only at optimizer-logic level; numerical layer
  (std floor min=1.0) is implicitly binary-aware; prob constraints are gradient-dark in deep slack
  (explains §9 inert attitude/cumul_yaw).
- reward/cost PARALLEL structure: justified mirroring, NOT lazy reuse. Two real couplings found ->
  [[reward_cost_parallel_structure_mostly_mirroring_two_real_couplin]] + PROMPT (triage).
- §3 classification + hard-rail vs soft-shaping thresholds + actuator hard-cap layering ->
  [[constraint_threshold_budget_tuning_thresholds_split_into_hard_ph]].
- avg-max = time-averaged soft-peak (theoretically fine).

## Artifacts produced this session (all persisted)

1. omx wiki (2 new pages, both quality 100):
   `reward_cost_parallel_structure_mostly_mirroring_two_real_couplin.md`,
   `constraint_threshold_budget_tuning_thresholds_split_into_hard_ph.md`.
2. docs/reference/constraints.md (+ .ko mirror): §3.2 (max soft-peak), §3.4 NEW (threshold
   provenance / actuator layering), §4.3 (feasibility = GAE-return estimator coupling), §4.6
   (separate critics + shared grad-clip coupling).
3. .sp/plans/PROMPT_constraint_reward_cost_parallel_coupling_triage.md (confirm-then-fix work
   order for the two couplings; NOT git-tracked, /workspace is not a repo).

## Pending / not yet done

- constraints.md §5 (margin normalization J_C/d_k) and §9 (which constraints actually bind) were
  NOT yet walked in Q&A -- natural next topics if the deep-dive resumes.
- cumul_yaw 8*pi -> 6*pi: user intent = cosmetic (a). Recorded as a behavioral NO-OP (peak ~1.22
  rev << 3 rev); NO fix-prompt created, NO functional change queued. Rides a future config touch.
- The two reward/cost couplings are (C)-tentative; the PROMPT gates any code change on runtime
  evidence (value-group grad-norm split; GAE-return vs raw-MC feasibility).

## Branch / commit state

Work done on branch exp/latency-dr. constraint_trpo.py / _policy_base.py cites verified against
disk (exp/latency-dr) this session; the reward.md branch-stale caveat is rewards.py-specific and
does NOT affect the constraint_trpo.py cites. Doc + wiki changes committed at compaction-prep.

