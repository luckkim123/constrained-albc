---
title: "Closed-loop latent collapse suspicion: legacy student measured 11-17x worse in-loop, deployed student unverified"
tags: ["experiment-lead", "distillation", "covariate-shift", "latent", "student", "sim-to-real", "eval", "albc", "priv-obs"]
created: 2026-07-21T10:03:29.000311
updated: 2026-07-24T03:34:55.200764
sources: []
links: ["albc_stage_2_is_teacher_driven_off_policy_bc_with_mixed_latent_a.md", "experiment_idea_feed_o_t_into_the_encoder_alongside_p_t_state_co.md", "next_from_scratch_retrain_manifest_what_rides_on_the_post_tam_ba.md", "student_distillation_converges_to_a_residual_that_rules_out_late.md", "engine_gap_eval_npz_saves_no_raw_obs_std_privileged_blocks_exact.md"]
category: decision
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: resolved
blocked-on: "Both E4 eval fixes PUSHED to origin/main (9de2da1->88e0849, 2026-07-24): b751d22 teacher + 88e0849 student. DGX unblock = git fetch + checkout origin/main (no patch relay). Then re-run E4 (cross-machine, DGX unreachable from workstation). Prompt v3+: .sp/plans/2026-07-24-dgx-C4a-prompt.md"
---

# Closed-loop latent collapse suspicion: legacy student measured 11-17x worse in-loop, deployed student unverified

A legacy student's latent estimate degraded 11-17x when it drove the loop itself, versus its
open-loop training residual. The DEPLOYED student has never been run through this diagnostic. The
honest statement is "there is precedent for collapse and the deployed checkpoint is unverified",
NOT "the student collapses".

## The instrument already exists -- zero new code

`constrained_albc/analysis/eval.py` student mode runs the student IN THE LOOP and writes
`latent_<level>.npz` (`l_hat`, `l_true`) plus `summary_latent.json` across all four DR levels.
`_summarize_latent` (`eval.py:897-915`) emits `overall_mse`, `per_dim_mse`, `l_true_envvar_mean`,
`l_hat_envvar_mean`, `l_true_tvar_mean`, `l_hat_tvar_mean`, `per_env_rmse_mean/std`. The probe
below is one eval invocation, not an engineering task.

## Legacy measurement (`trpo_student_tcn_260526_043607`, 87D-era, training loss_latent 0.0144, 4 envs)

| DR level | in-loop latent MSE | `l_true_envvar_mean` | ratio |
|:--|--:|--:|--:|
| none | 0.1612 | 0.0 | (undefined -- see below) |
| soft | 0.2058 | 0.0297 | 6.9x |
| medium | 0.2500 | 0.0659 | 3.8x |
| hard | 0.1942 | 0.0800 | 2.4x |

The in-loop error is 2-8x LARGER than the env-to-env variance the latent is supposed to resolve
(R^2 deeply negative -- predicting the global mean would beat it), and 11-17x worse than the same
student's open-loop training residual.

## The decisive row is `none`

At DR level `none`, `l_true` is a CONSTANT: `l_true_envvar_mean` = 0.0 and `l_true_tvar_mean` ~ 1e-9
(the privileged vector is the fixed DR parameter set). Yet the in-loop error is 0.161, and `l_hat`
itself moves -- envvar 0.062, tvar 0.0019. A student estimating a constant should output a constant.
Instead it is being dragged around by the instantaneous state.

That signature is **covariate shift**, not multimodality: the student is reacting to states its
training distribution never contained. The teacher-driven rollout documented in
[[albc_stage_2_is_teacher_driven_off_policy_bc_with_mixed_latent_a]] is the direct candidate cause --
the student is never trained on the distribution it induces.

## UNVERIFIED -- state this every time

The deployed pack_B student `trpo_student_tcn_260629_085241` has **never** had this diagnostic run.
The legacy student differs on three axes at once: 87D-era observation space, only 4 eval envs, and a
training `loss_latent` (0.0144) about 4x worse than the deployed student's 0.00493. The legacy
numbers are a precedent, not a measurement of the deployment.

