# Program: dgx-final-teacher — the last training round for the ALBC teacher

**Status: PLAN ONLY — this document authorizes NO launch.** Both runs named here are queued
pending-approval; `omx queue-launch` queues, it does not run.

Created 2026-08-09, revised the same day after the G0 gate ran and after four rounds of user
steering. Supersedes `dgx-final-scaleup` as the active program: that program's question (does a 4x
env budget buy anything) is answered and closed. This one asks what configuration maximizes the
FINAL teacher under the constraints that actually hold today.

Evidence base, all read from disk on 2026-08-09, nothing recalled:
`teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md`;
`teacher_iter_budget/README.md`; `teacher_baseline_buoyfix/.../diagnose-20260723-134359/report.md`;
`.omx/programs/dgx-final-scaleup/{PLAN,HANDOFF-DGX}.md`; `.omx/programs/backlog-closeout/PLAN.md`;
`constrained_albc/envs/main/config.py`, `doraemon.py`, `agents/rsl_rl_ppo_cfg.py`; omx wiki
(527 pages); TB event files of five runs; the G0 evals run today.

---

## Objective (user, verbatim)

> "다음 실험을 dgx에서 진행할껀데, num envs나 max iter 같은 경우는 늘리기는 하되
> claude의 판단에 맡기는거야. num envs가 3만이 과하다 하면 줄여도 괜찮고, max iter도
> 마찬가지로 20,000 정도가 과하다 하면 낮춰도 괜찮아. 어쨌든 중요한건 **최고의 성능이
> 나오도록 학습**할 수 있게 하면 되고, **관련된 결합 파라미터도 파악해서 수정**하는거지.
> marinelab에 여러 실험 기록이 있으니 그걸 참고하고. **이 한번을 마지막이라고 생각하고
> 꼼꼼하게 분석 및 조사 후 계획**을 세우도록 하고, 지금 현재 완료된 dgx 실험의 결과도
> 포함해서 분석하도록 말이야."

Every decision below is argued against that line. Where readability, single-variable isolation or
comparability would cost performance, the trade is escalated to §Decisions for the user rather than
resolved here.

---

## The lever this plan is built on — expansion RATE, not box width or env count

The 16k report named the declared DR bounds as the binding constraint, and widening them is blocked
(§Decisions D5). But there is a second way to change what the policy experiences without touching
the bounds: **change how fast the curriculum walks to them.** That lever was never tested on this
plant, and three independent pieces of the record point at it.

**1. The project already named it as the untested cell.** omx wiki
`kl_ub_up_and_per_difficulty_learning_are_antagonistic`, written 2026-06-14 in answer to a nearly
identical user question:

> "The untested cell is: raise the difficulty target and/or extend max_iter, while keeping `kl_ub`
> LOW so per-difficulty dwell-time stays high. That combination was never run."
> "Do NOT read the dr_harder pages as 'kl_ub is forbidden'. Read them as 'on a FIXED 5000-iter
> budget, kl_ub-up buys reach by spending attitude'."

**2. The causal direction is measured, not assumed.** The E1-vs-E2 orthogonal factorial reached the
SAME final difficulty (ocean coverage 0.421 vs 0.409) with OPPOSITE attitude outcomes (E1, which
raised `kl_ub` 0.06 -> 0.12: hard roll/pitch +34/+69% WORSE; E2, which reached the same difficulty by
shifting the nominal: attitude kept). A deterministic E4 control made this causal rather than seed.
**Expansion speed is the attitude-killer; reached difficulty is not.** The mechanism the wiki
records is "fewer gradient steps spent per unit of difficulty" — a bigger jump inside an unchanged
250-iteration dwell window under-trains the policy relative to the new distribution.

**3. The reason `kl_ub` = 0.12 was adopted has expired.** `config.py:605-607`, verbatim:

> "kl_ub 0.06 -> 0.12: doubles the per-step trust region so the distribution widens fast enough to
> **compensate for the slower expansion that the raised lb induces**. Both levers move together by
> design."

So 0.12 is a compensation for a *budget shortfall* at 5000 iterations with `lb` = 250 — not a claim
that fast expansion is good. At 20000 iterations the same reach is bought with iterations instead,
and the three-lever table is explicit that `max_iterations` UP has "**none on the curriculum itself;
only wall-clock cost**" while `kl_ub` UP under-trains each difficulty.

### The one measurement that looked like a refutation does not test this

`trpo_stepint400_260720_180208` (si 250 -> 400) is on record as "the worst of three arms at the fair
`none` level", and the previous plan used it to keep si at 250. Its actual config, read today:
`max_iterations: 8000`, `step_interval: 400`, `kl_ub: 0.12`.

