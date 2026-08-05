---
title: "reward-sigma / integral-obs-gate coupling (reward.md 7) theory review: conditionally sound; shared-sigma ALIASING is the defect (decouple gate threshold), gate is a settling-band accumulator not anti-windup, clamp is dead code in gated mode, Hwangbo-2017 citation is wrong (use Yu&Lee 2023)"
tags: ["albc", "envs-main", "reward", "integral-obs", "error-gate", "leaky-integrator", "sigma-coupling", "anti-windup", "settling-band", "doe-confounding", "aliasing", "theory-review", "literature", "experiment-lead", "gate", "sigma", "r1", "applied"]
created: 2026-07-11T07:09:55.881613
updated: 2026-08-05T07:35:59.670236
sources: ["fea5974"]
links: ["bias_reward_bias_ema_penalty_theory_review_conditionally_sound_h.md", "leaky_integral_and_ema_bias_carry_over_the_mid_episode_command_r.md"]
category: decision
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: resolved
blocked-on: "R1 (gate/sigma decouple) is APPLIED on main since fea5974 with a per-axis threshold and a byte-identical default -- do NOT cherry-pick 3a6a4b7 off preserved/r1-integral-gate-impl, that version is a weaker scalar-with-None-default and would regress it. What remains open here is ONLY the R6 training probe, parked under the 2026-07-20 batch-pass decision."
---

# reward-sigma / integral-obs-gate coupling (reward.md 7) theory review: conditionally sound; shared-sigma ALIASING is the defect (decouple gate threshold), gate is a settling-band accumulator not anti-windup, clamp is dead code in gated mode, Hwangbo-2017 citation is wrong (use Yu&Lee 2023)

Theoretical review of reward.md section 7 — the reward-sigma / integral-obs-gate coupling (envs/main, `Isaac-ConstrainedALBC-TRPO-v0`). Code-verified 2026-07-11, branch exp/latency-dr (coupling identical on main; main differs only by joint1 removal). Literature grounded by 3 parallel search agents (all sources opened, unverified marked). Full report: `/workspace/.sp/plans/REVIEW_reward_sigma_integral_gate.md`. THEORY/LITERATURE review — no run data, no code change. Companion to the bias review [[bias_reward_bias_ema_penalty_theory_review_conditionally_sound_h]] (that card covers the ungated `_bias_ema` reward; this one covers the gated `_error_integral` observation).

WHAT SECTION 7 IS (code fact): NOT a reward term. Two unrelated systems share ONE scalar `sigma`. (1) tracking reward kernel width `exp(-e^2/2 sigma^2)` (att_rp.sigma=yaw_vel.sigma=0.10). (2) integral-OBS gate: `_integral_gate_sigmas` is built at init by COPYING those reward sigmas (`albc_env.py:196-203`), and each step the leaky integrator accumulates only while `|err| < sigma` (`:1120-1129`, leak=0.99, clamp=2.0, `config.py:367-371`). The integral feeds 3D of the 69D obs, NEVER the reward sum. So retuning `reward.att_rp.sigma`/`yaw_vel.sigma` silently retunes the observation-gate threshold too.

VERDICT: CONDITIONALLY SOUND, with ONE genuine defect (shared-sigma aliasing) + 3 secondary findings. Not a runtime bug; nothing crashes or corrupts. The leaky-clamped-integral-as-observation is literature-backed. But the coupling is a real defect on the experiment-reproducibility axis.

1. SHARED-SIGMA ALIASING (the one real defect). Reward-kernel width (how sharply return falls off target) and settling-band threshold (how close counts as "settled, start accumulating bias") are conceptually orthogonal — you might want a WIDE kernel but a TIGHT settling band. The code makes that impossible: one number. This is textbook DOE CONFOUNDING/ALIASING (NIST e-Handbook 5.3.3.4.3 — two effects change in lockstep, individual contributions non-estimable). Andrychowicz et al. 2021 (What Matters in On-Policy RL): "experiments where only a single choice is varied but interacting choices are kept fixed may be misleading" — here they are the SAME variable, so OFAT is not misleading, it is STRUCTURALLY IMPOSSIBLE. Concrete failure: a "widen the tracking kernel" probe (att_rp.sigma 0.10->0.15) also widens the obs gate 5.7deg->8.6deg, confounding the run. Directly violates .claude/rules/03 min-change-revert. Also easy to miss: the coupling comment lives at the gate-build site (`albc_env.py:196`), not next to the sigma field in `rewards.py`.

