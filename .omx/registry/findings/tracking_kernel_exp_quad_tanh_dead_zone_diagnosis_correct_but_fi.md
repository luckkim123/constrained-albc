---
title: "Tracking kernel exp-quad-tanh: dead-zone diagnosis correct but fix is on wrong axis (yaw not att_rp); the exp+L1+tanh stack has no literature precedent"
tags: ["reward", "tracking", "kernel", "dead-zone", "att_rp", "literature", "exp-design", "rule-03-gate"]
created: 2026-07-08T23:49:37.492504
updated: 2026-07-21T03:34:32.487023
sources: []
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: resolved
blocked-on: "Parked under the 2026-07-20 batch-pass decision."
---

# Tracking kernel exp-quad-tanh: dead-zone diagnosis correct but fix is on wrong axis (yaw not att_rp); the exp+L1+tanh stack has no literature precedent

Scope: envs/main (Isaac-ConstrainedALBC-TRPO-v0) shared tracking kernel `_exp_quad_saturating`
(rewards.py:97-117). Code-verified + theory-analyzed (architect) + literature-surveyed
(document-specialist, local references/ + web, grounded not from-memory). 2026-07-09.

## What the kernel is
Three tracking terms (att_rp, yaw_vel, dead lin_vel) call one kernel:
`r = exp(-e^2/2sigma^2) - q_quad*e^2 - q_lin*|e| - [tanh if coef>0] - [arctan if coef>0]`.
Shipped effective: att_rp runs ONLY `exp - 0.833*e^2` (sigma=0.10, no saturating); yaw_vel runs
`exp - e^2 - tanh` (tanh_coef=0.3, eps=0.10); lin_ratio=0 everywhere (linear penalty inert on all).
k is per-second, *dt=0.02 per-step. att_rp err_sq roll-weighted (1.5*roll^2+pitch^2), err_norm Manhattan.

## Theory verdict (CONFIRMED by gradient computation)
1. **Dead-zone diagnosis is correct.** att_rp `exp-q*e^2` has EXACTLY zero gradient at e=0 (both terms
   even, derivative vanishes at origin). exp gradient magnitude peaks at |e|=sigma=0.10rad=5.73deg. So
   once error is inside ~sigma the policy has no 1st-order pressure to drive roll/pitch SS-error to zero.
2. **yaw_vel tanh is a textbook-clean fix**: restores gradient -0.3 (=-tanh_coef) at e->0+, tail
   saturates to 0.03 (untouched). Never pulls reward negative near zero (crossover 0.225 rad/s).
3. **THE defect = the fix is on the WRONG axis (asymmetry).** tanh mitigates yaw (a RATE target);
   att_rp (roll/pitch = ANGLE targets) has NO dead-zone mitigation. But SS DC-offset is an ANGLE-axis
   failure mode -- the whole reason bias_ema_penalty (k_bias=-2.0) exists is to punish sustained att
   offset. The rate-vs-angle justification is INVERTED: angle SS-error is precisely what needs the
   non-vanishing gradient. bias_ema only helps in the slow (~100-step EMA) band and is itself squared
   (also vanishes at 0), so it narrows but does not close the per-step att_rp dead zone.
4. **Secondary: negative tail is unbounded.** att_rp `exp-0.833*e^2` crosses 0 at e=14deg, then -> -inf
   (-8.2 at 180deg). Latent (no attitude-triggered early-termination wired to termination_penalty=0 in
   this config -- UNVERIFIED, termination MDP not audited), but a give-up/termination-seeking setup if
   early-termination is ever added. Clamp candidate: `.clamp(min=-1..-2)` at rewards.py:117.

## Literature verdict (grounded, local refs + web fetched)
- Diagnosis IS documented: Lagos Suarez et al. 2026 (arXiv:2605.19166) diagnose the identical
  vanishing-near-target problem for quadrotor setpoint tracking with single-sigma Gaussian reward.
