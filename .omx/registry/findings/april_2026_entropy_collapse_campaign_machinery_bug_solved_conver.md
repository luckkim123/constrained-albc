---
title: "April 2026 entropy-collapse campaign: machinery bug SOLVED, converged-sigma collapse NOT -- and min_std is the wrong lever"
tags: ["entropy", "exploration", "noise_std", "min_std", "entropy_coef", "per-dim", "legacy-campaign", "april-2026", "erc-trpo", "limit-cycle", "backlog-correction", "rule03", "std_min", "posttam", "zero-gpu"]
created: 2026-07-20T06:08:58.240967
updated: 2026-07-20T07:10:35.387858
sources: ["docs/reference/experiments-archive.md", "docs/reference/experiments-index.json", "3132605", "d7c65c3", "885327a", "26b2f54", "constraint_encoder_runner.py:366-367", "TB Noise/std_min 5 posttam runs"]
links: ["n_gt20_and_os_env_are_overshoot_percent_of_step_magnitude_not_de.md"]
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: needs-experiment
blocked-on: "Item 1 THRUSTER half CLOSED 2026-07-20 via Noise/std_min (biasema+extend8k clamped at 0.05; baseline/perflb/moreiters not clamped). ARM half still needs the per-dim log_std read from model_7999.pt -- zero-GPU, unblocked. Item 2 (training probe) parked under the 2026-07-20 batch-pass decision."
---

# April 2026 entropy-collapse campaign: machinery bug SOLVED, converged-sigma collapse NOT -- and min_std is the wrong lever

The exploration/entropy collapse now flagged every run in `teacher_baseline_posttam` is NOT a new
finding. A 49-run campaign (2026-03-27 ~ 04-22) attacked it directly, found the root cause, shipped
two fixes that are still in HEAD config, and then closed with the problem explicitly recorded as
UNRESOLVED. None of that had ever been migrated into the omx wiki, so 2026-07 sessions keep
re-deriving it from scratch. This page is the migration.

## Where the campaign records live

- Narrative: `constrained-albc/docs/reference/experiments-archive.md` (168 lines, round-by-round).
- Machine index: `constrained-albc/docs/reference/experiments-index.json` (49 runs +
  `settled_decisions[]`, sourced from changelogs that were compressed away 2026-05-25).
- Plots only: `constrained-albc/experiments/legacy/plots/rsl_rl/fulldof_albc/2026-04-*_r{9..13}*`.
- Surviving checkpoints: ONLY `experiments/legacy/final_models/r13_{A,B}/model_4999.pt`.
- GONE by documented decision (2026-05-25, `experiments/legacy/README.md`): all April TensorBoard
  event files, all wandb data, all other checkpoints. Reason recorded: the 3-repo split
  (isaaclab -> marinelab -> constrained-albc) + `marinelab.core` OceanCurrent API migration means
  the runtime that produced them no longer exists, and no April run ever passed `play`. Do NOT go
  looking for April TB data; it is not recoverable.

## SOLVED (and still in HEAD config)

1. **Root cause: `log_std` was outside the trust region.** It was being updated by a SEPARATE Adam
   optimizer, not by the TRPO natural-gradient step. Commit `3132605` (04-10) folded it back in;
   the message records the symptom it cured: entropy 8.5 -> 0.7 in 4500 iters. Same commit removed
   the SAC-style adaptive-entropy experiment.
2. **`entropy_coef` is the SOLE upward pressure on sigma.** A/B preserved as a code comment at
   `envs/main/agents/rsl_rl_ppo_cfg.py:230-232` and in the archive: coef=0.003 recovers noise
   0.36 -> 0.55 (run 04-09); coef=0 collapses to 0.12 (run 04-10). Restored by `d7c65c3` (04-13).
3. **Per-dim entropy coef (PerDimEnt) beat uniform.** Round 1 (04-14, `885327a`): arm=0.01 /
   thr=0.001 vs uniform 0.003 -> reward +5.6%, att_rp 5.03 deg (+9.1%), smoothness 2.2x better.
   Round 2 (04-14~15, kl_ub=0.06, 2048 envs/5000 it, `d0a3370`): PerDimEnt best (reward 151.3,
   DORAEMON success 0.811). **The key ingredient is the THRUSTER REDUCTION, not the arm boost** --
   the ArmOnly arm (thr=0.003) was WORSE than baseline because the arm boost propagates to
   thrusters and diverges (thr std 1.36). Still the permanent config today.
4. **Per-dim `min_std`** (`b64c6e6`, 04-13): arm 0.10 / thruster 0.05, because arm dims hit the
   scalar floor by iter 1404 while thrusters stayed above 0.14.

## REJECTED (do not re-propose without new argument)

