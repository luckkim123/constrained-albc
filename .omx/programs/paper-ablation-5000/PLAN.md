# Program: paper-ablation-5000 — RA-L comparison-suite (7-arm ablation) for the D13 table

**Status: PENDING USER APPROVAL — this document authorizes NO launch.** This program was scoped
as investigation + proposal only; the assigning message explicitly forbids launching training from
this session. Every `scripts/train.py` command below is a **proposed** command, not a fired one.

Created 2026-08-24 by the exp-design worker dispatched from the paper-hub coordinator, reading
`/workspace/constrained-albc` on ksm-ubuntu (container `marinelab-isaaclab`, read-only this
session) plus vault `0_Project/in_progress/albc/notes/2026-08-23-paper-hub/`.

---

## Objective (user, verbatim via coordinator relay — D13)

> RA-L 논문 비교 표 신설. 본문 최종 결과는 model_9998(run trpo_iterbudget_s30_260805_012813)
> 유지. 비교군 7 arm: TDC(고전, eval-only, 별도 worker), PID(고전, eval-only, 구현 필요 여부
> 조사), PPO(vanilla: constraint·privileged encoder 둘 다 없음, 5000 iter), no-both(vanilla
> TRPO: constraint·encoder 둘 다 제거, 5000 iter), no-constraint(encoder는 유지, CMDP 장치만
> 제거, 5000 iter), no-encoder(constraint는 유지, privileged encoder만 제거, 5000 iter),
> full-method@5000(기존 incumbent 런의 iter≈5000 체크포인트가 있으면 그걸 사용 — 재학습
> 금지). 학습 arm 전부 5000 iter 동일 예산, teacher 레벨 비교(재증류 없음), env·obs·DR 설정은
> incumbent와 동일(ablated 요소 외 변경 0).

Every decision below argues against this line. Where "동일 예산" (matched budget) and "재학습
금지" (no retraining the full method) pull in different directions, that tension is escalated to
§Decisions rather than resolved here.

---

## Diagnosis

### D1 — Three of the four training arms already exist as registered gym tasks; zero new code

`constrained_albc/envs/main/__init__.py:35-92` registers five tasks. Four map directly onto
D13's requested arms; the fifth (`PPO-Enc`) is an *extra* variant nobody asked for (encoder + PPO,
no IPO) and is out of scope here.

| D13 arm | gym task id | env cfg | runner cfg | status |
|:--|:--|:--|:--|:--|
| **no-encoder** | `Isaac-ConstrainedALBC-NoEncoder-v0` | `config:ALBCEnvCfg` (constraints on) | `rsl_rl_ppo_cfg:ALBCNoEncoderRunnerCfg` | **exists, unused** [EVIDENCE: `__init__.py:46-55`, `agents/rsl_rl_ppo_cfg.py:308-345`] |
| **PPO** | `Isaac-ConstrainedALBC-PPO-v0` | `config:ALBCEnvCfg` (constraints computed, ignored) | `rsl_rl_ppo_cfg:ALBCPPORunnerCfg` | **exists, unused** [EVIDENCE: `__init__.py:57-66`, `agents/rsl_rl_ppo_cfg.py:353-432`] |
| **no-constraint** | `Isaac-ConstrainedALBC-TRPO-NoIPO-v0` | `config_noconstraint:ALBCNoConstraintEnvCfg` (empty terms) | `agents/ablation_cfgs.py:ALBCTRPONoIPORunnerCfg` | **exists, unused** [EVIDENCE: `__init__.py:68-77`, `ablation_cfgs.py:33-38`] |
| **no-both** | — none registered — | would reuse `ALBCNoConstraintEnvCfg` | would combine `_ALBCNoEncoderPolicyCfg` (no-encoder policy) + `RslRlConstraintTRPOAlgorithmCfg` (auto no-ops IPO when `num_constraints=0`, per `ablation_cfgs.py:26-28` comment) | **missing — new code, see D4** |
| full-method@5000 | `Isaac-ConstrainedALBC-TRPO-v0` (same task as incumbent) | — | — | not a new launch, see D2 |