- BUT this exp+quad+L1+tanh+arctan STACK has NO located precedent. Every read source uses either
  pure negative-quadratic (NORBC=this project's algo, RMA, Sim-to-Real Locomotion) or pure single
  Gaussian `exp(-e^2/sigma)` (legged_gym/IsaacGym canonical, and this project's own RL-ALBC/RL-TDC
  precursor) -- none ADD an L1/saturating term to a Gaussian. Genuine negative finding, not weak search.
- Literature's documented fix for the SAME problem is DIFFERENT: dual-bandwidth Gaussian (sum of two
  Gaussians, different sigma) -- stays smooth+bounded. Adding quad reintroduces the unbounded far-field
  that Gaussians are usually chosen to avoid.
- Counter-consideration: dm_control `tolerance` primitive makes the near-target region flat (zero
  gradient) BY DESIGN -- "vanishing gradient at e=0 = bad" is a design choice, not settled fact.
- This project's OWN precursor note (NORBC - Application to RL-ALBC.md, "Improvement 3: Reward
  Simplification") recommends SIMPLIFYING the gated-Gaussian-plus-penalty pattern and moving hazard
  handling into a CONSTRAINT -- i.e. add fewer reward terms, not more. Current kernel goes the opposite way.

## Three improvement leads (NONE validated -- exp-design gate required; rule 03 forbids "common ML pattern")
- **(a) enable small tanh on att_rp** (coef 0.15-0.3, eps=0.10): closes dead zone on the axis that needs
  it, per-axis restoring force -1.5*coef roll / -1.0*coef pitch (Manhattan weight propagates). RISK:
  constant setpoint gradient may induce jitter (the exact reason raw linear was disabled) -- MUST A/B
  against ss_jitter vs ss_error separately (rule 03). architect's #1 pick.
- **(b) dual-bandwidth Gaussian** (Lagos Suarez 2026): only lead with a published same-setting precedent;
  smooth+bounded. document-specialist's best-supported alternative.
- **(c) migrate the anti-drift signal to a constraint** (IPO/CMDP -- already available, ConstraintTRPO+IPO):
  matches NORBC's own recommendation. Structurally available, not hypothetical.
- Do NOT shrink sigma (narrows strong-gradient region too; wrong lever).

## Tension to resolve in exp-design
architect's local-optimal pick (a) GROWS an already-bespoke stack; literature (b)/(c) are more principled
but unvalidated on this UUV attitude task. The discriminating probe should weigh "close the att_rp dead
zone" (a) vs "replace the stack with a bounded/principled form" (b/c), measuring ss_error AND ss_jitter
across all 4 DR levels.

UNVERIFIED: termination MDP (tail-benign claim), whether att_rp tanh induces jitter (empirical),
ScienceDirect flexible-link paper (403), ManiSkill2 exact reward. Cross-ref: yaw_command_is_rate_not_angle
card, reward_penalty_terms card, action_bounding card.

---

## Update (2026-07-20T07:54:39.625436)

STATUS PROMOTION (2026-07-20 wiki sweep): the discriminating probe among the 3 fix candidates (small yaw-axis tanh dead-zone / kernel simplification / no-op) measuring ss_error AND ss_jitter across all 4 DR levels is unstarted; promoted to needs-experiment.

---

## Update (2026-07-21T03:34:32.487023)

## CLOSED 2026-07-21 by the rule-03 measured-deficiency gate (campaign item Z9)

