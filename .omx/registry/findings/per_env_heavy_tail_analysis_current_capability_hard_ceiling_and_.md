---
title: "per-env heavy-tail analysis: current capability, hard ceiling, and what fault-tolerant-control research needs added"
tags: ["heavy-tail", "per-env", "fault", "fault-tolerant", "thruster-failure", "sensor-noise", "joint-fault", "dr_snapshot", "eval-npz", "research-direction", "infrastructure"]
created: 2026-06-14T04:36:22.611736
updated: 2026-06-14T04:36:22.611736
sources: []
links: ["engine_gap_eval_npz_saves_no_raw_obs_std_privileged_blocks_exact.md", "state_dependent_std_difficulty_null_now_confirmed_on_real_dr_med.md", "heavy_tail_vs_sample_mean_divergence_are_independent.md"]
category: reference
confidence: high
schemaVersion: 1
---

# per-env heavy-tail analysis: current capability, hard ceiling, and what fault-tolerant-control research needs added

# per-env heavy-tail analysis: current capability, hard ceiling, and what fault-tolerant-control research needs added

Scopes the existing per-env heavy-tail tooling against a planned fault-tolerant-control (FTC) research direction (thruster failure / sensor noise / joint malfunction robustness). Code-verified 2026-06-14. The motivation: a heavy-tail (most envs fine, a minority catastrophically failing) is structurally the SAME problem as FTC worst-case guarantees -- "keep it from moving abnormally even under fault" = bounding the tail. So FTC robustness can reuse the heavy-tail analysis frame, IF the fault becomes a measured per-env axis.

## What EXISTS today (per-env heavy-tail tooling)
- `constrained_albc/analysis/_eval_dr/dr_snapshot.py:per_env_dr_from_tensors()` records each env's POST-CLAMP physics DR as a `dr_<name>[N]` schema (linear_damping, added_mass diagonal, cog/cob offset, payload/body mass). Wired into eval.py:578 (`_read_per_env_dr`) -> :686 (`**per_env_dr`) -> `data_<level>.npz`.
- `.omx/profile/eval_adapter.py heavy-tail <eval_dir>` computes per-level per-axis heavy-tail / sample-mean-divergence / cross-axis correlation.
- `_analyze/` eval_dr subcommand does the `failure<->DR join`: correlates worst-roll envs against the dr_* arrays (this is what produced baseline report's "low-damping/cog-shifted cluster" finding).
- `_eval_dr/metrics.py` does per-env peak counting (peak>20 deg env count) and `_pick_sample_env` (median-att env).

## The 3 HARD CEILINGS (why current tooling can't go deeper)
1. **dr_snapshot schema is DR-ONLY.** Its input keys (dr_snapshot.py:19-27) are payload_mass/cog/cob/added_mass/linear_damping. FAULT is NOT a DR param -- thruster failure, sensor noise, joint malfunction are dimensions that DO NOT EXIST in this schema. Current tooling can say "low-damping envs are hard" but has no variable for "the env whose thruster 3 died".
2. **eval npz saves no raw obs/privileged vector** ([[engine_gap_eval_npz_saves_no_raw_obs_std_privileged_blocks_exact]]). Only the trajectory + a SUBSET of DR params. This is the documented reason per-env causal attribution hits a ceiling -- state_std report had to demote its per-env causal claim to MED because the std head's policy-obs leg couldn't be reconstructed.
3. **failure<->DR join is UNIVARIATE (linear corr only).** Single-param corr (e.g. lin_damp -0.318). No multivariate / clustering ("which COMBINATION blows up", e.g. low-damping AND cog-shift jointly), no fault-type clustering. This is why baseline's "low-damping cause" did NOT cleanly reproduce in state_std's per-env re-analysis (corr sign-flipped hard<->ood) -- a univariate frame is fragile when the tail is a multivariate interaction.

## What FTC research needs ADDED (infrastructure, before any FTC training)
- **Fault injection** in marinelab (`marinelab/core/thruster.py` + sensor/joint paths): per-env, eval-fixed, same pattern as DORAEMON DR. Minimum 3: thruster health[N,6] (partial degradation, not just on/off), sensor noise scale[N], joint response degradation[N]. MUST be toggle-off byte-identical (regression test).
- **Schema extension** of `per_env_dr_from_tensors()` to emit `fault_thruster_{0..5}[N]`, `fault_sensor_noise[N]`, `fault_joint[N]` (skip-if-absent pattern, never fabricate). Wire into eval npz.
- **Engine-gap fix** (optional, opt-in flag): save raw per-env obs so per-env causal attribution loses its ceiling.
- **Analysis deepening**: univariate corr -> multivariate / clustering on the joined (fault + DR) per-env table.

## NET
The heavy-tail frame is reusable for FTC -- a fault is just a new per-env variation axis joined the same way DR is. But the DR-only schema + obs-less npz are hard blockers: you cannot heavy-tail-analyze a fault you do not record per-env. So FTC research order is: (1) fault injection + per-env fault snapshot (infra), THEN (2) heavy-tail/cluster analysis over fault envs, THEN (3) FTC training. Step 1 is a separate session's job (handoff prompt issued 2026-06-14). Related: [[state_dependent_std_difficulty_null_now_confirmed_on_real_dr_med]] (the per-env causal ceiling in practice), [[heavy_tail_vs_sample_mean_divergence_are_independent]] (the analysis frame).

VERIFIED: dr_snapshot.py:19-27/35-85 (DR-only schema); eval.py:39/486/517/578/686 (per_env_dr wiring + npz); eval_adapter.py:45/121-131 (heavy-tail subcommand); wiki fault query returned 0 FTC pages (greenfield). Source: user FTC research-direction discussion, 2026-06-14.