`git log --oneline -- constrained_albc/envs/main/agents/ablation_cfgs.py` shows only formatting
commits (ruff/pyright autofix, the FullDOF→ALBC rename) [EVIDENCE: git log output, 2 commits, no
feature commit visible in the searched range] — combined with no `experiments/` or `logs/`
directory named `ppo`/`noencoder`/`noconstraint`/`vanilla`/`ablation` anywhere in the repo
[EVIDENCE: `find experiments logs -iname '*ppo*' -o -iname '*no*encoder*' ...` → only unrelated
`teacher_baseline_*` hits], these three registered ablation tasks have **never been launched**.
Confirm-not-assume: I did not check commit dates before the searched log window, so "never
launched" is evidence-backed for the current repo state, not a claim about deleted history.

### D2 — `model_5000.pt` is NOT "5000 iterations of full-method training from scratch"

Traced via `manifest.json`, `launch.log`, and directory listings, the incumbent run
`trpo_iterbudget_s30_260805_012813` **resumed** rather than started at iteration 0:

- `launch.log:56`: `Loading model checkpoint from: .../RESUME_SRC/model_4999.pt`
- `launch.log:~90`: `Learning iteration 4999/9999` — the run's own budget (`max_iterations: 5000`
  in `manifest.json`) is a **relative** continuation, not an absolute target.
- `RESUME_SRC/` (Aug 4 04:29) itself holds `model_2350.pt` … `model_4999.pt`, and *its own*
  `launch.log:56,59` shows it too resumed: `Loading model checkpoint from:
  .../RESUME_SRC/model_2350.pt` targeting `Learning iteration 2350/5000`.

So the checkpoint nearest "iter≈5000" (`model_5000.pt`, saved literally within the first ~50
iterations after loading `model_4999.pt`) sits at the **third observed stage of a chained,
multi-run curriculum lineage** (…→2350→4999→9998), not at "5000 gradient steps since a fresh
initialization." I did not trace the lineage further back than `model_2350.pt`'s own resume
source — whether that stage itself started at iteration 0 is **not confirmed**.

### D3 — At iteration ≈5000 the DR curriculum is measurably unsaturated; this is not new information, the campaign already measured it

`experiments/.../teacher_iter_budget/README.md` (campaign's own closed analysis, 2026-08-05)
measured directly from `doraemon_state.pt`, not inferred:

| | E-int at iter 4999 (≈ what `model_5000.pt` represents) | Run A at iter 9998 (`model_9998.pt`, the incumbent) |
|:--|:--|:--|
| DR dims at Beta(1,1) (fully expanded) | **0 of 21** | **21 of 21** |
| KL budget spent | 2.28 / 3.52 (65%) | 3.52 / 3.52 (100%) |
| Saturation point | — | **iteration 7748** |

`curriculum_trajectory.json` for the iterbudget run corroborates this directly: at logged
iteration 5248, Beta shape params `a`/`b` are still 1.79-2.27 (well above 1.0 = uniform); they do
not reach 1.0 across all 21 dims until iteration 7748-7998
[EVIDENCE: `curriculum_trajectory.json` trajectory array]. The README also names specific
near-degenerate dims at this point (`fault_severity` Beta(1, 10.1) ≈ 9% of range).

`main/config.py:608`: `doraemon: DoraemonCfg(kl_ub=0.12, performance_lb=250.0,
step_interval=250)`. At `step_interval=250`, a 5000-iteration budget allows **at most 20**
expansion boundaries; the campaign measured saturation needing **~30**. So even a from-scratch
5000-iteration run would *also* land mid-expansion — this is not unique to `model_5000.pt`.

**What this does and does not mean for the ablation:**
- Does not invalidate the arm design — DORAEMON is iteration-clocked and config-identical across
  arms trained from scratch, so the 4 freshly-trained arms (no-encoder/no-constraint/no-both/PPO)
  will reach a *comparable* curriculum position at their own iteration 5000 (all starting from a
  fresh, un-resumed `doraemon_state.pt`).
- Does undermine `model_5000.pt` specifically as a peer for those 4 arms: its curriculum position
  is inherited from ≥2350 prior iterations of a lineage whose own genesis is unconfirmed, not from
  5000 fresh iterations under a freshly-initialized Beta distribution. Whether that inherited
  position happens to resemble "iteration 5000 since curriculum genesis" is **not established** —
  I did not trace the lineage to its root.
- At any 5000-iteration budget, hard-DR eval differences between arms may be attenuated relative to
  what the paper's headline (fully-saturated, iteration ≈7750+) results show, because none of the
  seven arms will have trained under the fully-expanded box. This applies to the whole suite, not
  just the full-method arm — flag as a caveat for the RA-L table's discussion section, not a
  blocker.

### D4 — the "no-both" arm needs new code, but it is a direct recombination of existing pieces

No file combines "no encoder" with "no IPO" while keeping the TRPO algorithm. The two existing
ablation variants each remove exactly one:
- `ALBCNoEncoderRunnerCfg` (`rsl_rl_ppo_cfg.py:333-345`) removes the encoder, **keeps** IPO
  (`algorithm = RslRlConstraintTRPOAlgorithmCfg()`, `policy = _ALBCNoEncoderPolicyCfg()`).
- `ALBCTRPONoIPORunnerCfg` (`ablation_cfgs.py:33-38`) removes IPO, **keeps** the encoder
  (inherits `ALBCTRPORunnerCfg` verbatim except `experiment_name`).

"no-both" = `_ALBCNoEncoderPolicyCfg` (policy) + `RslRlConstraintTRPOAlgorithmCfg` (algorithm,
auto-disables IPO when `num_constraints=0`) + `ALBCNoConstraintEnvCfg` (env, empty constraints) +
a new `gym.register(id="Isaac-ConstrainedALBC-TRPO-NoIPO-NoEncoder-v0", ...)` entry. This mirrors
`ALBCTRPONoIPORunnerCfg`'s own pattern almost exactly (that class only overrides
`experiment_name` on top of the full-method runner; "no-both" would override `policy` too).
Estimated: one new `@configclass` (~15 lines, same file as the other three) + one new
`gym.register` block (~10 lines) in `__init__.py`. **This is code, and this session's mandate is
investigation-only — flagged, not written.** See §Decisions.