[DECISION] Z9 asked whether this lead becomes a launchable probe (campaign A7). Verdict:
NO PROBE. The lead is closed as resolved-by-gate; A7 is dropped from the optional tier.
The dead-zone diagnosis on this page stays CORRECT -- what fails is the case for spending
4.7 GPU-hours on it.
[CONFIDENCE: HIGH -- decided on this workspace's own eval data + code, no new run]

### Why the fix does not clear the bar

1. The dead zone is ASYMPTOTIC; at the achieved operating point the gradient is not small.
   Differentiating the real shipped expression (`rewards.py:141-158`, k=9, sigma=0.10,
   quad_ratio=0.833, roll weight 1.5) at the reference run's `none`-level roll ss_error of
   0.215 deg = 3.75e-3 rad gives about -5.14 reward/rad. Adding `tanh_coef=0.15` would add
   about -2.02/rad -- it RAISES an existing restoring gradient by ~39%, it does not restore
   a vanished one. New equilibrium approx 0.13 deg, i.e. a predicted improvement of ~0.085 deg.

2. That improvement is far below the sensor floor the policy trains against. `config.py:271-287`
   sets the euler observation-noise std to 0.02 rad = 1.15 deg, plus a per-episode bias of
   the same magnitude. The 0.215 deg residual is already ~5x BELOW one noise sigma, and the
   predicted 0.085 deg gain is ~1/13 of a sigma. It is visible only because `eval.py:964-965`
   nulls `observation_noise_model` for the exam. Under rule 03 that is an artifact of the
   noise-free harness, not a measured deployable deficiency.

3. The probe cannot discriminate against ordinary run-to-run movement on the metric it would
   move. `none`-level att_norm ss_error across posttam runs that never touched the tracking
   kernel spans 0.250-0.426 deg (a ~25% band); `minstdthr008`, a `min_std` change, moved
   att_norm 0.319 -> 0.250 (-22%) as a SIDE EFFECT -- larger than the kernel model predicts
   for the tanh fix.

4. The axis that already carries the tanh shows no deficiency to generalize from: yaw
   ss_error 0.0052 rad/s, ss_jitter 4.4e-5, CV 2.4%.

Steelman considered and rejected: SS error is exactly what `k_bias=-2.0` (`config.py:493`)
was added to punish, so the project has already spent a reward term here. It still fails,
because the residual DC-bias tail was concluded AUTHORITY-limited (not gradient-limited) on
the bias_ema observability page, and the `none`-level residual is sub-noise-floor anyway.

### Reopen triggers (any ONE, read at DR `none` in the run's experiments/ eval tree)

- roll or pitch `ss_error` >= 1.0 deg (approaching the 1.15 deg euler noise std) with
  `ss_jitter` staying low -- a DC offset the policy is not being pushed out of.
- a sub-noise-floor attitude residual becomes the binding constraint on a real deliverable
  (e.g. hardware / Stonefish transfer where end-effector error traces to attitude DC bias
  rather than estimator error).
- attitude-triggered early termination gets wired up (`termination_penalty=0.0`,
  `rewards.py:112`): the unbounded `exp - 0.833 e^2` far field reaches about -8.2 at 180 deg
  and becomes a give-up incentive. That reopens the kernel as a BOUNDING question (a
  `.clamp(min=-1)` code change at `rewards.py:158`), which is not what A7 was scoped as.
- `ss_jitter` climbing above `ss_error` on the attitude axes (oscillation rather than offset).
  Currently roll jitter 0.094 < ss 0.215, so no.

### Campaign-plan errors found while deciding this

- The plan (`.sp/plans/2026-07-20-final-teacher-batch-campaign.md:130,164`) names candidate
  (a) as the "yaw-axis tanh dead-zone" and A7's question as "yaw dead-zone / kernel fix".
  That is BACKWARDS and code-verified so: `config.py:488` gives `yaw_vel` the only live
  `tanh_coef=0.3`, while `att_rp` (`rewards.py:106`) leaves it at the 0.0 default. This
  page's candidate (a) was always "enable a small tanh on att_rp". A7 as the plan worded it
  would have asked to add a tanh to the one axis that already has one.
- The plan compressed this page's FOUR options into three by folding the structural one --
  "migrate the anti-drift signal to a constraint (IPO/CMDP)" -- into "no-op". That is a
  different and cheaper question (ConstraintTRPO+IPO is already wired) and is NOT closed by
  this decision; it should be carried as its own zero-GPU lead.
- A schedule-conditional probe anchored to the `biasema` comparator is stale before launch
  if Stage A adopts a config that moves that comparator (`minstdthr008` already moved
  att_norm at `none`). Any late-tier probe must declare its band against the ADOPTED config,
  not the current anchor.

Also inert in every shipped config: `lin_ratio` is 0 everywhere, so the L1 leg of the stack
this page names does not actually run.