Expansion budget = (8000/400) x 0.12 = **2.40 KL**. Saturation on that same posttam plant needed
**3.12** (extend8k, 26 boundaries x 0.12). So stepint400 was **23% short of the budget required to
saturate and could not have reached the box ceiling.** Its poor result is confounded with
under-saturation — precisely the failure the recalibration protocol names ("widen at a fixed budget
and the run stops short of the new bound: the same exam, arrived at later").

A slow ramp WITH the budget to finish it has never been run. That is the workstation arm below.

### Why more envs is not the same lever

Lowering `kl_ub` buys **more gradient steps per unit of curriculum movement** (the dwell window stays
250 iterations while the distribution moves half as far). Raising `num_envs` buys **better gradient
steps, same count** (250 iterations is 250 TRPO updates either way; each just uses 4x the data). The
wiki's stated cause of the E1 failure is step COUNT per difficulty. Step quality has now been
measured three times — 8192 NULL, 16384 within 2% at `none`, and today's G0 showing 4096 wins-or-ties
at `hard`/`ood` — and returned nothing each time. So the 16k null does not refute the ramp
hypothesis: they are different mechanisms, and only one of them has been tested.

---

## The G0 finding — there was no valid `hard`-level comparison until today

The 16k report's headline ("11x the compute landed in the same place") is a **`none`-level**
statement, and `none` is nominal physics. At `hard`, the two runs had never been compared, because
their exams were different boxes. Verified from the eval npz, not from prose:

| DR draw (level `hard`) | Run A (4096 x 10000) | 16k `model_13400` | B/A |
|:--|--:|--:|--:|
| `dr_payload_mass` std | 0.7154 | 0.9799 | 1.37x |
| `dr_body_mass` std | 1.1728 | 1.3947 | 1.19x |
| `dr_cob_x` std | 0.0086 | 0.0116 | 1.35x |
| `dr_added_mass_0` std | 1.4558 | 1.6940 | 1.16x |
| `dr_lin_damp_0` std | 0.7058 | 0.7620 | 1.08x |

At `none` the same arrays are elementwise identical — the control proving the instrument is sound.
Cause: Run A's eval was anchored on E-int, whose box was only 65% expanded; the 16k run graded itself
on its own saturated box.

### G0 RESULT — executed 2026-08-09, 3/3 evals rc=0, 31.8 min, zero training GPU

Pairing verified before any metric was read: **24/24 `dr_*`/`fault*` arrays elementwise identical at
`none`, `hard` AND `ood` across all three evals.** Paired per-env attitude error (deg), 64 shared
seed-42 scenarios, steady state over the last 50% of each of 11 target segments; positive t = B worse:

| A -> B | `none` | `hard` | `ood` |
|:--|--:|--:|--:|
| RunA `model_9998` -> 16k `model_7500` | 0.4152 -> 0.3823, **t = -2.51** (57/64) | 0.6575 -> 0.7607, t = +1.51 | 0.7121 -> 0.7268, t = +0.17 |
| RunA `model_9998` -> 16k `model_13400` | 0.4152 -> 0.4617, **t = +4.28** | 0.6575 -> 0.7542, t = +1.93 | 0.7121 -> 0.8923, t = +1.54 |
| 16k `model_7500` -> 16k `model_13400` | **t = +9.69** (4/64) | t = -0.12 | **t = +3.16** |

**Verdict: 4096 x 10000 wins or ties at `hard`/`ood` against both 16384 checkpoints.** 16384
separates only at `none`, by 0.033 deg, on a four-way-confounded contrast. `model_9998` is therefore
the **incumbent** every new run must beat.

Two by-products carried forward: a per-axis trade the aggregate hides (16k better on roll, RunA
better on pitch, both past the 0.10 floor, while `att_norm` stays inside floors at every level); and
**`none`-invariance holds within a machine, not across machines** — RunA reproduced its 0.5070
exactly (always evaluated on the workstation) while 16k `model_7500` moved 0.4968 -> 0.4767 (-4%)
because its recorded value came from the DGX. That 4% is the noise floor under any cross-machine
comparison and it is why every arm below is evaluated on ONE machine.

---

## Recommended run — two arms, parallel, different machines

**User decision 2026-08-09: run both in parallel** (sequencing was proposed and declined).

| | **Arm W — workstation, 4096 envs** | **Arm D — DGX, 16384 envs** |
|:--|:--|:--|
| role | **deliverable candidate** | **also a deliverable candidate**, gated by D1 (machine rule), NOT by expected performance |
| `num_envs` | 4096 | 16384 |
| `kl_ub` | 0.12 -> **0.06** | 0.12 (unchanged) |
| `step_interval` | 250 | 250 |
| `max_iterations` | **20,000** | 10,000 |
| `entropy_coef_per_dim` | unchanged | **x k**, k fixed by the probe below |
| seed | 30, single | 30, single |
| expected saturation | ~14,750 (59 boundaries x 250) | ~7,250 (measured on this exact config) |
| measured s/iter | 4.19 (median of 3 workstation runs) | 18.14 |
| wall-clock | **23.3 h** | 3 h probe + **50.4 h** |

Wall-clock is set by Arm D: **~53 h (2.2 days)**; the deliverable candidate lands at 23 h.

**Budget arithmetic for Arm W.** Saturation distance measured on Run A is **3.5209 KL** over 30
expansions. At `kl_ub` = 0.06 that needs 3.5209/0.06 = 58.7 -> **59 boundaries = 14,750 iterations**;
20,000 gives 80 boundaries x 0.06 = 4.80 budget (the same 33% margin the current config carries) and
5,250 post-saturation iterations, more than Run A's 2,250. Expansion rate falls from 4.8e-4 to
2.4e-4 KL/iteration — exactly half.

**Why `kl_ub` down rather than `step_interval` up.** Both halve the rate (0.06/250 = 0.12/500 =
2.4e-4). `kl_ub` = 0.06 is the value the lineage ran before E1 and that E1's factorial identifies as
attitude-preserving, so it is a measured anchor rather than a guess; the 250-iteration dwell window
stays byte-identical to every run on record, so exactly one quantity moves; and 59 small jumps are a
smoother curriculum than 30 large ones. `step_interval` = 500 has no anchor — its one prior test was
budget-starved (above).

### Launch commands (queued, never auto-run)

Arm W, workstation:

```bash
cd ~/workspace/constrained-albc
TERM=xterm ~/workspace/isaaclab/isaaclab.sh -p scripts/train.py \
  --task Isaac-ConstrainedALBC-TRPO-v0 \
  --num_envs 4096 --max_iterations 20000 --headless --seed 30 \
  --run_group teacher_final_ramp \
  --logger wandb --log_project_name teacher_final_ramp \
  env.fault.enable=True env.doraemon.kl_ub=0.06 \
  agent.run_name=rampw_kl006_s30
```

Arm D, DGX (only after its probe passes):

```bash
cd ~/workspace/constrained-albc
TERM=xterm ~/workspace/isaaclab/isaaclab.sh -p scripts/train.py \
  --task Isaac-ConstrainedALBC-TRPO-v0 \
  --num_envs 16384 --max_iterations 10000 --headless --seed 30 \
  --run_group teacher_final_entcomp \
  --logger wandb --log_project_name teacher_final_entcomp \
  env.fault.enable=True \
  agent.algorithm.entropy_coef_per_dim='[<k*0.01>,<k*0.01>,<k*0.001>,...]' \
  agent.run_name=entcomp_x<k>_s30
```

`env.fault.enable=True` is required on both, not polish: `FaultInjectionCfg.enable` defaults False
and its omission has voided two runs in this project. Verify the Hydra list-override for
`entropy_coef_per_dim` parses into a tuple with a 50-iteration smoke before the probe; if it does
not, make the change as a commit on a tagged branch instead — which is the protocol this project
already requires (clean tree, tagged branch, sha in manifest).

### Arm D's exploration probe — 3 h, and it can cancel Arm D

Measured today, plant-controlled (Arm D's config at 16384 vs `trpo_hydrorc_s30` at 4096, same current
plant, matched iteration windows):

| iteration window | 16384 | 4096 target | deficit |
|:--|--:|--:|--:|
| 400-600 | 0.1307 | **0.1851** | -29% |
| 900-1100 | 0.1024 | **0.1376** | -26% |
| 2400-2600 | 0.0860 | 0.1030 | -17% |
| 4800-5000 | 0.0813 | 0.0915 | -11% |

`Policy/entropy` shows the same ordering (-5.37 vs -2.62 at 400-600). `Loss/kl` is identical to three
digits (0.00496 vs 0.00490), so the trust region is NOT mis-scaled and `max_kl` needs no change.
`DORAEMON/success_rate` at 400-600 is 0.327 vs 0.030 — 16384 genuinely learns faster per iteration
early — and by 2400-2600 the advantage is gone (0.865 vs 0.854), which is the whole 16384 story in
two numbers: it converges faster, spends exploration doing it, and arrives at the same place.

Because the divergence is fully resolved by iteration 1100, the probe is **600-1100 iterations, ~3 h
at 16384**. Launch Arm W first; 1.3 h later its own sigma at 400-1100 is on disk and becomes the
probe's target (this recipe's actual trajectory, not an older run's). Run k = 2 first (a sqrt(4)
noise-scale heuristic, flagged as a heuristic — the literature behind it explicitly excludes
trust-region methods); if sigma is still low, k = 3.