### D5 — env-step budget matches automatically between PPO and TRPO arms; no decision needed here

All runner cfgs inherit `_BaseALBCRunnerCfg` (`rsl_rl_ppo_cfg.py:255-266`:
`num_steps_per_env = 64`), and `num_envs` is a shared CLI flag (4096 for the incumbent, per
`manifest.json`). Env-steps collected per iteration = `num_envs * num_steps_per_env`, identical
across PPO and TRPO — the algorithm difference (PPO: 5 epochs / 4 minibatches; TRPO: trust-region
line search) only changes **wall-clock per iteration**, not env-steps per iteration. So "iteration
budget" and "env-step budget" are the same axis here; no separate env-step-matching correction is
needed. [EVIDENCE: `rsl_rl_ppo_cfg.py:255-266`, `_ALBCPPOAlgorithmCfg` at `:382-403`]

### D6 — PID arm: TDC minus TDE equals PD in the code, but it inherits the TDC worker's legacy-env problem — cross-checked against the parallel D-5/D11 investigation

`constrained_albc/envs/tdc/controllers/thruster_pd.py` implements a stateless 6-DOF wrench PD
controller with TAM pseudo-inverse allocation, and its module docstring states it is "the only
honest comparison baseline to a 6D RL policy that has access to the full thruster authority." It
is wired into `tdc/tdc_env.py:45,85,154` and `tdc/config.py:21,43`, driving **all thruster
commands** for the existing TDC eval env, with no TDE term anywhere in the thruster path.

The **arm** (2-DOF, roll/pitch) is the only place TDE appears. `TDCController.compute()`
(`tdc.py:256-309`) already branches per-step between the TDE-augmented and pure-PD torque:

```python
tau_full = tde_term + m_hat_u_pd
tau_desired = torch.where(init_mask, tau_full, m_hat_u_pd)   # tdc.py:299-301
```

`m_hat_u_pd` alone (skipping `tde_term`) *is* the PD-only arm law — TDC minus TDE equals PD is
literally true in this code, not just conceptually. In isolation this would be a one-line toggle
(a `use_tde: bool` on `TDCControllerCfg`, gating step 5).

**But it is not in isolation — cross-checked against
`0_Project/in_progress/albc/notes/2026-08-23-paper-hub/findings/baseline-feasibility.md` (the
parallel D-5/D11 TDC investigation, same repo, same session window), whose finding overrides the
"just reuse `ALBCTDCEnv`" assumption above:** `ALBCTDCEnv` inherits `full_dof.ALBCEnv` (legacy,
87D obs / 24D privileged / lin_vel-tracking), not `main.ALBCEnv` (72D obs, attitude-only — the
family the paper's actual deployed policy and this ablation's other 6 arms all belong to).
`docs/reference/task-reference.md`'s task table, as quoted in that finding, confirms
`Isaac-ConstrainedALBC-TDC-v0` → `envs/full_dof` explicitly. Running PID (or TDC) against the
existing task therefore compares **legacy full_dof RL vs. classical control**, not **the paper's
policy vs. classical control** — a different, less relevant comparison than D13 asks for.

