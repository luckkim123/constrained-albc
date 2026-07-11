---
title: "reward.md deep-dive session 2026-07-11: 4 review/fix prompts queued in .sp/plans/ (§6 dt-scaling, §7 sigma-gate, §9 gotchas-triage pending; bias-reward DONE)"
tags: ["reward", "reward-md", "theory-review", "prompt-index", "line-cite-drift", "sigma-integral-gate", "dt-scaling", "gotchas", "pending-work"]
created: 2026-07-11T07:04:10.303838
updated: 2026-07-11T07:10:13.879453
sources: []
links: ["joint1_centering_reward_is_removed_on_main_6_term_but_alive_on_e.md", "reward_md_6_error_buffers_reward_call_site_dt_scaling_theory_rev.md", "reward_absolute_scale_is_invariant_to_the_constrainttrpo_actor_o.md", "reward_sigma_integral_obs_gate_coupling_reward_md_7_theory_revie.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# reward.md deep-dive session 2026-07-11: 4 review/fix prompts queued in .sp/plans/ (§6 dt-scaling, §7 sigma-gate, §9 gotchas-triage pending; bias-reward DONE)

reward.md deep-dive session 2026-07-11: 4 review/fix prompts queued in .sp/plans/ (§6 dt-scaling, §7 sigma-gate, §9 gotchas-triage pending; bias-reward DONE).

Index of the reward.md (`constrained-albc/docs/reference/reward.md`) code-level review prompts authored in a
2026-07-11 doc-Q&A session, so a later session does NOT re-derive or duplicate them. These are PROMPTS staged
for separate-session execution — their RESULTS get their own wiki cards when run (bias already did, below).

## Prompts in `/workspace/.sp/plans/` (as of 2026-07-11)

| Prompt file | Scope | Type | Status |
|:---|:---|:---|:---|
| `PROMPT_bias_reward_theory_review.md` | bias term (`bias_ema_penalty`) theory/logic | read-only review | **DONE** → card `bias_reward_bias_ema_penalty_theory_review_conditionally_sound_h` (verifier PASS), report `REVIEW_bias_reward_theory.md` |
| `PROMPT_reward_error_buffer_dt_scaling_theory_review.md` | reward.md §6 (error buffers / reward call site / `k*dt` scaling) theory/logic | read-only review | PENDING (no result card yet) |
| `PROMPT_reward_sigma_integral_gate_theory_review.md` | reward.md §7 (reward-sigma reused as integral-obs gate threshold) theory/logic | read-only review | PENDING |
| `PROMPT_reward_gotchas_triage_and_fix.md` | reward.md §9 twelve gotchas: triage (A)code-bug/(B)stale-doc/(C)intended, then fix | **code+doc EDIT** (approval-gated for code) | PENDING |

## Key facts these prompts pin (code-verified 2026-07-11, branch exp/latency-dr)

- **reward.md line-cites are broadly STALE** (code shifted after the doc was written). Every §9 `Cite` and the
  §6/§7 anchors need re-grep. Confirmed shifts: `k_bias` override `config.py:429`->`:453`; bias-EMA update
  `albc_env.py:1042-1052`->`:1133-1143`; `_get_rewards` `:1009`->`:1100`; integral-gate build `:164-173`->`:196-203`,
  apply `:1029-1038`->`:1120-1129`; termination penalty `:1061`->`:1152`. Mechanism prose is accurate; only
  anchors drifted. See [[joint1_centering_reward_is_removed_on_main_6_term_but_alive_on_e]].
- **§7 is a COUPLING, not a term**: `_integral_gate_sigmas` is built by COPYING `reward.att_rp.sigma` /
  `reward.yaw_vel.sigma` (both 0.10) at init (`albc_env.py:196-203`); the integral-OBS gate accumulates only when
  `|err| < sigma` (`:1120-1129`, gated + leak=0.99 + clamp=2.0). So retuning reward sigma silently retunes the
  observation gate threshold — a hidden confound for any sigma A/B. (§7 prompt reviews whether this is sound.)
- **§6 dt-scaling**: all terms scaled once at `value*weight*dt` in `RewardManager.compute` (`rewards.py` ~:231);
  `k` is PER-SECOND, step_dt=0.02 (=sim.dt 0.005 x decimation 4, framework-inherited). termination_penalty is
  the ONE reward contribution OUTSIDE this scaling (added post-compute, no *dt). (§6 prompt reviews dt<->gamma<->
  performance_lb absolute-scale coupling vs the "reward abs scale invariant to actor" card.)
- **§9 is mostly NOT bugs**: the doc itself says most gotchas are stale-doc/intended-design, not functional bugs.
  The fix prompt's core is TRIAGE (do not "fix" intended design: applied_torque #8, roll-weight 1.5 #11, fork
  separation #12, single dt-scaling). Also gated on branch: joint1_center gotchas (#3/#7/#12) differ main(6-term,
  removed) vs exp/latency-dr(7-term). And several (#2 docstring, #4 arctan) may already be fixed on main.

## Why recorded

Only the INDEX + pinned facts are here. The three PENDING prompts' conclusions are NOT yet knowledge — when run,
each writes its own result card (as bias did). This card exists so a future session finds the queued work instead
of re-authoring it, and inherits the verified line-drift / branch-divergence facts up front.

---

## Update (2026-07-11T07:10:13.135481)

## §6 dt-scaling review DONE (added 2026-07-11)

`PROMPT_reward_error_buffer_dt_scaling_theory_review.md` is now **DONE** (was PENDING in the table above).
Result card: [[reward_md_6_error_buffers_reward_call_site_dt_scaling_theory_rev]], report
`/workspace/.sp/plans/REVIEW_reward_error_buffer_dt_scaling.md`. Verdict: §6 mechanism CONDITIONALLY SOUND.

Headline findings (see the card for the full 10-question A1-D10 table):
- **B4 is the one real exposure, and it is LATENT.** reward is scaled `value*weight*dt` but gamma is FIXED 0.99
  (dt-independent). Tallec/Blier/Ollivier ICML 2019 (arXiv:1901.09732) prove this exact combo makes the physical
  planning horizon `dt/(1-gamma)` NOT dt-invariant (=2.0s here; halves to 1.0s if dt->0.01) => optimal policy
  changes if dt/decimation changes. But NO run changes step_dt (latency-DR DRs only integer control_delay_steps,
  not sim.dt/decimation) => a documented trap for a future control-frequency ablation, not a present bug. Fix if
  ever needed: gamma -> gamma^(dt_new/dt_old) alongside reward*dt.
- **B5 "contradiction" REFUTED**: performance_lb-dependence and actor scale-invariance are DIFFERENT consumers
  (actor sees standardized advantage; DORAEMON success gate compares RAW return). Already captured as leak-path #3
  in [[reward_absolute_scale_is_invariant_to_the_constrainttrpo_actor_o]]. Any reward-rescale (or dt change) must
  re-calibrate performance_lb by the same factor.
- `k*dt` is Isaac Lab's OWN built-in convention (RewardManager docstring: weight*dt "to balance w.r.t. timestep").
- Remaining questions (wrap A1/A2, wrap-asymmetry A3, single-scaling-point B6, termination-outside-dt C7/C8,
  shared-buffer coupling D9, 3-consumer dt-asymmetry D10) all "no problem". Recommendations are DOC-ONLY (reward.md
  §6 premise + warnings); NO code change warranted under the dt-fixed premise.

Status table update: §6 row = DONE. Remaining PENDING: §7 sigma-integral-gate, §9 gotchas-triage.

---

## Update (2026-07-11T07:10:13.879453)

## UPDATE 2026-07-11 (later same day): section-7 prompt DONE

`PROMPT_reward_sigma_integral_gate_theory_review.md` was executed (read-only review). Status **PENDING -> DONE**. Result card: [[reward_sigma_integral_obs_gate_coupling_reward_md_7_theory_revie]] (verdict: conditionally sound; shared-sigma aliasing is the one real defect; gate is a settling-band accumulator NOT anti-windup; clamp is dead code in gated mode `I_ss=0.20 << clamp 2.0`; Hwangbo-2017 citation is wrong, use Yu&Lee 2023 / Weber 2022). Report `/workspace/.sp/plans/REVIEW_reward_sigma_integral_gate.md`.

Remaining PENDING from this session's queue: `PROMPT_reward_error_buffer_dt_scaling_theory_review.md` (section 6 dt-scaling) and `PROMPT_reward_gotchas_triage_and_fix.md` (section 9 triage, code+doc edit, approval-gated). The bias (DONE earlier) and section-7 (DONE now) reviews are both conditionally-sound-with-caveats; both surface the same recurring theme — a hidden env-state buffer (`_bias_ema` ungated / `_error_integral` gated) coupled to reward/obs in a way that breaks clean single-variable experiments.