**If the probe cannot restore the trajectory, Arm D is not launched.** An arm whose treatment does
not take does not discriminate, and 50 h is not spent on it.

### Pre-launch gates

**G1 — plant table.** Verify each dumped `env.yaml`/`agent.yaml` against the HANDOFF Step 1 table
(obs 72, `fault.enable` true, `max_thrust_scale` (0.85,1.15), `performance_lb` 250.0, `alpha` 0.5,
`step_interval` 250, `num_mini_batches` 4, `num_learning_epochs` 5, `max_kl` 0.005, encoder latent 9 /
priv 28, `save_interval` 50), plus the one intended delta per arm. One unintended mismatch = kill.

**G2 — record what this plant is NOT.** See §Deferred: three plant-fidelity items read
`status: resolved` in omx, but that status means "moved to the hardware queue", not "applied in
code". The launch gate will therefore not fire. Both arms are pre-vertical-TAM, pre-IMU-45deg,
pre-plant-batch-v2, and must be recorded as such.

---

## Parameter coupling

Three tiers. Every escalated item below carries an explicit DECISION-REQUIRED marker and is listed
again in §Decisions for the user, without exception — the absence of that link is the single
documented cause of the last run's null.

### Tier 1 — follows mechanically; nothing to set

| quantity | Arm W (4096) | Arm D (16384) |
|:--|--:|--:|
| batch per update (`num_envs` x `num_steps_per_env`) | 262,144 | 1,048,576 |
| critic minibatch (batch / `num_mini_batches` 4) | 65,536 | 262,144 |
| critic Adam steps / iteration (5 x 4) | 20 | 20 |
| episodes finished / iteration (`num_envs` / 23.4) | ~175 | ~700 |
| DORAEMON buffer time window (2000 / above) | ~11.4 iters | ~2.9 iters |
| boundaries fired (`max_iterations` / `step_interval`) | 80 | 40 |
| expansion budget (boundaries x `kl_ub`) | 4.80 | 4.80 |