That other investigation already scoped the fix (its own D11, marked "approved" per today's
auto-memory) as a thin glue class — `main.ALBCEnv` subclass overriding `_pre_physics_step`,
reusing `TDCController`/`ALBCKinematics` verbatim, deciding whether to shrink `thruster_pd`'s 6-DOF
allocation to attitude-only's yaw-rate-only actuation — plus a config + gym-registration file, ~3
new files, control-law bodies (`tdc.py`, `kinematics.py`, `thruster_pd.py`) reused as-is.

**Consequence for this proposal: PID should not be scoped as independent "small" work on top of
the existing TDC env — it should piggyback on whatever main-env porting glue the TDC worker
produces, plus this program's `use_tde` toggle on top.** Scoping PID separately risks two
independently-drifting env adapters (e.g. different thruster-PD gain decisions) for what should be
nested variants of one controller family. See §Decisions — this replaces the "reuse `ALBCTDCEnv`
directly" framing from an earlier draft of this section.

### D7 — resource/timing baseline, single GPU, measured

`nvidia-smi` (2026-08-24, idle, no training running): RTX 4070 12282 MiB (701 MiB used), RTX 4060
8188 MiB (18 MiB used) — both idle. **Peak VRAM during an actual 4096-env training run was not
measured this session** (no run was live to sample); infer from the fact the incumbent run used
only `cuda:0` (the 4070) per `launch.log:52` (`[AppLauncher]: Using device: cuda:0`) — the 4060's
compatibility/capacity for a second concurrent 4096-env run is **unconfirmed**.

Wall-clock, measured from the incumbent run's own log: 5000 `Learning iteration` lines
(`grep -c` confirms exactly 5000), throughput 69,660-77,407 steps/s sampled across the run
(collection ≈1.5-1.9s + learning ≈1.9s per iteration), run start 01:28:13 → last checkpoint
(`model_9998.pt`) mtime 06:29 → **≈5h01m for 5000 TRPO iterations** at `num_envs=4096` on the RTX
4070. PPO's per-iteration learning cost (5 epochs × 4 minibatches) is a similar order of magnitude
to TRPO's trust-region step but was not separately measured — treat ≈5h as an order-of-magnitude
estimate for all four training arms, not a tight bound.

---

## Parameter coupling

### Tier 1 — follows mechanically; nothing to set

- `num_envs=4096`, `num_steps_per_env=64` (via `_BaseALBCRunnerCfg`) — held identical to incumbent
  across all 5 training-eligible arms (D5); env-step budget follows automatically.
- `env.doraemon.*` (`kl_ub=0.12`, `performance_lb=250.0`, `step_interval=250`) — held byte-identical
  per the objective's "env·obs·DR 설정은 incumbent와 동일"; this is what makes the 4 freshly-trained
  arms' curriculum positions comparable to each other at their own iteration 5000 (D3).
  `logger=wandb`, `log_project_name` set per-run-group for provenance, not a comparison variable.
- Seed: all 5 training-eligible arms proposed at `seed=30`, matching the incumbent
  (`trpo_iterbudget_s30_...`) — this is forced, not chosen: `full-method@5000` is a fixed
  checkpoint with no seed freedom (D2), so multi-seeding only the other 4 arms would make the
  comparison seed-asymmetric rather than more robust. `[DERIVED]`

### Tier 2 — real coupling; a decision is required

