---
title: "performance_lb (DORAEMON gate) is causally independent of the actor exploration collapse"
tags: ["doraemon", "exploration", "entropy", "noise_std", "performance_lb", "eval", "rule03"]
created: 2026-07-15T04:54:06.615107
updated: 2026-07-23T07:42:44.866132
sources: ["diagnose-20260715-133249", "static_260715_141532"]
links: ["april_2026_entropy_collapse_campaign_machinery_bug_solved_conver.md"]
category: decision
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
---

# performance_lb (DORAEMON gate) is causally independent of the actor exploration collapse

Probe trpo_perflb200_260715_023744 vs baseline trpo_baseline_260714_192020 (single variable DORAEMON performance_lb 250->200, seed 30, verified via git show d3789a7 = one-line config diff + git log = no other envs/main|_core commit between launches).

RESULT: lowering performance_lb UN-STALLS the curriculum but does NOT touch exploration.
- DORAEMON channel MOVED: mode -2.00->0.00 (baseline re-stalls at -2 late; perflb holds 0), success_rate 0.407->0.712, ess_ratio 0.414->0.754, DR widened (ocean_current 0.03->0.07, payload 1.36->1.48). [TB DORAEMON/*, analysis diagnose-20260715-133249 report.md central table]
- Exploration UNTOUCHED: Policy/entropy -7.758->-7.796, Policy/mean_noise_std 0.0995->0.0985; trajectories near-identical across all 5000 iters (max abs dev 0.18 entropy ~1% of collapse range, 0.003 noise_std) = two orders below the DORAEMON-side divergence. [TB Policy/entropy, Policy/mean_noise_std strided trajectory]

CONCLUSION: the actor entropy/noise_std collapse (noise_std pinned near min_std=0.05 floor, entropy ~-7.8) is causally INDEPENDENT of the DORAEMON feasibility gate. Engine [DIAGNOSIS] 'exploration dead: check min_std floor and entropy_coef' is IDENTICAL in both runs. The mode=-2 stall was a co-symptom, not the cause.

DECISION: adopt performance_lb=200 as the standing curriculum setting (stabilizes mode at 0 vs baseline's late re-stall). The next exploration lever must target the actor noise/entropy machinery (min_std, entropy_coef=0.003, or the noise parameterization / entropy schedule) — NOT the curriculum. Re-testing performance_lb / DORAEMON knobs for the exploration collapse is refuted; do not re-run that lever for exploration.

---

## Update (2026-07-15T05:35:05.619160)

## Eval confirmation (post-hoc +-30 eval static_260715_141532, added 2026-07-15)

perflb200 (lb=200) eval'd vs lb=250 baseline (static_260715_003649). RULE-03: eval.py auto-loads each run's
DORAEMON-learned DR, so soft/medium/hard are RUN-RELATIVE (perflb box WIDER: data_hard.npz dr_payload_mass std
0.817 vs 0.511) — ONLY 'none' (DR=0) is a fair cross-run comparison.
- At none (fair): perflb200 BEATS baseline on every attitude axis — roll ss_error 0.670->0.395 (-41%), pitch
  -18%, att_norm 0.738->0.457 (-38%); overshoot os_env_mean -45..-83%; n_gt20 slashed (roll 47->21, pitch 22->0,
  yaw 31->0); 100% survival all levels.
- medium/hard ss_error 'regressions' (roll hard +192%, att_norm hard 2.201) are the run-relative-DR ARTIFACT
  (perflb graded on its own wider box), NOT a real regression.
CONCLUSION: lb=200 is benign-to-POSITIVE for control (lowered nominal DC-bias floor + slashed overshoot while
widening DR coverage). Reinforces ADOPT. Canonical rule-03 lesson: never read cross-run soft/medium/hard from a
DORAEMON-DR eval as comparable; anchor on 'none'. Remaining gap: fixed-box OOD (--extreme-ood) deferred.

---

## Update (2026-07-20T07:54:39.322598)

CORRECTION (2026-07-20, source: diagnose-20260715-133249 CORRECTION section): the 'pinned near min_std=0.05 floor' language above and the min_std next-lever suggestion are WRONG on two counts, fully resolved in [[april_2026_entropy_collapse_campaign_machinery_bug_solved_conver]]. (1) The scalar `min_std` is dead code in this config -- `constraint_trpo.py:507-511` takes the per-dim `_log_min_std` clamp branch whenever `min_std_per_dim` is set, and it IS set (`rsl_rl_ppo_cfg.py:246` = arm 0.10 / thruster 0.05, never the scalar 0.05). (2) Neither baseline nor perflb200 is floor-clamped: `Noise/std_min` (= `policy.log_std.exp().min()`, `constraint_encoder_runner.py:366-367`) = 0.0604 (baseline) / 0.0607 (perflb), both 1.21x ABOVE the 0.05 thruster floor -- the safety clamp never fired in either run. Contrast the biasema-lineage runs (`trpo_biasema_260715_142543`, `trpo_biasema_extend8k_260716_162849`), which ARE clamped exactly at `Noise/std_min`=0.0500 -- floor-pinning is a per-run property, not a campaign constant, so do not generalize either direction without checking `Noise/std_min` for the specific run. CONSEQUENCE: raising `min_std` is a no-op for baseline/perflb and would produce a meaningless null result -- drop it from this page's candidate-lever list. The single variable that actually targets exploration (for non-biasema runs) is `entropy_coef_per_dim` (thruster leg), consistent with the April 2026 campaign's own conclusion ('min_std was NOT binding; per-dim entropy IS', commit 26b2f54, r13_B).

---

## Update (2026-07-23T07:42:44.866132)

2026-07-23 curation: REVERSAL NOTE -- the 'adopt performance_lb=200' recommendation on this page was reversed 2026-07-16 (standing value stays lb=250; see decision_do_not_adopt_performance_lb_200 page). The core causal-independence finding here (DORAEMON gate independent of actor exploration collapse) stays valid.