## Next probe (this lead's experiment)

Run `eval.py` student mode ONCE using the student + teacher checkpoints named in pack_B's
`MANIFEST.json`, then compare `summary_latent.json`'s per-level in-loop MSE against the same level's
`l_true_envvar_mean` -- the same table as above, for the deployed checkpoint. The run also yields, for
free, the task-metric oracle gap: teacher driven by `z_gt` vs student driven by `z_hat`.

WARNING -- do NOT auto-launch training. If any retrain follows from the result, queue it via
`omx queue-launch` and stop at the human gate.

## Related

- [[experiment_idea_feed_o_t_into_the_encoder_alongside_p_t_state_co]] -- the state-conditioned-z
  idea meshes directly with this observation; if z is already a function of `o_t`, the student's
  state-dragging behavior changes meaning.
- [[next_from_scratch_retrain_manifest_what_rides_on_the_post_tam_ba]] -- decide whether this lead
  earns a line in the retrain manifest (it is a diagnosis probe, not a code change, so it likely
  does NOT block the retrain -- but the decision should be recorded there rather than left implicit).
- [[student_distillation_converges_to_a_residual_that_rules_out_late]] -- the open-loop bound whose
  scope limit this page is.
- [[engine_gap_eval_npz_saves_no_raw_obs_std_privileged_blocks_exact]] -- adjacent eval-npz coverage gap.

---

## Update (2026-07-21T10:16:52.443487)

## Connection to A4 (priv-obs slim, 2026-07-21)