- **SAC-style adaptive entropy** (learnable log_alpha): added `68f3b8a` (04-10), disabled `2effa17`
  three days later.
- **ERC-TRPO** entropy-regularized trust region (Neurocomputing 2024): `19300ae` -> `51a8011` ->
  reverted `03aafe4` SAME DAY. Failure mode: the hard entropy floor froze policy updates after
  iter ~53, reward stuck at -306.
- **`max_std` cap 2.0 -> 1.0** (Round 1): negligible, no dim ever hit the cap.
- **Raising `entropy_coef` to fight collapse, pre-campaign**: run `asym_ent0.001` (03-30,
  DEPRECATED project) set entropy_coef=0.001 explicitly "to fight noise_std collapse" -> roll
  WORSENED 9.77 -> 13.59 deg, reward -17.49. Recorded verdict: "entropy bonus interfered with
  exploitation".
- **r14** (04-21, `26b2f54`): entropy reduction + aggressive HardDR + action_latency + latent=16,
  20000 iters. Verdict in index.json: **rejected** -- the DR widening made teacher labels OOD for
  student BC; r14 was removed and r13_A restored byte-identically (`f05ca6f5`). It never produced
  a kept policy, and its thruster `entropy_coef` reduction is NOT in HEAD (HEAD is 0.001).

## NOT SOLVED -- the campaign said so itself

`experiments-archive.md:134-136`, the R9 verdict: "BEST POLICY is a historical training-metric
label only -- open items (yaw OS, roll variance, **universal entropy collapse**) remained
unresolved and no successful training run was confirmed."

So the correct framing for 2026-07 is: the *machinery bug* was fixed in April and stayed fixed; the
*converged-sigma-is-tiny* phenomenon was never solved and has kept tightening since.

## Sigma across campaigns (the trend that matters)

| when | run | sigma |
|---|---|---|
| 2026-04-20 | r13_B (thruster dims) | 0.22 - 0.34 |
| 2026-06 | baseline / state_std | 0.175 / 0.167 |
| 2026-07-13 | `trpo_baseline_260713_031325` | 0.109 |
| 2026-07-14/15 | posttam baseline / perflb200 | 0.0995 / 0.0985 |
| 2026-07-16 | `trpo_biasema_extend8k` | 0.084 |

## CORRECTION: `min_std` is the wrong lever (two independent reasons)

The backlog "item 10" lead and several posttam reports name `min_std` (0.05) as a candidate probe
and describe noise_std as "pinned near the min_std=0.05 floor". Both are wrong:

1. **The scalar `min_std` is dead code in this config.** `constraint_trpo.py:507-511` takes the
   `_log_min_std` (per-dim) branch whenever `min_std_per_dim` is set, and it IS set
   (`rsl_rl_ppo_cfg.py:246` = `(0.10, 0.10, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05)`). Raising the
   scalar `min_std=0.05` is a NO-OP and would produce a meaningless null result.
2. **min_std was already shown not to bind.** Commit `26b2f54` states it outright for r13_B:
   "thruster std 0.22-0.34 (4-6x above min_std floor 0.05) ... **min_std was NOT binding; per-dim
   entropy IS**." There was also a dedicated probe run for this, `r10_thr_minstd` (04-19).

If exploration is probed at all, the single variable is `entropy_coef_per_dim` (thruster leg), and
the effective floor to reason about is arm 0.10 / thruster 0.05, not the scalar.

**Open sub-question (zero GPU, not yet done):** posttam `Policy/mean_noise_std` is a MEAN over 8
dims. If the two arm dims sit at their 0.10 floor, the mean of 0.084 implies thrusters ~0.079 --
i.e. 1.6x above their floor, nothing pinned. Confirm by reading the PER-DIM log_std from a
checkpoint (`experiments/.../trpo_biasema_extend8k_260716_162849/train/model_7999.pt`) instead of
the aggregate scalar. Until that is done, no report should assert which dims are floor-bound.

## Sigma has a TWO-SIDED failure mode

Reviving exploration is not free. The campaign documented the opposite failure: r13_B showed a
0.87 Hz roll limit cycle (`roll_fft_magnitude` 112) and `26b2f54` attributed it to excess thruster
std acting through the weak TAM roll arm (0.007 m). Caveat on attribution: index.json records that
r13_B's limit-cycle amplitude was **20x stronger than r13_A**, and the only difference was
`encoder_latent_dim` 9 vs 16 -- so latent dim is a competing explanation for the amplitude, and the
"excess thruster std" attribution in the commit message is not independently confirmed.

Related, from the same index: `r11_encdim16` (latent 9 -> 16) produced **policy entropy +94%** --
the largest entropy movement any single non-entropy-config intervention produced in the campaign.
Encoder latent width is an untested indirect lever on actor entropy.

## Also in the archive (adjacent, different failure)