| knob | current | options | coupling | marker |
|:--|:--|:--|:--|:--|
| `full-method@5000` source | `model_5000.pt` (existing, D2/D3-flawed) | (a) use as-is with caveat in the paper text (b) new from-scratch full-method 5000-iter run (c) redefine ALL arms' budget to iteration ≈7750 (curriculum-saturated) | directly contradicts either "재학습 금지" (b) or "동일 예산=5000" as literally stated (c) | `[DECISION-REQUIRED: full-method-5000-source]` |
| `no-both` implementation | missing | (a) write the ~25-line combination now, in this repo, before launch (b) skip the arm, report 6/7 | needs code-write permission this session does not have | `[DECISION-REQUIRED: no-both-implementation]` |
| PID arm implementation | `TDCController` has no TDE-disable flag, AND the existing `ALBCTDCEnv` is legacy-`full_dof`-only (D6, cross-checked against `findings/baseline-feasibility.md` D-5/D11 — approved, not yet built as of this session) | (a) wait for / pair with the TDC worker's approved main-env porting glue class, add `use_tde` on top (b) build a fully separate standalone PID env now, duplicating the port | (a) shares one env adapter across both classical baselines, avoids drift; (b) is strictly more work and risks silently-different thruster-PD gains between TDC and PID | `[DECISION-REQUIRED: pid-implementation-path]` |
| `control_delay_steps` wiki lead (`needs-apply-before-retrain`) | `(0,0)`, decided range `(0,1)` for "the next FROM-SCRATCH teacher round" | (a) apply to the 4 new-trained arms now (b) defer, keep `(0,0)` for parity with `full-method@5000` | applying breaks "env·obs 설정은 incumbent와 동일" against the checkpoint arm; deferring keeps the lead open past a round that arguably qualifies as "from-scratch" | `[DECISION-REQUIRED: control-delay-apply-or-defer]` |
| Launch scheduling | none proposed yet | (a) 4 arms sequential on the 4070 (~20h) (b) 2-wide, 4070+4060, unverified VRAM/compat on the 4060 | (b) needs a smoke test this session cannot run | `[DECISION-REQUIRED: launch-parallelism]` |

### Tier 3 — no coupling to the variables under test; leave byte-identical

`env.fault.enable` (whatever the incumbent used — not independently re-verified this session,
should be read off `experiments/.../teacher_iter_budget/config/env.yaml` before launch),
`save_interval` (ablation default 100 vs main's 50 — cosmetic, only affects checkpoint density,
not the trained policy), wandb project naming, `run_group` string.

---

## Decisions for the user

- `[DECISION-REQUIRED: full-method-5000-source]` **What does "full-method@5000" mean for the
  paper table?** Recommend (a) — use `model_5000.pt` as-is — **with the D2/D3 caveat stated
  explicitly in the paper's ablation-table footnote or discussion** (its curriculum state is
  inherited from a longer lineage, not 5000 fresh iterations). Option (b) costs another ≈5h GPU-run
  and technically violates "재학습 금지" as stated. Option (c) is the most internally consistent
  but silently changes the approved "5000 iter" spec for all 7 arms and was not what D13 approved.
- `[DECISION-REQUIRED: no-both-implementation]` **Who writes the ~25-line `no-both` config +
  registration?** This session cannot (investigation-only mandate). Recommend routing to whichever
  worker/session next has write permission in this repo, using D4's exact recombination as the
  spec — it needs no design work, only transcription.
- `[DECISION-REQUIRED: pid-implementation-path]` Recommend (a) — **do not scope PID as
  independent work.** The TDC worker's D-5/D11 investigation (already approved) already covers the
  main-env porting PID also needs (D6). Once that glue class lands, PID is that class plus a
  `use_tde=False` toggle (single-line branch change in `tdc.py:299-301`) — **coordinate with the
  TDC worker before either session edits `tdc.py` or adds the porting glue class**, since both
  baselines would share the same new files.
- `[DECISION-REQUIRED: control-delay-apply-or-defer]` Recommend **defer**, for this round only:
  the ablation's entire premise is a matched comparison against the existing `full-method@5000`
  checkpoint, which was trained under `control_delay_steps=(0,0)`. Applying `(0,1)` to only the 4
  new arms confounds the encoder/constraint/algorithm ablation with an unrelated delay-model
  change, and applying it to a hypothetical 6th "corrected" full-method run contradicts "재학습
  금지". State this explicitly as the defer reason if/when this lead is revisited — do not let it
  read as "forgotten."
- `[DECISION-REQUIRED: launch-parallelism]` Recommend starting sequential-only (a) until a smoke
  test on the 4060 confirms compatibility; not a hard blocker, just sequencing.

---

## Predicted outcome