Arm W's five per-iteration quantities are identical to E-int, Run A and every reference run — the
batch does not move, so the critic-regime and buffer-staleness questions do not arise for the
deliverable arm at all.

### Tier 2 — real coupling, escalated (every item here is marked and listed)

**(a) `kl_ub` 0.12 -> 0.06, and it carries `max_iterations` with it. [DECISION-REQUIRED: kl_ub]**
This is the plan's primary treatment. Halving the step size doubles the iterations needed to reach
the same box ceiling, so the two move together by arithmetic: 59 boundaries instead of 30, hence
20,000 iterations instead of 10,000. Evidence and mechanism are in §The lever above. What is given
up: this is the first run on this plant at any ramp rate other than 0.12, so there is no dose-response
— if it wins we will not know whether 0.04 would win more, and if this is the last round we never
will. Also the reach argument depends on the measured 3.5209 KL saturation distance carrying from
Run A's resumed chain to a from-scratch run; the gate at ~17,000 catches it if it does not.

**(b) `num_envs` 4096 vs 16384. [DECISION-REQUIRED: num_envs]** Every measured env-scale point is
null (8192 NULL; 16384 within 2% at `none`; today's G0 at `hard`/`ood`). The evidence and the user's
opening instruction point opposite ways, so the run splits: the deliverable comes from 4096 on the
faster, adoptable machine, and 16384 gets the machine whose only comparative advantage it is. What is
given up: the two arms differ in `kl_ub` and `max_iterations` as well as `num_envs`, so **they do not
compare to each other** — the env axis under a properly-paced curriculum stays unmeasured. Buying
that would cost 16384 x 20,000 = 100.8 h, outside the user's stated time budget.

**(c) `entropy_coef_per_dim` x k on Arm D only. [DECISION-REQUIRED: entropy_coef_per_dim]** Justified
by today's plant-controlled measurement (sigma -11 to -29% at every matched window) and by A2, which
established that the entropy BONUS, not the IPO barrier, is what holds sigma up. Not applied to Arm W,
where the 4096 batch is the one these constants were calibrated for. What is given up: Arm D now moves
two knobs, so a win could not be attributed to either alone — accepted because Arm D is not the
deliverable and the machine rule makes it exploration regardless.

**(d) `performance_lb` 250 / `alpha` 0.5. [DECISION-REQUIRED: performance_lb]** Measured p25 of
episode return is 255.8 (E-int) / 260.1 (obs76fault) against the 250.0 in code. **Keep 250 on both
arms.** At lb=250 this config reaches Beta(1,1) on 21/21 dims by 7748 with `success_rate` settling
0.62-0.70 — above `alpha` 0.5, far below the 0.95 inert line, i.e. the gate is live and not binding.
Raising it slows expansion and risks not saturating; lowering it to 200 was measured to pin success at
0.989 and make the constraint inert. What is given up: nothing measurable while the box is frozen —
but a slower ramp keeps success HIGHER, so the risk direction flips from the alpha floor to the 0.95
inert ceiling, and that is now a watch item rather than a free pass.

### Tier 3 — no coupling that this plan moves; byte-identical

`step_interval` 250 (the dwell window; changing it is the same rate lever as `kl_ub` but without an
anchor — see §The lever); `max_kl` 0.005 (the actor has no learning rate at all — natural gradient
plus line search inside a KL trust region — and `Loss/kl` was measured identical to three digits
across 4096 and 16384, so there is nothing to rescale); `cg_iters`/`cg_damping`/backtracks 10/0.1/10;
`gamma`/`lam` 0.99/0.95; `num_steps_per_env` 64; `value_lr` 1e-3; `max_grad_norm` 1.0;
`num_mini_batches` 4 (plant-controlled, the value critic gap at matched iterations is ~1% mid-run and
+12% only at the end; the **cost** critic ends +29% and diverging, which is recorded as a watch item
on Arm D rather than a third moving knob); `min_std_per_dim` (A3 measured raising the thruster leg as
a primary FAIL, `os_env_mean` +26.2%); `init_noise_std` 0.7; `save_interval` 50; obs width 72D;
encoder [256,128,64] / latent 9 / priv 28; the fault-DR block; `max_thrust_scale` (0.85, 1.15).

---

## Decisions for the user

Items the user settled today are recorded as DECIDED with their reasoning so the next session does not
re-litigate them; the rest remain open.

### D0 — the expansion rate itself: `kl_ub` 0.12 -> 0.06 on Arm W [DECISION-REQUIRED: kl_ub]

This is the plan's primary treatment and the one thing that makes this round different from what is
already on disk. Full evidence in §The lever above.

- **Option A (recommended): `kl_ub` 0.06 with `max_iterations` 20,000.** Basis: the E1/E2 factorial
  measured expansion SPEED (not reached difficulty) as the attitude-killer with a deterministic
  control; `config.py:605-607` records that 0.12 was adopted only to compensate a budget shortfall
  that a 20,000-iteration run removes; the three-lever table states `max_iterations` UP has "none on
  the curriculum itself, only wall-clock cost"; and the one measurement that appeared to refute a
  slow ramp (`stepint400`) had a 2.40 KL budget against the 3.12 needed to saturate, so it never
  tested this. omx wiki names this exact combination as the untested cell.
- Option B: keep 0.12. Then Arm W reproduces a configuration whose artifact already exists
  (`model_9998`), and the round's only new information comes from Arm D. Cost: the round produces no
  deliverable candidate at all.
- Option C: `step_interval` 250 -> 500 instead. Identical expansion rate (0.12/500 = 0.06/250), but
  it moves the dwell window that every run on record shares, and its one prior test was the
  budget-starved `stepint400`. No anchor; strictly worse-grounded than A.
- Option D: a stronger dose, `kl_ub` 0.04 with 30,000 iterations (34.9 h, +12 h). Rejected for this
  round only because a first point on an unmeasured axis should not be the extreme one; if A wins,
  D is the natural follow-up.
- **Cost of A, stated:** this is the first run on this plant at any ramp rate other than 0.12, so
  there is no dose-response. If it wins we will not know whether 0.04 would win more; if this is the
  last round, we never will. The reach argument also assumes the 3.5209 KL saturation distance
  measured on Run A's resumed chain carries to a from-scratch run — the ~17,000 gate catches it if
  it does not.

### D1 — Is a DGX-trained teacher adoptable as THE final model? [DECISION-REQUIRED: machine_adoptability]

**DISSOLVED, not answered.** The standing rule (+109% same-config same-seed cross-machine term)
forbids shipping a DGX-trained model. The two-arm split makes that moot: the deliverable comes from
the workstation, which is both the adoptable machine and — measured today — the **faster** one at
4096 (4.19 vs 5.50 s/iter). Arm D is exploration by the standing rule, which is what it was designed
as. Reopen only if Arm D produces something worth shipping. New evidence that bears on it if so: at
`none` the DGX 16k best reads 0.4968 against 0.5070 / 0.5067 for two workstation runs, all seed 30 on
this plant — a 2% three-way spread that is not compatible with a +109% term on this metric.

### D2 — `num_envs` [DECISION-REQUIRED: num_envs]

**DECIDED 2026-08-09 (user): both, on different machines, in parallel.** The user's opening
instruction was to increase it; the evidence says the axis is inert. Rather than resolve that against
the user, the plan splits it. Cost of the split, stated: the arms are not mutually comparable
(Tier 2b), so this round does not measure the env axis under a properly-paced curriculum, and since
this is the last round it stays unmeasured. Cost of the alternative (matching Arm D's ramp to Arm W's)
is 100.8 h, which the user ruled out.

### D3 — seed count [DECISION-REQUIRED: seeds]

**DECIDED 2026-08-09 (user): single seed. 3 seeds rejected as too slow.** The measured cross-seed
floor is 56.0% p2p on `none` (0.4967 / 0.2786 / 0.3934), and best-of-3 sits 28.5% below the mean —
the largest measured lever in this campaign, and it is being forgone deliberately. Partial recovery:
the within-run checkpoint wander is the same order (0.4968 -> 0.6644 -> 0.5366 across 6000 iterations),
so the dense selection pass in §Eval schedule buys some of it back for eval cost only. **Consequence
to accept: no cross-run delta from this round clears the 56% floor, so nothing here is an adoption
conclusion about a knob — only about which checkpoint to ship.**

### D4 — `max_iterations` [DECISION-REQUIRED: max_iterations]

**DECIDED 2026-08-09: 20,000 on Arm W, 10,000 on Arm D.** Both follow from their arm's `kl_ub` by the
budget arithmetic, not from a preference about length. Arm W needs 14,750 to saturate at 0.06 and
carries the same 33% margin the current config has; Arm D saturates at ~7,250 measured, so 10,000
matches the 16k run's own shape. The user's opening 20,000 is met on Arm W for a derived reason.

### D5 — The DR ceiling: accept it, or spend this round trying to lift it [DECISION-REQUIRED: dr_bounds]

**Recommendation: accept, and this time the defer is argued rather than scheduled away.** The
recalibration protocol's Step-0 gate for "is widening premature?" now PASSES for the first time — the
box saturates (21/21 Beta(1,1) at 7748 on Run A), `kl_step` sits at the cap, and `success_rate` is
above alpha without being inert. So the box IS the ceiling now. What blocks widening is Step 1 alone:
**new bounds must come from measured hardware variation**, and both routes to that are closed by the
user's own 2026-08-05 decisions (hardware measurement skipped; Stonefish dropped, so cross-sim
disagreement may not be cited as a target). `plant_change_batch_v2` batches four corrections behind
the T200 and XW540 benches.