A4 (`trpo_privslim24d_260721_114717`) dropped `root_lin_vel_b` from the teacher's
privileged vector and failed every eval clause of its band (`none` roll ss_error +73.6%,
pitch +95.3%), resolving `lin_vel` as LOAD-BEARING rather than redundant: `envs/main`'s
`compute_policy_obs` is 20D and carries no linear velocity in any form ("no DVL on real
robot"), so the privileged channel was its only route into the network.

That matters here because the student's observation is the 69D attitude-only history --
it likewise cannot see linear velocity directly. Whatever the teacher was doing with
`lin_vel`, the student must reconstruct from its observation history alone. A4 confirms
the channel is one whose removal collapses tracking, which raises the prior that
in-loop student degradation is concentrated on exactly the latent content `lin_vel`
drove (the anchor z_sweep shows Lin Vel U/V/W driving 9/9, 9/9 and 8/9 latent dims).

This is CIRCUMSTANTIAL, not evidence: A4 measured a teacher ablation, not a student
reconstruction failure, and a history-based estimator may well recover the signal.
The discriminating measurement is the next probe's `per_dim_mse` -- if the latent dims
that `lin_vel` drives carry disproportionate error relative to the other dims, the
suspicion is supported; if the error is flat across dims, this connection is refuted
and the in-loop gap lies elsewhere.

---

## Update (2026-07-24T02:01:10.735263)

## 2026-07-24 -- E4 (C4a in-loop latent diagnostic) DGX attempt: BLOCKED-then-DISPROVEN (obs-gate misdiagnosis)

E4 (proposal `next-20260724-034543`) was dispatched to the DGX and returned BLOCKED at its obs-width
gate: "buoyfix checkpoints are obs=72 but current code builds obs=69; 72 never committed; obsolete
artifact; re-scope or reconstruct." Disproven against workstation code the same day -- the block is
spurious; E4 is runnable.

FINDING: the buoyfix checkpoints (obs=72) MATCH the current env (obs=72). No obsolescence.
EVIDENCE:
- Current main-lineage code builds obs=72, not 69: `config.py:419 use_bias_ema_obs: bool = True`
  (standing default since P-B1 adoption commit `f42a67f`, 2026-07-16); `apply_bias_ema_obs`
  (`config.py:615`) does `observation_space 69 -> 72`. The DGX's own `main @ 9de2da1` CONTAINS
  `f42a67f` (`git merge-base --is-ancestor f42a67f 9de2da1` => true), so even the DGX revision builds 72.
- The `policy_obs_dim=69` the DGX read is an agent-cfg BASE default, synced to the env width at
  runtime -- never binding: `sync_policy_obs_dim` (`envs/_core/runners/__init__.py:13`, docstring
  "main's use_bias_ema_obs bumps it 69 -> 72 ... without this sync the actor/critic/encoder build at
  the wrong input width"); `eval.py:1184` "Encoder policies build at the env's real obs width (69->72
  with use_bias_ema_obs)"; `teacher.py:100` checkpoint-geom overrides cfg. There is NO `policy_obs_dim`
  literal in `envs/main/config.py` at all.
- Buoyfix student `trpo_buoyfix_s30_tcn_260722_184632/models/student_999.pt`: `cfg.policy_obs_dim=72`
  (direct load); trained 2026-07-22, AFTER bias-EMA adoption -- i.e. the CURRENT standing 72, not the
  old dropped-terms 72.
CONFIDENCE: high

ROOT CAUSE of the false block: (1) the E4 prompt embedded a stale 2026-07-23 claim ("9de2da1 builds
obs=69") into its gate; (2) the DGX executor never launched eval -- it inferred incompatibility from
static checkpoint tensors vs that stale literal, contrary to the prompt's own "just run the eval"
fallback. Both report recommendations -- (a) re-scope to a 69-obs student (none exists; current
students are 72) and (b) reconstruct a 72-obs env (already the standing default) -- rest on the false
premise; NEITHER is warranted.

CROSS-ROOT DRIFT: the DGX-side omx wiki (root `/home/seungmin/workspace/constrained-albc`, slug
`e4_buoyfix_student_latent_diagnostic_blocked_checkpoints_are_obs`, status needs-experiment) records
the WRONG block finding and must be corrected on that root by the next DGX session.

NEXT: E4 remains needs-experiment (the in-loop latent measurement still has not been produced).
Corrected DGX prompt at `.sp/plans/2026-07-24-dgx-C4a-prompt.md` -- verify `use_bias_ema_obs=True` on
the DGX checkout, then LAUNCH eval (do not infer from static tensors). Checkpoints already relay-copied
to the DGX; no re-transfer.

---

## Update (2026-07-24T02:32:54.512785)

## 2026-07-24 (v3) -- E4 2nd attempt LAUNCHED: true cause is a STALE DGX CHECKOUT, not a code bug

E4 was actually launched on the DGX this time (cuDNN enabled). The buoyfix teacher (obs=72) failed to
load: `FrozenTeacher` built at obs=69 -> shape mismatch (actor.0.weight ckpt[256,81] vs [256,78];
actor_obs_normalizer._mean ckpt[1,72] vs [1,69]; gap = the 3 bias-EMA dims). The DGX diagnosed "a code
bug in eval.py student-mode teacher construction, fails identically on the workstation."

FINDING: NOT a live bug -- the DGX is on a STALE checkout; the fix already exists and is verified.
EVIDENCE:
- The teacher-geometry fix is commit `b751d22` (2026-07-22 18:46, "fix(student): build the frozen
  teacher from its checkpoint geometry, not StudentCfg defaults"): `infer_teacher_geometry`
  (`_core/student/teacher.py:41`) reads obs/priv/latent widths off the teacher checkpoint tensors;
  `FrozenTeacher.__init__` builds `ActorCriticEncoder(policy_obs_dim=geom[...])` from it. Its own commit
  message records the 72D teacher loading + student building + entering `learn()`. This is EXACTLY the
  DGX report's recommended fix (option 2, "auto-infer teacher obs width from ckpt") -- already
  implemented, not something to write.
- The DGX is on `main @ 9de2da1`, which PREDATES `b751d22` (`git merge-base --is-ancestor b751d22
  9de2da1` = false). On the workstation HEAD and on `main`, `main/student/teacher.py` is a shim ->
  `_core`, which HAS the fix; the student-eval path loads the 72D teacher fine. The DGX's "fails
  identically on the workstation" claim is WRONG.
- The fix is on local `main` but NOT on `origin/main`: local `main` is 28 commits ahead of `origin/main`
  (clean fast-forward). The DGX pulled `9de2da1` from the stale `origin/main`.
CONFIDENCE: high

UNBLOCK (no eval.py edit): land `b751d22` on the DGX, then re-run the exact command. Either (A) push
local main -> origin (user-gated) + DGX syncs to current main, or (B) relay the patch
`.sp/plans/b751d22-teacher-geom-fix.patch` (verified to `git apply` clean onto 9de2da1; touched files
byte-identical between 9de2da1 and the patch base) with no push. Corrected prompt v3:
`.sp/plans/2026-07-24-dgx-C4a-prompt.md`. E4 remains needs-experiment (the in-loop latent measurement
still has not been produced).

---

## Update (2026-07-24T02:46:05.594650)

## 2026-07-24 (v4) -- E4 has a SECOND obstacle (student load), now fixed: bf44964

After the teacher-load fix (b751d22, stale-checkout, v3 above), a second obstacle in the SAME eval
path was found by reading the code: `StudentInLoopPolicy.__init__` (`analysis/student_policy.py`)
restores the student's TCN/GRU arch fields from its saved cfg but NOT `policy_obs_dim`, leaving
`StudentCfg`'s stale default 69. With `use_bias_ema_obs` at 72, `make_student_encoder` then builds the
channel transform `nn.Linear(69, 32)` while the buoyfix student checkpoint's `channel_transform.0.weight`
is (32,72) -> a second `load_state_dict` shape mismatch, one line after the teacher one.

FINDING: genuine code bug in the eval student path, distinct from b751d22; now fixed + tested.
EVIDENCE:
- Proven by direct checkpoint load (plain torch): student `channel_transform.0.weight` = (32,72),
  `saved_cfg["policy_obs_dim"]` = 72, but `StudentCfg.policy_obs_dim` default = 69
  (`_core/student/config.py:37` -- this is the "config.py:37 policy_obs_dim=69" the FIRST DGX attempt
  misread as the env obs). `student_policy.py` restores only the `tcn_*` fields, never `policy_obs_dim`.
- FIX commit `bf44964` (branch `fix/student-eval-obs-width`): restore `cfg.policy_obs_dim` from the
  student's saved cfg before building the encoder + ring, and raise a named error on a student/teacher
  obs-width disagreement (mirrors b751d22's teacher/env guard). Sim-free test
  `tests/test_student_eval_obs_width.py` (2 passed): the TCN encoder width tracks `policy_obs_dim`, a
  72D checkpoint refuses to load into a 69D-built encoder (the exact DGX RuntimeError) and loads clean
  at 72D.
CONFIDENCE: high

UNBLOCK (updated): E4 needs BOTH fixes on the DGX -- `b751d22` (teacher) AND `bf44964` (student).
Relay both patches (`.sp/plans/b751d22-teacher-geom-fix.patch` + `.sp/plans/bf44964-student-eval-obs-width.patch`,
both verified to `git apply` clean onto 9de2da1), apply in order, then re-run. Syncing to origin/main is
NOT sufficient -- b751d22 is on main but bf44964 is not yet (unpushed fresh fix). FOLLOW-UP hygiene:
cherry-pick bf44964 onto main (deferred -- blocked now by uncommitted .omx divergence on the working
tree). E4 remains needs-experiment (measurement still not produced). Prompt v3+:
`.sp/plans/2026-07-24-dgx-C4a-prompt.md`.

---

## Update (2026-07-24T03:02:54.840166)

## 2026-07-24 (v5) -- fix bf44964 cherry-picked to main (88e0849)

bf44964 is now on `main` as **88e0849** (cherry-pick -x). `main` therefore carries BOTH E4 eval
fixes: b751d22 (teacher) + 88e0849 (student obs width). Still NOT on origin/main (unpushed). So the
DGX now has two delivery options: (a) if main is pushed, `git fetch && checkout origin/main` gets
both; (b) no-push patch relay of the two .patch files (still valid). The "origin/main sync alone
insufficient" caveat from v4 is SUPERSEDED -- main now has both, it is just unpushed.

---

## Update (2026-07-24T03:05:53.032386)

## 2026-07-24 (v6) -- both E4 fixes PUSHED to origin/main

`git push origin main` done (user-approved): `origin/main` went `9de2da1 -> 88e0849`, now carrying
BOTH b751d22 (teacher) + 88e0849 (student). DGX unblock is now a plain `git fetch origin && git
checkout main && git pull` (no patch relay). origin/main is fully current (was 29 behind). The
stale-checkout root cause (DGX pulled 9de2da1 from a lagging origin/main) is closed. Remaining: the
DGX-side fetch + E4 re-run itself (cross-machine; workstation session cannot reach ksm-nas).

---

## Update (2026-07-24T03:34:55.200764)

## 2026-07-24 (v7) -- E4 RAN TO COMPLETION: closed-loop latent collapse CONFIRMED severe

E4 executed on the DGX after the two obs-width fixes landed (git pull 9de2da1->88e0849; clean 72D
teacher+student load, cuDNN on, all 4 DR levels, no OOM). Result (`summary_latent.json`; base open-loop
residual 0.002145):

| level | overall_mse | xBase | l_true_envvar | l_hat_envvar |
|:--|--:|--:|--:|--:|
| none | 0.15584 | 72.7x | 0.01908 | 0.00347 |
| soft | 0.16190 | 75.5x | 0.02590 | 0.00356 |
| medium | 0.16829 | 78.5x | 0.04382 | 0.00801 |
| hard | 0.17613 | 82.1x | 0.09522 | 0.01302 |

VERDICT: H2 (healthy) DECISIVELY RULED OUT -- in-loop overall_mse is 72-82x the open-loop base at EVERY
level and >> l_true_envvar everywhere (the student adds far more error than the cross-env variance it is
supposed to resolve; H2 required <= 0.0043 at every level). The pre-registered STRICT score is
INCONCLUSIVE only because the "constant-target" signature does not hold: l_true_envvar is nonzero at
`none` (0.019) and GROWS with DR (-> 0.095 hard), so the teacher latent is not a constant even at
nominal -- consistent with ocean current ENABLED (per-env current realizations vary at `none`) +
privileged per-env variation. Substantively the result is UNAMBIGUOUS: severe closed-loop latent
degradation. Failure mode = the student UNDER-disperses (l_hat_envvar << l_true_envvar at every level,
0.013 vs 0.095 at hard) -- it collapses toward a near-constant latent and fails to track the cross-env
variation the teacher expresses. Covariate-shift-consistent.

STATUS: the diagnostic question ("does the current-recipe buoyfix student collapse in-loop?") is
ANSWERED -- CONFIRMED severe; the deployed/current-recipe student is no longer "unverified". This lead
is RESOLVED as a diagnostic. NEXT (new experiment, human-gated): an on-policy (DAgger-style)
distillation correction before any deployment claim -- see the follow-up lead
`on_policy_dagger_correction_for_the_buoyfix_student`. Raw artifacts
(`summary_latent.json`/`latent_*.npz`/`*.png`) are on the DGX at
`logs/rsl_rl/albc_trpo_student/trpo_buoyfix_s30_tcn_260722_184632/models/eval_dr/` and must be pulled
(rsync from the Mac; the workstation cannot reach ksm-nas) into the experiments tree for a full
exp-analyze. DGX-root parallel finding: `e4_measured_buoyfix_student_in_loop_latent_mse_is_72_82x_its_ope`.

CONFIDENCE: high

