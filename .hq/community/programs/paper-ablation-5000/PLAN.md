# Program: paper-ablation-5000 — RA-L comparison-suite (7-arm ablation) for the D13 table

> 🔴 **이 머리말은 2026-08-24 판이다. 이 프로그램은 그 뒤 실행됐다** — 4 학습 arm 전부
> `model_4999.pt` 완주, 5-arm eval 5/5 성공. 아래 §Decisions 다섯 항목의 **현재 상태와
> 그 뒤 바뀐 플랜트**는 문서 최하단 `## Update 2026-09-06` §1·§2 가 정본이다.
> 이 절만 읽고 낡은 결정을 집지 말 것.

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

> 🔴 **SUPERSEDED 2026-09-06 (부분).** 위 원문 중 "**재학습 금지**"(full-method@5000 은 기존
> incumbent 체크포인트를 쓰라)는 사용자의 2026-09-06 앵커 (B) 결정으로 **무효**다 — 새 플랜트에서
> 그 체크포인트는 다른 저울이라 쓸 수 없다. "5000 iter 동일 예산" · "teacher 레벨 비교" ·
> "ablated 요소 외 변경 0" 셋은 **유효**하며, 그중 동일 예산은 §8-R-7 에서 새 플랜트 기준으로
> 재확인이 필요하다(새 플랜트에는 full-method@5000 이 존재하지 않는다). 원문은 기록이므로
> 고쳐 쓰지 않는다.

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

---

## Update 2026-09-06 — 비교 알고리즘 축 확장 (ablation → 외부 알고리즘 비교)

**Status: PROPOSAL — 이 절도 발사를 승인하지 않는다.** 아래 학습 명령은 전부 제안이다.
작성: ksm-mac 세션, 컨테이너 `marinelab-isaaclab` 읽기 + 로컬 소스 스냅샷(227 py 파일) 정독.
자매 세션 2개와 분업 — 이 절은 **arm 설계**, 평가 하네스는 workspace-c0, 실기 배포는 별도 세션.

### 0. 사용자 지시 (원문)

> constrained rl 제어기와 비교 검증을 위한 알고리즘 구현.
> tdc, pid, non constrained rl, non encoder rl, ppo rl 등
>   이외에도 비교 검증 가능한 알고리즘 제안.
> 계획 수립까지 수행.
>
> \# 제약 조건:
> 문헌 조사 및 충분한 코드 분석을 통해 근거 확보.
> 학습이 필요한 경우 ksm-ubuntu 및 ksm-nas둘 다 사용 가능.

아래 모든 판단은 이 다섯 줄에 대해 논증한다. 지시가 명시한 5종(tdc·pid·non-constrained·
non-encoder·ppo)은 **전부 이미 존재**하므로(§1), 이 절의 실질은 "무엇을 더 넣을 것인가"(§3)와
"옛 결과를 살릴 것인가 다시 잴 것인가"(§2)다.

### 1. 상태 정정 — 위 계획은 PENDING 이 아니라 **실행 완료**다

이 문서 머리의 `Status: PENDING USER APPROVAL` 은 2026-08-24 판이고, 그 뒤 실제로 발사됐다.

| 옛 §Decisions 항목 | 현재 상태 | 근거 |
|:---|:---|:---|
| `no-both-implementation` | **종결** — 구현·등록됨 | `constrained_albc/envs/main/__init__.py:92` `gym.register(id="Isaac-ConstrainedALBC-TRPO-NoIPO-NoEncoder-v0")`, 러너 `agents/ablation_cfgs.py:102` |
| `pid-implementation-path` | **종결** — (a) 채택된 형태로 구현됨 | `envs/tdc_main/` 신설. `pid_env.py:49` 가 매 스텝 `self._tdc._is_initialized[:] = False` 로 `tdc.py:301-303` 의 pure-PD 분기에 고정. `tdc.py` 무수정 |
| `launch-parallelism` | 사실상 (a) 순차로 실행됨 | 4 arm 타임스탬프가 `260824_163300` → `260824_195749` → `260825_002302` → `260825_024716` 로 겹치지 않음 |
| `full-method-5000-source` | (a) 채택 — 기존 체크포인트 사용 | eval 로그의 arm 이름에 `full_method` 가 있고 학습 디렉터리는 4개뿐 |
| `control-delay-apply-or-defer` | **defer 됐으나 그 전제가 무너졌다** | §2 |

학습 완주 실측 — `logs/rsl_rl/albc_ablation/paper_ablation_5000/` 아래 4 디렉터리가 각각
`model_4999.pt` 보유:
`noenc_paper_abl_noenc_260824_163300` · `ppo_paper_abl_ppo_260825_002302` ·
`trpo-noipo_paper_abl_noconstr_260824_195749` · `trpo-noipo_paper_abl_nobo_260825_024716`.

평가 완주 실측 — `eval_5arm_auto.log` 최종 줄:
`=== 종료 — 성공: ppo full_method no_encoder no_constraint no_both / 실패: 없음 ===`,
`summary.json` 4건(+full_method 는 incumbent 트리).

**즉 RA-L ablation 표의 숫자는 이미 있다.** 이 절이 여는 것은 그 표가 아니라 그 **옆 칸**이다.

### 2. 그 사이 플랜트가 바뀌었다 — 위 결과 전체가 옛 플랜트 산이다

`retrain-simtoreal-2026-09` 이 §5 델타로 플랜트를 갈았다: `thrust_coefficient` 40 → **13 N/unit**,
`thruster_dead_frac` **0.5**, `control_delay_steps` (0,0) → **(0,3)**, 계수 밴드 (0.7,1.3) →
**(0.5,2.0)**. 배포 후보는 `deploy/retrain_simtoreal_p3/pack_r3a_p3b7500_gru_260906_145553` 다.

> 🔴 **정정 2026-09-07 — 위 목록은 4개지만 실제 델타는 7개다.** `finding/352`
> (status **`needs-apply-before-retrain`** — 재학습을 명시적으로 막는 리드). 빠진 셋:
> `performance_lb` 250.0 → **200.0** (`config.py:612`), `fault.enable` False → **True**
> (`config.py:371`), `fault.thruster_fail_prob` 0.10 → **0.30** (`config.py:377`).
> 위에 적힌 넷의 출처는 `config.py:141`(thrust_coefficient) · `:231`(scale) ·
> `:263`(control_delay_steps) · `:381`(thruster_dead_frac).
> **일곱 개 전부 launch override 전용이고 코드 기본값은 여전히 옛 플랜트다.** 블록 없이
> 발사하면 조용히 40 N zero-delay fault-free lb250 으로 되돌아가며, 그 설정은 `finding/315`
> 에서 런 하나를 통째로 정지시켰다(DORAEMON mode −2 전 구간, fault_severity 0.0045).
> arm 별 적용 방법은 §4-5.

08-24~25 의 4 arm 은 전부 그 이전 플랜트에서 학습됐다(디렉터리 mtime 08-24~25, 델타 커밋은 09-03~04).
따라서:

- 옛 `control-delay-apply-or-defer` 의 defer 근거("기존 full-method@5000 체크포인트와 맞춰야 한다")는
  **더 이상 성립하지 않는다** — 배포 후보가 이미 (0,3) 에서 학습됐다.
- 08-24 결과는 **옛 플랜트 안에서는 유효**하다. 무효가 아니라 *다른 저울*이다.

`[DECISION-REQUIRED: comparison-anchor]` **비교의 "우리 쪽"이 무엇인가.**

| | (A) `model_9998` 유지 (옛 플랜트) | (B) R3a 배포 후보 (새 플랜트) |
|:---|:---|:---|
| 기존 5-arm 결과 | 그대로 살아 있음 | **전량 폐기 → 재학습** |
| TDC·PID 수치 | 살아 있음(단 §5 게인 확인 필요) | 재평가 필요(학습은 불필요) |
| 논문 본문과의 정합 | 현행 본문과 일치 | 본문 수치 전면 교체 |
| 배포와의 정합 | **어긋난다** — 실기에 올라가는 것은 R3a | 일치 |
| 추가 GPU 비용 | 신규 arm 분만 | 신규 arm + 기존 4 arm 재학습 ≈ +20 h |

이 결정 전에는 신규 arm 정의를 **플랜트-불문**으로 쓴다(아래 §3 은 그렇게 썼다). 어느 쪽이든
arm 목록·구현·이음매는 같고 학습 예산만 갈린다.

### 3. arm 카탈로그

「방어하는 주장」열이 이 표의 목적이다 — 그 주장이 논문에 없으면 그 arm 은 넣지 않는다.

#### 3-1. 이미 있는 것 (구현 0)

| # | arm | task id | 상태 | 방어하는 주장 |
|:--|:---|:---|:---|:---|
| A1 | Proposed (ConstraintTRPO+IPO+Encoder) | `Isaac-ConstrainedALBC-TRPO-v0` | 학습·평가 완 | (기준) |
| A2 | non-encoder RL | `...-NoEncoder-v0` | 학습·평가 완 | privileged encoder 가 적응력을 만든다 |
| A3 | PPO (vanilla) | `...-PPO-v0` | 학습·평가 완 | 알고리즘 자체의 기여 |
| A4 | non-constrained RL (IPO 제거) | `...-TRPO-NoIPO-v0` | 학습·평가 완 | CMDP 장치가 제약 위반을 줄인다 |
| A5 | no-both | `...-TRPO-NoIPO-NoEncoder-v0` | 학습·평가 완 | 둘의 교호작용 |
| A6 | PPO+Encoder | `...-PPO-Enc-v0` | **등록만, 미학습** | encoder 가 알고리즘과 무관하게 기여하나 |
| A7 | TDC (고전) | `...-Main-TDC-v0` | 구현·평가 완 | 고정 M-bar TDC 의 한계 |
| A8 | PID/PD (고전, TDE off) | `...-Main-PID-v0` | 구현·평가 완 | TDE 항의 기여 분리 |
| A9 | Student (TCN/GRU) | (배포 팩) | 학습 완 | 증류 손실 |

A6 은 등록만 되고 학습 디렉터리가 없다(`paper_ablation_5000/` 에 4개뿐). 옛 §D1 이
"out of scope" 라 적은 그대로 남아 있다. **비용이 학습 1회뿐이라 복원 1순위다.**

#### 3-2. 신설 제안 — 심사 위험 순

| # | arm | 왜 필요한가 (근거) | 구현 | 학습 |
|:--|:---|:---|:---|:---|
| **N1** | **PPO-Lagrangian / TRPO-Lagrangian** | 현행 표에 제약을 *다르게* 거는 arm 이 **0개**다. IPO 를 *끄는* arm(A4)만 있어서 "IPO 가 Lagrangian 보다 낫다"는 주장이 근거 없이 남는다. Lagrangian 은 safe-RL 의 사실상 표준 비교군 | 중 (§4-1) | 1 런 |
| **N2** | **ATDC (gradient adaptive gains)** | 논문 References [5] Baek et al. 2018 을 "ATDC 비교 대상" 이라고 **명시**해 놓고 구현이 없다. Main Ideas 가 자기 기여를 "고정된 형태의 적응 법칙, 추적 오차만 사용(reactive)" 에 대해 정의하므로, 이 arm 이 없으면 기여 주장의 대조군이 없다 | 중 (§4-2) | 없음 |
| **N3** | **RL-TDC (M-hat 을 학습)** | References [8] Baek et al. 2022 를 "RL-ALBC 의 직접적 선행 연구", Experiments 노트 Related Notes 가 "직접 비교 대상" 이라 적었다. 세대 1 `Isaac-ConstrainedALBC-TDC-v0` 는 **고정** m-hat 이라 이 arm 이 아니다 | 대 (§4-3) | 1 런 |
| **N4** | **Residual RL over TDC** | `tdc.py:263,275,307-308` 의 `residual_tau` (Step 5b) 가 **이미 배선돼 있고 호출자가 0건**이다. "고전 제어기 + 학습 residual" 은 model-based/model-free 통합 주장의 가장 강한 대조군 | 소 (§4-4) | 1 런 |
| **N5** | **Teacher upper bound** (privileged 직접 입력) | Experiments 노트 Ablation 표가 이미 계획해 놓고 미실행. 배포 불가 상한선이라 student 손실의 분모 | 소 | 1 런 |
| **N6** | **No-DORAEMON (fixed DR) / No-DR** | Experiments 노트 DORAEMON DR Ablation 표가 계획해 놓고 미실행. DORAEMON 이 기여 목록에 있는데 대조군이 없다 | 소 (플래그) | 2 런 |

**넣지 않기를 권하는 것** — MPC·LQR: 이 플랜트에 선형화 모델이 없고, `Fz`·`My` 랭크 1(m3 사망)
같은 배포 제약이 sim 모델에 없어서 "공정한 MPC" 를 세우는 비용이 arm 하나 값을 넘는다.
Koopman 은 이미 별도 프로그램 `koopman-lifting` 이 있으므로 그 라인에 남긴다(중복 금지).

### 4. 신규 arm 구현 계획

#### 4-1. N1 Lagrangian — `ConstraintTRPO` 의 barrier 항만 교체

`envs/_core/algorithms/constraint_trpo.py` (642줄) 는 이미 cost critic·cost GAE·per-constraint
cost-advantage 표준화까지 다 갖고 있다: `_compute_cost_returns` (`:295`), `cost_advantages`
표준화 (`:447-452`), IPO barrier (`:459-476`). Lagrangian 은 그 barrier 블록만 갈아끼우는 것이다.

- 새 파일 `envs/_core/algorithms/constraint_lagrangian.py` — `ConstraintTRPO` 상속, `update()` 의
  barrier 항을 `-sum_k lambda_k * cost_surr_k` 로 치환 + lambda 이중상승(softplus 매개변수화, lr 별도).
- 🔴 **경로 정정 2026-09-07**: `constrained_albc/envs/main/agents/ablation_cfgs.py` 에
  `ALBCTRPOLagrangianRunnerCfg` 1개. (원래 `agents/ablation_cfgs.py` 라 적혀 있었으나 그 경로에는
  파일이 없다. 실측한 형제 클래스: `ALBCTRPONoIPORunnerCfg:37` · `ALBCPPOEncRunnerCfg:70` ·
  `ALBCTRPONoIPONoEncoderRunnerCfg:102`, 기반은 `envs/main/agents/rsl_rl_ppo_cfg.py`
  `ALBCTRPORunnerCfg:269`.) 그리고 `main/__init__.py` 에
  `gym.register` 1개. env cfg 는 **`config:ALBCEnvCfg` 그대로** — 같은 K=10, 같은 budget 을 써야
  비교가 성립한다(`envs/main/config.py:56-74`).
- 주의: 같은 파일 주석이 `thruster_rate` 항을 `entropy_coef>0` 와 구조적 비호환이라 제거했다고 적었다.
  새 arm 에서 되살리지 말 것.
- 위험: TRPO 의 line search 는 목적함수 부호에 민감하다. lambda 가 크면 backtrack 이 항상 실패해
  정책이 안 움직이는 조용한 실패가 난다 — 사전등록 판독에 line-search 성공률을 넣는다.

#### 4-2. N2 ATDC — `TDCController` 에 적응 법칙 하나

`tdc.py:117` 이 `self._m_hat` 을 이미 `(num_envs, 2)` 텐서로 들고 있다(스칼라가 아니다).
Baek 2018 의 gradient 적응 법칙은 그 텐서를 매 스텝 추적오차로 갱신하는 것이다.

- `TDCControllerCfg` 에 `adaptive_m_hat: bool = False` + 적응 게인/상하한 필드.
- `compute()` 안 `_compute_pd_torque` 직후에 갱신 블록 ~20줄. 기본값 False 라 기존 arm 비트동일.
- 새 env 클래스 불필요 — `ALBCTDCEnv` 를 그대로 쓰고 cfg 만 다른 task id 로 등록.
- **학습 0.** eval-only arm.

#### 4-3. N3 RL-TDC — 가장 비싼 arm, 유일하게 새 알고리즘

세대 1(`_archive/tdc_generation_2026_02/`)이 "4D TDC 게인 출력" 이었으므로 **구조는 있었던 것**이다.
다만 (a) 그 세대는 69D 이전이고 (b) SAC 가 이 저장소에 없다(rsl_rl 은 on-policy).

- 최소 경로: **SAC 를 새로 넣지 말고** 현행 on-policy 러너로 "M-hat 을 내는 정책" 을 학습한다.
  Baek 2022 의 기여는 *적응 법칙이 structure-free 하다*는 것이지 *SAC 라는 것*이 아니다.
  action = 2D `m_hat` (+ 선택적으로 kp/kd), 나머지는 TDC 가 계산.
- 그러면 `ALBCTDCEnv._pre_physics_step` 의 `del actions` 를 **지우고** actions 를 m-hat 으로 해석하는
  파생 클래스 하나 + action_space 2D 로 좁힌 cfg. ~60줄.
- 논문에 "SAC 대신 on-policy 로 재구현했다" 를 명시해야 한다. 이것이 이 arm 의 유일한 취약점이다.
  `[DECISION-REQUIRED: rl-tdc-algorithm]` — SAC 를 진짜로 넣을지(비용 대), on-policy 재구현으로
  갈지(비용 소, 서술 부담).

#### 4-4. N4 Residual TDC+RL — 이음매가 이미 있다

`tdc.py:307-308` 이 `tau_desired = tau_desired + residual_tau` 를 이미 한다. 필요한 것은
`ALBCTDCEnv` 파생 클래스가 정책 action 을 `residual_tau` 로 넘기는 것뿐(~30줄).

설계 결정 하나: **제약을 residual 에 걸 것인가 합성 토크에 걸 것인가.** 표의 다른 arm 과
같은 의미가 되려면 **합성 토크**다 — 그리고 이건 자동으로 성립한다. `compute_all_costs` 는
로봇 상태를 재지 action 을 재지 않기 때문이다(`albc_env.py:1411-1412`).

### 5. 고전 제어기 게인 공정성 — 이 계획의 가장 약한 고리

**정정: 실효 게인은 kp=48.0 / kd=14.0 이다.** `tdc.py:48-49` 의 dataclass 기본값이 그것이고
(`kp: float = 48.0  # omega_n = sqrt(48/0.15) = 17.9 rad/s (was 40, +20%)`),
`tdc_main/config.py:34` 가 `TDCControllerCfg()` 를 오버라이드 없이 만든다. `tdc/config.py:39` ·
`tdc_main/config.py:39` docstring 의 "kp=40.0, kd=12.0 을 ROS 원본에서 상속" 은 **낡았다** —
tdc.py 가 그 뒤 +20% 로 올렸다. m_hat=(0.15,0.16) 은 맞다(`tdc.py:45`).

플랜트가 바뀌면(추력 40 -> 13 N/unit) 이 게인이 공정하다는 보장이 사라진다. 심사에서 처음 맞는
지점이 정확히 여기다("baseline 을 튜닝하지 않았다"). 프로토콜 제안:

1. **탐색 공간과 예산을 먼저 공표한다** — kp·kd 각 log-grid, m-hat 스케일 1축, 총 N 점.
2. 🔴 **탐색 예산을 공표하고 그 안의 최선을 쓴다** (2026-09-07 정정). 원래 여기 적혀 있던
   "RL 과 같은 env-step 수를 준다"는 **성립하지 않는다.** RL 의 5000 iter × 4096 env ≈ 2×10⁸
   env-step 이고, kp·kd 2축 그리드로 그만큼을 쓰려면 점당 롤아웃이 비현실적으로 길거나 점 수가
   수천이다 — 게다가 §5-1 의 N 이 미정이라 검증할 수치 자체가 없었다. 두 최적화의 단위가 달라
   env-step 등가는 애초에 의미가 약하다. 방어 가능한 형태는 **N 을 먼저 확정해 공표**하는 것이다
   (권고: kp × kd log-grid 5×5 = 25 점, m̂ 스케일 3 점 → 총 75 점). "튜닝하지 않았다"는 지적은
   예산을 논문에 적어 막고, "충분히 튜닝했나"는 그 예산 크기로 답한다.
3. **튜닝 분포와 시험 분포를 분리한다** — 튜닝은 `none`/`soft` 에서, 보고는 4 tier 전부.
   같은 tier 에서 튜닝하고 같은 tier 에서 보고하면 고전 쪽에 과적합 이점을 준다.
4. 선정 게인·탐색 로그를 산출물로 남긴다. 이게 없으면 3번 주장이 검증 불가다.

이 프로토콜이 계획에 없으면 **구현이 끝나도 수치를 못 쓴다.**

### 6. 평가 프로토콜 (자매 세션 workspace-c0 담당, 여기는 arm 쪽 요구사항만)

- 기준 하네스는 `scripts/eval_5arm_auto.sh` 다. 새로 짜지 말 것 — DR 앵커·GPU 핀·
  `RUN_CONDITIONS.txt` 기록이 이미 들어 있다.
- 🔴 **fair-exam 앵커 — 2026-09-07 정정. `--doraemon-dr-from` 은 플랜트 지정자가 아니다.**
  `finding/391`(confidence high, 2026-09-06 실측): `load_doraemon_dr` 는 DORAEMON 관리 19~21
  파라미터만 덮어쓰는데 `thrust_coefficient_scale` 이 그 목록에 없어(`doraemon.py` 에 등장조차
  안 한다) 클래스 기본값 **(0.7, 1.3)** 으로 떨어진다. `control_delay_steps` 도
  `_DR_TUPLE_FIELDS` 밖이라 **(0, 0)** 으로 채점됐다. `--no-doraemon-dr` 로도 못 고친다 —
  그 플래그는 앵커를 `_DORAEMON_FULL_DR` ↔ `DomainRandomizationCfg()` 로 바꿀 뿐이고 둘 다
  런의 플랜트가 아니다. **필수 플래그는 새로 추가된 `--env-dr-anchor`(기본 OFF, opt-in)** 이며,
  `--doraemon-dr-from` 은 여전히 DORAEMON 커리큘럼 앵커로 필요하다 — **둘 다 준다.**
  세 site 가 다 고쳐졌는지는 `tools/check_env_dr_anchor.py`(15/15) 로 확인한다.
  빼면 arm 마다 다른 플랜트로 채점돼 비교가 무효가 된다 — 이 프로젝트가 이미 두 번 밟았다
  (`finding/318`, `finding/391`).
- **GPU 핀**: 학습 GPU0(4070 12 GB), eval GPU1(4060 8 GB). eval hang 의 원인은 자원 경합이었다.
- **K=10 제약 열은 측정값으로 채운다.** `albc_env.py:1411-1412` 가 `extras["costs"]` 로 매 스텝
  `(num_envs, K)` 를 낸다. `ALBCTDCEnvCfg(ALBCEnvCfg)` 가 `constraints` 를 상속하므로 **TDC·PID
  arm 도 같은 10개 비용을 낸다.** 즉 학습 시 제약을 안 건 arm(PPO·vanilla TRPO·TDC·PID)도 같은
  저울에서 위반량을 말할 수 있다 — constrained RL 논문 표의 중심이 여기다.
  현재 `eval.py` 롤아웃 3곳(`941`·`1910`·`2298`)이 `env.step()` 의 네 번째 반환값을 버린다.
- 🔴 **시드 — 이 계획의 최대 미해결 (2026-09-07).** 원래 "신규 arm 은 최소 2 시드"라 적었으나
  §7 예산표와 §8-R-2 순서표는 **arm 당 1 런**으로 계산돼 있었다(문서 내부 모순). 그리고
  `finding/395`(2026-09-06)가 더 나쁜 사실을 실측했다: **기존 성분 ablation 의 평균은 꼬리
  통계이고, median 으로 보면 PPO 가 hard 에서 full method 를 이기고(0.658 vs 0.685)
  no-encoder 가 soft 에서 이긴다. 셋 사이 median 격차는 전부 시드 간 산포의 1/3~1/5 다.**
  살아남는 신호는 tail control 뿐이다(max 4.46 vs 15.78 deg). 즉 **1 시드로 재현하면 같은
  "변별 불가"를 35 GPU-h 주고 다시 산다.** 판단은 §8-R-6.
- 🔴 **표 지표**: `finding/395` 에 따라 mean 단독 보고 금지. **median + P90(또는 max)** 를 함께
  낸다. mean 만 적은 표는 이봉 분포의 꼬리를 성능 우열로 잘못 읽는다.
- 🔴 **K=10 중 한 열은 사문이다.** `finding/378`: `joint1_pos` = `I(|θ₁| > 4π)` 가 ±2π 로
  래핑된 측정값을 읽어 **구조적으로 발화 불가**다(`envs/main/config.py:64`,
  `mdp/constraints.py:120-131`). 상시 margin 1.00 은 "위반 없음"이 아니라 "못 봄"이다. 실제로
  incumbent 는 pair34/hard 64 env 중 7 개에서 joint1 을 41 rev 이상 감았고 그 열은 0 이었다.
  10 열을 그대로 실으면 심사에서 잡힌다 — 그 열에 "measurement-limited, not satisfied" 각주를
  달거나 9 열로 보고한다.

### 7. 예산 — 실측 기반

| 자원 | 실측 | 함의 |
|:---|:---|:---|
| GPU0 RTX 4070 12,282 MiB | 교사 학습 시 VRAM 11.5/12 GB @ 4096 env, 4.5 s/iter | 학습 전용. 5000 iter 약 **5 h/arm** |
| GPU1 RTX 4060 8,188 MiB | 현재 유휴(18 MiB) | 4096 env 학습은 **미검증이고 가능성 낮다**(위 11.5 GB 근거의 추론). eval 전용이 현행 프로토콜 |
| **ksm-nas** | `192.168.10.34:9931` — 이 맥에서 `Connection refused`, 컨테이너에서도 도달 불가 | **현재 학습에 못 쓴다.** 사용자 지시가 "둘 다 사용 가능" 이라 했으므로 접속 경로 확인 필요 |

학습 소요(순차, GPU0):

| 시나리오 | arm | 시간 |
|:---|:---|---:|
| 최소 (신규만, 앵커 A) | A6, N1, N4, N5 | 약 20 h |
| 권장 (신규 + N3) | + N3 | 약 25 h |
| 앵커 B (전량 재학습) | + 기존 4 arm | 약 **45 h** |

N2(ATDC)는 학습 0 — eval 만.

> 🔴 **정정 2026-09-07 — 위 표는 승인 범위(§8-R-2)와 안 맞고 세 항목이 빠져 있다.**
> 승인된 것은 N5·N3 을 뺀 A6·N1·N4 + 기존 4 arm = **7 런**이므로 기준선은 45 h 가 아니라 35 h 다.
> 여기에 아래가 더해진다:
>
> | 항목 | 추가 | 근거 |
> |:---|---:|:---|
> | 참조 arm(우리 방법)을 새 플랜트에 세우기 | +1 런 이상 | §8-R-7 — 새 플랜트에 full-method@5000 이 **없다** |
> | arm 별 플랜트 적용(cfg subclass 또는 override 블록 + 검증) | 학습 0, 작업 반나절 | §4-5 |
> | 시드 2개로 갈 경우 | ×2 → 총 55~70 h | §8-R-6 |
>
> 따라서 현시점 정직한 범위는 **35 h(1 시드·참조 arm 미정) ~ 75 h(2 시드·참조 arm 신규 학습)**
> 이고, 이 폭을 좁히는 것이 §8-R-6·§8-R-7 결정이다.

### 8. 결정 필요

- `[DECISION-REQUIRED: comparison-anchor]` §2 표. **권고 (B)** — 배포되는 것과 논문이 재는 것이
  다르면 sim-to-real 주장 자체가 흔들린다. 비용은 +20 h 이고 GPU0 이 유휴다.
- `[DECISION-REQUIRED: arm-scope]` §3-2 중 무엇을 넣나. **권고: N1·N2·N4 + A6.**
  N1 은 없으면 표에 구멍(제약 대 제약 비교 0건), N2 는 논문이 스스로 비교 대상이라 적었고,
  N4·A6 은 학습 1런짜리다. N3 은 §4-3 결정 뒤, N5·N6 은 여력.
- `[DECISION-REQUIRED: rl-tdc-algorithm]` §4-3. **권고: on-policy 재구현** + 논문에 명시.
- `[DECISION-REQUIRED: classical-gain-retune]` §5 프로토콜을 채택할 것인가, 아니면 게인을
  플랜트 변경 전 값으로 동결하고 그 사실을 각주로 적을 것인가. **권고: 채택.**
- `[DECISION-REQUIRED: ksm-nas-access]` §7. NAS 를 학습에 쓰려면 접속 경로가 필요하다. GPU 유무도
  미확인이다.

### 8-R. 결정 반영 (사용자, 2026-09-06)

§8 의 다섯 항목 중 셋이 닫혔다. 아래가 정본이고 §8 은 그 항목들의 *선택지*를 남긴 기록이다.

| 항목 | 판정 | 사용자 원문 |
|:---|:---|:---|
| `comparison-anchor` | **(B) 새 플랜트로 통일** | "일단 권장대로. 근데 재학습할 수도 있다." |
| `arm-scope` | **N1 + N2 + N4 + A6** | "N1+N2+N4+A6 (권장, ~20h)" |
| `classical-gain-retune` | **재튜닝 프로토콜 채택** (§5) | "재튜닝 프로토콜 채택 (권장)" |
| `rl-tdc-algorithm` | **보류** — N3 이 이번 범위 밖이라 물을 대상이 없다. 범위가 늘면 다시 연다 | (해당 없음) |
| `ksm-nas-access` | **열림** — §7 실측대로 도달 불가 | (해당 없음) |

#### 8-R-1. 앵커는 체크포인트가 아니라 **포인터**로 쓴다

사용자가 (B)를 고르면서 "재학습할 수도 있다" 를 붙였다. 즉 R3a
(`pack_r3a_p3b7500_gru_260906_145553`) 는 *현재의* 배포 후보이지 고정점이 아니다.
따라서 이 프로그램의 산출물은 다음 규약을 따른다:

- arm 정의·구현·이음매는 **플랜트 불문**으로 쓴다(§3·§4 는 이미 그렇게 썼다). 재학습이 일어나도
  코드는 안 바뀐다.
- 학습·평가 명령의 플랜트를 **한 곳에 모아 둔다.** 🔴 **2026-09-07 정정: 그것은 값 하나가
  아니다.** 평가는 `--env-dr-anchor` + `--doraemon-dr-from` **두 플래그**가 필요하고(§6),
  학습은 그 둘로 되지 않으며 **섹션-5 7-오버라이드 블록 또는 arm 별 cfg subclass** 가 필요하다
  (§4-5, `finding/352`). 원래 규약이던 "값 하나만 바꾸면 된다"는 **성립하지 않는다** — 앵커가
  움직이면 평가 플래그 2개와 학습 오버라이드 7개를 함께 옮긴다.