- Option A (recommended): accept the ceiling. The ramp lever is the substitute — it changes the path
  to the same ceiling, needs no physical source, and is the untested cell the wiki already named.
- Option B: schedule the two benches first, apply batch v2, then retrain. The only path that raises
  the ceiling. Cost: unknown bench lead time, plus the batch obsoletes every student distilled from
  the current teacher — the largest hidden cost and it should be decided explicitly.
- Option C: widen on an unsourced band. **Rejected on evidence, not deferred:** E1 measured a
  3.6x-wider DR as worse everywhere; the one unclamp probe (E-ftc1) was rejected; the open-actionable
  ledger forbids unsourced bands; and widening silently moves encoder input normalization, whose
  bounds are auto-derived from the live DR cfg with margin 0 (`priv_obs_bounds.py`), forcing a
  from-scratch retrain and breaking comparability with every run on record.
- Cost of A: the last teacher ships with a robustness ceiling set by an un-validated box on a plant
  carrying four known-wrong items.

**Open question only the user can answer: how much do the T200 command-to-thrust bench and the
XW540-T260 step response actually cost?** If half a day, that is the highest-value action available
and it should precede this round. If days or the rig does not exist, Option A stands.

### D6 — Acknowledge that the plant-fidelity launch gate will not fire [DECISION-REQUIRED: plant_gate_ack]