Pre-campaign encoder ablation (03-27~03-30, 20+ single-variable runs): the root cause of
encoder-co-training instability was `sample().clamp(-1,1)` in `ActorCriticEncoder.act()` piling
actions at the boundary -> KL spikes 100x -> LR crash, with a secondary env-clamp / unclamped-buffer
positive-feedback loop that drove `noise_std` to **148**. That is sigma DIVERGENCE, the opposite
pole, and it is why the current design samples raw Gaussian with an external clamp.

---

## Update (2026-07-20T06:10:36.535973)

## Actionable status (2026-07-20): carry this page into the batch planning pass

Marked needs-experiment so the batch pass enumerates it automatically rather than re-deriving the
April history a fourth time. Two concrete open items, in cost order:

1. ZERO-GPU, unblocked: read PER-DIM `log_std` from an extend8k checkpoint
   (`experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/train/`)
   to establish which action dims are actually floor-bound. `Policy/mean_noise_std` is an 8-dim
   mean and cannot answer it. Every current claim about "pinned at the floor" rests on that mean.
2. TRAINING probe, only if (1) shows a dim genuinely bound: single variable =
   `entropy_coef_per_dim` thruster leg. NOT `min_std` (dead scalar), NOT the DORAEMON gate
   (refuted as causally independent). Must be weighed against the r13_B roll limit-cycle
   precedent, whose attribution to thruster std is itself unconfirmed (latent=16 is a competing
   cause, 20x amplitude difference vs r13_A).

Untested indirect lever worth a line in the batch plan: `encoder_latent_dim` 9 -> 16 produced
policy entropy +94% in `r11_encdim16` -- the largest entropy movement of the whole April campaign,
from a non-entropy config knob. It is not currently on any roster.

---

## Update (2026-07-20T07:10:35.387858)

## Item 1 PARTIALLY CLOSED (2026-07-20, zero-GPU): `Noise/std_min` answers the thruster half from TB

The open sub-question above ("read the PER-DIM log_std from a checkpoint; until that is done no
report should assert which dims are floor-bound") does NOT need a checkpoint read for the thruster
leg. `Noise/std_min` is already logged every iteration and is exactly the min over the 8 per-dim
sigmas (`constraint_encoder_runner.py:366-367`, `policy.log_std.exp().min()`). Read directly from
each run's TB event file:

| run | `Noise/std_min` | `Noise/std_mean` | thruster floor (0.05) binding? |
|---|---|---|---|
| `trpo_baseline_260714_192020` (5k) | 0.0604 | 0.0993 | NO (1.21x above) |
| `trpo_perflb200_260715_023744` (5k) | 0.0607 | 0.0985 | NO (1.21x above) |
| `trpo_perflb200-moreiters_...` (8k) | 0.0580 | 0.0958 | NO (1.16x above) |
| `trpo_biasema_260715_142543` (5k) | **0.0500** | 0.0860 | **YES -- exactly at floor** |
| `trpo_biasema_extend8k_...` (8k) | **0.0500** | 0.0838 | **YES -- exactly at floor** |

Reasoning: the per-dim floors are arm 0.10 / thruster 0.05, so any `std_min` below 0.10 must belong
to a THRUSTER dim. A value strictly above 0.05 therefore proves no thruster dim is clamped; a value
of exactly 0.05 proves at least one is.

**This splits the campaign in two, and the split matters for lever selection.** The two `biasema`-
lineage runs ARE floor-clamped on at least one thruster dim, so for THOSE configs raising
`min_std_per_dim`'s thruster leg is a live intervention, not a no-op. The three baseline/perflb
runs are not clamped at all, so for them the floor is genuinely irrelevant. Any statement about
"the campaign" that picks one of these two behaviours and generalises it is wrong -- state the run.

**What is STILL open (the arm half).** `std_min` cannot see the arm dims: their floor is 0.10, which
is above every `std_min` observed, so an arm dim sitting exactly at 0.10 would be invisible here.
Establishing whether the arm dims are floor-bound still requires the per-dim read from a checkpoint
(`.../trpo_biasema_extend8k_260716_162849/train/model_7999.pt`). That remains zero-GPU and unblocked.

**Unaffected by this update:** the scalar `min_std` is still dead code (the per-dim branch is taken
whenever `min_std_per_dim` is set), so a probe that raises the SCALAR is still a no-op on every run
above -- the numerically-identical 0.05 that binds in the biasema runs is the per-dim thruster entry,
not the scalar. And the campaign-wide entropy collapse is still unexplained by the floor: three runs
collapse to sigma ~0.096-0.099 with no clamp firing at all.

Metric-naming caveat in the same family: [[n_gt20_and_os_env_are_overshoot_percent_of_step_magnitude_not_de]].