2. GATE IS MISLABELED (not anti-windup — the OPPOSITE direction). Classical conditional-integration anti-windup STOPS the integrator when error is LARGE / actuator saturates (LibreTexts 9.6; arXiv:2606.01959 review). This gate does the reverse: `gate=1 only when |err| < sigma` = accumulate ONLY when error is SMALL. It is a SETTLING-BAND ACCUMULATOR, not windup prevention. The clamp part IS textbook anti-windup (bounded integral term); gate + clamp are complementary (inflow-block vs magnitude-limit), not redundant.

3. CLAMP IS DEAD CODE IN GATED MODE (quant). Gated SS saturation `I_ss = sigma*dt/(1-leak) = 0.10*0.02/0.01 = 0.20 rad` = exactly 1/10 of clamp=2.0. To hit the clamp needs a sustained UNGATED error of 1.0 rad (57.3deg), which the gate blocks by construction. So `integral_clamp=2.0` can NEVER bind while `integral_gated=True` — it is a guard for the `gated=False` branch only. (leak tau = -1/ln(0.99) = 99.5 steps ~ 2.0 s; half-life 69 steps ~ 1.38 s.)

4. HWANGBO 2017 CITATION IS WRONG (`config.py:366`). The comment cites "Hwangbo 2017 pattern" for the integral-obs. Both candidate papers were opened: Hwangbo 2017 (quadrotor RA-L, arXiv:1707.05110) uses an 18D rotation-matrix obs, NO integral; Hwangbo 2019 (ANYmal, Science Robotics, arXiv:1901.08652) uses a joint-state HISTORY (t-0.01, t-0.02 s), NOT an integral. The real literature match is Yu & Lee 2023 (arXiv:2311.06144) — leaky anti-windup integral of tracking error IN the observation (`e_I_dot = -alpha*e_I + e`, alpha=0.01 "to mitigate integral windup"), a direct structural match; and Weber et al. 2022 (arXiv:2201.13331, IASA/PID-I analogy, integrator in the action path). Re-cite recommended.

B-5 DEAD-ZONE PARADOX: CONFIRMED but BOUNDED. While `|err| >= sigma` the gate is 0, so a large sustained error NEVER enters `_error_integral` — the integral OBSERVATION goes uninformative exactly for the large-bias regime (LibreTexts warns the control analog "may get stuck at a nonzero control error"). BUT this blind spot is covered by the sibling UNGATED `_bias_ema` reward (`k_bias=-2.0`), which always accumulates and penalizes large offset. Apparent role split: gated integral = fine-settling obs feature; ungated EMA = coarse persistent-offset penalty. Whether intentional or convergent-accident is NOT documented anywhere. So the paradox is real but its severity is bounded — the policy learns about large bias through the reward gradient, not via this obs channel.

C-7 UNIT MIX: roll/pitch gate threshold is rad (wrapped angle err), yaw is rad/s (un-wrapped rate err, correctly un-wrapped). All three are 0.10 only because the reward sigmas are 0.10 — a coincidence, not a physical equality. No runtime error (each gates in its own units) but a latent trap. (Same class as the bias-term dimensional mismatch in [[bias_reward_bias_ema_penalty_theory_review_conditionally_sound_h]].)

RECOMMENDATIONS (no code changed; each tagged prompt-worthy). R1 (highest, code, behavior-preserving default): add an independent per-axis `integral_gate_threshold` (default = current 0.10, byte-identical) so the gate reads from IT, not from `reward.*.sigma` — removes the aliasing, unblocks clean reward-kernel ablations. R2 (doc): fix the Hwangbo citation -> Yu & Lee 2023 + Weber 2022. R3 (doc): put the coupling warning next to the sigma field in `rewards.py` (do even if R1 deferred). R4 (doc): relabel the gate as settling-band accumulator, not anti-windup. R5 (doc): note clamp inert in gated mode; do NOT lower it toward 0.20 without an A/B. R6 (experiment, design-only, exp-design gate, DO NOT launch): A/B an independent/decoupled gate threshold, and ungated-vs-gated integral as an obs feature; needs from-scratch checkpoint, fold into sim-to-real retrain batch.

UNCERTAINTY (declarative): A/B-only — (a) whether decoupling the gate from sigma actually changes learned performance (may be behaviorally neutral); (b) whether the gated integral earns its 3 obs dims vs an ungated variant; (c) whether sigma=0.10 is the RIGHT settling band vs merely plausible. Intent-vs-accident of the gated/ungated role division is undocumented. Whether R7/R8 validated the integral obs under the GATED regime specifically is unknown (git blame lost under repo rename; see [[leaky_integral_and_ema_bias_carry_over_the_mid_episode_command_r]]). Not verified: Astrom & Hagglund anti-windup chapter text, Bohn & Atherton 1995 abstract, Ogata/Franklin primary PDFs (convention confirmed via secondary sources), any paper naming the exact sigma-reuse construction (none found).