Not a knob. `omx wiki list --status` returns 0 pages for both actionable statuses, but that is because
`backlog-closeout` flipped the DEFERRED-HARDWARE items to `resolved` on 2026-08-05 meaning "off the
experiment queue", not "applied in code" — verified today: `config.py:93` still models the Fz row as
two independent heave channels. `omx queue-launch` will not refuse. Both arms must be recorded as
pre-vertical-TAM, pre-IMU-45deg, pre-plant-batch-v2 in their launch ack.

### D7 — `performance_lb` 250 [DECISION-REQUIRED: performance_lb]

**Recommendation: keep 250 on both arms** (reasoning in Tier 2d). Option B, re-deriving to the
measured p25 (~256-260), makes the feasibility gate harder and risks the one failure that would waste
the round — not saturating inside the budget. Option C, lowering to 200, is measured to pin success at
0.989 and make the constraint inert. If D5 ever moves the box, `lb` and the KL budget must be
re-derived **together** per the recalibration protocol, and this row becomes live.

### D8 — `entropy_coef_per_dim` on Arm D [DECISION-REQUIRED: entropy_coef_per_dim]

**Recommendation: scale by k, with k chosen by the 3 h probe rather than by argument.** Option B,
leaving it at the 4096-calibrated value, reproduces the configuration that already returned a null
twice — spending 50 h to re-measure a known result. Option C, `min_std_per_dim` instead, is measured
bad (A3, `os_env_mean` +26.2%). The probe is the gate: if the treatment does not take, Arm D is not
launched, and the 50 h is not spent.