Absent the caveats above: the 4 freshly-trained arms should each land near iteration-5000
curriculum position (65% KL budget per D3, comparable across all four since DR config is
identical), so differences between them at `none`/`soft` DR levels are expected to be small
(consistent with the campaign's own finding that extension gains concentrate at `hard`), while
`hard`-level differences are the ones most likely to separate the arms — but may be **attenuated**
relative to what the same ablation would show at a fully-saturated iteration count (≈7750+),
because `fault_severity` and similar late-expanding dims are still near-degenerate at 5000. The
`full-method@5000` arm's own eval numbers should be read with the D2/D3 caveat in mind — it may
look artificially strong or weak relative to the freshly-trained arms simply because its curriculum
history differs, independent of the encoder/constraint ablation being tested.

## Eval schedule

Reuse the existing static-eval methodology already used for the incumbent run (`eval/static_*`
directories under `experiments/.../teacher_iter_budget/trpo_iterbudget_s30_260805_012813/`) —
`analysis/eval.py`'s runner-class dispatch already handles `ALBCConstraintEncoderRunner` (used by
3 of the 7 arms) and would need the same "OnPolicyRunner"/"OnPolicyDoraemonRunner" dispatch for the
PPO/no-both arms (`eval.py:1441,1483,2064,2071,2465,2467` already list `ALBCConstraintEncoderRunner`
in a class map — verify the map also resolves plain `OnPolicyRunner`/`OnPolicyDoraemonRunner`
before eval time; **not independently verified this session**). Evaluate all 7 arms across the same
four DR levels used elsewhere in this project (`none`/`soft`/`medium`/`hard`) at each arm's final
checkpoint (iteration 5000, or nearest saved — `save_interval=100` for ablation runs means the
closest checkpoint to exactly 5000 may be off by up to 99 iterations; confirm the exact saved
iteration before eval).

## Wall-clock and budget

- 4 training arms (PPO, no-both, no-constraint, no-encoder) × ≈5h each (D7) ≈ **20h sequential**
  on the RTX 4070, order-of-magnitude (PPO's true cost not independently measured).
- `full-method@5000`: **zero new compute** if using `model_5000.pt` as-is (Decision above).
- PID: eval-only, but **gated on the TDC worker's main-env porting landing first** (D6) — not
  schedulable independently. Once the glue class + `use_tde` toggle exist, per-arm eval wall-clock
  was not measured this session (existing `eval/static_*` directories don't isolate a clean
  eval-only wall-clock in what was inspected) — estimate from an existing eval launch before
  committing to a schedule.
- TDC: out of scope, tracked by the other worker (`findings/baseline-feasibility.md`, D-5/D11).
- Total, sequential, single-GPU, order-of-magnitude: **~21-22h of GPU time** for the 4 training
  launches + PID/TDC eval passes, before accounting for the `no-both` and PID implementation work
  in §Decisions.

## Deferred

`omx wiki list --status needs-apply-before-retrain` (1 page) and `--status needs-experiment`
(4 pages), enumerated in full:

- **`the_deployed_teacher_trained_with_control_delay_steps_0_0_while_.md`** (needs-apply-before-
  retrain) — see Tier-2 `control-delay-apply-or-defer` above. **Deferred for this round**: applying
  it breaks matched comparison against the existing `full-method@5000` checkpoint (D13's explicit
  premise), and this ablation is not empowered to retrain a corrected full-method arm either
  ("재학습 금지"). Revisit once a future FROM-SCRATCH round is scoped that does not need to match
  an existing checkpoint.
- **`joint_target_runaway_is_not_a_sim_to_real_gap_...md`** (needs-experiment) — hardware/physical
  robot (XW540-T260 bench test). No training-config surface; not applicable to this ablation.
  Carried as-is, no action here.
- **`open_on_land_the_policy_winds_j2_to_pi_...md`** (needs-experiment) — hardware/deployment
  (board IMU/joint rate mismatch). No training-config surface; not applicable. Carried as-is.
- **`the_c3_recipe_does_not_transfer_across_teachers_...md`** (needs-experiment) — blocked on a
  real dgx16k C3 training run, a different teacher/campaign entirely. Not applicable to this
  ablation's arms. Carried as-is.
- **`where_is_arm_w_losing_the_8_points_of_return_...md`** (needs-experiment) — blocked on
  `eval.py` missing a per-env episode-return channel. Not blocking the aggregate-level eval this
  ablation needs (D3/Eval schedule above), but would matter if the paper later wants a per-DR-
  dimension breakdown of *why* an arm underperforms. Optional follow-on, not carried into this
  round's scope.
