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