---

## Predicted outcome

**Arm W is the only arm predicted to possibly improve on what we already have, and the prediction is
genuinely uncertain rather than confidently positive.** The ramp lever has zero measurements on this
plant. What supports it is a causal factorial on a retired plant (E1/E2: same reached difficulty,
opposite attitude, expansion speed the discriminator), a code comment showing the current value was
adopted to compensate a budget shortfall that no longer exists, and the demonstration above that the
one apparent counter-measurement was budget-starved. What is absent is any direct measurement of a
slow, fully-funded ramp. A null is entirely possible, and if Arm W comes back inside the floors
against `model_9998`, **the correct action is to ship `model_9998`** — the incumbent is already on
disk and this round costs nothing to abandon.

**Arm D is predicted to be null on the aggregate**, and it is being run to find out whether the
previous null was a tuning artifact. Three prior env-scale measurements returned nothing; the one new
input is that exploration was measurably depressed and is now compensated. Even a win is directional
only: single seed on a non-reference machine, two knobs moved, 56% p2p floor unmet.

Neither arm can lift the DR ceiling, so neither can produce a teacher better than what this box
allows. If both come back inside the floors, the honest conclusion for the campaign is that the
teacher is finished at this plant fidelity, and the next gain has to come from the benches in D5 or
from the distillation step — where the measured bottleneck actually is (five students land at
2.5-3.1 deg hard roll dispersion regardless of whether their teacher sits at 1.07 or 2.02).

---

## Eval schedule

Designed against the failure that ended the last run: a 4-point schedule with 2500-iteration gaps
straddled a transient regression, reported it as a plateau, and fired a two-strikes stop rule on the
artifact.

- **No adaptive stop rule on either arm.** Fixed budgets, post-hoc selection. A stop rule is what
  needs a dense schedule; removing it removes the failure mode outright.
- **Selection pass, per arm, `none` only.** Arm W: 15,000 / 16,000 / 17,000 / 18,000 / 19,000 /
  20,000 (consecutive 1000-iteration gaps starting just past expected saturation). Arm D: 7,500 /
  8,000 / 9,000 / 10,000. All at `--seed 42`, so per-env differencing applies — the recovery steps in
  the 16k run were 0.01-0.02 deg, invisible in a mean and decisive when paired.
- **Finalist pass.** Best checkpoint per arm, plus the incumbent `model_9998`, re-scored together in
  ONE batch, on ONE machine (the workstation), under ONE saturated anchor via `--doraemon-dr-from`,
  at `none` + `hard` + `ood`. **Select here, not at `none`** — the ranking measured at `none`
  (t = +7.53) dissolved at `hard` (+0.63) and `ood` (+1.59).
- **Selection-overfit check.** Winner and runner-up re-scored at `--seed 43`. If the ranking flips,
  the win was exam-specific and must be reported as such.
- **Pairing verified before any metric is read** on every anchored comparison (24/24 elementwise).
- Cost: 10 selection evals + 3 finalist evals + 2 checks ~= 15 x 12 min ~= **3 h**.
- Do not use TensorBoard to schedule evals or to detect degradation: a 34% `none` regression moved
  every training metric under 1%, `Reward/att_rp` flat to three digits. Only the fixed exam sees it.

### Monitoring gates during training

Iteration-500 abort (both arms): `DORAEMON/kl_step` not at its arm's cap while `mode <= -2`;
`success_rate` pinned > 0.95 or < 0.5; any dim already Beta(1,1); NaN in metric lines.

Arm W, saturation gate: expect Beta(1,1) on 21/21 and `kl_step` -> 0 at **~14,750**. Not saturated by
**17,000** = the budget arithmetic is wrong -> report, do not kill. Scan `kl_step > 0` over ALL steps
(it is written 0 on every non-boundary iteration).

Arm W, inert-gate watch — **the risk direction is inverted here.** A slower ramp keeps `success_rate`
HIGHER, so the danger is the 0.95 inert ceiling rather than the alpha 0.5 floor. Healthy at saturation
on this plant is 0.62-0.70 under the fast ramp; a slow ramp should settle above that. Sustained > 0.95
means `performance_lb` = 250 has stopped constraining anything -> kill and keep the best checkpoint.

Arm D: the probe's manipulation check (sigma tracking Arm W's 400-1100 trajectory) gates the launch.
During the run, watch `Loss/cost_value` against the 4096 reference at matched iterations — it ended
+29% and diverging in the 16k run, and if it repeats, `num_mini_batches` 4 -> 16 (regime-preserving,
no lr change) is the pre-registered follow-up, not a mid-run change.