- **모든 산출 디렉터리의 `RUN_CONDITIONS.txt` 에 앵커 경로를 박는다.** 앵커가 한 번 움직이면
  그 전에 나온 수치는 전부 다른 저울이 되고, 그때 어느 수치가 어느 저울에서 나왔는지 구분할
  유일한 근거가 이 파일이다.
- 표를 만들 때 **앵커가 같은 arm 끼리만** 한 표에 넣는다. 재학습이 일어나면 그 시점 이전 arm 은
  재평가 대상이지 그대로 옮겨 적을 대상이 아니다.

#### 8-R-2. 확정 범위와 순서

| 순서 | arm | 왜 이 순서인가 | 학습 |
|---:|:---|:---|:---|
| 1 | **A6 PPO-Enc** 복원 | 코드 0줄(등록 기존재). 새 플랜트 파이프라인 카나리아 — 🔴 단 **as-run params 대조 게이트가 붙어야 카나리아다**(§4-5). 게이트 없이는 옛 플랜트로 조용히 학습돼도 "성공"으로 보인다(`finding/318` 의 실패 양상) | 1 런 |
| 2 | **N2 ATDC** | 학습 0. 코드 약 20줄. eval 만이라 GPU0 을 안 막는다 | 없음 |
| 3 | **N1 Lagrangian** | 표의 가장 큰 구멍(제약 대 제약 0건). line-search 실패 위험이 있어 일찍 드러내야 한다 | 1 런 |
| 4 | **N4 Residual-TDC** | 이음매 기존재. 앞 셋이 서면 가장 안전하게 붙는다 | 1 런 |
| + | 기존 4 arm 재학습 | 앵커 (B) 의 대가. 위 넷과 같은 앵커여야 한 표에 들어간다 | 4 런 |

**총 7 런 x 약 5 h = 약 35 h (GPU0 순차).** §7 의 "약 20 h" 는 신규 arm 만 센 값이고, 앵커 (B)를
고른 이상 기존 4 arm 재학습이 따라온다 — 그것을 빼면 표가 두 저울로 갈린다.
(신규 학습 arm 은 A6·N1·N4 셋이고 N2 는 학습 0이므로 신규분은 3 런 = 약 15 h,
기존 재학습 4 런 = 약 20 h.)

발사는 **`omx queue-launch` 큐만** 건다. 사람 승인 게이트를 지난다.

#### 8-R-3. 재튜닝 프로토콜 채택에 따라 추가되는 산출물

§5 의 4항이 산출물을 요구한다. 구체화:

- `experiments/.../classical_gain_search/<TS>/` 아래에 그리드 정의(JSON), 점별 `summary.json`,
  선정 게인과 그 근거 1줄.
- 탐색은 `none`/`soft` tier 에서만. 보고는 4 tier 전부. 이 분리가 문서에 없으면 3항 주장이 무효다.
- TDC 와 PID 는 **같은 그리드**를 돈다. 둘이 게인이 다르면 "TDE 항의 기여" 라는 A8 의 주장이
  게인 차이와 교란된다.
- 시작점은 kp=48 / kd=14 / m_hat=(0.15,0.16) — §5 의 정정값이다. 40/12 에서 시작하지 말 것.

#### 8-R-4. 이 절 이후의 다음 행동

사용자 지시가 "계획 수립까지 수행" 이므로 **여기서 멈춘다.** 구현(§4)·게인 탐색(§5)·
큐 등록은 별도 승인 사항이다.

> 🔴 **2026-09-07 갱신.** 사용자가 적대적 검토를 요청했고 BLOCKER 3건이 나왔다. **위 "멈춘다"는
> 유효하되 그 앞에 §8-R-6·§8-R-7 두 결정이 선행 조건으로 추가됐다** — 그 둘이 닫히기 전에는
> 큐 등록이 무의미하다(무엇을 몇 시드로 돌릴지가 안 정해졌다). 검토 전문과 백로그 대조는
> 아래 `## Update 2026-09-07`.

### 9. 문헌 근거

| 주장 | 출처 |
|:---|:---|
| Lagrangian 이 safe-RL 표준 비교군, 진동·오버슛 문제와 PID 보정 | Stooke, Achiam, Abbeel, *Responsive Safety in RL by PID Lagrangian Methods*, arXiv:2007.03964 |
| Lagrangian 계수 설정의 실무적 함정 | Spoor et al., *Towards a Practical Understanding of Lagrangian Methods in Safe RL*, arXiv:2510.17564 |
| ATDC(gradient 적응 게인) — 논문이 지정한 비교 대상 | Baek et al., IEEE TIE 65(7), 2018 — 본 논문 References [5] |
| ATDC(적분 SMC + TDE) | Lee et al., IEEE TIE 64(8), 2017 — References [6] |
| RL-TDC(SAC 로 M-hat) — "직접적 선행 연구" | Baek et al., ACC 2022 — References [8] |
| Residual RL over classical controller | Johannink et al., arXiv:1812.03201 |
| PID + residual RL (외란 강건성) | Ishihara et al., arXiv:2308.01648 |

주의: arXiv id 는 검색 결과에서 옮겼다. `.bib` 에 넣기 전에 각 항목의 서지사항을 원문에서 재확인할 것
(이 프로젝트의 인용 규율 — 인용 날조 금지).

### 10. 이 절이 만들지 않은 것

- 코드 0줄. 위 §4 는 전부 제안이다.
- 발사 0건. `omx queue-launch` 도 걸지 않았다.
- 옛 §Decisions 를 지우지 않았다 — §1 표가 그 현재 상태를 적는다. 옛 절을 읽는 사람이 §1 을
  못 보고 낡은 결정을 집는 위험이 남아 있다.

---

## Update 2026-09-07 — 적대적 검토 반영 (BLOCKER 3 · MAJOR 6)

사용자 지시: **"계획을 다시 한번 적대적 검토해줘. 이상 없는지"** → **"전부 검토하고 이상 없으면
결함 수정 진행해줘."**

이 절은 번호상 **§4-5** 와 **§8-R-5 ~ §8-R-8** 을 담는다 — 위 절들의 연속이고 위치만 문서 끝이다.
위 본문의 🔴 표시 열 곳이 이 절과 짝을 이룬다.

**검토가 찾은 근본 원인은 하나다.** 2026-09-06 갱신 절을 쓰면서 `omx wiki list --status
needs-experiment` / `--status needs-apply-before-retrain` **백로그 열거를 돌리지 않았다.**
omx 라우팅 훅이 "요약/plan 작성 전 필수"라고 명시한 그 단계다. 하루 뒤 돌리니 이 계획의 전제를
정면으로 반박하는 열린 리드가 셋 나왔고, 전부 계획서에 한 줄도 없었다.

---

### 4-5. 학습 arm 에 새 플랜트를 실제로 적용하는 방법 — 이 계획에 통째로 빠져 있던 작업

§2 정정대로 섹션-5 플랜트는 **7개 launch override 전용**이고 코드 기본값은 옛 플랜트다
(`finding/352`, status `needs-apply-before-retrain`). 계획은 7 런의 학습을 세우면서 이 블록을
한 번도 적지 않았다.

**편의 장치가 있지만 이 arm 들에는 안 통한다.** `Isaac-ConstrainedALBC-TRPO-SimToReal-v0`
(env cfg `ALBCSimToRealEnvCfg`, `envs/main/config_simtoreal.py`, `envs/main/__init__.py` 등록)이
일곱 개를 한 토큰으로 묶어 두었다. 그러나 이것은 **full-method 전용 task id** 다 — 승인된
arm(A6 PPO-Enc · N1 Lagrangian · N4 Residual-TDC · 재학습 4종)은 각자 다른 task id 라 그 cfg
subclass 를 상속하지 않는다. 즉 **arm 수만큼 손이 간다.**

| 경로 | 작업량 | 장단 |
|:---|:---|:---|
| **(a) arm 별 SimToReal cfg subclass** (권고) | task id 7개 × cfg 서브클래스 1개씩, 학습 0 | 저장소 자체 선례가 이것이다(`config_noconstraint.py` → `...-TRPO-NoIPO-v0`). **블록을 잊을 방법 자체를 없앤다.** base default 를 안 건드리므로 다른 실험에 영향 0 |
| (b) 발사 줄마다 7-오버라이드 블록 verbatim | 런당 복붙 | 한 줄이라도 빠지면 조용히 옛 플랜트. `finding/352` 가 "블록을 잊는 방법을 없애야 한다"고 적은 바로 그 실패 |

**검증 게이트(필수).** 어느 경로를 택하든 학습 시작 후 **as-run params 를 7 필드와 대조**한다.
이것이 §8-R-2 의 A6 카나리아를 실제 카나리아로 만드는 유일한 장치다 — 없으면 옛 플랜트로 학습돼도
"성공"으로 보인다(`finding/318` 의 실패 양상). 주의: 저장소의 `test_simtoreal_cfg.py` 는 이
컨테이너에서 못 돈다(standalone AppLauncher 가 Kit 기동 중 traceback 없이 exit 0 —
`finding/352`·`finding/379`). 따라서 실전 게이트는 **런 디렉터리의 as-run params 대조**다.

**평가 쪽은 별개다.** `--env-dr-anchor` + `--doraemon-dr-from` 두 플래그(§6), 검증은
`tools/check_env_dr_anchor.py`(15/15). 학습 오버라이드와 평가 플래그는 서로를 대신하지 못한다.

#### 4-5-1. 구현 결과 (2026-09-07, ksm-ubuntu 컨테이너 세션)

경로 (a) 채택. 구현된 것과 실측 증거:

**env cfg — 클래스 2개로 7 task id 를 덮는다.** cfg 축은 (플랜트) x (제약 on/off) 둘뿐이고
제약 축은 값이 두 개뿐이라, arm 마다 서브클래스를 하나씩 두면 7-필드 블록이 여러 벌로 갈라진다
(= `finding/352` 가 없애라고 한 바로 그 형태). 그래서:

| 클래스 | 파일 | 담당 arm |
|:---|:---|:---|
| `ALBCSimToRealEnvCfg` (기존) | `envs/main/config_simtoreal.py` | A1 참조, A2 NoEncoder, A3 PPO, N1 Lagrangian |
| `ALBCSimToRealNoConstraintEnvCfg` (신설) | 같은 파일 | A4 TRPO-NoIPO, A5 no-both, A6 PPO-Enc |
| `ALBCResidualTDCEnvCfg` (신설) | `envs/tdc_main/config.py` | N4 Residual-TDC |

7 필드 값은 `ALBCSimToRealEnvCfg` 한 곳에만 있고 나머지는 전부 그것을 상속한다. `ALBCResidualTDCEnvCfg`
가 `ALBCTDCEnvCfg` 가 아니라 `ALBCSimToRealEnvCfg` 를 상속하고 컨트롤러 필드 2개를 다시 선언하는 것도
같은 이유다 — 플랜트 블록을 복제하는 쪽이 위험하고 컨트롤러 기본값 2개를 복제하는 쪽은 안 위험하다.

**신규 task id (6개, 전부 `-SimToReal-` 접미):** `NoEncoder` · `PPO` · `TRPO-NoIPO` ·
`TRPO-NoIPO-NoEncoder` · `PPO-Enc`(A6) · `TRPO-Lagrangian`(N1) — 모두 `envs/main/__init__.py`.
N4 는 `Main-ResidualTDC-SimToReal-v0`(`envs/tdc_main/__init__.py`). 기존 `-TRPO-SimToReal-v0` 가
참조 arm 자리를 이미 갖고 있어 §8-R-7 결정과 무관하게 등록은 완결이다.

**as-run 대조 게이트 = `tools/check_simtoreal_params.py`** (신설). `<run>/params/env.yaml` 을
7 필드와 대조하고 불일치 시 exit 1. Isaac 도 torch 도 필요 없다 — `python3` 만으로 돈다(env.yaml 의
`!!python/object` 태그를 버리는 로더). 그래서 §4-5 가 지적한 `test_simtoreal_cfg.py` 의 함정
(AppLauncher 가 traceback 없이 exit 0 → 안 돌아서 통과)을 피한다. 측정하는 것도 다르다: cfg 클래스는
*무엇을 설정했나*, 이 게이트는 *무엇으로 돌았나* 다.

**실측 (2026-09-07, `--num_envs 16 --max_iterations 2 --headless`, `--run_group ablation_smoke`).**
4 arm 전부 런 디렉터리 + `model_0.pt`/`model_1.pt` + `params/env.yaml` 생성. 게이트 결과:

| 런 | 게이트 |
|:---|:---|
| `albc_ablation/ablation_smoke/ppo-enc_smoke_*_260907_010358` (A6) | 7/7 ok, exit 0 |
| `albc_ablation/ablation_smoke/trpo_smoke_*Lagrangian*_260907_010421` (N1) | 7/7 ok, exit 0 |
| `albc_ablation/ablation_smoke/main_residualtdc_*_260907_010433` (N4) | 7/7 ok, exit 0 |
| `albc_trpo_teacher/ablation_smoke/main_atdc_*_260907_010408` (N2) | **7/7 BAD, exit 1** — 음성 대조 |

마지막 줄이 이 게이트의 검증이다. N2 는 평가 전용이라 `ALBCTDCEnvCfg` → `ALBCEnvCfg` 를 상속해
의도적으로 구 플랜트에 있고, 게이트가 그것을 40 N / delay (0,0) / fault off / lb 250 으로 정확히
집어냈다 — `finding/318` 의 실패 형태 그 자체다. 통과만 확인한 게이트는 아무것도 증명하지 않는다.

**주의 — N2 런이 `albc_trpo_teacher/` 트리에 떨어진다.** 등록이 `ALBCTRPORunnerCfg` 를 스크립트
호환용으로 재사용하기 때문이고(TDC·PID arm 과 동일한 기존 관례), `experiment_name` 이 거기서 온다.
바꾸면 형제 고전 arm 들과 어긋나므로 그대로 뒀다. 표를 모을 때 트리가 갈린다는 것만 알고 있을 것.

---

### 8-R-5. 백로그 대조 — 열린 리드가 이 계획에 실렸는가

`omx wiki list` 실측(2026-09-07): `needs-experiment` 30건, `needs-apply-before-retrain` 2건.
이 프로그램에 걸리는 것만 추린다. **나머지 19건은 student 증류·하드웨어·retrain 프로그램
소관이라 teacher 레벨 비교표와 무관하므로 명시적 defer 한다.**

| 리드 | status | 이 계획에 실렸나 |
|:---|:---|:---|
| `finding/352` 섹션-5 7설정 launch-override 전용 | **needs-apply-before-retrain** | **누락 → §2 정정 + §4-5 신설** |
| `finding/264` 배포 teacher 가 delay (0,0) 학습 | **needs-apply-before-retrain** | 7-오버라이드의 `control_delay_steps (0,3)` 로 함께 닫힌다 → §4-5 |
| `finding/391` exam 이 DR 클래스 기본값으로 채점 | needs-experiment | **누락(치명) → §6 앵커 정정** |
| `finding/395` 성분 ablation 평균은 꼬리 통계 | needs-experiment | **누락(치명) → §6 시드·지표 + §8-R-6** |
| `finding/378` `joint1_pos` 제약 발화 불가 | needs-experiment | **누락 → §6 사문 열 각주** |
| `finding/382` · `debugging/319` | needs-experiment | `finding/391` 과 **같은 결함**이다(별건 아님) → §6 에서 함께 닫힘 |
| `finding/362` model_7500 > model_9999 | needs-experiment | 참조 arm 선택에 직결 → §8-R-7 |
| `decision/390` 배포 후보 = R3a | needs-experiment | 앵커 (B) 의 대상. §2 에 이미 있음 |
| `decision/301` retrain 프로그램 | needs-experiment | 상위 프로그램. 플랜트 델타의 출처 |

---

### 8-R-6. `[DECISION-REQUIRED: seed-and-claim]` — 이 프로그램을 할 가치가 있는가

`finding/395` 가 **재학습하려는 바로 그 4 arm 의 기존 결과를 이미 "시드 노이즈 안"으로 판정했다.**
median 으로는 PPO 가 hard 에서 full method 를 이기고, 셋 사이 격차는 시드 간 산포의 1/3~1/5 다.
1 시드로 새 플랜트에서 재현하면 **같은 "변별 불가"를 35 GPU-h 주고 다시 산다.**

| | (a) 1 시드 + 주장 전환 **(권고)** | (b) 2 시드 | (c) 성분 arm 은 옛 플랜트 결과 유지 |
|:---|:---|:---|:---|
| GPU | 35 h + 참조 arm | 55~75 h | 15~20 h |
| 표의 주장 | **tail control**(max 4.46 vs 15.78 deg) — `finding/395` 가 "살아남는다"고 한 바로 그 신호 | 성분별 우열을 다시 시도 | 외부 알고리즘 비교만 새 플랜트 |
| 위험 | 기여 서술을 tail 로 좁혀야 함 | 20~40 h 더 쓰고도 같은 결론일 확률이 높다 | 표가 두 저울로 갈려 §8-R-1 규약을 스스로 어긴다 |

**권고 (a).** mean 주장이 안 선다는 것은 이미 실측이지 추측이 아니다. (b)는 그 실측을 무시하고
예산을 두 배로 쓰는 선택이고, (c)는 앵커 (B) 결정을 사실상 되돌린다.

### 8-R-7. `[DECISION-REQUIRED: reference-arm]` — 새 플랜트의 "우리 방법"이 없다

**실측.** `logs/rsl_rl/albc_ablation/paper_ablation_5000/` 의 학습 디렉터리는 **4개**다
(noenc · ppo · nobo · noconstr). full_method 디렉터리가 없다 — 그 열은 D13 의 "재학습 금지"에
따라 incumbent 체인에서 왔다. 즉 §8-R-2 의 "기존 4 arm 재학습"을 다 해도 **비교의 기준선이 빈다.**

새 플랜트 teacher 는 `logs/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518`
(model_9999 까지, 배포는 model_7500 — `finding/362`). 그대로 쓰기 어려운 이유 둘: 이름 그대로
**r2050 resume 체인**인데 D13 이 resume 체인 lineage 를 명시적으로 기각했고, 예산이 5000 이
아니다.

| | (i) 새 플랜트 full-method 5000 iter from scratch **(권고)** | (ii) 전 arm 예산을 7500 으로 | (iii) p3b_7500 을 그대로 |
|:---|:---|:---|:---|
| GPU | +5 h | 7 런 × 7.5 h ≈ 52 h | +0 h |
| D13 동일 예산 | 유지 | 유지(값만 이동) | **깨짐** |
| lineage | 깨끗 | resume 체인 잔존 | resume 체인 잔존 |

### 8-R-8. 발사 ack — `finding/352` 는 ack 없이는 안 풀린다

그 리드는 "**task id 를 명시한 retrain launch ack**"(또는 오버라이드 블록 verbatim 을 담은 ack)
으로만 unblock 된다. 큐 등록 시점에 **arm 별 task id 를 나열한 ack 문장**을 발사 승인과 함께
남긴다. ack 은 사람이 하는 것이므로 이 문서가 대신할 수 없다.

---

### 이 검토의 한계 — 교차 계열 검증은 **하지 못했다**

이 계획은 내가 썼으므로 나는 판정자가 될 수 없다(저자-승인자 동일 금지). 다른 벤더 계열에
넘기려 했으나 둘 다 막혔다:

- **codex** — `turn.failed: You've hit your usage limit` (exit 1). 한도 소진.
- **agy** — headless 에 필요한 `--skip-permissions` 를 Claude Code auto-mode 분류기가 거부.
  플래그와 `CODEAGENT_SKIP_PERMISSIONS` env 두 형태 모두 차단. 우회하지 않았다.

따라서 위 결함 목록은 **단일 모델 + 자기 검토**의 산물이다. 이 프로젝트 기준으로 가장 약한
구성이며, 2-family 병렬 검증이 발견을 거의 겹치지 않게 나눠 준다는 실측 전례가 있다. 이
프로그램이 발사되기 전에 한 번은 외부 계열로 다시 걸 것을 권한다.

---

## Update 2026-09-11 — 발사 전 재검토 (비교군 세션 프롬프트 + 논문 인계문)

입력: vault `10-19_Projects/11_Research/01_albc/03_notes/2026-09-11-comparison-arm-training-session-prompt.md`(운영자 21:17 "이번주 주말에 비교군 실험까지 완료하고 싶은데 그럼 지금 비교군 학습을 시작하고 있어야 하는거 아니야?"), vault `.hq/work/scholar/albc/handoff-marinelab-2026-09-11.md`. 발사·큐 등록 0건.

| 무엇 | 결과 | 정본 |
|:---|:---|:---|
| §4-2 p5 yaw 불일치 sim 재현 | 🔴 23:2x 정정 — 첫 두 실행의 INVALID 와 "R3a 전복" 은 계측기 결함(episode_length_buf 지터 → 시간 초과)이었다. 수정 후 사전등록 판정 **V3**(R3a 대조군 4/4 유효, p5 서명 보드식 1/4·학습식 1/4), 단 같은 조건 반복(diagC)은 V1 → roll ≥3° 문턱 노이즈라 **귀속 판정 없음**. 안정 사실: p5 기동 pitch 45.8~57.0° 는 yaw 의미·10/50 Hz·지연 0/3/8 무관(p5 고유, 수조 50.9/51.1°), 보드식 yaw 는 (0,0) roll 오프셋을 +1.0~+2.1° 키움(8/8 짝 비교) | **finding/445** (442 는 대체됨) |
| 선택 교사 플랜트 사실 확인(논문 §4) | 완료 | finding/443 |
| HEAD SimToReal cfg | 혼합 플랜트(섹션-5 7필드 + p5 코드 측 − p5 오버라이드 3) — 앵커 결정에 직결 | finding/444 §1 |
| regrade438 | heading 코드에서 실행. 하네스에서 R3a 에 heading 관측을 주면 +15° 추종이 4 yaw 중 3 에서 무너짐(오차 −15.7~−18.1°, 팔 177° 접힘) → 교란이 클 수 있다. **R3a vs p5 순위는 4078564 이전 트리로 한 셀 재채점하기 전까지 보류** | finding/444 §2, finding/445 §4 |
| finding/441 #7·#6 | 수정·교차검토 완료, **저장소 미적용**(분류기 거부), 패치 `/root/patches/fix441.patch` | finding/444 §5 |
| finding/441 codex 5건 | #5 ATDC m_hat 래칫 확정(N2 행 수치 무효화), #4 확정·무시, #3 설계대로, #1·#2 미정·잠복 | finding/444 §7 |

**발사 전 결정 대기(사용자)**: 앵커(R3a 계열 → `ea42375` 이하 트리 + 패치 이식 / p5 계열 → 오버라이드 3개 cfg 동결 + lb 스케줄), §8-R-6 시드, §8-R-7 참조 arm, 주말 초과분(N6 2런·다중 시드·파지 계단 파일럿) 우선순위, #6·#7 패치 적용·커밋. N2 는 #5 수정(또는 γ 를 §8-R-3 그리드에 포함) 전에는 표에 넣지 않는다.

### 8-R-9. 결정 반영 (사용자, 2026-09-11 23:4x KST, AskUserQuestion)