---

## Update (2026-07-20T07:54:39.698724)

STATUS PROMOTION (2026-07-20 wiki sweep): R1 (decouple integral_gate_threshold from reward sigma -- behavior-preserving code change) and the R6 training probe remain unstarted; promoted to needs-experiment.

---

## Update (2026-07-24T01:20:04.835298)

[FINDING] R1 (the highest-priority recommendation, zero-GPU code change) IMPLEMENTED 2026-07-24.
The shared-sigma ALIASING defect is removed: added an independent per-axis cfg field
`integral_gate_threshold` (default (0.10,0.10,0.10)) that the integral-obs gate reads instead of
copying reward.att_rp.sigma / reward.yaw_vel.sigma at env init. Behavior-preserving -- the default
reproduces the historical copied value byte-identically, so no prior run is invalidated -- but a
reward-kernel sigma ablation (att_rp.sigma 0.10->0.15) no longer silently retunes the obs gate.
On branch exp/integral-gate-decouple (commit fea5974: config.py integral_gate_threshold +
albc_env.py gate-build rewire + tests/test_integral_gate_decouple.py), NOT yet merged to main.
[EVIDENCE: commit fea5974; sim-free test tests/test_integral_gate_decouple.py -- default==historical
(0.10,0.10,0.10) AND the env gate reads integral_gate_threshold not reward.*.sigma, 2 passed; config
contract intact via test_attitude_only_dims + test_bias_ema_obs, 12 passed]
[CONFIDENCE: HIGH]

STATUS: still needs-experiment. R1 (the enabling refactor) is DONE; what remains is R6 -- the A/B
that measures whether decoupling the gate from sigma actually changes learned performance (needs a
from-scratch checkpoint; design-only, exp-design gate, DO NOT launch; fold into the sim-to-real
retrain batch). R2-R5 are doc-only (Hwangbo->Yu&Lee 2023 citation fix, relabel the gate as a
settling-band accumulator not anti-windup, note the clamp is inert in gated mode) and are not yet
applied.

---

## Update (2026-07-30T05:22:44.654801)

## R1 IS APPLIED ON MAIN 2026-07-30 (and the tagged commit is a WEAKER superseded version -- do not cherry-pick it)

[FINDING] The R1 half of this lead -- decouple the integral-obs gate threshold from the tracking-reward sigma -- is DONE and has been on main since commit fea5974. The plan's standing instruction to recover R1 by cherry-picking 3a6a4b7 off the tag preserved/r1-integral-gate-impl is stale AND harmful: that commit's implementation is strictly weaker than what main already carries, so applying it would be a regression, not a recovery.

[EVIDENCE] Verified 2026-07-30 by attempting the cherry-pick in a throwaway worktree off main and reading the conflict. main (commit fea5974, "feat(env): decouple integral-obs gate threshold from reward sigma (R1)") has `integral_gate_threshold: tuple[float, float, float] = (0.10, 0.10, 0.10)` -- PER-AXIS and unconditionally decoupled, with the config comment stating the default reproduces the historical shared-sigma value byte-identically (att_rp.sigma = yaw_vel.sigma = 0.10) so no behavioural change ships with the decoupling. It is consumed at albc_env.py:216-220 ("R1 decouple: read the independent per-axis integral_gate_threshold") and applied at albc_env.py:1194. main also carries tests/test_integral_gate_decouple.py. The tagged commit 3a6a4b7 (2026-07-21) instead has `integral_gate_threshold: float | None = None` -- a SCALAR override whose default None still reuses reward.att_rp.sigma / reward.yaw_vel.sigma, i.e. still aliased unless someone opts out. Same intent, worse implementation.

[CONFIDENCE] HIGH

Consequence for the tag: preserved/r1-integral-gate-impl still holds a legitimate piece of history (it also carried a 64-line test), but its stated purpose -- "the only reachable copy of the never-run R1 implementation" -- no longer holds, because R1 exists on main in a better form. Keep the tag as history; never cherry-pick from it. Anything referring to R1 as pending work should be read as already-shipped.

