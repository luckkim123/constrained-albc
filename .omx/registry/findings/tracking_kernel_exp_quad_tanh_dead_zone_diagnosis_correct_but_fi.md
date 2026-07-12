---
title: "Tracking kernel exp-quad-tanh: dead-zone diagnosis correct but fix is on wrong axis (yaw not att_rp); the exp+L1+tanh stack has no literature precedent"
tags: ["reward", "tracking", "kernel", "dead-zone", "att_rp", "literature", "exp-design"]
created: 2026-07-08T23:49:37.492504
updated: 2026-07-08T23:49:37.492504
sources: []
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
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