| 항목 | 판정 |
|:---|:---|
| 앵커 | **R3a 계열** — `ea42375` 에서 판 브랜치 `anchor/r3a-5000`, worktree `/workspace/constrained-albc-r3a`. p5 코드 측 변경(yaw heading 4078564·관성 대역/공칭 416bf56·G5 31a1497·수직 사망/Fz 71301a4·지연 DORAEMON 차원 58ca3d6)은 들어가지 않는다 |
| 시드 (§8-R-6) | **(a) 1 시드 + tail 주장** |
| 참조 arm (§8-R-7) | **(i) 새 플랜트 full-method 5000 it 새로 학습** (`Isaac-ConstrainedALBC-TRPO-SimToReal-v0`) |
| 주말 추가 | **N6 2 런**(No-DORAEMON 고정 DR / No-DR) + **ATDC 래칫(#5) 수정 후 N2** + **파지 계단 파일럿** + **R3a 옛 트리 재채점 1 셀** |

파생: 학습 10 런 = A6·N1·N4 + 기존 4 arm(NoEncoder·PPO·TRPO-NoIPO·TRPO-NoIPO-NoEncoder) + 참조 1 + N6 2, 전부 anchor 브랜치·GPU0 순차. GPU1 = N2 시험·§8-R-3 게인 탐색·파지 파일럿·R3a 재채점.
발사는 여전히 `omx queue-launch` + 사람의 ack(열린 HARD 게이트 finding/264·352·441 을 arm 별 task id 와 함께) 뒤에만.

## Update 2026-09-12 (00:2x KST) — R3a 앵커 커밋·큐 등록 (발사 0)

근거 finding/446. 사용자 선택: **커밋·큐까지만**(발사는 사람이 한다).

| 항목 | 상태 |
|:---|:---|
| 코드 | constrained-albc 워크트리 `/workspace/constrained-albc-r3a` anchor/r3a-5000 @ **3791441** (ea42375 + #6·#7 + ATDC 누설 + N6a·N6b + N6b 인코더 경계) |
| 플랜트 코드 짝 | marinelab 워크트리 `/workspace/marinelab-r3a` @ **8cc84a5** — HEAD 는 log_probs 제거로 ea42375 가 죽고, velocity_limit_sim 2.40(p5)을 싣는다 |
| N6 정의 (§8-R-9 보강) | N6a = DORAEMON off, section-5 정적 범위 균일. N6b = eval none 공칭 점 + buoy 스케일 1.0, enable True(추력기 고장·초기 관절 무작위 유지), 인코더 경계는 section-5 범위 |
| 큐 | `.hq/work/experiments/runs/r3a5000_{a6_ppoenc,n1_lagrangian,n4_residual,noenc,ppo,noipo,noboth,ref_full,n6a_nodoraemon,n6b_nodr}_s30/pending-launch.json`, ack 264·352·441·444 |
| 발사 | `EXPECT_HEAD=3791441 nohup bash .hq/community/programs/paper-ablation-5000/launch_chain_r3a.sh &` — preflight(두 워크트리 HEAD·clean·import origin·GPU0 idle), variant 게이트 + velocity 3.1, 종료까지 nan·Traceback·20분 정지 감시, 프로세스 그룹 kill |
| 발사 후 세션 몫 | A6 의 게이트·it50 직접 확인, 500~1000 it 마다 DORAEMON mode·fault_severity TB 스칼라, 끝난 arm 은 pending-launch status 갱신 |

열린 lead 처리 (queue-launch 가 42건을 open_leads 로 실음):
- 이 라인의 표에 영향: finding/378(joint1_pos 제약 불발 — 모든 arm 공통, 표 각주), 410(관측잡음 그룹 불일치 — 공통, 각주), 362·405(마지막 체크포인트 ≠ 최선 — 평가는 공통 sidecar 로 복수 체크포인트), 395(꼬리 통계 — 1시드 + tail 주장 결정과 한 짝, median·P90 병기), 318·391·396(시험 플랜트 교란 — 채점은 `--env-dr-anchor` + 공통 sidecar).
- GPU1 병행 몫: 438·439(재채점·잠재 오차), 445(T4). 
- 이 라인과 무관(학생·배포·보드·p5 교사): 163·198·263·296·301·305·309·312·313·315·319·321·355·363·379·380·382~387·389·390·397·401·402·404·407·408·442 — defer, 사유: 비교군 학습 플랜트·채점 방식에 입력이 없다.

GPU1 병행(승인된 주말 추가분) 상태:
| 항목 | 상태 | 막힌 곳 |
|:---|:---|:---|
| N2 시험 + §8-R-3 게인 탐색 | 도구 초안(codex, 미검토) | `eval.py static` 은 tier 선택이 없어 4 tier 를 다 돈다 → 선정은 none/soft 값만 읽고 보고는 4 tier (§8-R-3 조건 충족 가능). ATDC leak 격자 {0.1, 0.5, 2.0} 이상 필요(스모크에서 0.5 도 상한 도달) |
| 파지 계단 파일럿 | eval.py `--hold-zero-cmd` 초안(미검토) | 기존 `--flat-target` 과 겹침, 페이로드 질량의 step 궤적 기록이 없어 판독기가 거부 |
| R3a 옛 트리 재채점 1셀 | 방법 미정 | 이제 옛 트리 = 이 앵커 워크트리 쌍. 단 p5 sidecar(23 dim)를 ea42375 DORAEMON 이 받는지 미확인, HEAD 와 비교하면 yaw 의미·p5 플랜트 코드가 섞인다 |

## Update 2026-09-12 (01시 KST) — 재검토 수정·채점 규약·v14 회신 (발사 0)

사용자 요청 "재학습 계획 및 큐를 꼼꼼히 다시 검토" 에서 결함 3건이 나왔다. 사용자 선택(AskUserQuestion): **결함 3건 + 순서 변경**, 참조 arm 과 p3b model_5000 **둘 다 채점**, 채점 규약 **지금 작성**.

### 발사 체인 수정 — `launch_chain_r3a.sh` f939507d → **a9db0c55** (옛 판 `/root/patches/launch_chain_r3a.sh.f939507d`)

| 결함 | 증상 | 수정 |
|:---|:---|:---|
| nan 정규식 오탐 | 옛 `Traceback\|(^\|[^a-z_])nan([^a-z_]\|$)` 가 건강한 10001 it p5 교사 로그의 DORAEMON 경고 `Entropy opt rejected ... (neg_H 44.3 -> nan, KL=229.6)`(doraemon.py:666) 3줄에 걸린다 — 멀쩡한 arm 을 죽인다 | `Traceback\|:[[:space:]]+-?nan[[:space:]]*$`(지표 줄 끝의 nan). 건강한 전체 로그 3개(20,043 it) 적중 0, 깨진 런 52 |
| preflight 사문 | GPU0 대기 루프 안의 `return 0` 이 dirty·import origin 검사보다 앞에 있어 두 검사가 도달 불가 | HEAD·marinelab HEAD·dirty·import origin 을 GPU 대기 앞으로 |
| 큐 예측 거짓 | ref·A6 "it 1000 까지 fault_severity > 0.05 (p3b 처럼)" — p3b 실측은 it 1000 에 0.013, it 2000 에 0.023. N4 "it 1000 커리큘럼 개방" 은 무측정, NoIPO·NoBoth "제약 위반 더 큼" 은 eval 이 비용을 안 남겨 판정 불가 | p3b TB 실측(mode it 250/500/750/1000 = −3/−2/0/0)으로 교체. A6 커리큘럼 개방은 파이프라인 검사가 아니라 arm 의 성질로, N4 는 기본 게인 kp 48 / kd 14 명시, NoIPO·NoBoth 는 비용 판독 필요 명시, N6b 는 참조 task 채점 명시 |
| 순서 (사용자) | — | **ref_full 먼저**(p3b 대조 카나리아) → A6 → N1 → N4 → NoEnc → PPO → NoIPO → NoBoth → N6a → N6b. run dir 에 `model_4999.pt` 가 있는 arm 은 SKIP(컨테이너 재시작 뒤 재학습 방지) |

모의 시험 `/root/chaintest2`: 실제 체인 파일에 경로·시간 상한만 sed 로 바꾸고, 실 git 저장소와 실 Isaac python(find_spec), 가짜 trainer 를 썼다. 11 경로 모두 기대대로 나왔다 — GATE ok·END rc 0(DORAEMON 경고 줄 포함), nan kill, END rc 3, STALL kill, velocity 2.40 게이트 실패, variant 게이트 실패, 손자 프로세스 잔존 0, 재실행 때 SKIP 뒤 dirty·marinelab HEAD·import origin·albc HEAD FATAL(각 rc 2).

큐: 10건 재등록(2026-09-12 00:46 KST, queued_commit 3791441, `queue_r3a.sh` 57dd8afe 가 CHAIN_MD5 기록, ack 264·352·441·444, open_leads 42 — 처리는 00:2x 절 그대로). 옛 JSON 은 `/root/patches/queue-0912a/`.

교차검토: agy 5건은 로그·코드 대조로 전부 기각(run dir 이름 형식 오해, 로그에 ANSI 없음 `cat -A`, 정상 로그 적중 0 등). codex 는 사용량 한도로 미실행 — 채점 체인까지 넣어 02:48 KST 재시도 예약.

### 채점 규약 — `exam_chain_r3a.sh` **082bb33f** (GPU1, 직렬, 재진입: summary.json 이 있는 설정은 건너뜀)

| arm | task | 체크포인트 |
|:---|:---|:---|
| p3b_5000 (같은 시드 두 번째 실현) | `Isaac-ConstrainedALBC-TRPO-SimToReal-v0` | `retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/model_5000.pt` |
| ref_full · N6a · N6b | `Isaac-ConstrainedALBC-TRPO-SimToReal-v0` | 각 run 의 `model_4999.pt` |
| A6 · N1 · N4 · NoEnc · PPO · NoIPO · NoBoth | 각자의 task | 각 run 의 `model_4999.pt` |

공통 조건: `--env-dr-anchor --doraemon-dr-from <p3b r2050 run dir>`(TB 마지막 값의 mean ± 2 std), 64 envs, seed 42, `--att-amp-deg 15`, p4 CORE 4 설정(healthy · pair34 = m3+m4 사망 · healthy_d1 · healthy_d2), 산출 `.hq/work/paper_ablation_r3a/exam/<arm>/<cfg>/` + `RUN_CONDITIONS.txt`. p3b_5000 은 시작 즉시, 이후 600 s 마다 `model_4999.pt` 가 생긴 arm 을 채점하고, 전부 끝나거나 chain.log 에 CHAIN COMPLETE 가 뜨면 끝난다.

전제 검증 (2026-09-12 01:1x KST):
- 앵커 출처는 `--task` 레지스트리 cfg 다 — `@hydra_task_config(args_cli.task, …)`(eval.py:2568), run dir 에서는 agent.yaml 만 읽는다(eval.py:1293). 로그 문구 "the run's own env cfg"(dr_config.py:82)는 표현이 틀렸다.
- 자기 task 로 채점하는 7 arm: 스모크 run 의 `params/env.yaml` 이 참조 스모크와 `randomization.*`·`doraemon.*`·`fault.*` 차이 0. N4 는 제어기 게인 `thruster_pd.*` 만, A6·NoIPO·NoBoth 는 `constraints.terms` 만 다르다. `observation_noise_model` 3 필드는 참조 스모크끼리도 다르고 eval.py:1201 이 None 으로 덮는다.
- N6b 인코더 경계(`priv_obs_bounds_randomization`)는 참조 `randomization` 범위와 전 필드 일치. 경계는 등록 버퍼(actor_critic_encoder.py:150-154)라 체크포인트에서 복원된다 — 러너가 none 수준 env cfg 로 경계를 새로 만들어도(constraint_encoder_runner.py:105) 학습 때 경계가 쓰인다.
- 체인 간 간섭: 스모크 뒤 두 워크트리 dirty 0. 채점 체인의 CHAIN_LOG 는 학습 체인 `LOGDIR/chain.log` 와 같은 경로이고 아직 없다(남은 CHAIN COMPLETE 없음). `--control-delay` 는 static 서브파서 옵션(eval.py:146).

스모크(EXAM_SMOKE=1: anchor_smoke 체크포인트, 4 envs, 0.5 s 구간, healthy 만): **11/11 rc 0·summary.json**(00:52~01:07 KST, `/root/examsmoke/`). 표의 nan 은 vx·vy·vz 열(전 arm, p3b 포함)과 0.5 s 안에 기준을 못 넘은 상승시간 칸이다(metrics.py:76 empty slice) — 러너 결함이 아니다. pair34·healthy_d1·healthy_d2 는 스모크가 돌리지 않았다.

한계: eval.py 는 제약 비용을 기록하지 않는다 — NoIPO·NoBoth 의 제약 충족도, v14 A1 도 이 체인으로는 못 낸다. 결정론적으로 죽는 설정은 CHAIN COMPLETE 까지 600 s 마다 재시도된다.

발사(둘 다 사람): 학습은 `EXPECT_HEAD=3791441 nohup bash .hq/community/programs/paper-ablation-5000/launch_chain_r3a.sh &`(GPU0, 약 49 h). 채점 체인은 **큐 미등록** — v14 인계문 규칙("학습·평가 발사는 exp-design proposal → 사용자 승인 → `omx queue-launch` 만")에 따른 등록 방식은 사용자 결정 대기.

### v14 인계문 회신 요지 — vault `.hq/work/scholar/albc/handoff-marinelab-2026-09-12-v14-reply.md`

- 큐의 10 런은 설정 변경이 필요 없다.
- B1~B5 코드 사실 확인 완료: 비용은 보상에 안 들어간다(albc_env.py:1410-1412), 표 II 값은 D_k 예산이고 d_k = D_k/(1−γ_c)(constraint_trpo.py:149), 적응 상한 α = 0.05(rsl_rl_ppo_cfg.py:228), 46D = 추종 특징 10 × 3 스텝 + 행동 8 × 2 스텝(config.py:518-526), F_bu 26.2 N 은 부이 총부력(marinelab albc.py:104-109).
- A1(제약별 비용)은 eval 코드 수정이 필요하다 — 학습 워크트리를 고치면 체인의 dirty FATAL 이 다음 arm 을 멈추므로 **별도 평가 워크트리**에서. IPO 를 끈 arm 의 비용은 참조 제약 cfg 로 계산해야 한다. A2~A5·A7 미착수, A6 부분(eval.py:1214 에피소드 길이), C1~C4 proposal 미작성 — 범위 사용자 결정 대기.
- AC 는 full vs PPO ≥3 시드를 overshoot 효과의 1순위 증거로 꼽았다 — 1시드 결정(§8-R-9) 재검토 여부는 사용자 몫.

남은 일: codex 교차검토(02:48 예약) · 채점 체인 등록 방식 · v14 A/C 범위 · GPU1 병행 3건(00:2x 절 표 그대로) · 발사 뒤 ref 카나리아를 p3b TB 궤적과 500~1000 it 마다 대조.

### 사용자 결정 (2026-09-12 01:2x KST, AskUserQuestion)

| 질문 | 답 |
|:---|:---|
| 채점 체인 등록 | **proposal + 큐 등록** — pending-launch 1건, 발사는 사람 |
| v14 A 범위 | **A1·A2·A3·A4·A5·A6·A7 전부** (GPU1 은 기승인 추가 3건과 나눠 씀) |
| v14 C | **C1·C2 proposal 작성** (발사는 체인 뒤·승인 뒤) |
| 다중 시드 (AC 1순위 증거) | **체인 결과를 보고 결정** — 노이즈 바닥 = 같은 시드 두 실현(p3b model_5000 vs 새 ref_full) |

### 채점 체인 큐 등록 (2026-09-12 01:31 KST)

- `exam_chain_r3a.sh` 082bb33f → **0bb2a54a**: 평가 호출을 `flock /root/gpu1.lock` 안으로 옮기고 `RUN_CONDITIONS.txt` 에 `lock_acquired=` 를 남긴다. GPU1(8 GB)에는 v14 A1~A4 계측 평가·게인 탐색도 올라가므로, 모든 GPU1 작업은 이 잠금을 같이 쓴다. 옛 판 `/root/patches/exam_chain_r3a.sh.082bb33f`.
- 모의 시험 `/root/examlocktest` (가짜 평가기, GPU 0): 선점된 잠금이 풀린 뒤에야 첫 평가가 시작했고, 도중에 들어온 다른 잠금 작업과 실행 구간 13개가 겹침 0, 실패 rc 3 은 `summary=NO` 로 기록. 두 워크트리 dirty 0.
- pending-launch `.hq/work/experiments/runs/r3a5000_exam_gpu1/` — proposal_id `paper-ablation-5000`(이 절이 규약), queued_commit 3791441, ack 264·352·441·444, open_leads 42(00:2x 절 처리 그대로). exp-design 은 분석 report.md 에서 진단 탐색을 뽑는 절차라 측정 규약에는 쓰지 않았다 — 학습 10건과 같은 등록 방식.
- 발사(사람, `/workspace/constrained-albc` 에서): `nohup bash .hq/community/programs/paper-ablation-5000/exam_chain_r3a.sh > .hq/work/paper_ablation_r3a/exam_chain.out 2>&1 &`

## Update 2026-09-12 (02시 KST) — v14 판독 결과·A1~A4 계측 설계·A2 학생 행·C1·C2 proposal (발사 0)

사용자 지시(2026-09-12 01:5x KST, 원문): "나 이제 자러 갈꺼거든? 나한테 따로 질문하지 말고 끝까지 진행해줘. 그리고 커뮤니티 기록 열심히 해주고." — 앞선 결정(01:2x 절: A1~A7 전부, C1·C2 proposal, 시드는 체인 결과 뒤)을 그대로 집행한다. **발사는 계속 사람 몫이다**: 이 절의 설계·proposal 은 전부 승인 대기이고, 사용자 판단이 필요한 선택은 권고안을 사전등록해 두었다.

### v14 판독 결과 — finding/447·448·449

| 항목 | 결과 | finding |
|:--|:--|:--|
| A5 교사 복제 | Table IV 에 ±SD·n 64·생존 64/64 부착. 선택 교사(iterbudget) DORAEMON 은 it 7748 에 21/21 차원 Beta(1,1) 포화. **원고의 "2350 이후 두 세그먼트만 보정" 은 틀림** — 세그먼트 1(`trpo_eint_s30_260727_160913`, resume false)부터 부피 0.0079·추력 대역 (0.85, 1.15) | 447 |
| A6 평가 프로토콜 | 궤적 31 × 5 s = 155 s(54.4 s 는 평가 에피소드 안 전복 시각, 30 s 는 학습 horizon). Table V 채점·앵커 B 모두 **yaw rate** 계단(±0.5 rad/s), Yaw OS = rate 계단 크기 대비 %. 종료 2.5 rad 축별 | 448 |
| A7 paired SE | roll OS Hard full−PPO 1.65× → **1.92×**(tie 유지), pitch OS Hard full−no_encoder(원고의 1.72× 비교는 PPO 가 아님) 1.72× → **3.58×(separation)**. Table V Roll OS Hard 는 공통 집합 보정값 → finding/393 반박 댓글 | 448 |
| B1~B5 | 코드 사실(비용은 보상에 안 들어감, 표 II = D_k, α 0.05, 46D = 10×3 + 8×2, F_bu 총부력) | 449 |
| A1 학습 측 | TB `Constraint/viol`·`margin` 에서 J_Ck·d_k^i·적응 활성·N1 λ 가 매 iteration 복원된다(판독기 `/root/v14/a1_train_costs.py`). p3b: 적응 threshold 는 0..2092 구간 iteration 의 ≤ 4 %(J/d 가 1−α 를 넘은 넷)에서만 켜졌고 **2050..9999 에서는 10개 모두 0 %** | 449 |

조사 에이전트 보고 중 **틀린 주장 2건을 판정 단계에서 걸렀다**: (1) main HEAD 코드를 읽고 "yaw 는 heading 목표, 원고 yaw rate 서술이 낡음" — heading 전환 4078564 는 09-07 12:49 로 두 채점보다 뒤, (2) "측정 joint1 각도는 언랩 누적값(4π 한도로 추론)" — finding/378 이 Phase 4 npz 로 **±2π 래핑**을 실측했다(그래서 `joint1_pos` 제약은 발화 불가, TB 의 작은 J_Ck 는 cost critic 편향). 둘 다 finding 과 계측 명세에 반영.

### A1·A3·A4 계측 — 별도 평가 워크트리, 채점과 한 번에

- 워크트리 `/workspace/constrained-albc-eval`(branch `eval/r3a-5000-v14`, 3791441 에서 분기, 02:0x 생성). 학습 워크트리 `constrained-albc-r3a` 는 dirty 검사가 걸려 있어 손대지 않는다(생성 뒤 dirty 0 확인).
- `eval.py static` 에 opt-in 두 플래그. 끄면 기존 산출(`data_<level>.npz/.mat`, `latent_<level>.npz`)과 출력이 **바이트 동일**해야 한다(수용 기준). 새 산출은 새 파일 `extras_<level>.npz` + `extras_meta.json` 에만:
  - `--save-extras`: 매 스텝 `extras["costs"]`(E, 10) · 관절 위치(float32)·속도. **IPO 를 끈 arm(noipo·noboth·A6)은 env 가 비용을 계산하지 않으므로**, 정책 로드 뒤 `raw_env._constraints_cfg` 만 참조 10제약으로 바꿔 끼운다. 그 속성은 `_get_rewards` 비용 계산에서만 읽히고(albc_env.py:206·1411), 러너는 `env.unwrapped.cfg.constraints` 로 동기화하므로 정책은 영향이 없다. 비용 함수는 상태를 읽기만 한다. eval 루프에서 사후 계산하지 않는 이유: `rp_vel_settling` 은 `_prev_root_lin_vel_b` 갱신 **전** 값을 봐야 한다(albc_env.py:1414-1416 주석).
  - `--save-moments`: root(선체) 링크 원점 기준·선체 프레임 외부 모멘트 분해 — 추진기 `B τ`(`thruster.body_torques`), 선체 유체력, **부이 링크 유체 렌치(부력 몫)**, 그리퍼 payload 렌치, 부이·팔·선체 중력. 근거: env 렌치는 `is_global=False`, IsaacLab 이 `apply_forces_and_torques_at_position(position_data=None)` 로 쓰고 PhysX 문서상 "position 미지정 = 링크 변환 위치에 적용"; 중력은 질량중심.
- 판독 `v14_extras_readout.py`(numpy 만): 제약별 활성률·스텝 평균 비용/D_k·J(시작점)·**평균 할인 cost-to-go**(학습의 J_Ck 와 같은 뜻, 전진 누적식)·여유 d_k − J, 전복 env 는 전복 전 구간만; joint1 누적 회전은 적분기 `joint1_target` 과 주기 4π 언랩 측정값 둘 다, 30 s 창 최대; 모멘트 RMS 와 부이 몫 = RMS_buoy / (RMS_buoy + RMS_thr)(부이 중력 포함판 병기), 자세 블록 한정판.
- 사전등록 판정: A1 표 셀은 None·Hard × CORE 4설정 × arm, 통계 mean·median·P90·max(finding/395: 평균이 꼬리 통계일 수 있음).
- 구현 경로: 명세 `SPEC.md`(세션 작성, 설계 확정) → codex develop(ground 1, 02:48 사용량 해제 뒤) → 세션 리뷰 → 평가 워크트리 커밋 → Isaac python 테스트 → GPU1 스모크(모두 `flock /root/gpu1.lock`): (V1) 앵커 무플래그 2회가 같은지, 그리고 플래그 켠 평가 워크트리의 `data_*.npz` 가 같은지 — 기록이 궤적을 안 바꾼다는 판별 시험, (V2) noipo 스모크 체크포인트로 참조 swap, (V3) p3b model_5000 전체 길이 1셀로 크기·시간. 통과 전에는 채점 체인을 바꾸지 않는다.

### A2 학생 행 — 채점 체인에 합류 (옛 트리 R3a 재채점도 이것으로 닫힌다)

앵커 B 에는 학생이 없다. 새 §V 의 학생은 R3a 계열이므로, 채점 체인에 준비된 행 셋을 p3b_5000 처럼 **즉시 채점 가능한 행**으로 넣는다:
`p3b_7500`(학생들의 교사, 참조 task) · `r3a_gru` = `albc_trpo_student/retrain_simtoreal_p3/trpo_sd_p3b7500_c3_dr5_beta0_s30_260906_003754/models/student_999.pt`(배포 팩과 같은 체크포인트) · `r3b_tcn` = `trpo_sd_p3b7500_tcn_dr5_s30_260906_013849/models/student_999.pt`(finding/388, 실패 arm). 학생 모드 인자 `--student_ckpt --teacher_ckpt <p3b model_7500> --encoder_type gru|tcn`, GRU 경로에는 cuDNN preamble 이 필요하다(finding/382, `sd_exam_generic2.sh`). 규약은 다른 행과 같다(앵커 워크트리 = rate 트리, p3b 최종 DORAEMON 박스, CORE 4설정, att 15°, 64 env, seed 42). 잠재 오차는 `latent_<level>.npz`(기존 계측)에서 tier 별 ‖ẑ−z‖, 두 학생이 잃은 env 비교, 공통 완주 집합 기준 교사 평균. 이 행들이 09-08 regrade438(heading 코드에서 돈 R3a 재채점, finding/444) 을 대신한다.

### C1 proposal — 고정 가중 penalty arm (**pending approval**, 체인 뒤 GPU0)

- 질문(F-11): IPO 의 적응 barrier 대신 **같은 10개 비용을 고정 가중 보상 penalty 로** 걸면 무엇이 달라지나. N1(Lagrangian, 큐)과 짝을 이루는 "제약을 다르게 거는" 두 번째 arm.
- 한 변수: 큐의 **noipo arm**(`Isaac-ConstrainedALBC-TRPO-NoIPO-SimToReal-v0`: 인코더 on, `constraints.terms=[]`, 러너 K=0 자동 동기화로 barrier·cost critic 없음)에 `reward.extra_terms` 10개만 더한다. 기존 레지스트리 `RewardTermCfg(func, params, weight, name)`(rewards.py:87-101)가 비용 함수 시그니처와 같고, 매니저가 `weight × dt × value` 로 합산한다(rewards.py:249-252). 계산 시점도 비용과 같다(`_get_rewards` 안, `_prev_root_lin_vel_b` 갱신 전). ConstraintTRPO 러너에 K=10 을 남기면 auto-sync 가 barrier 를 되살리므로(constraint_encoder_runner.py:48-54) noipo 경로가 가장 작은 변경이다. 대가: 학습 중 `Constraint/*` TB 태그가 없다 — 비용은 A1 평가 계측(참조 swap)으로 잰다.
- **가중치 규칙(사전등록, 발사 전 고정)**: `weight_k = −ρ · r̄ / (K · D_k · dt)`, K = 10, dt = 0.02 s, **ρ = 1**, **r̄ = 0.1529** = p3b r2050 의 iteration 4900–4999 평균 스텝 보상(TB `Train/mean_reward` 217.28 / `Train/mean_episode_length` 1421.0, 5000 it 예산과 같은 시점, `/root/v14/reward_scale.py`). 뜻: 10개 제약이 모두 정확히 예산(c_k = D_k)에 있으면 스텝마다 참조 계열 평균 스텝 보상만큼 잃는다. p3b 운용점(J/d 0.01~0.83, 평균 약 0.23)에서는 약 23 %.

  | 제약 | D_k | weight_k |
  |:--|--:|--:|
  | attitude · joint1_pos · cumul_yaw | 0.01 | −76.45 |
  | arm_joint_vel | 0.02 | −38.225 |
  | manipulability | 0.05 | −15.29 |
  | arm_torque | 0.08 | −9.556 |
  | rp_rate · yaw_rate | 0.10 | −7.645 |
  | rp_vel_settling | 0.20 | −3.8225 |
  | thruster_util | 0.40 | −1.911 |

  `joint1_pos` 는 래핑 때문에 발화하지 않지만(finding/378) "같은 10개" 를 지키려고 그대로 둔다(실효 0).
- 기각한 규칙: (a) N1 최종 λ_k 동결 — λ 는 표준화된 비용 advantage surrogate 에 곱해지는 승수라(constraint_trpo.py:449-452, constraint_lagrangian.py:90-96) 스텝 비용 가중치로 바꾸는 원칙적 변환이 없고 N1 결과를 기다려야 한다(λ 는 TB viol 재생으로 복원은 된다, finding/449). (b) IPO 암묵 승수 1/(t·margin) — 같은 스케일 문제. (c) 격자 탐색 — 여러 런이 필요하고 시험 결과로 고르는 것이 된다.
- 해석(사전등록): C1 이 참조(IPO)와 Hard 자세 오차·생존에서 floor(0.10°)·2×SE 안이고 제약 여유도 비슷하면 "적응 barrier 는 고정 penalty 대비 이득 없음" 을 보고한다. C1 이 제약은 지키지만 추종이 나쁘면(또는 반대) 고정 가중의 trade-off 로 보고한다. 어느 쪽이든 1시드·단일 ρ 라는 한계를 같이 적는다(§8-R-9).
- 구현(승인 뒤): 3791441 에서 새 브랜치 `anchor/r3a-5000-c12` + 새 워크트리(학습 워크트리·체인 무접촉). 파일: `config_simtoreal.py` 에 `ALBCSimToRealFixedPenaltyEnvCfg(ALBCSimToRealNoConstraintEnvCfg)`, `__init__.py` 에 `Isaac-ConstrainedALBC-TRPO-FixedPenalty-SimToReal-v0`(러너 = noipo 와 같은 cfg). 게이트 `check_simtoreal_params.py --variant section5` 는 task id 를 안 보므로 그대로 통과한다. 5 it 스모크(nan 토큰 0 + `extras_terms` 10개 env.yaml 확인) → `omx queue-launch`. 예산 5000 it ≈ 4.9 h(GPU0, 체인 뒤).

### C2 proposal — 팔 고정(추진기 전용) arm (**pending approval**, A4 판독 뒤 사용자 판단 권고)

- 질문(F-10): 움직이는 부이(ALBC 기구)가 추진기만으로 얻을 수 없는 이득을 주는가. A4 는 모멘트의 **귀속**을 보여 주고, C2 는 **반사실**(기구를 안 움직였을 때)을 보여 준다 — 서로 대체하지 않는다. 그래서 권고는 A4 결과와 무관하게 C2 를 돌리는 것이고, 판단은 A4 부이 몫(p3b_5000 채점 셀이 가장 먼저 나온다)을 본 뒤 사용자가 한다.
- 설계: 참조 arm(`-TRPO-SimToReal-v0`)과 알고리즘·러너·제약·DR·예산 동일, 변수 하나 = **관절 행동 무효화**.
  - 마스킹 지점: `_pre_physics_step` 진입, `_update_action_buffers` **전**에 행동 [0:2] 를 0 으로(albc_env.py:740-750). 물리·행동 이력 관측·smoothness 보상이 모두 "적용된 0" 을 본다. 적용 지점(albc_env.py:794)에서만 막으면 정책 출력이 이력에 남아 관측과 실제가 어긋난다.
  - 초기 자세: 참조는 관절을 ±π 균일로 초기화하고 리셋 때 PD 목표를 측정값에 스냅한다(config.py:507, albc_env.py:1668). 행동이 0 이면 그 무작위 자세에 에피소드 내내 고정된다. **사전등록: 팔을 접은 자세 (θ1, θ2) = (0, π)** — 두 링크가 0.233 m 로 같고(marinelab `albc.py:166-167`) 두 관절이 같은 수평면에서 돌므로 부이가 관절 1 축(선체 중심 + base 오프셋 2 mm) 위에 온다. 부이 부력이 선체에 수평 지레를 만들지 않는 **트림된 기체**다. 관절 초기화만 끄고 나머지 DR 은 유지. 새 cfg 필드 2개(`freeze_arm_actions`, `arm_init_pose`), 기본값이면 바이트 동일.
  - 기각한 자세: 배포 홈 (0, π/2) 은 부이가 선체 중심에서 수평으로 약 0.33 m 떨어진다. 부이 총부력 26.2 N(순 17.1 N)이면 약 5.6~8.7 N·m 의 상수 모멘트인데, roll 추진기 지레는 0.007 m(pitch 0.145 m, rewards.py:109 주석)라 추진기로 상쇄할 수 없다 — 기구의 기여가 아니라 "트림이 틀어진 기체" 를 시험하게 된다. 무작위 초기 자세 유지도 같은 이유로 기각.
  - 접은 자세는 manipulability 특이점(θ2 = π, w = 0)이라 그 비용은 에피소드 내내 상수다. 상수 비용은 적응 threshold 아래에서 barrier 여유가 α·d_k 로 고정되고 표준화 cost advantage 가 0 에 가까워 기울기를 만들지 않는다. 보고 때 manipulability 열은 이 arm 에서 의미가 없다고 적는다.
  - 제약 10개는 그대로 둔다. 팔이 고정되면 팔 관련 비용이 상수가 되어 적응 threshold 아래에서 기울기를 만들지 않는다(표준화 cost advantage ≈ 0).
- 해석(사전등록): C2 가 참조보다 Hard 자세 오차·생존에서 floor·2×SE 밖으로 나쁘면 기구 기여의 반사실 증거, 안이면 "이 시험 분포에서 추진기만으로 충분" 으로 보고한다. roll 추진기 지레가 작아 roll 계단(±15°)에서 차이가 가장 크게 날 것으로 예상하지만 예측일 뿐이다. 접은 자세 한 점만 본다는 한계를 적는다.
- 구현(승인 뒤): C1 과 같은 브랜치·워크트리, task `Isaac-ConstrainedALBC-TRPO-ArmFrozen-SimToReal-v0`, 스모크에서 관절 위치가 접은 자세에 머무는지와 행동 이력 [0:2] 가 0 인지 확인 → 큐. 예산 5000 it ≈ 4.9 h.

### 고전 제어기 게인 탐색 — proposal (**pending approval**, GPU1, §5·§8-R-3 규약의 실행판)

주말 필수 4건(09-11 사용자 결정) 중 하나. 비교 표의 TDC·PID·ATDC 행은 "튜닝 안 한 baseline" 지적을 막으려면 이 탐색을 거쳐야 수치를 쓸 수 있다(§5). 도구 초안(`classical_gain_search.py`, 09-11 codex 초안, 미검토)을 읽고 결함을 판정했다:

| 초안의 문제 | 판정 · 수정 |
|:--|:--|
| static 에 tier 선택이 없어 실제 발사를 거부 | 평가 워크트리 패치의 `--levels none,soft` 로 해소(tier 인덱스 기반 시드 유지, 부분 실행은 튜닝 전용) |
| `--parallel 3` | GPU1 8 GB 에 Isaac 평가 두 개가 동시에 뜨면 충돌 — **직렬 + `flock /root/gpu1.lock`** |
| 산출을 워크트리 안 `experiments/` 에 씀 | 워크트리 dirty → 채점 체인 `code_clean` FATAL. 산출은 `$MAIN/.hq/work/paper_ablation_r3a/gain_search/<controller>/` |
| ATDC override `env.tdc_controller.m_hat_leakage` | 필드 이름이 틀렸다 — `m_hat_leak`(tdc_main/config.py:78·98), 적응 이득은 `m_hat_adapt_gain` |
| 선정 지표를 summary.json 평균으로 "대체" 하며 자체 guard(생존 −1, soft ×1.10)를 정함 | 선정 규칙은 사용자 결정 사항 — 아래에 권고안으로 사전등록, 승인 대기 |

- 탐색 공간(§8-R-3 그대로): kp ∈ {24, 34, 48, 68, 96} × kd ∈ {7, 10, 14, 20, 28} × m̂ 스케일 ∈ {0.67, 1.0, 1.5}(기준 m̂ (0.15, 0.16)) = 75점, TDC 와 PID 는 같은 격자. ATDC 는 TDC 선정 (kp, kd, m̂) 위에서 `m_hat_leak` ∈ {0.1, 0.5, 2.0} × `m_hat_adapt_gain` ∈ {0.01, 0.02, 0.04} = 9점(ATDC 적응 이득·누설은 이 절이 처음 정하는 격자 — 승인 대상).
- 채점 규약: 앵커 B 채점과 같은 박스(p3b 최종 DORAEMON, `--env-dr-anchor`), healthy, 64 env, seed 42, att 15°, `--levels none,soft` 만. 보고는 선정 게인으로 **채점 체인의 CORE 4설정 × 4 tier 전체**(다른 arm 과 같은 셀).
- 선정 규칙 권고(사전등록): 점수 = none·soft 두 tier 의 `att_norm.ss_error`(64 env 평균) 평균, 최소값 선정. 동률(차 < 0.10° floor)이면 기본값 (48, 14, 1.0)에 로그 거리로 가까운 점. 제외 조건: soft `survival_pct` 가 기본값보다 1 env(1.5625 pp) 넘게 낮은 점. median·P90 은 `--save-extras` 없이도 data npz 로 계산 가능하지만, 선정은 평균 하나로 고정하고 median·P90 은 기록만 한다(선정 지표를 여러 개 두면 사후 선택이 된다).
- 범위 밖으로 둔 것(명시): 추진기 PD 게인(`thruster_pd.kp_att 24, kd_att 6, kp_yaw 30, kp_lin 120`)은 기본값 고정. 추력 13 N 플랜트에서 이 게인도 재조정 여지가 있지만 §5 규약에 없고, 넣으면 격자가 곱으로 커진다 — 한계로 보고.
- 예산(실측 기준): 앵커 트리 64 env 전체 길이 채점 1셀(4 tier × 155 s) = **536 s**(02:18~02:27, `/root/v14smoke/v5a_p3b5000_full_anchor`). 2 tier 점 ≈ 5 분 → TDC 75점 ≈ 6.2 h, PID 75점 ≈ 6.2 h, ATDC 9점 ≈ 0.8 h, 합 ≈ 13 h(GPU1, 채점 체인과 잠금 공유). 같은 측정으로 채점 체인 arm 1행(CORE 4설정) ≈ 36 분, 준비 행 4개 ≈ 2.4 h, 셀당 산출 147 MB(npz + mat).
- 구현 경로: 초안을 버리고 명세 `SPEC_GAIN.md`(세션 작성, 위 결함 반영, `selection.json` 스키마 고정)로 codex develop 재작성(ground 1) → 세션 리뷰 → 평가 워크트리 커밋. Hydra 게인 override 가 `eval.py static` 까지 닿는지는 검증 스모크 V6(기본 vs kp=24 배열 차이, m_hat 리스트 문법, ATDC `m_hat_leak`)으로 확인한다.
- 채점 체인 연결: v3 는 `gain_search/<controller>/selection.json` 이 생기면 `classical_tdc|pid|atdc` 행을 `--checkpoint none` + 선정 게인 override 로 CORE 4설정 채점한다(파일이 없으면 무동작, 깨진 파일은 ERROR 후 그 행만 건너뜀).
- 발사: 도구 검증 뒤 `omx queue-launch`(pending approval) — 사람 발사.

### 백로그 대조 (00:2x 절 이후 변동)
- HARD 게이트 4건(264·352·441·444) 그대로 — C1·C2 도 같은 ack 대상이다.
- 이 절에 실린 열린 리드: finding/378(joint1 제약 발화 불가 → A3 는 적분기·언랩으로 잼, C1 가중치 표 주석), finding/395(평균 = 꼬리 → A1 표 median·P90), finding/391·396(앵커) → 채점 규약 그대로, finding/382(cuDNN preamble → 학생 행), finding/393(반박 댓글). 나머지 needs-experiment 리드 37건은 이 절과 무관(00:2x 절 처리 유지).

### 남은 일 (이 절 기준)
codex 교차검토(학습·채점 체인, 02:48 자동) 판정 · 계측 패치 구현·리뷰·스모크 · 채점 체인 v3(평가 워크트리·플래그·학생 행) 모의·재큐 · v14 회신 표 갱신 · 발사 뒤 ref 카나리아 대조.


## Update 2026-09-12 (03시 KST) — 체인 교차검토 반영·계측 패치 검증·게인 탐색 도구 (발사 0)

### codex 교차검토 판정과 반영 — finding/450
- codex(ground 4, 02:48~02:57) 18건 중 15건 수용, 3건 증거로 기각(빈 통계 nan 경고: 정상 로그 38,275 it 0회 / 런 이름 공백: 도달 불가 / 학습 FATAL 뒤 채점 대기: GPU 미사용).
- **학습 체인 a9db0c55 → d456ec66, 배포·큐 재등록 완료.** 완료 판정은 체인이 쓰는 `<run>/.chain_ok`(rc 0 + 종료 뒤 로그 전체 재스캔 + `torch.load` 성공), SKIP·채점은 그것만 본다. 치명 패턴은 ANSI 제거·CR 분리 뒤 `±nan|inf` 줄끝 — 옛 정규식은 ANSI 로 감싼 `inf` 를 통과시키는 것을 모의로 재현했다. source 검사를 arm 루프 전에 1회, `CHAIN START/COMPLETE id=`. 모의 `/root/chaintest2` 전 경로 통과. 큐 10건은 launch_delta 에 d456ec66 을 싣고 재등록(옛 항목 `/root/patches/queue-0912b/`). **발사 명령은 그대로**: `EXPECT_HEAD=3791441 nohup bash .hq/community/programs/paper-ablation-5000/launch_chain_r3a.sh &`.
- **채점 체인 v4 dbbd1832**(0bb2a54a 대체 예정): 코드 = 평가 워크트리 14b5ee8 고정(`EXPECT_EVAL_HEAD` 필수) + marinelab 8cc84a5, 두 트리 clean 과 시험 박스(p3b 이벤트 파일 md5)를 시작·잠금 안에서 매 셀 확인, 체크포인트는 `.chain_ok` 런만, 셀 완료는 입력 identity 가 같은 `.complete`(rc 0 + summary·tier 별 extras·meta·healthy 모멘트 키 검증 뒤), 출력 루트 `exam_v3`, 준비 행(p3b 5000·7500, R3a GRU·R3b TCN 학생)과 선정 파일이 있는 classical 행까지 완료 조건, 학습 종료 뒤 미완 셀이 있으면 목록과 함께 종료코드 1, TERM trap 이 실행 중 평가까지 끊는다(셀을 백그라운드 + `wait`), 평가 5400 s 상한. 모의 `/root/examv4mock` A~G 통과.

### 계측 패치 — 평가 워크트리 커밋 14b5ee8 (branch eval/r3a-5000-v14, 로컬)
- 명세(세션) → codex develop(02:49~03:02) → 세션 리뷰(결함 0) → 커밋 → 컨테이너 torch 테스트 7/7, readout selftest 통과.
- GPU1 동일성 검증(`/root/v14smoke/validate.sh`, 앵커 스모크 셀은 두 번 돌려 192/192 바이트 동일 = 판별력 확인):

| 검증 | 결과 |
|:--|:--|
| V1a 평가 워크트리·플래그 없음 vs 앵커 | data 배열 192/192 동일, extras 파일 0 |
| V1b `--save-extras --save-moments` vs 앵커 | 192/192 동일 — 기록이 궤적을 바꾸지 않는다 |
| V2a noipo 자기 task(비용 계산 없음) | 192/192 동일, `costs_source=reference_swap` |
| V2b A6 PPO-Enc 자기 task(OnPolicyRunner) | 192/192 동일, `reference_swap` |
| V3b R3a GRU 학생(학생 모드·cuDNN) | 앵커 무플래그 학생 실행과 192/192 동일 |
| V4 `--levels none,soft` | none·soft 배열이 전체 실행과 동일 |
| V5 p3b model_5000, **64 env 전체 길이**, 두 플래그 vs 앵커 무플래그 | **192/192 동일**, 607 s(앵커 536 s, +13 %), 248 MB(extras 4 tier 105 MB) — 채점 셀 ≈ 10 min, 행 ≈ 40 min |

- 판독 교차검산: 세션이 따로 쓴 무차별 검산기(`/root/v14/ref_readout_check.py`)와 readout 이 v1b hard 에서 제약별 c/D·할인 cost-to-go·joint1 최대 이동을 같은 값으로 냈다. 모멘트 크기도 사전 추정과 맞다 — roll 추진기 RMS 0.03 N·m 대 부이 3.1 N·m(roll 추진기 지레 0.007 m), pitch 0.35 대 4.3. **스모크 체크포인트(4~5 it)라 수치 자체는 결과가 아니다.**

### 게인 탐색 드라이버 — override 타입 결함을 큐 전에 잡음, 커밋 afa3c6b — finding/451
- agy(ground 1, 03:22~03:25)가 SPEC_GAIN 으로 쓴 `tools/classical_gain_search.py` 는 격자 kp·kd 를 int 로 override 에 넣었다. GPU1 스모크 V6b: `env.tdc_controller.kp=24` → Hydra `Expected float, Received int`, rc 1·5 s — 그대로 발사했으면 TDC·PID 150점 전부 실패. `build_cmd` 에 `float()` 캐스트 + 테스트(음성 대조: 수정 전 드라이버에 rc 1), 평가 워크트리 **afa3c6b**(14b5ee8 위, `tools/`·`tests/` 두 파일, `eval.py` 불변). 컨테이너 python 3.12.3 에서 테스트 통과.
- V7(`/root/v14smoke/validate_v7.sh`, 7셀): float override 가 TDC(kp)·PID(kp, m_hat)·ATDC(leak, adapt_gain) 모두에 도달, TDC 기본값 명시(kp 48.0·kd 14.0·m_hat [0.15, 0.16])는 기본 셀과 48/48 동일 — 드라이버의 기본점 판정(48/14/1.0, ATDC 0.5/0.02)이 task 기본과 맞다.
- PID 토크는 `m_hat·(kp·e + kd·ė)`(`tdc.py` `_compute_pd_torque`)이고 PID env 가 매 스텝 TDE 를 끈다(`pid_env.py:49`) → PID 의 m_hat 배율은 두 게인에 곱해진다. 사전 등록 규칙은 그대로 두고 **PID 행은 유효 게인 m·kp, m·kd 로 보고**한다.

### 배포·큐 (03:4x~03:5x KST, 발사 0)
- 채점 체인 `exam_chain_r3a.sh` 0bb2a54a → **dbbd1832** 배포(옛 판 `/root/patches/exam_chain_r3a.sh.0bb2a54a`). `r3a5000_exam_gpu1` 옛 항목은 `/root/patches/queue-0912c/`(검증 사본 + `_held_from_runs`)로 옮기고 평가 커밋 afa3c6b 로 재등록.
- 게인 탐색 큐 3건 `r3a5000_gain_{tdc,pid,atdc}`(드라이버 @ afa3c6b). 큐 합계 14건(학습 10·채점 1·게인 3) 전부 pending approval. 디스크 여유 765 GB(셀당 248 MB × 약 68셀 ≈ 17 GB).

### 발사 명령 (전부 사람, 승인 뒤 — 세 줄 모두 `/workspace/constrained-albc` 에서)
1. 학습(GPU0): `EXPECT_HEAD=3791441 nohup bash .hq/community/programs/paper-ablation-5000/launch_chain_r3a.sh &`
2. 채점(GPU1): `EXPECT_EVAL_HEAD=afa3c6b nohup bash .hq/community/programs/paper-ablation-5000/exam_chain_r3a.sh > .hq/work/paper_ablation_r3a/exam_chain_v3.out 2>&1 &` — 준비 행 4개(p3b 5000·7500, R3a GRU, R3b TCN) ≈ 2.7 h, 이후 arm 이 `.chain_ok` 를 쓸 때마다 한 행.
3. 게인 탐색(GPU1, 같은 잠금): `nohup /workspace/isaaclab/_isaac_sim/python.sh /workspace/constrained-albc-eval/tools/classical_gain_search.py --controller tdc --run > .hq/work/paper_ablation_r3a/gain_search_tdc.out 2>&1 &` → 끝나면 같은 드라이버 `--controller tdc --select`. pid 는 같은 형식, atdc 는 `tdc/selection.json` 이 생긴 뒤. 점당 ≈ 4.5 min(V5 에서 2 tier·무플래그로 환산한 추정) → tdc·pid 각 ≈ 5.6 h, atdc ≈ 0.7 h. 채점 체인과 동시에 띄우면 GPU1 잠금으로 셀 단위로 번갈아 돈다. 채점 체인은 selection.json 이 생기면 다음 pass 에서 classical 행을 채점한다.  <!-- STALE 2026-09-12 23:40: 실측 셀당 20 min. 정정은 '## Update 2026-09-12 (23시 40분 KST)' 절 -->

### 백로그 확인 (03:5x)
- needs-apply-before-retrain 4건(finding/264·352·441·444) — 큐 14건 모두 ack.
- needs-experiment 42건(최신 finding/445) — 이 절의 작업은 어느 lead 도 닫거나 열지 않는다(447~451 은 status 없음).

## Update 2026-09-12 (04시 KST) — grasp-step 시험 도구·proposal (발사 0)

사용자가 03:5x 보고 뒤 "이어서 진행해줘" — 남은 승인 항목인 파지 계단(grasp-step) 파일럿을 착수했다. 초안은 vault `.omc/proposals/grasp-step-exam-draft.md`(09-11 23:4x 주말 필수로 승인, 요청 원문 `.hq/work/scholar/albc/handoff-marinelab-2026-09-11.md` §1). 학습 큐 14건은 그대로다.

### 무엇을 하나
- 평가만. 30 s 동안 명령 (0, 0) 유지, t = 15 s 에 payload 토글, 두 방향(빈 손→파지 = pick, 파지→놓음 = drop), payload 값은 그 레벨의 DR 분포에서(점값 대입 없음), `--env-dr-anchor`, seed 42, 64 env.
- **파일럿**: 선택 교사 `teacher_iter_budget/trpo_iterbudget_s30_260805_012813/model_9998` — 자기 task `Isaac-ConstrainedALBC-TRPO-v0`, 자기 DORAEMON 박스, 고장 플래그 없음(Table V 채점 조건). 논문 표에 넣지 않는다.
- **정본(앵커 B)**: 지금 준비된 4행 — p3b model_5000·7500, R3a GRU·R3b TCN 학생 — SimToReal task, p3b 최종 DORAEMON, healthy. 10 arm·고전 제어기 행은 학습·게인 선정 뒤 같은 셀을 체인 행 한 줄로 추가한다.
- 코드: 평가 워크트리와 분리한 `/workspace/constrained-albc-grasp`(branch `eval/grasp-step`, afa3c6b 위 커밋 `1a5981d`) — 평가 워크트리 HEAD 를 옮기면 큐의 채점 체인(`EXPECT_EVAL_HEAD=afa3c6b`)이 FATAL 이 되기 때문.

### 초안에서 바뀐 것 — **tier 는 사용자 판단 필요**
| 초안 | 확인한 사실 | 바꾼 것 |
|:--|:--|:--|
| tier none·hard | eval `none` 레벨의 payload 는 공칭 0 kg(`analysis/dr_config.py` `_TRUE_NOMINAL_PHYSICS`). pick 은 env 의 stash 보정이 `uniform_(0.1, 0.0)` 으로 RuntimeError(스모크 G3 실측), drop 은 0 → 0 이라 계단이 없다 | **soft·medium·hard 로 교체(권고)**. none 에 해당하는 "payload 만 DR" 레벨은 새 설계라 넣지 않았다 |
| 토글 = cfg `payload_toggle_steps` | static 은 env 를 none DR 로 생성한다(`eval.py` `apply_dr_config(env_cfg, DR_SCALE["none"])`). Hydra `env.payload_*` override 로 켜면 생성 리셋에서 pick 이 soft·hard 에서도 크래시(G1·G4·G5) | 새 플래그 `--payload-toggle-step`·`--payload-start-with` 를 **레벨 DR 적용 뒤** `raw_env.cfg` 에 주입. payload 가 없는 레벨은 명시적 FATAL 로 거부 |
| 토글 시각은 설정값 | 판독이 토글 시각을 가정하면 틀린 셀이 조용히 통과한다 | extras 에 스텝별 `payload_mass`·`payload_cog_offset` 궤적 — 판독기가 궤적에서 토글 스텝을 찾고, 생존 구간 안에서 한 번이 아니면 계측 실패(rc 2) |
| hold 에피소드 슬랙(codex 초안 +0.02 s) | 마지막 스텝이 time-out 이 되어 모든 env 가 terminated 로 읽혔다(G2) | 궤적 경로와 같은 +10 s |
| 리셋 뒤 모든 env 가 토글한다 | 리셋이 지터한 `episode_length_buf`(에피소드의 최대 절반)로 "토글 시점 지남" 을 표시한다(`albc_env.py:1756`). 40 s 에피소드에서 지터 750~999 인 env 는 토글하지 않았다(스모크 3 F1 hard 1/4, 판독기 `no_toggle` 로 검출) | eval 이 buf 를 0 으로 되돌린 직후 토글 표시·카운터를 다시 무장 |

### 사전등록 판독 (`tools/grasp_step_readout.py`, 실행 전 고정)
- 토글 스텝 k = 생존 구간 안에서 `payload_mass` 가 바뀐 유일한 스텝.
- **피크 편차** = 토글 후 10 s 창의 max|θ| − 토글 전 5 s 의 mean|θ| (roll·pitch 따로).
- **정착 시간** = 편차 |θ − 토글 전 평균| 가 band = max(0.5°, 0.10 × 피크 편차) 안에 3 s 머무는 첫 시각 − 토글 시각. **탐색은 편차 최대 시점부터** — 토글 직후부터 찾으면 느린 과도가 0 s 로 읽힌다(테스트 6). band 를 넘은 적이 없으면 0 s, 끝까지 못 들어오면 미정착(개수 보고).
- **전·후 정상상태** = 토글 전 5 s mean|θ|, 마지막 5 s mean|θ|(완주 env 만). **survival** = 30 s 완주 비율.
- 통계 mean·median·P90·max·n, 방향 × 축 × tier. 계단 크기(질량 전·후, CoG 오프셋 크기)도 같은 표.
- 열은 vault `handoff/199`(실기 요구 명세)와 같다: 피크 편차 / 정착 / 전·후 정상상태 / survival / n.
- 나쁘게 나와도 결과다. 토글을 학습에 넣는 재학습은 별도 proposal.

### 검증
- GPU1 스모크 4회(4 env, K1 만 64 env). 게이트는 스모크 4 이고, 그 트리를 그대로 `1a5981d` 로 커밋했다.

| 셀 | 조건 | 결과 |
|:--|:--|:--|
| K0 | 새 플래그 없이 기존 경로 | data 192/192 키, extras 공통 44/44 키가 패치 전(V1b)과 비트 동일. 새 extras 키는 `payload_mass`·`payload_cog_offset` 둘 |
| K1 | 파일럿 pick, hard, 64 env | 64/64 env 가 생존 구간에서 정확히 한 번 토글, `instrument_ok`, survival 1.0. 재무장 전 스모크 3 은 4 env 중 1 이 토글하지 않았다 |
| K2 | 파일럿 drop, soft·hard | eval rc 0, 판독 rc 0, 전 env ok |
| K3 | none 레벨 pick | `RuntimeError` rc 1, npz 0. `SystemExit` 였을 때는 rc 0 이었다(H3) |
| K4 | p3b model_7500 pick, medium | rc 0, 판독 ok |
| K5 | R3a GRU 학생 pick, soft | rc 0, 판독 ok |
| K6 | R3b TCN 학생 drop, hard | rc 0, 판독 ok |

- 판독기 테스트 8종 통과. 변이 둘(정착 탐색을 토글 시점부터 / 생존 창 제한 제거)이 각각 테스트를 실패시킨다.
- 체인 실검증 `NENV=4 ONLY=pilot_inc9998 OUT=/root/v14grasp/chain_smoke EXPECT_GRASP_HEAD=1a5981d`: pick·drop 2셀 × soft·medium·hard 전부 판독 ok, `.complete` 에 입력 identity 기록, `grasp_summary.md` 생성, 셀당 93 s, 네 워크트리 clean. 4 env 수치는 결과가 아니다.
- hold 모드의 `summary.json` 스텝 궤적 총계(`total_att_error` 등)는 구조상 nan 이다. hold 구간 이름이 attitude·lin_vel·yaw 블록으로 분류되지 않아 집계할 스텝이 없다(`_eval_dr/metrics.py` `_classify_segment`). 이 시험의 계측기는 판독기다.
- 교차검토 agy(ground 4, eval diff + 체인 초안), 4건: **수용 1** — `SystemExit` 가 Kit 안에서 rc 0 으로 끝나 일부 레벨이 빠진 셀이 완료로 찍힐 수 있다 → `RuntimeError`, 체인 판독에 `--levels soft,medium,hard` (빠진 레벨 = rc 1). **기각 3** — (i) hold 가 targets 를 1차원으로 만들어 형상 오류: 채널은 원래 1차원 시계열이고(`_eval_dr/trajectory.py:111`) eval 은 스텝마다 스칼라를 명령 열에 쓴다(`eval.py:875-994`); (ii) 잠금 `9>"$LOCK"` 가 내용을 지운다: 잠금 파일은 내용을 담지 않고 flock 에만 쓴다; (iii) 합본이 만들어지지 않는 `.md` 를 찾는다: 판독기가 `grasp_step_readout.md` 를 기본으로 쓰고, 체인 실검증에서 합본이 생성됐다.
- 큐: `r3a5000_grasp_v1` pending approval, 체인 `grasp_chain_r3a.sh` md5 f7f0697d.

### 비용·발사 (사람만)
- 셀 = 행 × 방향 = 10셀, 64 env × 3 tier × 30 s. 셀당 약 2~3 min 추정(4 env 실검증 93 s, 64 env hard 한 레벨 48 s) → 약 30 min. GPU1 잠금을 채점 체인·게인 탐색과 공유.
- `EXPECT_GRASP_HEAD=1a5981d645ea8f3e6eda2b9b646c04eccc034f98 nohup bash .hq/community/programs/paper-ablation-5000/grasp_chain_r3a.sh > .hq/work/paper_ablation_r3a/grasp_chain_v1.out 2>&1 &`
- 산출 `.hq/work/paper_ablation_r3a/grasp_v1/<row>_<pick|drop>/`(data·extras npz, `grasp_step_readout.json`·`.md`), 합본 `grasp_summary.md`. 셀 완료 표식 `.complete` 는 입력 identity(행·task·체크포인트 경로+크기·인코더·DR 박스·고장·grasp/marinelab 커밋·env 수)와 판독 rc 0 뒤에만 쓴다.

## Update 2026-09-12 (15시 KST) — 발사 (운영자 결정 B+C, 두 머신 분할 + 범위 축소)

밤새 발사가 0이었다. 도구·검증·기록을 끝내고 큐(17건)만 채운 채 사람 게이트에서 멈췄고, 그 사이 8시간 30분 동안 GPU0·GPU1·DGX 가 모두 놀았다. 원인은 취침 전에 발사 명령을 제시하지 않은 것. 집행층을 만들었다 — 워크스페이스 `.claude/scripts/sleep-launch-guard.py`(UserPromptSubmit 훅): 운영자가 취침을 알리면 대기 큐와 발사 명령을 그 턴에 화면으로 올리도록 강제한다.

또 하나 기록해 둘 사실: **10 arm 48 h 체인은 애초에 주말에 안 들어갔다.** 토요일 06시에 띄웠어도 종료는 월요일 아침이다. 그래서 운영자가 B(분할)+C(축소)를 택했다.

| 자원 | 내용 | 예상 |
|:--|:--|:--|
| GPU0 | `launch_chain_r3a_split.sh` md5 85c8a9b8 (원본 d456ec66 불변): ref_full → a6_ppoenc → noenc → ppo → noipo → noboth | 약 24 h, 일요일 15시경 |
| DGX GB10 | `~/xyz_launch/launch_paper_dgx.sh` md5 88ffc833: DGX 기준선 → n1_lagrangian → n4_residual → depth-xy arm. 코드는 DGX anchor 워크트리 `~/workspace/constrained-albc-r3a` @3791441(depth-xy arm 만 `constrained-albc-xyz` @51f6a05) | 약 30 h, 일요일 21시경 |
| GPU1 | 채점 체인(EXPECT_EVAL_HEAD=afa3c6b) + grasp 체인(1a5981d) + 게인 탐색 tdc. `/root/gpu1.lock` 직렬화, pid·atdc 는 tdc 뒤 | 약 16 h + 채점 |  <!-- STALE 2026-09-12 23:40: 실측 셀당 20 min. 정정은 '## Update 2026-09-12 (23시 40분 KST)' 절 -->

발사 시각: DGX 14:48:50(기준선 it 114/5000 확인), GPU0·GPU1 14:5x. **n6a_nodoraemon·n6b_nodr 은 주말 범위에서 제외(월요일)** — 큐 항목은 그대로 둔다.

**표 읽는 규칙(신규, 이 분할의 대가):** arm 은 **같은 머신의 기준선 대비 델타**로만 비교한다. DGX 절대값을 워크스테이션 arm 과 직접 비교하지 않는다(머신 효과 +109 %, `finding/001:23`). DGX 기준선 한 런이 논문 표 DGX 블록의 기준선이자 depth-xy arm 의 기준선이다.

발사가 두 번 조용히 실패한 원인도 남긴다: ssh 로 보낸 명령에서 리다이렉트를 상대경로로 주면 `cd` 가 백그라운드 목록 안에 묶여 홈 기준으로 평가된다 — 프로세스가 아예 안 뜨고 로그도 안 생긴다. 발사 명령의 리다이렉트는 절대경로로 쓴다.

## Update 2026-09-12 (15시 KST) — n6a·n6b 영구 제외 (운영자 결정)

운영자 지시 원문: **"n6a랑 n6b는 빼고 그냥 가자"** (2026-09-12 15:1x KST).

09-12 14시 분할 때 n6a·n6b 는 "월요일로 연기"였다. 이 결정으로 **연기가 아니라 제외**가 된다.

### 무엇이 바뀌나

| | 전 | 후 |
|:--|:--|:--|
| 큐 등록 arm | 10 | 8 |
| GPU0 체인 | ref_full · a6_ppoenc · noenc · ppo · noipo · noboth (6) | 변화 없음 |
| DGX 체인 | ref · n1_lagrangian · n4_residual · depthxy (4) | 변화 없음 |
| 빠진 것 | — | n6a_nodoraemon (DORAEMON 커리큘럼 제거), n6b_nodr (DR 제거, nominal-point 플랜트) |

실행 중인 체인은 손대지 않았다 — 두 arm 은 `launch_chain_r3a_split.sh:113-114` 에서 이미 주석이었고,
채점 체인은 완주 기록(`.chain_ok`)이 없는 arm 을 `exam_chain_r3a.sh:192` 에서 "(no complete run)" 으로 건너뛴다.
따라서 이 결정은 **도는 것을 멈추지 않는다**.

### 적용한 처리

- `\.hq/work/experiments/runs/r3a5000_n6a_nodoraemon_s30/pending-launch.json` → `withdrawn-launch.json`
  (`status: withdrawn`, `withdrawn_reason` 에 지시 원문 기록). n6b 동일.
- `queue_r3a.sh:28-29` 의 `q` 두 줄 주석화 — 스크립트를 다시 돌려도 재등록되지 않는다.
- 검증: `omx loop-status --all` 의 `pending approval` **0건**.
- 롤백: `withdrawn-launch.json` 을 되돌리고 주석을 풀면 복구된다. 태스크 등록(`...-NoDoraemon-v0`,
  `...-NoDR-v0`)과 변형(`n6-nodoraemon`, `n6-nodr`)은 코드에 그대로 남아 있다.

### 대가 (원고에 반영해야 함)

RA-L 표에 **DORAEMON 커리큘럼 ablation 도, DR ablation 도 없다.** 지금 원고의 커리큘럼·DR 관련 주장은
ablation 증거 없이 서게 된다. 논문 작법 25편 딥리드에서 이미 "DR ablation 부재"를 공백으로 적어 둔 항목과
같은 자리다. 선택지는 둘뿐이다 — 해당 주장을 측정 가능한 범위로 좁히거나, 개정판 실험으로 미루고 한계로 명시하거나.
원고 쪽 결정은 이 계획서의 범위 밖이며 운영자 판단이다.

### 일정 효과

n6a·n6b 는 각 7 h 예정이었다. 빼지 않았으면 GPU0 체인이 월요일로 넘어갔다.
현 실측 3.57 s/iter 기준 GPU0 6 arm = 일요일 19시경, DGX 4 arm = 일요일 21시경.

## Update 2026-09-12 (23시 KST) — DGX 체인 재편성 (depth-xy 우선)

운영자 지적으로 DGX arm 순서를 `ref → depthxy → n1_lagrangian → n4_residual` 로 되돌렸다 (finding/456).
비교군 두 arm(n1·n4)은 depth-xy 뒤로 간다 — n1 일요일 15시경, n4 22시 30분경.

n1 은 22:35 에 시작해 약 350 iteration 에서 중단됐다. 부분 런 `trpo_dgx_n1_lagrangian_260912_223520` 은
`.chain_ok` 가 없어 채점 대상이 아니며, 재실행은 새 디렉터리로 간다. **표를 읽을 때 이 빈 디렉터리를 arm 으로 세지 말 것.**

GPU0 쪽은 변화 없다 — noenc 진행 중, ppo·noipo·noboth 이어서 일요일 10시경 종료.

## Update 2026-09-12 (23시 40분 KST) — 게인 탐색 셀당 시간 실측, 계획 추정치 4.4배 정정

`### 발사 순서` 의 "점당 ≈ 4.5 min → tdc·pid 각 ≈ 5.6 h" 와 `GPU1 ... 약 16 h` 는 **폐기한다**. 그 추정은 V5 스모크를 2 tier·무플래그로 환산한 것이고, 실제 런은 채점 체인·grasp 체인과 `/root/gpu1.lock` 을 나눠 쓰므로 대기 시간이 셀당 시간에 들어간다.

**실측 (2026-09-12 23:35, `summary.json` mtime 기준)**

| 컨트롤러 | 완료 | 그리드 | 첫 셀 | 마지막 셀 | 셀당 |
|:--|--:|--:|:--|:--|--:|
| tdc | 25 | 75 | 15:12:03 | 23:12:45 | **20.03 min** |
| pid | 25 | 75 | 15:29:19 | 23:18:17 | **19.54 min** |

셀당 = (마지막 − 첫) / (n − 1). 그리드 75 = `KP_VALS` 5 × `KD_VALS` 5 × `M_SCALES` 3 (`classical_gain_search.py:13-15`).

**남은 일정**

- tdc 50셀 × 20.0 min = 16.7 h → **일요일 16시 10분경**, 그 뒤 `--select` 가 `selection.json` 을 쓴다.
- pid 50셀 × 19.5 min = 16.3 h → **일요일 15시 40분경**, 그 뒤 `--select`.
- atdc 는 `get_grid` 가 `tdc/selection.json` 을 요구하고(`classical_gain_search.py:62`, 없으면 FATAL) 격자가 `LEAK_VALS` 3 × `AG_VALS` 3 = **9셀**(`:75`) → 3 h → **일요일 19시 10분경**.

주말 마감 안에 들어온다. 채점 체인의 `classical_tdc|pid|atdc` 행은 각 `selection.json` 이 생긴 뒤 다음 pass 에서 채점되므로, 표의 고전 제어기 3행은 일요일 저녁에 채워진다.

**왜 틀렸나.** 진행률을 셀 디렉터리 수로만 세고 분모를 `grid.json` 에서 안 읽어, 23시 보고에서 "각각 24/25 셀"(=96%)이라고 알렸다. 실제는 33% 였고 `--select` 를 곧 돌릴 단계라는 후속 판단도 같이 틀렸다. 분모를 산출물에서 읽는 규칙이 진행률에도 적용된다.

## Update 2026-09-13 (05시 50분 KST) — 야간 실측으로 일정 재산정, 주말 마감 여유 1.5 h

`## Update 2026-09-12 (23시 40분 KST)` 절의 게인 종료 예상(tdc 16:10 · pid 15:40 · atdc 19:10)은 **폐기한다**. 그 셀당 20 min 은 낮에 GPU0 학습 arm·채점·grasp 가 `/root/gpu1.lock` 을 나눠 쓰던 구간의 값이었다. 야간 실측은 셀당 5~6 min 이다.

**실측 (2026-09-13 05:48 기준)**

| 자원 | 상태 | 근거 | 종료 예상 |
|:--|:--|:--|:--|
| GPU0 | 완주 4/6 (ref_full · a6_ppoenc · noenc · ppo), noipo 진행 | noipo model_0→model_250 828 s = **3.31 s/iter** | noipo 09:40, noboth 14:15~14:40 (noboth 는 3.3~3.6 s/iter 가정) |
| GPU1 게인 | 105/150 (tdc·pid 합산) | 30 min 당 3~6셀 | tdc·pid 09:30경 → atdc 9셀 → **12:30경** |
| GPU1 채점 | 29셀, arm당 4셀 | 다음 arm 학습 완료를 while+sleep 600 으로 대기 | GPU0 따라감 |
| DGX | depth-xy model_3150 @04:06 | 5.74 s/iter | depth-xy 07:00 → n1 15:00 → **n4 22:30** |

arm 소요 실측: noenc 3 h 36 m (22:46:28→02:22:33), ppo 2 h 40 m (02:22:43→05:02:47). 둘 다 `END rc=0 ok=1`, `model_4999.pt` 와 `.chain_ok` 가 `constrained-albc-r3a` 워크트리에 있다.

**주말 마감.** 오늘 2026-09-13 은 일요일이다. 병목은 DGX 의 마지막 arm n4_residual 로 22:30경 종료 예상, 마감까지 **여유 약 1.5 h**. DGX 체인이 한 번이라도 재시작되면 월요일로 넘어간다. GPU0·GPU1 은 오후에 끝나 여유가 크다.

**경로 주의.** 체인 로그의 `run=logs/rsl_rl/...` 은 상대경로다. 학습 런은 `/workspace/constrained-albc-r3a/` 기준이고 `/workspace/constrained-albc/` 에서 찾으면 없는 것으로 보인다(09-12 와 09-13 에 두 번 재발).

## Update 2026-09-13 (11시 30분 KST) — noipo 완주, 게인 격자 완료·선정 미실행, 세션 교대

`## Update 2026-09-13 (05시 50분 KST)` 표의 GPU1 게인 행("tdc·pid 09:30경 → atdc 9셀 → 12:30경")은 **폐기한다**. 격자는 끝났지만 `--select` 가 돌지 않아 atdc 가 시작되지 않았다.

| 자원 | 11:23 실측 | 다음 |
|:--|:--|:--|
| GPU0 | noipo `END rc=0 ok=1` 09:41:04. noboth `GATE ok` 09:41:14 (`trpo-noipo_r3a_noboth_260913_094109`), model_2500 @11:22:39, **2.43 s/iter** (05:50 절의 3.3~3.6 가정보다 빠름) | 13:05경 END → 체인 종료, 완주 6/6 |
| GPU1 게인 | tdc 75/75, pid 75/75 (`summary.json` 수 = `grid.json` 격자 길이, 마지막 셀 10:49). `selection.json` 0개, 게인 프로세스 없음 | `--select` tdc·pid → atdc `--run` 9셀 → `--select`. depth-xy 시험을 GPU1 에 먼저 둔다(운영자 우선순위, depth-xy PLAN 같은 시각 절) |
| GPU1 채점 | 36셀, noipo 4셀 11:05 완료, noboth 체크포인트 대기 | noboth END 뒤 4셀, `selection.json` 생긴 뒤 `classical_*` 행 |
| DGX | n1 model_2850 @11:23, 5.58 s/iter | n1 14:42경 → n4 22:30경 (마감 여유 약 1.5 h) |

GPU0 보류 시도: 운영자 지시("xy를 먼저 테스트할 수 있게 하라고 …")에 따라 noboth 시작 순간 체인 래퍼와 학습 그룹을 멈추는 대기 스크립트를 준비했다. auto mode 분류기가 `[Interfere With Workloads]` 로 거부해 실행하지 않았고, noboth 는 원래 순서대로 돌고 있다. 인계는 `.hq/community/sessions/2026-09-13-resume-brief.md`.

## Update 2026-09-13 (12시 KST) — GPU1 을 depth-xy 시험이 먼저 쓴다

- 운영자 1순위(depth-xy 시험)에 따라 GPU1 락을 depth-xy 작업이 연속 점유한다: 깊이·xy 그리드 11:50~12:15경 (`/workspace/xyz-exam/outputs/depthxy_exam/`), 이어서 DGX 두 런의 자세 시험 16셀 약 14:55 까지 (`/workspace/xyz-static/outputs/dgx_static_exam/`, 이 PLAN 의 CORE·플래그 그대로).
- 지연: noboth 채점 4셀(13:05 이후 준비)과 게인 `--select` → classical 행 채점 → atdc 9셀은 약 15시 이후. `exam_chain_r3a.sh` 는 무수정이고 락 대기로만 밀린다.
- 게인 `--select` 는 `summary.json` 만 읽는다 (`classical_gain_search.py:239` 이하, eval 발사 없음). 실행은 자세 시험 배치가 락을 잡은 뒤로 둔다 — 그 전에 `selection.json` 이 생기면 채점 체인의 classical 셀이 락 경합에 끼어든다.

## Update 2026-09-13 (12시 15분 KST) — depth-xy 포기로 GPU1 지연 해소, 게인 선택·atdc 발사, 비교군 yaw 확인

- 운영자 "그러면 그냥 detph xy는 포기하자. 그 외의 것들이나 진행해줘." → 12시 절의 GPU1 지연(noboth 채점·게인 약 15시 이후)은 **무효**. DGX 자세 시험 배치는 락 대기 중 취소(12:11:30, 한 셀도 안 돌았음). 깊이·xy 그리드 마지막 셀만 12:14경까지 GPU1 을 쓴다.
- 게인 `--select` 12:12 (tdc·pid 둘 다 rc 0, 각 75/75 셀): tdc `kp68_kd7_m1` (kp 68, kd 7, m_hat [0.15, 0.16], 자기 점수 1.263° — 13시 10분 절에서 정정, 1.216° 는 동률군 최저점 kp96_kd7_m0.67 의 값), pid `kp48_kd14_m1.5` (kp 48, kd 14, m_hat [0.225, 0.24], 자기 점수 8.608° — 같은 정정, 8.527° 는 kp48_kd7_m1.5 의 값; 사전 등록대로 유효 게인 m·kp 72, m·kd 21 로 보고). 채점 체인은 다음 pass(최대 10분 뒤)에 classical_tdc·classical_pid 각 4셀을 GPU1 락에 올린다.
- atdc `--run` 12:13 발사 (`/workspace/constrained-albc` 에서 `setsid nohup /workspace/isaaclab/_isaac_sim/python.sh /workspace/constrained-albc-eval/tools/classical_gain_search.py --controller atdc --run > .hq/work/paper_ablation_r3a/gain_search_atdc.out 2>&1 < /dev/null &`), 9셀, 첫 셀 `kp68_kd7_m1__leak0.1_ag0.01` 락 대기, 프로세스 생존 확인. 끝나면 `--controller atdc --select` → 체인이 classical_atdc 4셀 채점.
- GPU1 대기열 (락 셀 단위로 번갈아): classical_tdc 4 · classical_pid 4 · atdc 게인 9 · noboth 4 (13:05 이후) · classical_atdc 4.
- 운영자 질문 "비교군 모델들도 yaw 제어는 하는거 맞지? 학습 모델들 말이야" 에 대한 확인 (각 런 `params/env.yaml`): ref_full·a6_ppoenc·noenc·ppo·noipo·noboth (워크스테이션 `constrained-albc-r3a/logs`) 와 n1_lagrangian (DGX `~/workspace/constrained-albc-r3a/logs`) 은 전부 `yaw_rate_cmd_range` ±0.5 rad/s, `reward.yaw_vel.k` 3.5, `att_cmd_rp_range` ±0.5236 rad, `vel_cmd_zero_prob` 0.1 — **yaw rate 추종을 학습한다.** **예외 n4_residual**: RL 행동은 0:2 roll·pitch 팔 잔차 토크뿐이고 2:8 은 무시(`envs/tdc_main/residual_tdc_env.py:17-20,73`), 스러스터는 고전 ThrusterPD 가 몰며 yaw 는 `Tz = kp_yaw(30) × yaw rate 오차` P 제어(`envs/tdc/controllers/thruster_pd.py:56,140,147`) — n4 에서 yaw 는 학습 대상이 아니다. n4 는 아직 미시작이라 근거는 r3a 트리 코드다.

## Update 2026-09-13 (12시 30분 KST) — classical 채점 셀이 정수 게인으로 죽는다, 체인 수정본을 종료 후 설치

- 12:20:04 `classical_tdc/healthy rc=1 complete=NO` (시작 5초 뒤). 원인: `exam_chain_r3a.sh` 의 `selection_overrides` 가 `{kp:g}` 로 `env.tdc_controller.kp=68` 을 써서, Isaac Lab Hydra 가 `Incorrect type under namespace: /tdc_controller/kp. Expected: <class 'float'>, Received: <class 'int'>` 로 거부했다. 게인 탐색 도구는 v14 스모크 V6b(finding/451)에서 같은 결함을 `float()` 로 고쳤지만, 체인에 있는 사본은 고쳐지지 않았다. 체인 스모크는 selection.json 이 없어 classical 행을 건너뛰었으므로 이 경로는 한 번도 실행된 적이 없다.
- 실행 중인 체인(PID 906408)은 멈추지도 고치지도 않는다. 셀 식별자에 override 파일 해시가 들어가므로, 체인 밖에서 고친 값으로 같은 폴더를 채우면 체인이 그 셀을 `.stale_*` 로 치우고 다시 실패시킨다. GPU1 은 락 셀 단위로 직렬이라 지금 멈춰도 전체 종료 시각은 거의 같다.
- 수정본(md5 d29fb4d9; 원본 dbbd1832 은 설치 때 `exam_chain_r3a.sh.bak-v4-260913` 으로 보존; git 미추적 파일): kp·kd·m_hat·m_hat_leak·m_hat_adapt_gain 을 전부 `str(float(x))` 로 쓴다. 게인 도구 `build_cmd` 와 글자까지 같은 형식이다. 검증: 함수만 떼어 컨테이너 `/usr/bin/python3` 로 tdc·pid 실제 selection.json 과 leak=2 인 가짜 atdc selection 에 실행했다. 결과는 tdc `kp=68.0`·`kd=7.0`·`m_hat=[0.15,0.16]`, pid `m_hat=[0.22499999999999998,0.24]`, atdc `m_hat_leak=2.0`·`m_hat_adapt_gain=0.01` 이고 정수 토큰은 0 이었다.
- 설치·재발사 (**운영자 결정 대기**): 아래 절차를 로컬 대기 스크립트(Mac 스크래치 `relaunch_exam_chain.sh`)로 띄우려 했으나 auto mode 분류기가 [Modify Shared Resources] 로 거부했다. 우회하지 않는다. 절차는 PID 906408 종료를 기다리는 것부터다. 마지막 `===` 줄이 `TRAINING CHAIN FINISHED` 일 때만 원본 md5 확인 → 백업 → 설치 → md5 확인 → 원래 명령(`EXPECT_EVAL_HEAD=afa3c6b`, 출력은 `>>` 이어쓰기)으로 재발사한다. 옛 체인은 noboth 학습의 `CHAIN COMPLETE`(13:05경) 뒤 첫 pass 끝에서 종료한다. 그때까지는 10분 pass 마다 classical 셀을 5초 만에 실패시키며 `<cell>.stale_*` 폴더를 남긴다.
- 남는 위험: 재발사한 체인이 classical_atdc 차례에 atdc selection.json 을 못 찾으면 그 행을 건너뛰고 종료한다. 그때는 `--select` 뒤에 한 번 더 띄운다.
- 12:42 운영자 결정 "직접 대기 스크립트 실행" → 운영자가 `! nohup bash <Mac 스크래치>/relaunch_exam_chain.sh > <Mac 스크래치>/relaunch.out 2>&1 &` 실행. Mac PID 45110(부모 1) 생존·`sleep 120` 자식 확인, relaunch.out 0 B(옛 체인 종료 대기 중). 재발사 감지는 relaunch.out 을 따라가는 세션 Monitor 로 한다.

## Update 2026-09-13 (13시 10분 KST) — noboth 학습 완주, atdc 게인 선택, selection.json `score_deg` 오기 정정

- 13:04:19 `END noboth rc=0 ok=1`, `CHAIN COMPLETE id=20260912T145147-905945` — GPU0 분할 체인 6 arm 종료. 채점 체인(옛 v4)은 다음 pass 에서 noboth 4셀을 채점한 뒤 `TRAINING CHAIN FINISHED` 로 끝날 예정이고, 그때 12시 30분 절의 대기 스크립트가 수정본을 설치·재발사한다.
- atdc `--run` 13:06:06 종료(9/9), `--select` 13:06 → `kp68_kd7_m1__leak0.5_ag0.01` (m_hat_leak 0.5, m_hat_adapt_gain 0.01, 자기 점수 1.357°). 사전 등록 규칙(1078행: 최저점, 차 0.10° 안이면 기본값에 로그 거리로 가까운 점)대로다. 최저점 `leak2_ag0.01` 1.2745° 와 0.10° 안에 든 점은 `leak0.5_ag0.01` 하나이고, ATDC 기본값 (leak 0.5, ag 0.02) 까지 로그 거리가 0.69 로 2.08 보다 작다. 9점 전부 soft survival 100 %. 수정본 체인 함수로 이 선택을 변환하면 `m_hat_leak=0.5`·`m_hat_adapt_gain=0.01`, 정수 토큰 0.
- **`selected.score_deg` 는 선택된 점의 점수가 아니다.** 드라이버가 동률군 최저점 점수 `best_score` 를 넣는다(`classical_gain_search.py` 의 `"score_deg": best_score`). 세 선택 모두 해당한다: tdc 기록 1.216°(kp96_kd7_m0.67 의 값) vs 선택 점 1.263°, pid 8.527°(kp48_kd7_m1.5) vs 8.608°, atdc 1.2745°(leak2_ag0.01) vs 1.357°. 선택된 점 자체는 규칙대로 맞다. 12시 15분 절의 tdc·pid 점수는 제자리에서 고쳤다. 탐색 점수를 논문·표로 옮길 때는 `rows` 에서 선택 점 이름으로 읽는다. 드라이버는 고치지 않는다 — 평가 워크트리가 clean 이어야 채점 체인 `code_ok` 가 통과한다.

## Update 2026-09-13 (13시 55분 KST) — noboth 채점 완료, 채점 체인 수정본 설치·재발사

- noboth 채점 4셀 전부 `rc=0 complete=yes`: healthy 13:24:00, pair34 13:33:03, healthy_d1 13:42:14, healthy_d2 13:51:22. 외부 단일 셀 `.hq/work/board_fault_m3m4_260913/run.sh`(R3a GRU 학생, 보드 m3+m4 고장; 이 세션이 띄운 것 아님)가 13:04~13:14 에 GPU1 락을 잡아 첫 셀 시작이 13:14:26 으로 약 5분 밀렸다.
- 옛 체인(v4, PID 906408)은 같은 pass 에서 classical tdc·pid·atdc 12셀을 몇 초씩 실패시킨 뒤 `13:52:21 === TRAINING CHAIN FINISHED` 로 끝났다. 미완 목록에 noboth 는 없고, r3a_n1_lagrangian·r3a_n4_residual(DGX)과 r3a_n6a·n6b(운영자 제외)가 `(no complete run)` 으로 올라 있다.
- 12시 30분 절의 대기 스크립트가 13:53:01 에 절차대로 실행됐다: 원본 md5 확인 → `exam_chain_r3a.sh.bak-v4-260913`(dbbd1832) 백업 → 수정본 설치(d29fb4d9 확인) → 원래 명령으로 재발사. 새 체인 PID 1029684, `=== START eval=afa3c6b ml=8cc84a5 anchor_md5=762091d1`. 첫 셀 `classical_tdc/healthy` 는 13:53:02 에 시작했고, RUN_CONDITIONS 에 `hydra_overrides=env.tdc_controller.kp=68.0 env.tdc_controller.kd=7.0 env.tdc_controller.m_hat=[0.15,0.16]`(ovr md5 5802d0e5)가 적혔다. 셀 로그에 설정 타입 오류는 없다. 옛 실패는 5초 만에 설정 파싱에서 죽었다. 셀은 14:02:52 에 rc=0 complete=yes 로 끝났다(9분 50초). summary.json 의 nan 토큰 180개는 r3a_noboth/healthy 와 개수·키가 같다. 옛 실패 폴더는 `<cell>.stale_*` 로 남아 있다.
- 남은 일정: classical 12셀(셀당 약 9~10분) → 15:50경. 끝나면 체인은 미완 셀(n1·n4 DGX, n6 제외)을 적고 `TRAINING CHAIN FINISHED` 로 스스로 종료한다.

## Update 2026-09-13 (14시 50분 KST) — DGX n1 완주, n4_residual 시작, classical 채점 5/12

- 14:43:03 `END n1_lagrangian rc=0 ok=1`. run `trpo_dgx_n1_lagrangian_260913_065642` 에는 모델 101개(마지막 `model_4999.pt`)와 `.chain_ok` 가 있다. 학습 시간은 7시간 46분(06:56:37 시작)이다. DGX 결과는 DGX 기준선하고만 비교한다(머신 효과 +109 %).
- 14:43:13 `GATE ok n4_residual`(task `Isaac-ConstrainedALBC-Main-ResidualTDC-SimToReal-v0`, head 3791441), run `main_residualtdc_simtoreal_dgx_n4_residual_260913_144308`. 14:47 에 iteration 44/5000, 5.66 s/iter, ETA 7시간 38분이라 22:25경 끝난다. 커리큘럼 건강은 500·1000 iter(15:30경·16:20경)에 TB 스칼라로 확인한다.
- 워크스테이션 채점 체인(수정본 d29fb4d9)에서 classical_tdc 4셀과 classical_pid/healthy 가 전부 `rc=0 complete=yes` 로 끝났다(셀당 약 9분 40초). 남은 pid 3셀과 atdc 4셀은 15:50경 끝난다. atdc 는 이 체인에서 `m_hat_leak`·`m_hat_adapt_gain` override 를 처음 쓰는 행이라 첫 셀 rc 를 따로 확인한다.

## Update 2026-09-13 (15시 45분 KST) — n4_residual 커리큘럼 판독: 정책이 yaw 를 쥐지 못해 DORAEMON 이 열리지 않을 전망, 운영자 결정 "계속 + 1500 iter 확정"

- 판독: DGX n4 `main_residualtdc_simtoreal_dgx_n4_residual_260913_144308`(15:44 에 iteration 651/5000, ETA 22:25경)을 같은 DGX·같은 anchor(albc 3791441, marinelab-xyz 8cc84a5)의 완주 런 n1 `trpo_dgx_n1_lagrangian_260913_065642` 와 같은 iter 창에서 tfevents 로 대조했다. 두 런의 `params/env.yaml` `doraemon` 블록은 같다(performance_lb 200, alpha 0.5, kl_ub 0.12, step_interval 250, hard_performance_constraint true). 판독기는 세션 scratchpad `currpeek_dgx.py` 를 stdin 으로 DGX `python3` 에 넘겨 실행했다.

| 지표 | n4 (≈600 iter) | n1 대조군 |
|:---|:---|:---|
| `DORAEMON/mode` (0·250·500) | −3, −2, −2 | −3, −3, −2 → 750 −2 → 1000 **0** |
| `DORAEMON/success_rate` | 0.088(47) → 0.040(568) | 0(≤415) → 0.084(581) → 0.63(1000) |
| `Train/mean_reward` | −20~−113 진동, 추세 없음(−60.8 @629) | −206(83) → +135(581) → +207(1000) |
| `Reward/yaw_vel` | −5.9 @629 (52~629 내내 −4.7~−7.2) | +0.64 @700 |
| `Reward/att_rp` | +3.9 @629 | +4.6 @700 |
| `Track/yaw/rate_err` (rad/s) | 0.98(0) → 1.11(629), 평탄 | 0.94(0) → 0.18(700) |
| `Constraint/viol/yaw_rate` | 1.08(0) → 44(51) → 52~67 | −1.8~−9.3 (1500 까지 전부 음수) |
| `Constraint/viol/thruster_util` | 24~31 (51 이후) | −14~+11 |
| `Policy/mean_noise_std` | 0.70 → 0.81 (상승) | 0.70 → 0.20 |
| `DORAEMON/mean/fault_severity` | 0.0094 @517 | 0.0099 @498 (0.05 초과는 4000 iter 무렵) |

- 원인(코드, DGX anchor 3791441): n4 정책 행동은 0:2 roll·pitch 팔 잔차 토크뿐이고 2:8 은 무시된다(`envs/tdc_main/residual_tdc_env.py:17-24,73`). 스러스터는 고전 ThrusterPD 가 몬다(`envs/tdc_main/tdc_env.py:164-175`). 1321행(운영자 yaw 질문 확인)에 코드 근거로 적었던 "n4 에서 yaw 는 학습 대상이 아니다"가 학습 스칼라로 확인됐다. 자세 항 att_rp 는 n1 과 비슷한 수준(3.9 대 4.6)까지 올랐고, 격차는 정책이 손댈 수 없는 yaw_vel 항에서 난다. n4 의 `Reward/total` −2.406 @629 는 att_rp·yaw_vel·torque·thruster·smoothness·bias 여섯 항의 합과 일치한다.
- DORAEMON 은 에피소드 return ≥ performance_lb(200) 인 비율이 alpha(0.5) 이상일 때만 분포를 넓힌다. 미달이면 성공률 최대 분포를 유지하고 mode −2 를 찍는다(`marinelab/algorithms/doraemon.py:430-453`, marinelab-xyz 8cc84a5 와 `~/workspace/marinelab` 의 파일 diff 없음). n1 은 @700 에서 `Reward/total` 5.04 로 return 약 175 였다. 같은 비율이면 return 200 에는 total 약 5.8 이 필요하고, yaw_vel −5.9 와 나머지 항 −0.46 이 그대로면 n4 는 att_rp 약 12 가 필요하다(n1 의 약 2.6배). 대략의 산수지만 커리큘럼이 열릴 가능성은 낮다. **이것은 예측이다.** 정지 서명(1500 iter 이후 mode ≤ −2 3연속)은 1000·1250·1500 iter(16:20·16:45·17:10경) 스칼라로 확정한다. 이 프로그램에서는 건강한 n1 도 severity 0.05 를 4000 iter 무렵에야 넘으므로, 정지 서명의 severity < 0.05 조건은 판별력이 없다.
- 교차 확인: 채점 `exam_v3` healthy 셀의 yaw `os_env_mean` 은 classical_tdc 252/281, r3a_noboth 70/68, r3a_ref_full 13/17 이다. 고전 ThrusterPD 의 yaw 는 채점에서도 RL arm 보다 크게 나쁘다. 단위는 채점기 코드를 읽기 전이라 비교 방향만 적는다.
- 운영자 결정(15:4x, 푸시 후 질문에 대한 답): **계속 돌리고 1500 iter 에 확정한다.** 근거는 DGX 체인에서 n4 뒤에 대기 잡이 없어(`launch_paper_dgx.sh` 순서 ref → depthxy → n1 → n4) 계속 돌리는 비용이 없다는 것이다. 1000·1250·1500 iter 스칼라로 정지 서명을 확정한다. 완주본을 '팔 잔차만·커리큘럼 동결' 주석과 함께 표에 넣을지는 그때 정한다. 중단·재발사·설계 수정(스러스터 채널 잔차는 `residual_tdc_env.py` docstring 이 "scope decision" 으로 남긴 항목)은 하지 않는다.

## Update 2026-09-13 (15시 50분 KST) — classical 채점 12/12 완료, 채점 체인 종료

- classical 12셀이 모두 `rc=0 complete=yes` 로 끝났다. 셀당 9분 17초~9분 55초, 12셀 합계 1시간 54분이다.
  - tdc: healthy 14:02:52, pair34 14:12:09, healthy_d1 14:21:34, healthy_d2 14:30:53
  - pid: 14:40:42, 14:50:03, 14:59:22, 15:08:44
  - atdc: 15:18:39, 15:28:11, 15:37:42, 15:47:11
- 산출물 확인(15:50):
  - 12셀 모두 `summary.json` 이 있고, 셀당 npz 는 8개다.
  - NaN 토큰은 셀마다 180개로 r3a_noboth 4셀과 같다. 구조적 결측 키다.
  - RUN_CONDITIONS 의 override md5 는 제어기별로 일정하다: tdc 5802d0e5, pid 03388d15, atdc eb6cbbab. atdc 는 `m_hat_leak=0.5`·`m_hat_adapt_gain=0.01` 을 포함한다.
- 체인은 15:47:11 에 `=== TRAINING CHAIN FINISHED` 로 스스로 끝났다.
  - 미완 목록에는 r3a_n1_lagrangian·r3a_n4_residual·r3a_n6a_nodoraemon·r3a_n6b_nodr 네 개만 `(no complete run)` 으로 남았다.
  - n1·n4 는 DGX 산출이라 이 체인이 찾는 워크스테이션 logs 에 없다. n6a·n6b 는 운영자가 제외했다.
  - 15:50 에 컨테이너에 exam_chain 프로세스는 없고, GPU0·GPU1 사용률은 0% 다.
- 옛 실패 셀 폴더 `classical_*/<cell>.stale_<시각>` 20개가 남아 있다. 옛 체인이 600 s 마다 재시도하며 남긴 것을 새 체인이 해당 셀을 시작할 때 옮겼다. 지우지 않았다.
- 재발사 대기 스크립트(Mac PID 45110)는 13:53:01 에 한 번만 재발사했다.
  - ssh 원격 셸이 체인 수명 내내 붙어 있다가, 15:47:10 에야 돌아와 `relaunched` 줄을 찍고 15:47:18 에 끝났다.
  - 두 번째 재발사는 없다. exam.log 에 15:47 이후 START 줄이 없다.
- 남은 일:
  - DGX n4_residual 커리큘럼 확정 판독: 1000·1250·1500 iter(15시 45분 절)
  - DGX n4_residual 22:25경 완주 확인

## Update 2026-09-13 (16시 22분 KST) — n4_residual 1000 iter 판독: mode −2 네 번째, 15시 45분 절 예측 유지

- 판독 시점: 16:21, iteration 1047. 판독기와 대조군은 15시 45분 절과 같다.
- DORAEMON:
  - `mode` 는 0·250·500·750·1000 에서 −3, −2, −2, −2, −2 다. n1 은 1000 에서 0 이었다.
  - `success_rate` 는 87~1051 구간에서 0.028~0.076 이고, 1051 에 0.0585 다. n1 은 1000 에서 0.63 이었다.
  - `kl_step` 은 전 구간 0 이다.
  - `ess_ratio` 는 1 → 0.70 → 0.45 → 0.30 → 0.21 로 줄었다.
  - `mean/fault_severity` 는 0.0094 다.
- yaw 와 보상:
  - `Track/yaw/rate_err` 는 0.86~1.18 rad/s 에서 평탄하다.
  - `Reward/yaw_vel` 는 −4.4~−6.4, `Constraint/viol/yaw_rate` 는 41~66 이다.
  - `Reward/att_rp` 는 3.8~4.6 에서 평탄하다.
  - `Train/mean_reward` 는 −9.6~−72 이고, 1051 에 −9.6 이다.
  - `Policy/mean_noise_std` 는 0.85 로 계속 오르고 있다. n1 은 1000 무렵 0.20 이하였다.
- 판정: 예측과 어긋나는 신호가 없다. 운영자 결정대로 계속 돌리고, 1250·1500 iter(16:45·17:10경) 판독으로 확정한다.

## Update 2026-09-13 (16시 43분 KST) — n4_residual 1250 iter 판독: mode −2 다섯 번째, 예측 유지

- 판독 시점: 16:41, iteration 1264. 판독기와 대조군은 15시 45분 절과 같다.
- DORAEMON:
  - `mode` 는 250·500·750·1000·1250 에서 전부 −2 다. 0 에서는 −3 이었다.
  - `success_rate` 는 105~1264 구간에서 0.027~0.072 이고, 1264 에 0.049 다.
  - `kl_step` 은 전 구간 0 이다.
  - `ess_ratio` 는 1000 에서 0.21 이었다가 1250 에서 0.56 으로 올랐다.
  - `mean/fault_severity` 는 0.0096 이다.
- yaw 와 보상:
  - `Track/yaw/rate_err` 는 0.87~1.09 rad/s 로 평탄하다.
  - `Reward/yaw_vel` 는 −5.1~−6.6, `Constraint/viol/yaw_rate` 는 40~67 이다.
  - `Reward/att_rp` 는 4.0~4.6 이다.
  - `Train/mean_reward` 는 −45~−95 이고, 1264 에 −63 이다. 1000 판독(−9.6~−72)보다 낮은 쪽으로 흔들린다.
  - `Policy/mean_noise_std` 는 0.87 로 계속 오르고 있다.
- 판정: 예측과 어긋나는 신호가 없다. 1500 iter(17:10경) 판독에서 운영자 결정대로 확정한다.

## Update 2026-09-13 (17시 10분 KST) — n4_residual 1500 iter 확정 판독: mode −2 여섯 번째, 커리큘럼 동결 확정

- 판독 시점: 17:07, iteration 1531. 판독기와 대조군은 15시 45분 절과 같다.
- DORAEMON:
  - `mode` 는 250·500·750·1000·1250·1500 에서 전부 −2 다. 0 에서는 −3 이었다.
  - `success_rate` 는 127~1531 구간에서 0.032~0.073 이고 추세가 없다. 1531 에 0.052 로, 문턱 alpha 0.5 의 약 1/10 이다.
  - `kl_step` 은 전 구간 0 이다. 분포가 한 번도 넓어지지 않았다.
  - `ess_ratio` 는 1500 에서 0.41 이다.
  - `mean/fault_severity` 는 0.0092 로 초기값 0.01 에 머문다.
- yaw 와 보상:
  - `Track/yaw/rate_err` 는 0.79~1.16 rad/s 로 평탄하고, 1531 에 0.92 다.
  - 느리게 나아지는 항목은 있다(127→1531): `Constraint/viol/yaw_rate` 69→45, `Reward/yaw_vel` −6.5→−5.2, `Reward/total` −2.4→−1.4.
  - 그래도 `Train/mean_reward` 는 −19~−95 에서 흔들리고 1531 에 −54 다. 성공 문턱(return 200)과의 거리는 줄지 않았고, success_rate 에도 반영되지 않는다.
  - `Reward/att_rp` 는 3.6~4.5 이고, `Policy/mean_noise_std` 는 0.90 까지 계속 오른다.
- 판정: 운영자가 정한 확정 조건을 충족한다. 15시 45분 절의 예측 "정책이 yaw 를 쥐지 못해 DORAEMON 커리큘럼이 열리지 않는다" 를 확정한다.
  - 확정 조건은 1000·1250·1500 판독 모두 mode ≤ −2, kl_step 0, success 가 0.5 에 크게 못 미칠 것이다.
  - 메모리 규칙의 정지 서명("1500 iter 이후 mode ≤ −2 3연속")을 글자대로 적용하려면 1500·1750·2000 이 필요하다. 이번 확정은 운영자가 정한 1000·1250·1500 기준이다. 2500 도달 알림(감시 b5ifuaf9j) 때 mode 를 한 번 더 본다.
  - 정지 서명의 severity < 0.05 조건은 이 프로그램에서 변별하지 않는다(15시 45분 절).
- 런은 멈추지 않는다(운영자 결정). 17:07 로그 ETA 는 5시간 20분이라 22:27경 완주할 전망이다. 1531 시점 체크포인트는 31개다.
- 운영자 결정 대기: 완주본을 "팔 잔차만·커리큘럼 동결" 주석과 함께 비교표에 넣을지.

## Update 2026-09-13 (19시 45분 KST) — n4_residual: 운영자 결정 "주석 달고 표에 넣기", 3083 iter 판독과 n1 대조, 17시 10분 절 두 서술 정정

- 운영자 결정(17시 10분 절 대기 항목):
  - 완주본을 비교표에 넣고 주석을 단다. 주석 원안은 "팔 잔차만·커리큘럼 동결"이다.
  - arm 공통 커리큘럼 성공 문턱이 이 arm 에 불리했다는 한계를 본문에 한 줄 적는다.
- 판독:
  - 시점은 19:32, n4 iteration 3083 이다. 감시 b5ifuaf9j 가 18:41 에 2500 을 알렸다.
  - 대조군은 같은 DGX 에서 완주한 n1_lagrangian(`trpo_dgx_n1_lagrangian_260913_065642`)이고, 같은 iter 창에서 읽었다.

| 지표 (약 3096 iter) | n1_lagrangian | n4_residual |
|:---|:---|:---|
| DORAEMON mode | 1000 부터 0 | 250~3000 열두 번 모두 −2 |
| success_rate | 0.84 | 0.087~0.10 |
| entropy_after (시작 −49.49) | −37.13 (+12.4) | −48.91 (+0.58) |
| mean/fault_severity (시작 0.01) | 0.0297 | 0.0068 |
| mean/ocean_current_strength (시작 0.01) | 0.0307 | 0.0068 |
| std/inertia_scale (시작 0.144) | 0.222 | 0.174 |
| kl_step | 전 구간 0 | 전 구간 0 |

- 판정:
  - 1500·1750·2000 이 3연속 −2 라, 메모리 정지 서명을 글자대로 적용해도 충족한다. 17시 10분 절의 확정은 유지한다.
  - 분포 entropy 는 n1 이 움직인 양의 약 5% 만 움직였다. 커리큘럼이 열리지 않았다는 판정의 가장 직접적인 근거다.
  - success_rate 는 느리게 오른다(1028 0.047 → 2056 0.069 → 3083 0.10). 2056~3083 기울기(1000 iter 당 약 0.03)를 5000 까지 늘여도 0.16 안팎이라 문턱 0.5 에 닿지 않는다. 이 부분은 외삽이다.
- **정정 1 — kl_step 은 판별 신호가 아니다.**
  - 16시 22분 절(1401행), 16시 43분 절(1418행), 17시 10분 절(1435·1444행)이 `kl_step` 0 을 적었다.
  - 건강한 n1 도 전 구간 0 이라, 이 태그는 두 런을 가르지 않는다.
  - 따라서 1435행의 "분포가 한 번도 넓어지지 않았다"와 1444행 확정 조건의 "kl_step 0" 은 틀렸다.
  - 확정 조건에서 kl_step 을 빼고 mode·success·entropy 대조로 바꾼다. 결론은 바뀌지 않는다.
  - 세션 로그 16:22·16:43·17:10 행의 kl_step 값도 같은 이유로 판별 근거가 아니다.
- **정정 2 — 분포는 멈춰 있지 않다.**
  - 17시 10분 절의 "`mean/fault_severity` 는 초기값 0.01 에 머문다"는 1531 까지만 맞다.
  - mode −2 인 동안에도 분포는 조금씩 바뀐다. fault_severity·ocean_current 평균은 0.01→0.0068 로 쉬운 쪽으로 갔고, added_mass·inertia·buoy_volume·obs_noise 의 std 는 넓어졌다.
  - 그래서 주석의 "동결"은 엄밀하지 않다. "커리큘럼 미개방(mode 0 진입 0회, 분포 entropy 변화 n1 대비 약 5%)"이 관측과 맞는다.
  - 문구는 표를 쓸 때 운영자와 확인한다.
- 정책:
  - `Policy/mean_noise_std` 는 1500 의 0.90 에서 3083 의 1.19 로 계속 오른다.
  - `Track/yaw/rate_err` 는 0.74~1.08 rad/s, `Constraint/viol/yaw_rate` 는 45~60 이다. 1500 판독 뒤로 개선이 이어지지 않았다.
  - `Train/mean_reward` 는 −14~−71 이고, 3083 에 −17 이다.
- 런: 19:32 로그 ETA 는 2시간 57분이라 22:29경 완주할 전망이다. 최신 체크포인트는 model_3050 이다.

## Update 2026-09-13 (22시 40분 KST) — n4_residual 완주(rc 0), DGX 체인 종료: 끝까지 커리큘럼 미개방

- 완주 확인(22:37, DGX):
  - 체인 로그 `~/xyz_launch/paper_dgx_b.out` 에 `22:33:28 END n4_residual rc=0 ok=1` 이 찍혔고, 이어서 `DGX CHAIN END` 가 찍혔다.
  - 런 디렉터리에 `model_4999.pt`(22:32), `.chain_ok`(22:33), `curriculum_trajectory.json` 이 있다. 체크포인트는 101개다.
  - 학습 로그의 nan·Traceback 은 0건이다.
  - GPU 사용률은 0% 이고 계산 프로세스가 없다. DGX 에 대기 잡도 없다.
- 끝까지의 커리큘럼. n1 끝값은 같은 DGX 완주본 `trpo_dgx_n1_lagrangian_260913_065642` 에서 읽었다.

| 지표 | 3509 | 4522 | 4999 (끝) | n1 끝값 |
|:---|:---|:---|:---|:---|
| DORAEMON mode | −2 | −2 | 250~4750 열아홉 번 모두 −2 | 1000 부터 0 |
| success_rate | 0.099 | 0.113 | 0.0985 | 0.764 |
| entropy_after (시작 −49.49) | −48.55 | −49.15 | −49.14 | −28.62 |
| mean/fault_severity (시작 0.01) | 0.0071 | 0.0069 | 0.0091 | 0.0716 |
| Policy/mean_noise_std | 1.24 | 1.41 | 1.49 | 읽지 않음 |

- 판정:
  - 5000 iter 내내 DORAEMON 정상 최적화(mode 0)에 한 번도 들어가지 않았다.
  - 분포 entropy 는 끝에 시작값과 0.35 차이다. n1 은 +20.9 움직였으니, 사실상 움직이지 않았다.
  - 19시 45분 절의 "커리큘럼 미개방" 서술이 완주본에서도 그대로다.
  - 3083 판독 때 외삽한 success 상승(5000 에 0.16 안팎)은 일어나지 않았다. 3000 이후 0.09~0.11 에서 평탄하다.
  - noise std 가 끝까지 올라 1.49 다. 정책이 수렴하지 않은 채 끝났다.
- 남은 일(운영자 결정):
  - **n1·n4 채점 경로**: 둘 다 DGX 산출이라, 15:47 에 끝난 워크스테이션 채점 체인이 `(no complete run)` 으로 건너뛰었다. 채점 방식을 정해야 표 수치가 나온다. DGX 산출은 DGX 기준선하고만 비교한다는 제약이 함께 걸린다.
  - **주석 문구**: 원안 "팔 잔차만·커리큘럼 동결"과, 관측에 맞는 "커리큘럼 미개방" 중에서 고른다.
  - **체크포인트 선택**: model_4999 하나만 채점할지 정한다. 정책이 수렴하지 않았으므로, 같은 런의 다른 체크포인트와 비교할지가 쟁점이다.
- 감시:
  - b5ifuaf9j 는 종료 이벤트를 낸 뒤 스스로 끝났다.
  - bgnzrx5p7 은 감시 대상 셋(DGX 체인·GPU0 체인·채점 체인)이 모두 끝나 세션에서 멈췄다.

## Update 2026-09-14 (10시 15분 KST) — 운영자 결정 반영, DGX 세 런 채점 발사, 비교군 실기 검증 범위 확인

- 운영자 지시 원문(09-14 10시경): "depth xy는 배포 안하기로 결정했고, 채점경로는 너가 알아서 해줘. 그리고 비교군을 실제 로봇에 넣고 검증해야하는거 아니야? 그건 다 끝났다는건가?"
- **depth-xy**: 배포하지 않는다. 학생 증류는 돌리지 않는다. `/workspace/xyz-student` 의 미커밋 편집은 손대지 않고 둔다.
- **채점 경로** (운영자가 세션에 위임한 결정):
  - 채점기는 워크스테이션 행과 같다:
    - 코드: 평가 워크트리 `/workspace/constrained-albc-eval` afa3c6b + marinelab-r3a 8cc84a5(둘 다 clean)
    - 박스: p3b 최종 DORAEMON(`--env-dr-anchor --doraemon-dr-from`)
    - 설정: CORE 4설정, `--att-amp-deg 15`, 64 env, seed 42
    - 기록: `--save-extras`, healthy 셀은 `--save-moments` 추가
    - 셀 상한 5400 s
    - identity·`.complete`·`validate_cell` 형식은 `exam_chain_r3a.sh` d29fb4d9 와 같다.
    - GPU1 은 셀마다 `/root/gpu1.lock` 을 잡는다.
  - 이렇게 두면 DGX 행과 워크스테이션 행의 차이는 학습 머신 하나다. 채점까지 DGX 에서 하면 머신 차이가 두 겹이 된다.
  - 행은 셋이다:
    - dgx_ref: DGX 기준선. 한 번도 채점된 적이 없다(09-13 12:11:30 `dgx_static_exam` 이 셀 0개인 채 취소됨).
    - dgx_n1_lagrangian
    - dgx_n4_residual
  - 비교는 1200행 규칙대로 dgx_ref 대비 델타로만 한다.
  - 체크포인트:
    - 표에는 model_4999 를 쓴다. 워크스테이션 arm 과 같은 규칙이다(961행).
    - 같은 세 런의 model_2500 을 보조로 뒤에 채점한다. n4 는 noise std 1.49 로 수렴하지 않은 채 끝났다. 같은 런의 둘째 체크포인트로 마지막 체크포인트 효과와 실현 노이즈를 가늠한다.
    - 보조 행은 표 수치를 바꾸지 않는다.
  - n4 주석 문구는 "커리큘럼 미개방(DORAEMON mode 0 진입 0회/5000 iter; 정책은 팔 잔차만, yaw 는 고전 PD)" 으로 한다.
    - "동결"은 쓰지 않는다. 19시 45분 절에서 정정한 이유와 같다.
    - 한계 한 줄: 공통 DORAEMON 성공 문턱(return ≥ 200 비율 ≥ 0.5)에 이 arm 이 도달할 수 있는지를 발사 전에 따지지 않았다.
- 준비:
  - DGX 세 런을 컨테이너로 복사했다(10:06, `tar -k`).
    - 대상 파일: model_2500·model_4999·params·.chain_ok
    - 위치: `/workspace/constrained-albc/logs/rsl_rl/{albc_ablation,albc_trpo_teacher}/paper_ablation_r3a_dgx/`
  - md5 6개가 DGX 원본과 같다. 스크립트는 셀마다 잠금 안에서 md5 를 다시 확인한다.

    | 런 | model_4999 | model_2500 |
    |:---|:---|:---|
    | ref | 8a820d41 | 08484ef5 |
    | n1 | e9428c4a | 08c0fb75 |
    | n4 | f921699d | 6325f89f |

  - 스크립트:
    - `exam_dgx_r3a.sh`(이 디렉터리, md5 2a456c11), `bash -n` 통과
    - 산출 경로 `.hq/work/paper_ablation_r3a/exam_v3_dgx/<row>/<cfg>/`, model_2500 행 이름은 `<row>_m2500`
  - residual task 채점 경로는 채점 체인 스모크에서 이미 돌았다(969행, smoke_n4 포함 11/11 rc 0). 그래도 첫 셀을 n4 로 두었고, 첫 셀이 실패하면 배치 전체가 멈춘다.
- 발사: 10:09:46 KST.
  - 명령: `setsid nohup bash .../exam_dgx_r3a.sh > .hq/work/paper_ablation_r3a/exam_dgx_launcher.out`
  - 스크립트 PID 1055125
  - 10:12 확인: 첫 셀 dgx_n4_residual/healthy 가 none tier 6000/7750 step, 64/64 생존, GPU1 32 %
- 발사 함정: `ssh host 'cd X && setsid nohup bash s > out 2>&1 < /dev/null & echo'` 형태로 보내면 로컬 ssh 가 배치가 끝날 때까지 돌아오지 않는다. 발사 자체는 정상이다.
  - 원인: `&&` 목록 전체가 백그라운드 서브셸이 되고, 그 서브셸이 ssh 채널을 쥔 채 남는다.
  - 다음부터는 `cd X;` 를 분리해서 보낸다.
- 예상 시간: 24셀 × 9~10분(classical 12셀 실측 기준) ≈ 3시간 50분. model_4999 세 행(12셀)은 12시경, model_2500 세 행은 14시경 끝난다. 첫 셀 실측으로 다시 적는다.
- 감시: Monitor `buzkp7kcu` 가 exam.log 의 `done`·FATAL·FAILED·BATCH END 줄을 셀마다 알린다.
- **비교군 실기 검증 범위** (운영자 질문 확인):
  - 이 프로그램은 시뮬 비교다. 350행 분업표대로 실기 배포는 별도 세션 몫이다. 421행대로 실기에 올라가는 정책은 R3a 다.
  - 논문이 실기에 요구하는 것은 워크스페이스 스토어 `handoff/199` 에 있고, 배포 팩 R3a·p5 두 가지 시험뿐이다:
    - T4 자세유지(R-B)
    - S3 파지 계단 과도응답(R-A)
  - paper-ablation 의 RL arm(ref_full·a6·noenc·ppo·noipo·noboth·n1·n4)을 실기에 올리는 항목은 없다.
  - 실기 비교군은 수조 세션이 따로 정했다:
    - 고정 트림(decision/205)
    - 보드 TDC(decision/214, 운영자 09-13 15:35 "납을 달고 tdc랑 rl만 비교하도록 하자")
  - 스토어 기준 실측 상태. 마지막 글은 decision/215(09-13 17:3x)다.
    - T4·S1: 09-11 에 돌았다(finding/200).
    - C0 RL 대 트림 6런: 판독까지 끝났다(finding/213). n=3 이고, 잠정 판독은 "맨 막대에서 RL 팔이 트림보다 낫지 않다"이다.
    - C1 RL 대 보드 TDC: 아직 안 돌았다. 모드 5 는 anti-windup 이식과 게인 사다리를 재설계했고, 보드 빌드 시각이 미정이다(decision/215).
    - 수조 RL 은 팔 전용이다. 스러스터를 껐다(decision/211).
  - 이 세션은 로봇·보드 조작 금지라 실기 쪽은 진행하지 않는다.

## Update 2026-09-14 (12시 10분 KST) — DGX 세 런 model_4999 채점 12셀 판독, dgx_ref 대비 델타

- 셀: 표에 들어갈 12셀이 모두 rc 0·complete=yes 다. 셀당 9분 9초~9분 55초.
  - healthy·pair34·healthy_d1·healthy_d2 순으로 n4 10:19:41·10:29:26·10:39:05·10:48:42, dgx_ref 10:58:20·11:07:37·11:16:56·11:26:05, n1 11:35:58·11:45:11·11:54:25·12:03:47
  - model_2500 보조 12셀이 이어서 돌고 있다. 14시경 끝난다.
- 추출: 새 코드는 쓰지 않았다.
  - `.hq/runtime/experiments/scratch/student-distill-eint-analysis-scripts/arm_compare.py` 를 설정마다 dgx_ref 앵커로 돌렸다. arm 은 n4·n1·ws_ref(= `exam_v3/r3a_ref_full/<cfg>`, 머신 차이 참고용), 축은 att_norm·roll·pitch·yaw, 필드는 ss_error·os_env_mean.
  - 문턱은 앵커 summary.json 의 decision_floors 다: ss_error 0.1°, os_env_mean 10 pp, survival_pct 1.6 pp(잠정). yaw OS 에도 10 pp 를 그대로 적용했다.
  - JSON: `.hq/work/paper_ablation_r3a/dgx_cmp_4999/dgx_cmp_<cfg>.json`
  - 대조: ws_ref 의 healthy·pair34 값이 워크스페이스 스토어 `.hq/work/scholar/albc/reviews/2026-09-14-v14-evidence-delta.md` §B 의 r3a_ref_full 값과 표기 자릿수까지 같다. 같은 산출을 읽고 있다.
- att_norm 정상상태 오차. dgx_ref 줄은 값(deg), 나머지 줄은 dgx_ref 대비 델타, `*` 는 문턱 초과.

    | 설정 | 행 | none | soft | medium | hard |
    |:---|:---|---:|---:|---:|---:|
    | healthy | dgx_ref 값 | 0.675 | 0.738 | 1.211 | 4.619 |
    | | n1 | −0.098 | −0.21* | −0.45* | −0.83* |
    | | n4 | +3.22* | +3.38* | +2.86* | +0.01 |
    | | ws_ref | −0.15* | −0.17* | −0.45* | −0.59* |
    | pair34 | dgx_ref 값 | 2.007 | 1.823 | 2.895 | 6.753 |
    | | n1 | +1.03* | +0.75* | +0.39* | +1.74* |
    | | n4 | +1.18* | +1.59* | +0.63* | −1.99* |
    | | ws_ref | +0.33* | +0.06 | −0.45* | +0.70* |
    | healthy_d1 | dgx_ref 값 | 0.652 | 0.722 | 1.173 | 4.296 |
    | | n1 | −0.05 | −0.23* | −0.43* | −0.51* |
    | | n4 | +3.70* | +3.39* | +2.86* | −0.24* |
    | | ws_ref | −0.14* | −0.18* | −0.45* | −0.66* |
    | healthy_d2 | dgx_ref 값 | 0.662 | 0.759 | 1.323 | 4.330 |
    | | n1 | +0.09 | −0.24* | −0.57* | −0.62* |
    | | n4 | +4.21* | +4.11* | +3.71* | +0.68* |
    | | ws_ref | −0.13* | −0.19* | −0.57* | −0.28* |

- yaw-rate 오버슈트(스텝 대비 %). tier 는 none / soft / medium / hard. n1·ws_ref 는 dgx_ref 대비 델타(pp), n4 는 값.

    | 설정 | dgx_ref 값 | n1 델타 | ws_ref 델타 | n4 값 |
    |:---|:---|:---|:---|:---|
    | healthy | 19.5 / 24.9 / 23.5 / 29.3 | +9.9 / +12.0* / +13.6* / +18.0* | −6.3 / −7.6 / −5.9 / −3.3 | 237 / 267 / 277 / 301 |
    | pair34 | 16.1 / 19.6 / 21.9 / 29.4 | +5.3 / +6.1 / +6.9 / +18.1* | −3.0 / −4.2 / −5.2 / −5.4 | 188 / 215 / 225 / 261 |
    | healthy_d1 | 9.7 / 9.5 / 11.7 / 14.5 | +10.3* / +11.8* / +12.4* / +19.1* | +0.8 / +1.7 / +1.1 / +2.9 | 226 / 246 / 251 / 266 |
    | healthy_d2 | 16.7 / 21.8 / 22.6 / 22.9 | +11.2* / +13.5* / +14.4* / +22.5* | −3.7 / −4.6 / −3.9 / +2.4 | 323 / 348 / 365 / 378 |

- 생존: hard 에서만 갈린다. pair34 는 dgx_ref 98.4·n1 95.3(64 env 중 사망 3 대 1, −3.1 pp 로 문턱 초과)·n4 100·ws_ref 96.9 다. healthy_d1 은 n1·ws_ref 98.4, healthy_d2 는 ws_ref 98.4 이고 나머지는 전부 100 이다.
- hard roll OS: n4 가 네 설정 모두 dgx_ref 보다 11.6~17.3 pp 낮다(전부 문턱 초과). n1 은 −7.7~+4.1 pp 로 문턱 안이다.
- 판독 (n=1 채점, 런마다 실현 하나):
  1. **n1 의 healthy 계열 att ss 이득은 보류한다.** medium·hard 에서 n1 − dgx_ref 가 −0.43~−0.83° 인데, 같은 칸의 ws_ref − dgx_ref 도 −0.28~−0.66° 다. medium 값은 n1 0.760·0.742·0.753, ws_ref 0.762·0.722·0.751 로 거의 같고 dgx_ref 만 1.17~1.32 로 높다. 머신 효과가 DGX 를 나쁘게 만든 것이라면 같은 DGX 의 n1 도 나빠야 한다. 그러니 n1 의 실제 이득인지, dgx_ref 가 나쁜 쪽으로 실현된 것인지를 기준선 실현 하나로는 가를 수 없다.
  2. **n1 의 yaw-rate OS 증가는 네 설정 모두 같은 방향이다.** n1 − dgx_ref 가 +5.3~+22.5 pp 이고 16칸 중 12칸이 문턱을 넘는다. hard 에서는 +18.0~+22.5 pp 다. 같은 칸의 ws_ref − dgx_ref 는 −7.6~+2.9 pp 라 기준선 두 실현은 서로 8 pp 안에서 맞는다. 지금 표에서 n1 에 대해 가장 안정된 신호다.
  3. **n1 은 pair34(보드 m0+m2 사망)에서 기준선보다 나쁘다.** att ss 가 +0.39~+1.74° 로 네 tier 모두 문턱을 넘고, 대부분 pitch ss(+0.91~+1.63°)에서 온다. hard 생존도 95.3 대 98.4 % 다. 같은 칸의 ws_ref − dgx_ref(+0.33·+0.06·−0.45·+0.70)보다 none·soft·hard 는 크고 medium 은 그 안이다.
  4. **n4 는 주석대로 읽힌다.** att ss 는 설정·tier 와 무관하게 3.2~5.0° 로 평탄하다. yaw OS 는 188~378 % 로 classical_tdc(healthy 252/298 %) 수준이고 healthy_d2 에서 가장 크다. hard roll OS 가 낮고 pair34 hard att ss 가 −1.99°(4.76 대 6.75)이지만, yaw 를 고전 PD 가 쥐고 커리큘럼이 열리지 않은 행이라 장점으로 적지 않는다.
  5. **머신 차이는 상수 오프셋이 아니다.** ws_ref − dgx_ref att ss 가 healthy 계열에서는 −0.13~−0.66° 로 워크스테이션이 낫고, pair34 에서는 부호가 섞인다. 크기는 같은 머신 재실현 차(p3b_5000 대 ref_full, none 0.02·hard 0.14)보다 크다. DGX 행을 DGX 기준선 대비로만 읽는 1200행 규칙은 유지한다. 다만 그 기준선이 실현 하나라는 한계가 1번에서 드러났다.
- 다음:
  - 14시에 model_2500 보조 12셀을 같은 방식으로 읽는다. 같은 런의 다른 체크포인트라 체크포인트 간 흔들림만 보이고, 독립 재실현은 아니다.
  - n1 의 healthy 이득을 판정하려면 DGX 기준선의 독립 재실현이 필요하다. 학습 발사는 운영자 결정이다.

## Update 2026-09-14 (14시 05분 KST) — model_2500 보조 12셀 판독, 채점 배치 종료, 12시 10분 판독 수정

- 배치: 13:58:34 `=== BATCH END failed_cells=0`.
  - exam.log 에 `rc=0 complete=yes` 가 24줄 있다.
  - 발사 ssh(Mac 백그라운드)도 같은 시각 exit 0 으로 돌아왔다.
  - GPU0·GPU1 사용률은 모두 0 % 다.
- 보조 셀 완료 시각. healthy·pair34·healthy_d1·healthy_d2 순이다.
  - n4_m2500: 12:13:57·12:23:35·12:33:25·12:43:03
  - dgx_ref_m2500: 12:52:51·13:02:10·13:11:33·13:20:44
  - n1_m2500: 13:30:40·13:39:57·13:49:17·13:58:34
- 추출: 같은 `arm_compare.py` 를 dgx_ref_m2500 앵커로 돌렸다.
  - arm: n1_m2500·n4_m2500·dgx_ref(4999)·n1(4999)
  - JSON: `.hq/work/paper_ablation_r3a/dgx_cmp_m2500/dgx_cmp_m2500_<cfg>.json`
- **model_2500 은 학습 중간 상태다.**
  - dgx_ref 는 2500→4999 에 att ss 가 hard 에서 −3.1~−3.6°, medium 에서 −0.6~−1.5° 좋아졌다.
  - 그래서 보조 행은 실현 노이즈의 바닥이 아니라 학습 진행을 보여준다. 표는 4999 로 둔다.
  - 10시 15분 절의 "같은 런의 둘째 체크포인트로 … 실현 노이즈를 가늠한다"는 틀렸다.
    - 공짜 재실현은 다른 런의 같은 iter 체크포인트일 때만 성립한다.
    - 같은 런의 이른 체크포인트가 답할 수 있는 것은 하나다. 같은 두 런을 같은 체크포인트끼리 붙였을 때 arm 차이의 부호가 두 체크포인트에서 유지되는가.
- n1 − dgx_ref, att_norm ss (deg). 칸마다 "2500 / 4999" 이고 `*` 는 문턱 초과다.

    | 설정 | none | soft | medium | hard |
    |:---|:---|:---|:---|:---|
    | healthy | −0.21* / −0.098 | −0.29* / −0.21* | −0.46* / −0.45* | +0.22* / −0.83* |
    | pair34 | −0.85* / +1.03* | −0.18* / +0.75* | +0.33* / +0.39* | +3.27* / +1.74* |
    | healthy_d1 | −0.23* / −0.05 | −0.29* / −0.23* | −0.35* / −0.43* | +1.33* / −0.51* |
    | healthy_d2 | −0.24* / +0.09 | −0.26* / −0.24* | −0.36* / −0.57* | +0.49* / −0.62* |

- n1 − dgx_ref, yaw-rate OS (pp). 칸 형식은 위와 같다.

    | 설정 | none | soft | medium | hard |
    |:---|:---|:---|:---|:---|
    | healthy | +23.7* / +9.9 | +24.9* / +12.0* | +22.3* / +13.6* | +26.6* / +18.0* |
    | pair34 | +13.0* / +5.3 | +15.7* / +6.1 | +18.7* / +6.9 | +26.6* / +18.1* |
    | healthy_d1 | +16.0* / +10.3* | +17.3* / +11.8* | +21.5* / +12.4* | +32.0* / +19.1* |
    | healthy_d2 | +28.4* / +11.2* | +27.9* / +13.5* | +28.1* / +14.4* | +34.4* / +22.5* |

- hard 생존(%):

    | 설정 | dgx_ref 2500 / 4999 | n1 2500 / 4999 |
    |:---|:---|:---|
    | healthy | 98.4 / 100 | 96.9 / 100 |
    | pair34 | 96.9 / 98.4 | 93.8 / 95.3 |
    | healthy_d1 | 100 / 100 | 100 / 98.4 |
    | healthy_d2 | 100 / 100 | 98.4 / 100 |

  pair34 에서는 두 체크포인트 모두 n1 이 2 env 더 죽는다. 나머지 설정은 방향이 섞인다.
  위 셋 밖의 칸은 두 체크포인트 모두 100 이다.
- 판독:
  1. **n1 의 yaw-rate OS 증가를 이 두 런 안에서 확정한다.**
     - 두 체크포인트의 32칸이 모두 같은 부호다.
     - 2500 에서는 16칸이 전부 문턱을 넘는다(+13.0~+34.4 pp).
  2. **n1 의 pair34 악화는 medium·hard 로 좁힌다.**
     - medium·hard 는 두 체크포인트에서 att ss 가 +0.33~+3.27° 이고, hard 생존도 두 번 모두 낮다.
     - none·soft 는 2500 에서 부호가 뒤집힌다(−0.85·−0.18).
  3. **n1 의 healthy 계열 soft·medium 이득은 두 체크포인트에서 같은 크기로 남는다.**
     - 크기: 2500 −0.26~−0.46°, 4999 −0.21~−0.57°.
     - 그러니 dgx_ref 의 마지막 체크포인트만 나쁘게 나온 것은 아니다.
     - 그래도 같은 두 런의 체크포인트라, 런 실현 차이와 방법 효과를 가르지 못한다.
     - 다른 기준선 실현(ws_ref)이 4999 에서 n1 과 같은 값이므로 보류를 유지한다.
     - hard 는 2500 에서 부호가 뒤집혀(+0.22~+1.33°) 체크포인트에 따라 달라진다.
  4. **n4 는 2500→4999 사이 거의 변하지 않았다.**
     - att ss 차이는 0.31° 이하이고, yaw OS 도 같은 수준이다. 커리큘럼 미개방 주석과 맞는다.
     - 2500 에서 n4 의 hard 우위(−3.2~−5.3°)는 기준선이 hard 에서 아직 나빴기 때문이다.
- 12시 10분 절 판독 수정:
  - 판독 1(n1 healthy 이득 보류): 보류를 유지한다.
    - 마지막 체크포인트 탓일 가능성은 배제한다. 런 실현 차이일 가능성은 남는다.
    - hard 이득(−0.51~−0.83°)은 주장에서 뺀다.
  - 판독 2(yaw OS): 두 체크포인트 일치로 강화한다.
  - 판독 3(pair34 악화): "네 tier 모두" 를 철회하고 medium·hard 로 좁힌다.
- 다음:
  - 이 배치로 DGX 세 런 채점은 끝났다.
  - n1 healthy 이득을 판정하려면 DGX 기준선의 독립 재실현이 필요하다. 이 학습 발사는 운영자 결정이고, GPU 는 유휴다.

## Update 2026-09-14 (14시 35분 KST) — n1 판정용 재실현 두 런 발사 (운영자 승인)

- 운영자 지시 원문(14시 10분경): "그렇게 해줘. ksm-ubuntu 사용해도 괜찮고."
  - 14시 05분 절 "다음"에 적은 DGX 기준선 독립 재실현을 승인했다.
  - ksm-ubuntu 사용도 허락했다.
- 질문은 하나다. n1 의 healthy 계열 soft·medium 이득이 방법 효과인가, 런 실현 차이인가. 두 런을 동시에 돌린다.

    | 런 | 머신 | 짝 | 답하는 것 |
    |:---|:---|:---|:---|
    | dgx_ref_s31 (TRPO 기준선, seed 31) | DGX GB10 | dgx_ref(s30), dgx_n1(s30) | dgx_ref s30 이 나쁜 쪽 실현이었나(같은 머신 기준선 둘 대 n1 하나) |
    | ws_n1_lagrangian (seed 30) | ksm-ubuntu GPU0 | ws ref_full(s30) | 두 번째 머신에서 같은 시드의 n1 − ref 가 재현되나 |

  - ksm-ubuntu 에 n1 을 둔 이유:
    - 기준선을 더 돌리면 DGX 기준선 질문에 답하지 못한다(1200행 규칙).
    - 같은 머신·같은 시드의 ref_full 이 이미 있어서 n1 하나로 짝이 완성된다.
    - 09-11 큐의 워크스테이션 n1 행(`r3a5000_n1_lagrangian_s30`, 분할 때 DGX 로 옮김)과 같은 arm 이다.
- 발사 게이트 원장 대조(decision/197, decision/209):
  - 적용하지 않은 것: 197 의 열린 HARD-GATE 항목(2~4: 수직 TAM, IMU 45°, TAM DR 대역)과 209 플랜트 수정 묶음 v2.
  - 이유: 표의 모든 행이 같은 pre-<item> 상태다. 재실현은 표의 행과 같은 플랜트여야 비교가 된다.
  - 09-11 큐 기록의 ack(264·352·441·444)도 그대로다.
- **DGX** `~/xyz_launch/launch_dgx_ref_s31.sh` (md5 ec0eb006, 원본 `launch_paper_dgx.sh` 88ffc833 는 그대로)
  - 앵커 3791441 + marinelab-xyz 8cc84a5. task·variant·group·4096 env·5000 it 는 s30 과 같고 `--seed 31` 만 다르다.
  - 첫 발사(14:18:07)는 스크립트의 설정 동일성 게이트가 스스로 멈췄다.
    - 텍스트 diff 가 오탐했다. 차이는 pickle 텐서 블롭 3개 안의 프로세스별 저장소 키와 log_dir 뿐이었다.
    - 빈 런 디렉터리는 `albc_trpo_teacher/_failed_launch/` 로 옮겼다.
  - 비교기를 의미 비교 `cfgdiff.py`(md5 4566feeb; DGX `~/xyz_launch/`, 컨테이너 이 디렉터리)로 바꿨다.
    - 텐서는 값으로 비교한다. seed·run_name·log_dir 는 빼고, DGX 경로 접두어는 컨테이너 경로로 맞춘다.
    - 판별력 확인:
      - s30 대 s31: env·agent 동일(rc 0)
      - 기준선 대 n1: agent 에서 알고리즘 클래스, lagrangian 3키, experiment_name 이 다름(rc 1)
      - DGX 기준선 대 워크스테이션 기준선: env·agent 동일. 두 머신의 설정은 경로 말고 같다.
  - 재발사: 14:24:32 START, 14:24:44 GATE ok(cfgdiff 둘 다 동일).
    - 런: `trpo_dgx_ref_s31_260914_142436`
    - 5.5 s/iter, ETA 7시간 30분(22시경)
  - DGX ssh 는 stdio 를 모두 돌린 `( nohup setsid bash … & )` 형태에서도 학습 수명 동안 돌아오지 않는다. 원인은 확인하지 못했다. 발사는 정상이고, 컨테이너에서는 같은 형태가 바로 돌아왔다.
- **ksm-ubuntu GPU0** 이 디렉터리 `launch_ws_n1_r3a.sh` (md5 a43c79ce)
  - r3a 트리 3791441 + marinelab-r3a 8cc84a5, `CUDA_VISIBLE_DEVICES=0`, seed 30.
  - 작업 디렉터리를 r3a 트리 밖에 뒀다.
    - 위치: `.hq/work/paper_ablation_r3a/ws_train_cwd/`, `logs` 는 `/workspace/constrained-albc/logs` 로 심링크.
    - 이유: `train.py:216` 이 logs/ 를, Hydra 가 outputs/ 를 cwd 에 쓴다.
    - 메인 저장소 루트는 `constrained_albc` 패키지가 있어 import 를 가릴 수 있어서 피했다.
    - import 경로가 r3a 와 marinelab-r3a 로 잡히는 것을 확인했다.
  - 14:29:32 START, 14:29:45 GATE ok.
    - 게이트: check_simtoreal section5, velocity_limit_sim 3.1, seed 30, cfgdiff 가 DGX n1 과 동일.
    - 런: `logs/rsl_rl/albc_ablation/paper_ablation_r3a/trpo_r3a_n1_lagrangian_260914_142937`
    - 3.43 s/iter, ETA 4시간 38분(19시 10분경)
    - 발사 뒤 r3a 트리에 새로 생긴 파일 0개, git status 0.
- 감시:
  - Monitor 두 개(워크스테이션 belj1r78r, DGX). 체인 줄, 500 iter 마다 진행, Traceback 을 알린다.
  - 1000 iter 무렵 커리큘럼 건강을 짝 런과 같은 창으로 대조한다(DGX s30 기준선, DGX n1).
- 채점:
  - 끝나면 워크스테이션 행과 같은 채점기(eval afa3c6b·ml 8cc84a5·p3b 박스·CORE 4·att 15°·64 env·seed 42)로 model_4999 만 채점한다.
  - 런당 4셀, 약 40분, GPU1.
  - DGX 체크포인트는 컨테이너로 복사하고 md5 를 대조한다.
- **판정 규칙 (데이터 전 등록)**. 지표는 att_norm ss, 대상은 healthy·healthy_d1·healthy_d2 의 soft·medium 여섯 칸, 문턱은 0.1°.
  - DGX:
    - 여섯 칸 모두 |s31 − n1| ≤ 0.1° 이면 s30 이 나쁜 쪽 실현이었다. n1 이득을 철회한다.
    - 여섯 칸 모두 s31 − n1 > 0.1° 이면 DGX 안에서 이득이 기준선 두 실현 모두에 대해 선다.
    - 그 밖이면 보류한다.
  - 워크스테이션:
    - 여섯 칸 모두 ws_n1 − ws_ref < −0.1° 이면 재현이다.
    - 여섯 칸 모두 ≥ −0.1° 이면 재현이 안 된 것이다.
    - 섞이면 보류한다.
  - 종합:
    - DGX 가 철회이거나 워크스테이션이 비재현이면 n1 healthy 이득은 주장하지 않는다.
    - DGX 가 선다이고 워크스테이션이 재현이면 "기준선 두 실현·두 머신에서 선 이득"으로 적는다. n1 시드가 하나라는 한계는 같이 적는다.
  - yaw-rate OS 증가와 pair34 medium·hard 악화도 같은 짝으로 재현 여부를 본다. 문턱은 decision_floors(OS 10 pp, ss 0.1°)를 쓴다.

## Update 2026-09-14 (15시 30분 KST) — 재실현 두 런 커리큘럼 건강 대조 (500·1000 iter)

- TB 스칼라를 같은 iter 창으로 읽었다.
  - 대상: DORAEMON success_rate, mode, fault_severity 평균, ess_ratio.
  - 읽기 방법: `currpeek` 스크립트를 stdin 으로 넘겨 컨테이너는 `cwd=/root`, DGX 는 `~` 에서 돌렸다. r3a 트리에는 쓰지 않았다.
- 비교 기준은 이미 완주한 런의 같은 창이다.

    | 런 | 성공률 ~500 | ess_ratio 500 | mode 500·750·1000 | 성공률 ~1000 | 심각도 평균 ~1000 |
    |:---|:---|:---|:---|:---|:---|
    | dgx_ref s30 | 0.14 | 0.53 | −2·1·0 | 0.66 | 0.0121 |
    | ws ref_full s30 | 0.16 | 0.14 | −2·0·0 | 0.78 | 0.0115 |
    | dgx_n1 s30 | 0.006 | 0.62 | −2·−2·0 | 0.63 | 0.0100 |

- 워크스테이션 n1 (`trpo_r3a_n1_lagrangian_260914_142937`)
  - 520 iter: 성공률 0.0135, mode −2, ess_ratio 0.42. DGX n1 의 같은 창은 0.016, −2, 0.62.
  - 1005 iter(15시 28분): 성공률 0.65, mode 는 750 에서 −2, 1000 에서 0, 심각도 0.0089. mode 궤적이 DGX n1 과 같다.
  - 판정: 정상. 3.48 s/iter 이고, 19시 10분경 종료 예상은 그대로다.
- DGX 기준선 s31 (`trpo_dgx_ref_s31_260914_142436`)
  - 503 iter: 성공률 0.0235, mode −2, ess_ratio 0.18. 완주 런들의 같은 창 범위 안이다(성공률 0.006~0.16, ess_ratio 0.14~0.62).
  - s30 보다 성공률 기준으로 약 110 iter 늦다. 속도는 n1 두 런과 비슷하다.
  - 초반 속도는 같은 arm 안에서도 시드마다 이만큼 갈린다. 그래서 방법 차이의 근거로 쓰지 않고, 판정은 model_4999 채점으로 한다.
  - 1000 iter 기준(데이터 전 등록): 완주 세 런은 모두 1000 iter 에 mode 0 이다. s31 이 1000 iter 에서 mode ≤ −2 이고 심각도 < 0.05 이면 정지 서명으로 보고 진단한다. 16시경 도달한다.
- 15시 58분 추가, DGX 기준선 s31 1000 iter 판정: 정상.
  - 1004 iter: mode 는 500·750 에서 −2, 1000 에서 0. 성공률 0.58, 심각도 0.0109, entropy_after −49.03 → −47.43(분포 확장 시작).
  - 750 iter 의 ess_ratio 는 0.099 로 완주 세 런의 750 값(0.47~0.77)보다 낮았다. 1000 iter 에서 0.77 로 회복했다.
  - mode 궤적(−2·−2·0)은 dgx_n1 과 같다. 등록한 정지 서명에는 걸리지 않았다.
- 같은 창에서 워크스테이션 n1 1513 iter: mode 0 이 1000·1250·1500 에서 유지됐다. 성공률 0.77(dgx_n1 ~1500 은 0.83), 심각도 0.0118. 정상이다.
- 두 런 모두 커리큘럼이 열렸다. 감시는 종료까지 500 iter 마다 TB 스칼라 대조를 계속한다(커리큘럼 정지가 학습 중반에 온 사례: 09-04, 09-07). 채점은 각 런 종료 뒤 PLAN 14시 35분 절대로 한다. (18시 55분 정정: 처음에는 "다음 감시는 Traceback·체인 줄뿐"이라고 적었다.)
- 18시 55분 추가, 종료 전 커리큘럼 점검. 500 iter 알림마다 같은 창으로 대조했고, 두 런 모두 정지 서명은 없다.

    | 런 (짝) | iter | mode | 심각도 평균 (짝) | 비율 | 성공률 (짝) |
    |:---|:---|:---|:---|:---|:---|
    | ws n1 (dgx_n1) | 2512 | 0 | 0.0206 (0.0224) | 0.92 | 0.79 (0.86) |
    | ws n1 | 3011 | 0 | 0.0274 (0.0297) | 0.92 | 0.77 (0.86) |
    | ws n1 | 3511 | 0 | 0.0366 (0.0396) | 0.92 | 0.78 (0.84) |
    | ws n1 | 4006 | 0 | 0.0492 (0.0531) | 0.93 | 0.73 (0.82) |
    | ws n1 | 4506 | 0 | 0.0666 (0.0716) | 0.93 | 0.68 (0.77) |
    | dgx_ref_s31 (dgx_ref s30) | 2007 | 0 | 0.0191 (0.0212) | 0.90 | 0.82 (0.84) |
    | dgx_ref_s31 | 2503 | 0 | 0.0253 (0.0281) | 0.90 | 0.83 (0.83) |

  - 두 런 모두 심각도가 짝의 0.90~0.93 배로 일정하게 따라간다.
  - 성공률은 3000 iter 뒤 두 쌍 모두 내려간다. 심각도가 빨리 오르는 구간이다.
  - ws n1 성공률은 dgx_n1 보다 0.06~0.09 낮다. 학습 중 수치라 방법 판정에는 쓰지 않는다.

## Update 2026-09-14 (19시 25분 KST) — 워크스테이션 n1 완주, model_4999 채점 발사

- 학습 종료: 19:20:51, END rc=0 ok=1.
  - `.chain_ok`: seed 30, max_iterations 5000, num_envs 4096, machine=ksm-ubuntu-gpu0, pairs_with=trpo_r3a_ref_full_260912_145151.
  - model_4999.pt: md5 19e9b6a2982cae68eb1cb60c6170451e, 6187204 바이트.
  - 발사 뒤 r3a 두 트리(constrained-albc-r3a, marinelab-r3a)에 새로 생긴 파일은 0개다. `git --no-optional-locks status` 도 0줄이다.
- 채점 발사: 19:21:21, `exam_rerun_r3a.sh ws_n1_lagrangian 19e9b6a2…` (스크립트 md5 8c1ffb2d, pid 1075683).
  - 채점기는 exam_dgx_r3a.sh 와 같다: eval afa3c6b, ml 8cc84a5, anchor 762091d1, CORE 4, att 15°, 64 env, seed 42.
  - 출력은 `.hq/work/paper_ablation_r3a/exam_v3_rerun/ws_n1_lagrangian/<cfg>`, 로그는 같은 곳의 `exam.log`.
  - 19:23 에 healthy 셀이 GPU1 에서 돌고 있다(28 %, 2.3 GB). 4셀에 약 40분 걸린다.
- 발사 ssh 는 이번에도 돌아오지 않았다. DGX 와 같은 증상이고, 원격 `bash -c` 부모가 남아 있다. 채점 프로세스는 setsid·nohup 으로 떨어져 있어 영향이 없다.
- 끝나면 arm_compare 로 ws_n1 과 exam_v3/r3a_ref_full 을 비교하고, 14시 35분 절 판정 규칙의 워크스테이션 쪽을 적용한다.

## Update 2026-09-14 (20시 05분 KST) — 워크스테이션 n1 채점 4셀 판독: healthy 이득 비재현

- 채점: 19:21~19:58. 4셀 모두 rc 0·complete, BATCH END failed_cells=0.
  - 비교 대상 셀(exam_v3/r3a_ref_full)과 eval·ml·anchor·nenv 가 같다.
  - 비교 JSON: `.hq/work/paper_ablation_r3a/rerun_cmp/ws_cmp_<cfg>.json` (arm_compare, 앵커 ws_ref).
- **판정 칸**: att_norm ss_error, 단위 °, 차이는 n1 − 기준선.

    | 칸 | DGX 기준선 | DGX n1 | DGX 차이 | ws 기준선 | ws n1 | ws 차이 |
    |:---|:---|:---|:---|:---|:---|:---|
    | healthy soft | 0.738 | 0.529 | −0.208 | 0.573 | 0.787 | +0.214 |
    | healthy medium | 1.211 | 0.760 | −0.451 | 0.762 | 1.412 | +0.650 |
    | healthy_d1 soft | 0.722 | 0.489 | −0.232 | 0.539 | 0.639 | +0.100 |
    | healthy_d1 medium | 1.173 | 0.742 | −0.432 | 0.722 | 1.060 | +0.338 |
    | healthy_d2 soft | 0.759 | 0.521 | −0.238 | 0.574 | 0.725 | +0.151 |
    | healthy_d2 medium | 1.323 | 0.753 | −0.570 | 0.751 | 1.329 | +0.578 |

- **워크스테이션 판정: 비재현.** 여섯 칸 모두 ws_n1 − ws_ref ≥ −0.1° 다. 모두 양수이고, d1 soft 는 문턱과 같은 +0.100 이다.
- **종합 판정(14시 35분 규칙): n1 healthy soft·medium 이득은 주장하지 않는다.**
  - 규칙상 워크스테이션 비재현만으로 확정된다. DGX s31 결과로는 바뀌지 않는다.
  - 두 머신에서 차이의 부호가 반대이고 크기는 비슷하다.
  - 칸마다 좋은 쪽 값(soft 0.49~0.57, medium 0.74~0.76)은 dgx_n1 과 ws_ref 이고, 나쁜 쪽 값(soft 0.64~0.79, medium 1.06~1.41)은 dgx_ref 와 ws_n1 이다. (23시 정정: 처음에는 "arm 이 아니라 런 실현이 값을 가른다는 해석과 맞는다"고 적었다. DGX s31 이 s30 과 같은 쪽으로 나와 DGX 기준선 두 실현 차가 −0.01~+0.25° 뿐이므로 이 해석은 틀렸다. 23시 00분 절 참조.)
  - DGX s31 은 보조 근거로 채점한다. dgx_ref s30 이 나쁜 쪽 실현이었는지를 직접 본다. 22시 10분경 종료한다. (23시: s31 도 같은 쪽이라 이 가설은 기각됐다.)
- **yaw-rate 오버슈트 증가: 재현.**
  - ws n1 − ws_ref 가 4 설정 × 4 등급 16칸 모두 +16~33 pp 로 문턱 10 pp 를 넘는다.
  - DGX 는 +5~22 pp 였고, 일부 칸은 문턱 아래였다. 부호는 같다.
- **pair34 악화: hard 는 재현, medium 은 비재현.** (09-15 07시 50분 정정: ws n1 s31 − ws_ref 는 hard −1.023° 로 비재현, pair34 hard 발견은 강등됐다. 07시 50분 절)
  - hard: ws +1.859, DGX +1.735.
  - medium: ws −0.168, DGX +0.388.
- healthy hard(판정 밖): DGX −0.828, ws +1.946. 12시 10분 판독에서 체크포인트 간 부호가 뒤집혀 제외한 것과 같은 종류의 불안정이다.
- 생존율: ws 두 런 모두 none~medium 은 100 %, hard 는 96.9~100 %.
- 20시 40분 추가, DGX 기준선 s31 종료 전 커리큘럼 점검. 짝 dgx_ref s30 과 같은 창으로 봤고, 정지 서명은 없다.

    | iter | mode | 심각도 평균 (s30) | 비율 | 성공률 (s30) |
    |:---|:---|:---|:---|:---|
    | 3003 | 0 | 0.0338 (0.0373) | 0.90 | 0.79 (0.81) |
    | 3503 | 0 | 0.0453 (0.0498) | 0.91 | 0.76 (0.79) |
    | 4007 | 0 | 0.0611 (0.0669) | 0.91 | 0.70 (0.72) |

- 22시 10분경 s31 이 끝난 뒤의 순서(재개 지점):
  1. DGX 런 디렉터리에서 `.chain_ok` 를 확인한다. model_4999.pt, params/, .chain_ok 를 10시 복사(1548행, `tar -k` 파이프)와 같은 방식으로 컨테이너 `/workspace/constrained-albc/logs/rsl_rl/albc_trpo_teacher/paper_ablation_r3a_dgx/trpo_dgx_ref_s31_260914_142436/` 로 옮기고 md5 를 대조한다.
  2. 컨테이너에서 cwd=/root 로 `nohup setsid .hq/community/programs/paper-ablation-5000/exam_rerun_r3a.sh dgx_ref_s31 <md5>` 를 발사한다. GPU1, 4셀, 약 40분. 감시는 `exam_v3_rerun/exam.log` Monitor 다.
  3. 셀마다 `arm_compare.py --arm dgx_ref=exam_v3_dgx/dgx_ref/<cfg> --arm n1=exam_v3_dgx/dgx_n1_lagrangian/<cfg> --arm s31=exam_v3_rerun/dgx_ref_s31/<cfg> --axis att_norm --axis yaw --field ss_error --field os_env_mean` 를 돌려 `rerun_cmp/dgx_s31_cmp_<cfg>.json` 에 쓴다.
  4. 14시 35분 절의 DGX 규칙을 적용한다. 대상은 여섯 칸의 s31 − n1 이다.
     - 모두 |·| ≤ 0.1 이면 s30 이 나쁜 쪽 실현이었다.
     - 모두 > 0.1 이면 DGX 안에서는 이득이 선다.
     - 그 밖이면 보류다.
     - 종합 판정은 20시 05분 절에서 이미 확정됐다(주장 안 함). 이 결과는 보조 근거다.

## Update 2026-09-14 (22시 15분 KST) — DGX 기준선 s31 완주, 복사, model_4999 채점 발사

- 학습 종료: 22:10:58, END rc=0 ok=1. 학습 시간 27919.8 s.
  - `.chain_ok`: seed 31, machine=dgx-gb10, replicates=trpo_dgx_ref_260912_144855.
  - 종료 전 4500 iter 점검: mode 0, 심각도 0.0830(s30 0.0904, 비율 0.92), 성공률 0.65(s30 0.68~0.70). 정지 서명은 없다.
- 복사: DGX 에서 컨테이너 `logs/rsl_rl/albc_trpo_teacher/paper_ablation_r3a_dgx/trpo_dgx_ref_s31_260914_142436/` 로 model_4999.pt, params/, .chain_ok 를 `tar -xk` 파이프로 옮겼다.
  - model_4999.pt md5 54d20e44ca9f3d800cc08e32722b7614 로 DGX 원본과 같다.
- 채점 발사: 22:11:48, `exam_rerun_r3a.sh dgx_ref_s31 54d20e44…` (스크립트 md5 8c1ffb2d, pid 1080319).
  - 22:12 에 healthy 셀 평가 프로세스가 GPU1 에 올라왔다. 4셀에 약 40분 걸린다.
  - 비교 대상 셀 8개(exam_v3_dgx 의 dgx_ref·dgx_n1_lagrangian × CORE 4)는 모두 `.complete` 다.
- 발사 ssh 가 이번에는 바로 돌아왔다.
  - 19시 21분 발사는 `cd /root && nohup setsid … &` 형태였다. `&&` 목록 전체가 백그라운드 서브셸이 돼 ssh 채널을 쥐었다. 09-14 10시 채점 발사 때 확인한 함정이 재발한 것이다.
  - 이번에는 `cd /root; nohup setsid … > out 2>&1 < /dev/null &` 로 분리했다.
  - DGX 학습 발사의 `( nohup setsid bash … & )` 가 돌아오지 않은 원인은 여전히 확인하지 못했다.
- 끝나면 20시 40분 추가분의 3·4단계(arm_compare, DGX 보조 규칙)를 적용한다.

## Update 2026-09-14 (23시 00분 KST) — DGX 기준선 s31 채점 판독: DGX 안에서는 n1 이득이 선다, 종합은 여전히 주장 안 함 (09-15 10시 45분: n1 s31 에서는 D?, 보류)

- 채점: 22:11~22:49. 4셀 모두 rc 0·complete, BATCH END failed_cells=0.
  - 비교 JSON: `rerun_cmp/dgx_s31_cmp_<cfg>.json` (앵커 dgx_ref s30, 열 n1·s31).
- **DGX 판정 칸**: att_norm ss_error, 단위 °.

    | 칸 | s30 | s31 | n1 | s31 − n1 | s31 − s30 |
    |:---|:---|:---|:---|:---|:---|
    | healthy soft | 0.738 | 0.793 | 0.529 | +0.263 | +0.055 |
    | healthy medium | 1.211 | 1.459 | 0.760 | +0.699 | +0.248 |
    | healthy_d1 soft | 0.722 | 0.723 | 0.489 | +0.234 | +0.002 |
    | healthy_d1 medium | 1.173 | 1.352 | 0.742 | +0.610 | +0.179 |
    | healthy_d2 soft | 0.759 | 0.766 | 0.521 | +0.245 | +0.007 |
    | healthy_d2 medium | 1.323 | 1.314 | 0.753 | +0.561 | −0.009 |

- **DGX 판정(14시 35분 규칙): 여섯 칸 모두 s31 − n1 > 0.1° 다. DGX 안에서는 n1 이득이 기준선 두 실현 모두에 대해 선다.** (09-15 10시 45분 보충: n1 s31 에서는 medium 만 서고 soft 는 기준선과 같아 D? 다. 10시 45분 절)
- **종합 판정은 20시 05분 그대로다: 주장하지 않는다.** 규칙은 "DGX 선다 그리고 워크스테이션 재현"일 때만 이득을 적는데, 워크스테이션은 비재현이었다.
- **20시 해석 정정.** "arm 이 아니라 런 실현이 값을 가른다"와 "s30 이 나쁜 쪽 실현이었을 수 있다"는 틀렸다. 20시 절 해당 문장은 제자리에서 고쳤다.
  - DGX 기준선 두 실현은 서로 가깝다. 판정 여섯 칸의 s31 − s30 은 −0.01~+0.25° 이고, soft 는 0.06° 이하다.
  - DGX n1 은 두 기준선 모두보다 0.23~0.70° 좋다. 워크스테이션 n1 은 워크스테이션 기준선보다 0.10~0.65° 나쁘다.
  - 남는 설명은 둘이고, 지금 데이터로는 가르지 못한다.
    - (a) n1 실현 분산이 기준선보다 크다. n1 은 머신마다 한 실현뿐이다.
    - (b) 머신과 arm 의 상호작용.
  - 가르려면 같은 머신에서 n1 둘째 시드를 돌려야 한다. 발사는 운영자 결정이다.
- **같은 머신 기준선 재실현 바닥(참고, att ss 의 s31 − s30)**: healthy 계열 soft −0.01~+0.06°, medium −0.01~+0.25°, hard +0.51~+0.58°, pair34 −0.14~+0.88°. hard 와 pair34 에서는 0.1° 문턱이 실현 노이즈보다 작다.
- **yaw-rate OS 증가: 섰다.**
  - n1 − s31 은 16칸 모두 양수(+8.4~+20.1 pp)이고, 그중 14칸이 문턱 10 pp 를 넘는다. 넘지 못한 칸은 healthy_d1 none(+9.3)과 soft(+8.4)다.
  - s31 − s30 은 −7.1~+5.7 pp 다.
  - n1 − s30(12시)과 워크스테이션 쌍(20시)을 합치면 48/48 칸이 같은 부호다. 이 프로그램에서 가장 단단한 n1 발견이다. (09-15 10시 45분 정정: n1 s31 새 비교 48칸은 45/48 양수로 등록 규칙상 '부호 일관성 약화'다. 10시 45분 절)
- **pair34**
  - hard 악화는 세 비교 모두에서 선다: n1 − s31 +0.86°, n1 − s30 +1.74°, ws +1.86°. hard 생존율은 n1 95.3 %, 기준선 둘 98.4 %. (09-15 07시 50분 정정: 넷째 비교인 ws n1 s31 − ws_ref 가 −1.023° 라 등록 규칙대로 강등됐다. 07시 50분 절)
  - medium(n1 − s31 −0.27), soft(+0.25, ws −0.33), none(ws −1.07)은 비교마다 부호나 크기가 갈려 결론에서 뺀다.
- 생존율: s31 은 pair34 hard 98.4 % 말고 모두 100 %.

## Update 2026-09-15 (02시 25분 KST) — n1 시드 31 재실현 두 런 발사 (운영자 승인), 판정 규칙 등록, 남은 항목 정리

- 운영자 지시 원문(01시 25분경): "남은것도 진행해줘."
  - 23시 00분 절 뒤 보고의 "결정이 필요한 것: n1 을 한 번 더 학습할지"에 대한 답이다.
  - 같은 보고에 적은 나머지 항목(큐 기록, 미푸시 커밋, xyz-student 편집, `.stale_*`)도 포함한다. 아래 "정리" 참조.
- 질문은 하나다. DGX 에서만 선 n1 healthy soft·medium 이득이 n1 실현 분산인가, 머신×arm 상호작용인가. n1 은 머신마다 한 실현뿐이라 지금 데이터로는 가를 수 없다(23시 00분 절).
- 두 머신에 하나씩 동시에 돌린다. 두 머신이 모두 비어 있어 벽시계 비용이 없다. 한 머신만 돌리면 아래 해석 표의 한쪽 가지가 열린 채 남는다.

    | 런 | 머신 | 짝 | 답하는 것 |
    |:---|:---|:---|:---|
    | dgx_n1_lagrangian_s31 | DGX GB10 | dgx_ref s30·s31, dgx_n1 s30 | DGX n1 이득이 두 번째 n1 실현에서도 서나 |
    | ws_n1_lagrangian_s31 | ksm-ubuntu GPU0 | ws ref_full s30, ws_n1 s30 | 워크스테이션에서 n1 이 다시 기준선보다 나쁜가 |

- 발사 게이트 원장:
  - `omx wiki list --status needs-apply-before-retrain` 4건(finding/264·352·441·444)은 09-11 큐 기록의 acknowledged_gates 와 같은 집합이다.
  - needs-experiment 42건도 큐 기록의 open_leads 42건과 같은 집합이다.
  - 적용한 것은 없다. 표의 모든 행과 같은 pre-<item> 플랜트여야 비교가 된다(decision/197·209, 14시 35분 절과 같은 이유).
- **DGX** `~/xyz_launch/launch_dgx_n1_s31.sh` (md5 a1429d38)
  - `launch_dgx_ref_s31.sh`(ec0eb006) 사본이다. TAG, task, 설정 비교 대상 런만 바꿨다.
  - 앵커 3791441 + marinelab-xyz 8cc84a5, task Lagrangian-SimToReal, section5, group paper_ablation_r3a_dgx, 4096 env, 5000 it, `--seed 31`.
  - 02:09:29 START, 02:09:41 GATE ok.
    - 게이트: check_simtoreal section5, velocity_limit_sim 3.1, seed 31, cfgdiff env·agent 가 DGX n1 s30(`trpo_dgx_n1_lagrangian_260913_065642`)과 동일.
    - 런: `trpo_dgx_n1_lagrangian_s31_260915_020934`
    - 5.55 s/iter, ETA 7시간 36분(09시 45분경)
  - ssh 발사는 `cd …;` 뒤 단순 명령 하나로 보내고 도구 쪽에서 백그라운드로 돌렸다. 곧바로 돌아왔다.
- **ksm-ubuntu GPU0** 이 디렉터리 `launch_ws_n1_s31.sh` (md5 8ac3979f)
  - `launch_ws_n1_r3a.sh`(a43c79ce) 사본이다. SEED=31, TAG=n1_lagrangian_s31, 체인 로그 이름만 바꿨다.
    - TAG 를 바꾼 이유: 그대로 두면 skip 검사가 끝난 시드 30 런을 찾아 곧바로 종료한다.
  - 02:11:44 START, 02:11:57 GATE ok. 게이트는 DGX 와 같고, cfgdiff 가 DGX n1 s30 과 동일하다.
    - 런: `logs/rsl_rl/albc_ablation/paper_ablation_r3a/trpo_r3a_n1_lagrangian_s31_260915_021148`
    - 3.24 s/iter, ETA 4시간 38분(06시 50분경)
    - 발사 뒤 r3a 트리에 새로 생긴 파일 0개, git status 0.
- 감시:
  - Mac Monitor 하나(b1mubww6c)가 5분마다 두 머신을 본다. 500 iter 경계, 체인 END·FAIL·STALL 줄, 트레이너 프로세스 소멸을 알린다.
  - 1000 iter 무렵 커리큘럼 건강(TB 스칼라)을 같은 iter 창의 짝 런(각 머신의 n1 s30)과 대조한다.
- 채점:
  - 끝나면 `exam_rerun_r3a.sh` 에 추가한 행 `ws_n1_s31`, `dgx_n1_s31` 로 model_4999 만 채점한다.
    - 스크립트: md5 8c1ffb2d → 998fba7b. 두 행만 추가했고 백업은 `exam_rerun_r3a.sh.bak-260915`.
  - 채점기는 같다: eval afa3c6b·ml 8cc84a5·p3b 박스·CORE 4·att 15°·64 env·seed 42, GPU1 락.
  - DGX 체크포인트는 22시 15분 절과 같은 tar 파이프(`tar -xk`)로 컨테이너에 복사하고 md5 를 대조한다.
- **판정 규칙 (데이터 전 등록)**. 지표는 att_norm ss, 대상은 healthy·healthy_d1·healthy_d2 의 soft·medium 여섯 칸, 문턱은 0.1°.
  - DGX: n1_s31 − dgx_ref_s30 과 n1_s31 − dgx_ref_s31, 여섯 칸씩 열두 차.
    - 열두 차 모두 < −0.1° 이면 **D+**. DGX n1 이득이 두 번째 n1 실현에서도 선다.
    - 열두 차 모두 ≥ −0.1° 이면 **D−**. 서지 않는다.
    - 그 밖이면 **D?**.
  - 워크스테이션: ws_n1_s31 − ws_ref_s30, 여섯 차.
    - 여섯 차 모두 < −0.1° 이면 **W+**. 워크스테이션에서 이득이 나타난다.
    - 여섯 차 모두 ≥ −0.1° 이면 **W−**. 다시 나타나지 않는다.
    - 그 밖이면 **W?**.
  - 해석:

    | DGX | 워크스테이션 | 해석 | 논문 |
    |:---|:---|:---|:---|
    | D+ | W− | 네 n1 런이 머신별로 갈린다. 머신×arm 과 맞는다. 우연히 이렇게 갈릴 여지는 남는다 | 주장 안 함 유지. "이득은 머신 의존"으로 기술 |
    | D− | W+ | 좋은 실현과 나쁜 실현이 머신마다 섞인다. n1 실현 분산이 이득보다 크다 | 주장 안 함 유지. "실현 분산"으로 기술 |
    | D+ | W+ | 네 런 중 셋이 이득이고 ws_n1 s30 만 예외다 | 14시 35분 종합 규칙으로 이미 "주장 안 함"이다. 뒤집을지는 운영자 결정 |
    | D− | W− | 이득은 DGX n1 s30 한 런뿐이다 | 이득 없음으로 확정 |
    | D? 또는 W? | | 보류. 셀 단위로 기술 | 주장 안 함 유지 |

  - 한계: 워크스테이션 기준선은 한 실현(s30)뿐이다. 같은 머신·다른 시드 기준선 편차(soft ≤0.06°, medium ≤0.25°)는 DGX 에서만 쟀다.
  - 살아남은 n1 발견 두 가지도 같은 짝으로 다시 본다. 문턱은 decision_floors(OS 10 pp, ss 0.1°)다.
    - yaw-rate OS 증가: 새 비교 셋(DGX n1_s31 대 기준선 둘, ws n1_s31 대 ws 기준선)의 4 설정 × 4 레벨 48칸.
      - 48칸 모두 n1 − 기준선 > 0 이면 유지한다.
      - 한 칸이라도 < −10 pp 이면 강등한다.
      - 그 밖이면 "부호 일관성 약화"로 기술한다.
    - pair34 hard att ss 악화: 같은 세 비교가 모두 > +0.1° 이면 유지하고, 아니면 강등한다.
- 정리 (같은 지시의 나머지 항목):
  - 미푸시 커밋: 로컬 브랜치 넷을 origin 에 새 브랜치로 push 했다. main 은 건드리지 않았다.
    - `eval/grasp-step`(1a5981d), `eval/r3a-5000-v14`(afa3c6b, 14b5ee8 포함), `exp/depth-xy-exam`·`exp/depth-xy-ftc`(51f6a05)
    - 앵커 3791441 은 조상으로 같이 올라갔다.
    - 올리기 전에 확인한 것: 가장 큰 blob 141 KB, 비밀값 패턴 0건, dry-run 통과.
  - `/workspace/xyz-student` 미커밋 편집(09-13 08:25, 6파일 +67/−9, 테스트 1개):
    - 내용: depth_xy teacher 에서 tail 모드가 depth/XY task 채널을 IMU/heave 로 읽던 결함 수정, teacher 인코더 경계를 체크포인트 폭으로 만드는 수정.
    - `tests/test_student_depth_xy_layout.py` 6 passed 를 확인했다.
    - `exp/depth-xy-student` 에 커밋(3266595)하고 push 했다. depth-xy 는 포기한 프로그램이라 이 브랜치를 쓰는 런은 없다.
  - 큐 기록 `runs/r3a5000_n1_lagrangian_s30/pending-launch.json`: 고치지 않았다.
    - omx 스키마(v2)의 상태는 "pending approval" 하나뿐이고, omx 는 이 파일을 읽어 보고만 한다(`loop.py` read_pending_launch, `loop-status`).
    - r3a5000 기록 15개 중 13개가 발사된 행까지 모두 pending approval 그대로다. n6a·n6b 둘만 `withdrawn-launch.json` 이다.
    - 따라서 이 프로그램에서 큐 기록은 승인 산출물이고, 실제 발사는 PLAN 이 기록한다.
    - 이 arm 의 실제 런: DGX s30 `trpo_dgx_n1_lagrangian_260913_065642`, 워크스테이션 s30 `trpo_r3a_n1_lagrangian_260914_142937`, 이 절의 s31 두 런.
  - `exam_v3/classical_*/<cell>.stale_*` 20개(합 160 KB, 1387행): 컨테이너에 휴지통 도구가 없어 운영자에게 물었다. 답(02시 28분경)은 "묶어 보관 후 삭제"다. `exam_v3/_stale_20260913.tar`(40 KB, 항목 40개)로 묶고, 항목 수 대조와 `tar -d` 내용 비교가 통과한 뒤 원본 20개를 지웠다. 남은 폴더는 0개다. 복구는 exam_v3 에서 이 tar 를 풀면 된다.

## Update 2026-09-15 (03시 45분 KST) — n1 시드 31 두 런 커리큘럼 점검 (워크스테이션 500·1000·1500 iter, DGX 500·1000 iter)

- 02시 25분 절의 감시 항목 "1000 iter 무렵 커리큘럼 건강(TB 스칼라)을 같은 iter 창의 짝 런(각 머신의 n1 s30)과 대조한다"를 실행한 기록이다.
- 도구와 기준:
  - `currpeek_n1.py`(컨테이너 `/root`, DGX `~/xyz_launch`). TB 이벤트 파일을 읽기만 한다.
  - 정지 서명은 mode ≤ −2 가 3번 연속이면서 fault_severity < 0.05 인 경우다. 커리큘럼 전에는 정상 상태이므로 1000 iter 에서 판정한다.
- **워크스테이션**: s31 `trpo_r3a_n1_lagrangian_s31_260915_021148` 대 s30 `trpo_r3a_n1_lagrangian_260914_142937`. s30 값은 TB 기록 간격 때문에 괄호 안 iter 의 값이다.

    | 스칼라 | s31 | s30 |
    |:---|:---|:---|
    | mode (0·250·500·750·1000·1250·1500) | −3, −3, −2, 0, 0, 0, 0 | −3, −3, −2, −2, 0, 0, 0 |
    | success_rate (500 / 1000 / 1500) | 0.10 / 0.78 / 0.87 | 0.01 (520) / 0.65 (1040) / 0.76 (1560) |
    | fault_severity 평균 (1000 / 1500) | 0.0114 / 0.0150 | 0.0089 (1040) / 0.0118 (1560) |
    | ess_ratio (1000 / 1500) | 0.76 / 1.00 | 1.00 / 0.78 |
    | 평균 보상 (500 / 1000 / 1500) | 149 / 222 / 230 | 86 (520) / 209 (1040) / 221 (1560) |

  - 판독: s31 은 750 iter 에 커리큘럼이 열렸다. s30 은 1000 iter 에 열렸다. 그 뒤 두 런 모두 mode 0 을 유지하고 난이도가 오른다. 정지 서명은 없다.
- **DGX**: s31 `trpo_dgx_n1_lagrangian_s31_260915_020934` 대 s30 `trpo_dgx_n1_lagrangian_260913_065642`.

    | 스칼라 | s31 | s30 |
    |:---|:---|:---|
    | mode (0·250·500·750·1000) | −3, −3, −2, −2, 0 | −3, −3, −2, −2, 0 |
    | success_rate (약 500 / 약 1000) | 0.008 (504) / 0.666 (1016) | 0.036 (540) / 0.663 (1080) |
    | fault_severity 평균 (약 1000) | 0.0115 | 0.0113 |
    | ess_ratio (500 / 750 / 1000) | 0.53 / 0.46 / 0.78 | 0.62 / 0.47 / 0.76 |
    | 평균 보상 (약 1000) | 208 | 208 |

  - s31 은 672~756 iter 에서 한 번 내려갔다(success 0.35 → 0.11, 보상 148 → 123). 840 iter 부터 회복했고, 1000 iter 에서는 s30 과 같은 자리다.
  - 판독: s30 과 같은 1000 iter 에 커리큘럼이 열렸다. 정지 서명은 없다.
- 이 점검은 학습이 진행되는지만 본다. 성능 비교가 아니다. arm 판정은 02시 25분 절의 규칙대로 model_4999 채점으로만 한다.
- 다음 할 일:
  - DGX 1500 iter 점검(04시 30분경)은 감시 이벤트가 오면 한다.
  - 워크스테이션은 06시 50분경 끝난다. 끝나면 md5 를 확인하고 `exam_rerun_r3a.sh ws_n1_s31` 로 채점한다.
  - DGX 는 09시 45분경 끝난다. 끝나면 tar 로 복사하고 md5 를 대조한 뒤 `dgx_n1_s31` 로 채점한다.

## Update 2026-09-15 (07시 05분 KST) — 워크스테이션 n1 시드 31 완주, 채점 발사, 2000 iter 이후 커리큘럼 점검

- **완주**: `[2026-09-15T07:03:02+0900] END ws n1_lagrangian_s31 rc=0 ok=1`
  - 런: `trpo_r3a_n1_lagrangian_s31_260915_021148`
  - 체크포인트 101개. model_4999.pt 크기 6187204, md5 `4bd9bedd97f5c4cf4419f7a92d695c38`
  - `.chain_ok`: albc_head 3791441, marinelab_head 8cc84a5, seed 31, pairs_with `trpo_r3a_ref_full_260912_145151`, replicates `trpo_r3a_n1_lagrangian_260914_142937`
  - 소요 4시간 51분(평균 3.49 s/iter). 02시 25분 절의 ETA 06시 50분보다 13분 늦었다.
- **채점 발사**:
  - 07:05:20 `exam_rerun_r3a.sh ws_n1_s31 4bd9bedd…` (pid 1096162)
  - 출력: `.hq/work/paper_ablation_r3a/exam_rerun_ws_n1_s31.out`, 셀 `exam_v3_rerun/ws_n1_s31/<cfg>`
  - 발사 전 확인: GPU1 19 MiB, 도는 평가기 0개, 학습 프로세스 0개
  - 발사 뒤 확인: START 줄, `start ws_n1_s31/healthy`, healthy.log 기록 시작
  - 채점기는 02시 25분 절과 같다. 4셀이고 약 40분 걸린다.
- **커리큘럼 점검 (03시 45분 절 이후)**: 두 머신 모두 mode 0 을 유지했고 난이도가 계속 올랐다. 정지 서명은 없다.
  - 성공률 하락은 난이도 상승과 같은 구간에서 두 시드 모두에 나타났다.
  - s30 값은 TB 기록 간격 때문에 표의 iter 보다 최대 80 iter 뒤의 값이다.

    | 워크스테이션 iter | s31 severity / success | s30 severity / success |
    |:---|:---|:---|
    | 2000 | 0.0199 / 0.89 | 0.0156 / 0.79 |
    | 2500 | 0.0264 / 0.87 | 0.0206 / 0.78 |
    | 3000 | 0.0351 / 0.84 | 0.0274 / 0.76 |
    | 3500 | 0.0469 / 0.77 | 0.0366 / 0.73 |
    | 4000 | 0.0630 / 0.77 | 0.0492 / 0.70 |
    | 4500 | 0.0853 / 0.69 | 0.0666 / 0.66 |
    | 4999 (최종) | 0.0994 / 0.66, 보상 197 | 0.0777 / 0.645, 보상 200 |

    | DGX iter | s31 severity / success | s30 severity / success |
    |:---|:---|:---|
    | 1500 | 0.0152 / 0.74 | 0.0128 / 0.83 |
    | 2000 | 0.0201 / 0.74 | 0.0169 / 0.85 |
    | 2500 | 0.0266 / 0.77 | 0.0224 / 0.85 |
    | 3000 | 0.0354 / 0.78 | 0.0297 / 0.83 |

  - 워크스테이션 s31 은 끝날 때 학습 분포 난이도가 s30 보다 높았다(0.099 대 0.078).
    - 이것은 학습 상태의 차이이지 성능 차이가 아니다.
    - 채점은 두 런 모두 같은 p3b DORAEMON 박스에서 하므로 비교 분포는 같다.
- 다음 할 일:
  - 채점 종료는 Mac 백그라운드 루프가 감시한다. exam.log 에서 BATCH END, FATAL, FIRST CELL FAILED 줄이 나오거나 pid 가 사라지면 알린다.
  - 채점이 끝나면 워크스테이션 W± 판정을 먼저 적는다. 규칙은 02시 25분 절 그대로다.
  - DGX 는 09시 45분경 끝난다. 끝나면 tar 로 복사하고 md5 를 대조한 뒤 `dgx_n1_s31` 로 채점하고, D± 판정과 종합 해석을 적는다.

## Update 2026-09-15 (07시 50분 KST) — 워크스테이션 n1 시드 31 채점 판독: W−, yaw OS 16/16 양수, pair34 hard 발견 강등

- 채점: 07:05:20~07:42:52. 4셀 모두 rc 0·complete, `BATCH END failed_cells=0`.
  - 채점기 동일성: ws_ref(`exam_v3/r3a_ref_full`), ws_n1 s30, ws_n1 s31 셀의 RUN_CONDITIONS 가 eval afa3c6b, ml 8cc84a5, anchor 762091d1, nenv 64 로 같다.
  - 비교 JSON: `.hq/work/paper_ablation_r3a/rerun_cmp/ws_s31_cmp_<cfg>.json`
    - arm_compare, 앵커 ws_ref, arm ws_n1·ws_n1_s31
    - 축 att_norm·yaw, 필드 ss_error·os_env_mean
- **W 판정 칸**: att_norm ss_error, 단위 °.

    | 칸 | ws_ref | n1 s30 | n1 s31 | s31 − ref | s30 − ref |
    |:---|:---|:---|:---|:---|:---|
    | healthy soft | 0.573 | 0.787 | 0.561 | −0.012 | +0.214 |
    | healthy medium | 0.762 | 1.412 | 0.733 | −0.029 | +0.650 |
    | healthy_d1 soft | 0.539 | 0.639 | 0.536 | −0.003 | +0.100 |
    | healthy_d1 medium | 0.722 | 1.060 | 0.668 | −0.055 | +0.338 |
    | healthy_d2 soft | 0.574 | 0.725 | 0.563 | −0.011 | +0.151 |
    | healthy_d2 medium | 0.751 | 1.329 | 0.731 | −0.020 | +0.578 |

- **W−**. 여섯 차가 모두 ≥ −0.1° 다(−0.055 ~ −0.003).
  - s31 은 여섯 칸 모두 기준선과 0.06° 안에 있다. 두 번째 실현에서 워크스테이션 n1 은 이득도 손실도 없다.
  - 20시 05분 절의 s30 악화(+0.10 ~ +0.65°)는 s31 에서 재현되지 않았다. 그 악화는 s30 한 실현의 속성으로 읽는다.
  - 워크스테이션 n1 두 실현의 차(s30 − s31)는 soft 0.10~0.23°, medium 0.39~0.68° 다.
    - DGX 기준선 두 실현의 차(soft ≤ 0.06°, medium ≤ 0.25°, 23시 00분 절)보다 크다.
    - 머신 하나·arm 하나의 두 실현이라 일반화하지 않는다.
  - 해석 표에서 남은 칸은 D+W−, D−W−, D?W− 셋이다. D+W+·D−W+ 칸은 닫혔다.
    - D+W−: 머신×arm. "이득은 머신 의존"으로 기술한다.
    - D−W−: 이득 없음 확정.
    - D?W−: 보류.
    - 셋 모두 논문은 "주장 안 함"을 유지한다.
- **yaw-rate OS 증가 (워크스테이션 16칸)**: s31 − ws_ref 가 16칸 모두 양수다(+4.9 ~ +36.1 pp). −10 pp 미만은 0칸이다. 단위 pp.

    | 설정 | none | soft | medium | hard |
    |:---|:---|:---|:---|:---|
    | healthy | +22.2 | +25.4 | +24.5 | +28.9 |
    | pair34 | +4.9 | +9.0 | +11.5 | +19.8 |
    | healthy_d1 | +18.3 | +20.2 | +21.3 | +28.1 |
    | healthy_d2 | +26.0 | +28.0 | +28.9 | +36.1 |

  - 10 pp 문턱 아래는 pair34 none·soft 두 칸이다. 등록 규칙은 부호만 보므로 유지 조건에는 걸리지 않는다.
  - 48칸 판정은 DGX 32칸(n1_s31 대 기준선 둘)이 나온 뒤에 한다.
- **pair34 hard att ss 악화: 강등.**
  - 등록 규칙은 세 비교가 모두 > +0.1° 여야 유지한다.
  - ws n1_s31 − ws_ref 가 −1.023° 다(ref 7.448, s31 6.426). DGX 두 비교와 무관하게 강등이 확정된다.
  - pair34 는 시드마다 레벨별 부호가 뒤집힌다. 단위 °.

    | pair34 att ss | ws_ref | n1 s30 | n1 s31 | s31 − ref | s30 − ref |
    |:---|:---|:---|:---|:---|:---|
    | none | 2.340 | 1.275 | 4.091 | +1.751 | −1.065 |
    | soft | 1.885 | 1.559 | 3.186 | +1.301 | −0.326 |
    | medium | 2.445 | 2.277 | 3.561 | +1.116 | −0.168 |
    | hard | 7.448 | 9.307 | 6.426 | −1.023 | +1.859 |

  - 같은 머신 기준선 재실현 바닥은 pair34 에서 −0.14~+0.88° 였다(23시 00분 절).
  - pair34 att ss 는 n1 실현에 따라 부호가 바뀐다. arm 효과로 기술하지 않는다.
- 생존율: 세 런 모두 none~medium 100 %, hard 96.9~100 %.
- 다음 할 일:
  - DGX 는 09시 45분경 끝난다. 끝나면 tar 로 복사하고 md5 를 대조한 뒤 `dgx_n1_s31` 로 채점한다.
  - 채점 뒤 D± 판정, yaw OS 48칸 판정, 종합 해석을 적는다.
  - pair34 hard 는 이미 강등됐다. DGX 두 비교는 기술만 한다.

## Update 2026-09-15 (10시 45분 KST) — DGX n1 시드 31 완주·채점 판독: D? → D?W− 보류(주장 안 함 유지), yaw OS 45/48 양수로 부호 일관성 약화

- DGX 완주: 09:54:56 END rc=0 ok=1. START 02:09:29, 학습 시간 27904.5 s(7시간 45분, 평균 5.58 s/iter). 08시 48분 로그 ETA(09시 53분)보다 2분 늦었다.
  - model_4999 md5 `6d3c9608e2438efe029d3f05be5eb4b4`, 체크포인트 101개.
  - `.chain_ok`: albc_head 3791441, marinelab_head 8cc84a5, seed 31, machine dgx-gb10, replicates `trpo_dgx_n1_lagrangian_260913_065642`.
- 복사: tar 로 model_4999.pt, params, .chain_ok 를 컨테이너 `logs/rsl_rl/albc_ablation/paper_ablation_r3a_dgx/trpo_dgx_n1_lagrangian_s31_260915_020934/` 에 옮겼다. 컨테이너 쪽 md5 가 DGX 와 같다.
- 채점 발사: 09:57:05 `exam_rerun_r3a.sh dgx_n1_s31 6d3c9608…` (pid 1101293, 스크립트 md5 998fba7b).
  - 발사 전: GPU1 19 MiB, `/root/gpu1.lock` 비어 있음, 도는 평가기 0개.
  - 발사 뒤: START 줄의 ckpt·md5·eval afa3c6b·ml 8cc84a5·anchor 762091d1 확인, healthy 셀 진행, GPU1 2309 MiB.
- 커리큘럼 (TB 스칼라, DGX n1 두 실현): 정지 서명 없음.

    | DGX n1 | mode 0 개방 | severity 4160 | severity 4999 | success 4999 |
    |:---|:---|:---|:---|:---|
    | s31 | 1000 iter | 0.0636 | 0.1002 | 0.638 |
    | s30 | 1000 iter | 0.0531 | 0.0716 | 0.764 |

  - 두 실현 모두 500 iter 에 mode −2, 1000 iter 에 0 이고 끝까지 0 이다.
  - s31 최종 severity 는 ws s31(0.0994)과 거의 같다.
- 채점: 09:57:05~10:34:37. 4셀 모두 rc 0·complete, `BATCH END failed_cells=0`. 4셀 RUN_CONDITIONS 가 anchor 762091d1, nenv 64 다.
  - 비교 JSON: `.hq/work/paper_ablation_r3a/rerun_cmp/dgx_n1s31_cmp_<cfg>.json`
    - arm_compare, 앵커 ref30(`exam_v3_dgx/dgx_ref`), arm ref31(`exam_v3_rerun/dgx_ref_s31`)·n1s30(`exam_v3_dgx/dgx_n1_lagrangian`)·n1s31(`exam_v3_rerun/dgx_n1_s31`)
    - 축 att_norm·yaw, 필드 ss_error·os_env_mean
  - 판정 스크립트는 세션 scratch `dgx_s31_judge.py` 다. 채점 전에 s30 셀을 s31 자리에 넣어 돌려 23시 00분 절 값을 재현했다.
- **D 판정 칸**: att_norm ss_error, 단위 °.

    | 칸 | ref30 | ref31 | n1 s30 | n1 s31 | s31 − ref30 | s31 − ref31 | s31 − s30 |
    |:---|:---|:---|:---|:---|:---|:---|:---|
    | healthy soft | 0.738 | 0.793 | 0.529 | 0.701 | −0.036 | −0.091 | +0.172 |
    | healthy medium | 1.211 | 1.459 | 0.760 | 0.991 | −0.220 | −0.468 | +0.231 |
    | healthy_d1 soft | 0.722 | 0.723 | 0.489 | 0.674 | −0.047 | −0.049 | +0.185 |
    | healthy_d1 medium | 1.173 | 1.352 | 0.742 | 0.945 | −0.229 | −0.407 | +0.203 |
    | healthy_d2 soft | 0.759 | 0.766 | 0.521 | 0.729 | −0.030 | −0.037 | +0.208 |
    | healthy_d2 medium | 1.323 | 1.314 | 0.753 | 0.950 | −0.373 | −0.364 | +0.197 |

- **D?**. 열두 차가 모두 음수지만 −0.1° 미만은 medium 여섯 개(−0.468 ~ −0.220)뿐이고, soft 여섯 개는 −0.091 ~ −0.030 이다.
  - 02시 25분 절 해석표의 "D? 또는 W?" 행은 보류, 셀 단위로 기술, 주장 안 함 유지다. 워크스테이션 W−(07시 50분 절)와 합쳐 **D?W−** 다.
  - 셀 단위 기술:
    - soft: DGX n1 s30 은 ref30 대비 −0.21~−0.24° 였고, s31 은 −0.03~−0.05° 로 기준선과 같다. DGX 에서도 soft 이득은 n1 실현 하나에만 있다.
    - medium: DGX n1 두 실현 모두 기준선 두 실현보다 0.22° 이상 낮다(s30 −0.43~−0.57°, s31 −0.22~−0.47°). 워크스테이션 n1 두 실현은 medium 에서 기준선보다 낮지 않다(s30 +0.34~+0.65°, s31 −0.06~−0.02°).
    - medium 칸만 떼면 D+W− 모양이다. 등록 규칙은 열두 차 전부를 요구했으므로 판정은 D? 로 두고, 사후에 medium 만 골라 머신×arm 으로 읽지 않는다.
  - DGX n1 두 실현 차(s31 − s30)는 여섯 칸 모두 +0.17~+0.23° 다.
    - DGX 기준선 두 실현 차(ref31 − ref30)는 soft +0.001~+0.055°, medium −0.009~+0.248° 다. soft 에서 n1 쪽 차가 3배 이상 크고 medium 에서는 같은 크기다.
    - 워크스테이션 n1 두 실현 차(soft 0.10~0.23°, medium 0.39~0.68°, 07시 50분 절)와 합치면, 두 머신 모두 n1 의 soft 실현 간 차가 기준선보다 크다.
- **yaw-rate OS 증가 (48칸)**: 칸은 `n1_s31 − ref30 / n1_s31 − ref31`, 단위 pp. 워크스테이션 16칸은 07시 50분 절 표.

    | DGX 설정 | none | soft | medium | hard |
    |:---|:---|:---|:---|:---|
    | healthy | +3.9 / +7.5 | +5.3 / +7.5 | +8.2 / +9.6 | +10.2 / +10.5 |
    | pair34 | −2.3 / +2.6 | −2.7 / +2.1 | −3.9 / +3.2 | +19.8 / +21.8 |
    | healthy_d1 | +7.9 / +7.0 | +9.9 / +6.5 | +10.3 / +8.3 | +20.6 / +14.9 |
    | healthy_d2 | +8.4 / +8.5 | +8.6 / +7.2 | +12.6 / +10.3 | +20.9 / +15.2 |

  - 48칸 중 양수 45칸, −10 pp 미만 0칸, 최소 −3.9 pp, 최대 +36.1 pp 다. 등록 규칙상 **"부호 일관성 약화"** 다. 23시 00분 절의 "48/48 칸이 같은 부호, 가장 단단한 n1 발견"을 대체한다.
  - 음수 세 칸은 모두 DGX pair34 none·soft·medium 의 ref30 비교다.
    - 같은 칸의 ref31 비교는 +2.1~+3.2 pp 다.
    - 두 기준선 실현이 이 세 칸에서 서로 4.8~7.1 pp 차이 난다. 세 칸의 n1 차이는 기준선 실현 차 안에 있다.
  - pair34 none~medium 9칸(DGX 6, 워크스테이션 3)을 빼면 39칸(healthy 계열 36칸, pair34 hard 3칸)이 모두 양수이고 DGX 최소는 +3.9 pp 다. pair34 none~medium 9칸은 −3.9~+11.5 pp 로 0 을 넘나든다.
  - DGX n1 s31 의 ref30 대비 폭(−3.9~+20.9 pp)은 s30 의 16칸 범위(+5.3~+22.5 pp, 09-14 12시 10분 절)보다 아래로 넓다.
- **pair34 att ss (기술만)**: hard 는 07시 50분 절에서 강등됐다. 단위 °.

    | pair34 | ref30 | ref31 | n1 s30 | n1 s31 | s31 − ref30 | s31 − ref31 | s30 − ref30 |
    |:---|:---|:---|:---|:---|:---|:---|:---|
    | none | 2.007 | 1.864 | 3.039 | 2.263 | +0.256 | +0.399 | +1.032 |
    | soft | 1.823 | 2.324 | 2.569 | 2.197 | +0.375 | −0.127 | +0.746 |
    | medium | 2.895 | 3.556 | 3.283 | 2.671 | −0.224 | −0.885 | +0.388 |
    | hard | 6.753 | 7.632 | 8.488 | 8.554 | +1.802 | +0.923 | +1.735 |

  - hard: n1 네 실현 중 셋(DGX s30·s31, ws s30)이 기준선보다 나쁘고 ws s31 만 낫다(−1.02°). 기준선 두 실현 차가 +0.88° 라 0.1° 문턱은 노이즈보다 작다. 강등은 그대로다.
  - none~medium 은 비교마다 부호가 갈린다.
- 생존율: n1 s31 none~medium 100 %, hard 96.9~98.4 %.
- **n1 arm 종합 (등록 규칙 결과)**:

    | 발견 | 판정 | 논문 |
    |:---|:---|:---|
    | healthy 계열 soft·medium att ss 이득 | D?W− 보류 | 주장 안 함 유지 |
    | yaw-rate OS 증가 | 45/48 양수, 부호 일관성 약화 | "부호 일관성 약화"로 기술. healthy 계열·pair34 hard 는 양수, pair34 none~medium 은 0 근처 |
    | pair34 hard att ss 악화 | 강등 (07시 50분 절) | arm 효과로 기술하지 않는다 |

- 제자리 주석: 23시 00분 절 제목(1903행)과 DGX 판정 줄(1918행)에 s31 결과를, 1931행 "48/48" 에 대체 사실을 괄호로 달았다. 백업 `/root/PLAN.md.bak-0915-1045`.
- 백로그 대조: `omx wiki list --status needs-experiment` 42건 중 n1 판정에 걸리는 항목은 없다. `needs-apply-before-retrain` 4건(finding/264·352·441·444)은 이 판정과 무관하며 상태를 바꾸지 않았다.
- 다음 할 일:
  - n1 판정 라인(09-14 14시 35분 등록, 09-15 02시 25분 재등록)은 이 절로 닫힌다. 02시 25분 절의 나머지 정리 항목은 그 절에서 모두 끝났다.
  - 이 세션이 띄운 학습·채점 잡은 모두 끝났다. DGX 와 GPU1 에 도는 잡이 없다.
  - DGX 보류를 풀려면 DGX n1 실현이 더 필요하다. 발사는 운영자 결정이고, 등록 해석표상 어느 결과가 나와도 논문의 "주장 안 함"은 바뀌지 않는다.