Byte-identical-default discipline is what makes this safe to have landed without a retrain: the aliasing that confounded reward-kernel ablations is removed, but the numeric behaviour at the default is unchanged, so runs before and after fea5974 remain comparable on this axis. Retuning a tracking-kernel sigma no longer silently retunes the integral gate -- that was the actual defect this lead identified.

Still open on this page (unchanged): the R6 training probe remains parked under the 2026-07-20 batch-pass decision. The citation correction (Hwangbo-2017 -> Yu & Lee 2023) and the dead-clamp-in-gated-mode observation are documentation/cleanup items, not experiments.

---

## Update (2026-08-05T07:35:59.670236)

## R6 CLOSED 2026-08-05 — three-point sweep run, CLOSED-NULL, default confirmed at its optimum

The last open piece of this lead was the R6 training probe: does the integral-obs gate threshold
matter? It was run as a three-point sweep in campaign `teacher_integral_gate` and the answer is now
measured, not argued.

Arms, all 5000 iterations on the buoyfix plant with fault enabled, evaluated with
`--doraemon-dr-from` anchored on E-int so the four DR levels mean the same thing across runs:

| arm | threshold | run | verdict |
|:--|:--|:--|:--|
| reference | (0.10, 0.10, 0.10) | trpo_eint_s30_rs2350_260727_195102 (existing) | baseline |
| widen | (0.20, 0.20, 0.20) | trpo_gate020_s30_260805_063110 | NULL (fails clause 1) |
| narrow | (0.05, 0.05, 0.05) | trpo_gate005_s30_260805_112701 | NULL (fails BOTH clauses) |

Per the pre-registered DESIGN.md section 5, both arms null closes this CLOSED-NULL with
(0.10, 0.10, 0.10) confirmed. No code change follows.

**The knob is not inert — it is already at its optimum.** On roll n_gt20, the heavy-tail metric the
stated mechanism targets, the default beats both probes at all four DR levels (of 64 envs, reading
reference / widen / narrow): none 0.00 / 6.00 / 42.00, soft 0.33 / 7.00 / 33.33, medium
1.00 / 5.67 / 28.33, hard 5.00 / 5.67 / 21.33. Widening is mildly worse; narrowing is a cliff.

**The settling-band-accumulator reading is confirmed, with its sign.** Narrowing to 0.05 excludes
the sustained-offset population that needs integral action, so those envs keep their DC roll error
and the tail explodes; widening admits them along with noise, which is the mean-versus-dispersion
trade the widen arm showed (its pitch overshoot fell to about a third while its mean attitude error
rose). Damage concentrates on roll, then pitch; no yaw metric moved a floor at any level, which fits
roll being where buoyancy and CoG asymmetries put the sustained offsets.

**The pre-registered null-to-small expectation was half wrong, and that half is the finding.** It
was justified by the policy already receiving an ungated 3D bias-EMA buffer (_bias_ema, P-B1)
carrying sustained bias with no gate at all. That held for widening. It did not hold for narrowing:
the parallel ungated path does not rescue a too-narrow gate, so whatever _bias_ema supplies is not a
substitute for the gated integral channel on roll.

**Method notes that make the negative quotable.** Pairing was verified before any metric was read —
23 of 23 per-env draw arrays elementwise identical at all four levels for both arms against both
E-int baselines. Single-variable was verified from the runs' own recorded params: agent.yaml
identical line for line, env.yaml differing only in the three gate values once base64 pickle blobs
and run-identity fields are excluded. Survival is 100 percent everywhere except the narrow arm at
hard (98.44, one env of 64), below the 1.6 pp floor, so no level is survivorship-contaminated.

**An independent instrument agrees.** The narrow arm was already worst during training, before any
eval: last-500-iteration reward 251.8 against a performance_lb of 250.0 and DORAEMON success rate
0.5849 against alpha 0.5, which throttled its own curriculum to 17 box expansions versus 18 for the
widen arm and 19 for E-int. All three runs carry byte-identical DORAEMON constraints. DORAEMON
success is episode_return >= performance_lb (doraemon.py line 306), a reward threshold with no
dependence on the gate observation, so the treatment cannot contaminate that criterion.

**Limits.** One seed per arm. The pairing and single-variable checks make the ranking solid, but a
single seed cannot fix the shape of the curve between 0.05 and 0.20 or prove 0.10 is the true
optimum rather than merely better than both probes. E-int also reached 5000 as a resume chain while
both arms are fresh runs, so only widen-versus-narrow is a clean same-protocol comparison; the
reference sitting above both is consistent but confounded.

Results SSOT: experiments/rsl_rl/albc_trpo_teacher/teacher_integral_gate/README.md.