---

## Wall-clock and budget

Throughput measured today from checkpoint mtimes (median inter-checkpoint rate, n = 101-269 files):

| machine / envs | s/iter | source |
|:--|--:|:--|
| workstation 4096 | 3.48 / 4.19 / 4.22 | `buoyanchor_s30` / `hydrorc_s30` / `eint_s30_rs2350` |
| DGX 4096 | 5.50 | `seed_floor_dgx/trpo_dgxseed30` |
| DGX 16384 | 18.14 | `trpo_dgx16k_s30` (matches the report's 18.06) |

| item | machine | time |
|:--|:--|--:|
| Arm W — 4096 x 20,000 @ 4.19 s/iter | workstation | **23.3 h** |
| Arm D probe — 16384 x ~1,100, up to 2 candidates | DGX | 3-6 h |
| Arm D — 16384 x 10,000 @ 18.14 s/iter | DGX | **50.4 h** |
| eval (selection + finalist + overfit check) | workstation | 3 h |
| **total wall-clock, parallel** | | **~53 h (2.2 days)** |

At 4096 the DGX is 1.3-1.6x SLOWER than the workstation, which is why the deliverable arm does not
run there. Disk: Arm W 400 checkpoints x 5.9 MB = 2.4 GB; Arm D 200 x 5.9 MB = 1.2 GB.

---

## Deferred — and why the machine backlog reads empty

`omx wiki list --status needs-experiment` and `--status needs-apply-before-retrain` both return
**0 pages** (verified 2026-08-09 with `--root` explicit; the wiki holds 527). **That zero is not
evidence that nothing is open.** On 2026-08-05 the `backlog-closeout` program drove all 17 open leads
to a recorded verdict, and the DEFERRED-HARDWARE ones were flipped to `status: resolved` meaning
"moved off the experiment queue to the hardware queue" — explicitly not "applied in code".

| item | state | disposition |
|:--|:--|:--|
| `tam_vertical` — Fz/My rows model T4,T5 as two independent heave channels; the real robot is one motor, dual-ESC | **verified NOT applied today**: `config.py:93` Fz row is still `(0,0,0,0,1,1)`, header comment says "OPEN (unchanged)" | **DEFER** — blocked on m4 remeasurement (hardware fault) plus a B1 vertical characterisation, both skipped by user decision. No path to close inside this project. Both arms recorded pre-vertical-TAM |
| `imu_45deg_offset` | DEFERRED-HARDWARE | **DEFER** — needs a real-robot convention measurement; zero sim-side impact meanwhile |
| `sim_hydro_nominal` — TAM moment-arm DR band, the only systematic-bias axis with no DR | `max_thrust` half closed 2026-07-27; moment-arm band needs a CAD/bracket source | **DEFER** — ELEVATED STAKES, named in the launch ack |
| `plant_change_batch_v2` — 4 corrections (buoy added mass, buoy damping anisotropy, thruster static gain, arm actuator response) | `status: null`, never machine-enumerable | **DEFER as a unit** (user decision 2026-07-29), blocked on T200 + XW540. This is D5 option B |
| `thruster_static_gain` / `thruster_nonlinear_curve` | CLOSED-OUT-OF-SCOPE (Stonefish dropped) + DEFERRED-HARDWARE (T200) | **DEFER** — `enable_thrust_curve` stays False; an unverified curve manufactures a new gap |
| `the_obs76_teacher` distillation gap | five measured students land at 2.5-3.1 deg hard roll dispersion regardless of teacher quality | **NAMED, not carried.** The measured bottleneck for the shipped product is downstream of both arms |
| `roll_transient`, `experiment_idea_latency`, `joint1_stage_1`, `c4b_dagger`, `hydrorc_*`, `buoy_added_mass`, `reward_sigma_integral` | closed by `backlog-closeout` 2026-08-05 with recorded verdicts | no action; listed so the closure is visible rather than assumed |

Carried from `dgx-final-scaleup` §8 and never answered: **Q1 -> D1 (dissolved by the machine split)**;
**Q5 (schedule the bench before committing the GPU) -> D5, still open and still the highest-value
question in this document.**

---

## Standing limitation on every number this round will produce

Single seed per arm. The cross-seed floor is 56.0% p2p on `none` (corrected plant), so **no cross-run
delta from this round is an adoption conclusion about a knob.** The only conclusion the design
supports is which of {Arm W best checkpoint, Arm D best checkpoint, `model_9998`} to ship, judged on
one machine under one anchor at `hard` and `ood`. Arm D additionally runs on a non-reference machine
with two knobs moved, so its result is directional even by that weaker standard.
