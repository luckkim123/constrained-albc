# Program: retrain-simtoreal-2026-09 — teacher retrain on the REAL actuator set (m3 dead, m4 excluded) + latency DR

**Status: PENDING USER APPROVAL — this document authorizes NO launch.**

> ## REVISION PENDING — two user corrections, 2026-09-02 ~23:10 KST (read before anything below)
>
> The user rejected the design axis of this draft in two places. Phase 1's `fault.thruster_fixed_health=[1,1,1,0,0,1]`
> row, the parts of `[DECISION-REQUIRED: fault-config]` that treat a fixed dead set as the training plant, and the
> "REAL actuator set" framing in the title are **superseded**; the rest of the document (gates, held knobs, latency,
> budget, evaluation rules) stands. The corrections, verbatim:
>
> > 근데 내가 학습 내내 죽이는 방식 말고 FTC를 좀 강화하라는 식으로 하라고 누차례 말하지 않았나? 논문 쓸때 그럼 로봇
> > 고장났다고 말할꺼야? 리뷰어가 고장난거 왜 안고치냐고 말하면? 구구절절 못고치는 이유 말하게?
>
> > 그리고 실제 실험 해보니깐 TAM에서 수직 스러스터가 pitch 에 영향을 미치는게 좀 과대평가되어있었다고 말한건?
>
> **Correction 1 — the training axis is FAULT-TOLERANT CONTROL, not a plant with the thrusters glued off.** Faults stay a
> DISTRIBUTION the policy must absorb: strengthen the fault DR so single AND double actuator loss (including complete
> death and the vertical channels) is sampled at a rate the policy can learn from, keep the policy fault-agnostic or give
> only the critic/encoder the privileged health (student infers it from history), and treat the real robot's m3-dead /
> m4-excluded state as ONE test case of that distribution. Fixed-health vectors remain EVAL instruments (the fault
> exam matrix: healthy, each single loss, the real pair, other pairs) — never a training plant. Paper framing follows:
> "fault-tolerant attitude control under actuator loss, validated on hardware with real failures", not "the robot is
> broken". The record already held this direction (`finding/137` §7 (3): 운영자 제안 = 적응하는 정책) and the draft
> ignored it. Grounds to carry into the redesign: today's exposure is 1/30,000 per episode for two dead channels
> (`fault_fail_prob 0.1 × severity`, `health U(0,0.5)`); E-ftc1 showed a faster severity SCHEDULE made fault rejection
> worse (2.9–5.5×), so the lever is the sampler SHAPE (k∈{0,1,2} failures over channel pairs, explicit dead mass),
> not the schedule; FaultDR-AB rejected privileged fault obs on n=1 (seed floor 56 %), so that rejection is weak.
>
> **Correction 2 — the vertical thrusters' pitch authority in the TAM is OVER-estimated, per the tank.** The live TAM
> gives m0/m3 `My = ±0.145` (14.5 N·m at 50 N), which is why the incumbent learned pitch from thrust. The operator's
> observation (finding/137 §7 (2)) plus the artifact's own OPEN note (`deployed_tam.json.open.sim_tam_is_rotated`,
> `config.py` "vertical Fz/My row OPEN") say that number is an unmeasured assumption and too large. A retrain that keeps
> 0.145 re-teaches the wrong actuator. Options to argue in the redesign: (a) DR band on the vertical moment arm
> (a sim-fidelity axis, like the adopted `max_thrust_scale` band — `decision/197`'s "TAM moment-arm band" item),
> (b) nominal correction from a measurement (item C; m0/m3 motor identity G0-G decides whether the row exists at all),
> (c) both. Any of them is a plant-fidelity change, not a rule, and it must be listed in the launch ack.
>
> Next session: rewrite Phase 1, Tier 2, Phase 2 arms (S1 = strengthened fault DR; S1b = + privileged fault obs;
> S1c = + vertical moment-arm band), Phase 4 exam matrix, Predicted outcome, and decisions 2 / 10 / 11 accordingly.
> Nothing below has been launched.

Opened 2026-09-02 (evening) after `finding/137` (vault) located the T4 pitch failure in the policy's
learned actuator assignment, not in the robot. Supersedes nothing: `teacher-final-replicate` (closed
2026-08-11, incumbent kept) and `simtoreal-thrusters-live` (vault, robot side) remain the record this
program argues against. Store boundary (vault `project_albc_omx_split`): this program changes the
POLICY, so it lives here (marinelab); robot-side steps are registered in the vault PLAN by pointer only.

## Objective

User, verbatim (2026-09-02, Mac session):

> # 목표:
> - ksm-nas 에서 로봇 실험을 위한 재학습 수행.
> - ksm-ubuntu의 marinelab에서 5000 iter로 학습하여 여러 실험 진행.
>   - 해당 실험은 반드시 해야하는 것은 아니며, ksm-nas에서 로봇 실험을 진행하기 전에 혹시 필요할 경우 수행.
> # 작업 과정:
> 1. ksm_obsidian vault 및 marinelab에 있는 커뮤니티 및 여러 실험 결과들, 문서 등을 전수 조사하여 정독.
> 2. 정독한 내용을 기반으로 sim-to-real gap을 줄이기 위한 실험 계획 혹은 재학습 계획 수립.
>   - 필요한 경우 인터넷 조사 수행.
> 3. 계획 문서를 사용자에게 이해하기 쉽게 정리하여 설명.
> 4. compact 후 계획대로 진행.
> # 제약 조건:
> 1. 학습의 성능 평가에 맞지 않게 hard constraint 등으로 rule-based 처럼 만들 지 말것.
>   - 교묘하게 hard constraint를 넣는 것도 불가.
>   - 반드시 필요한, 로봇 파손 위험을 방지하는 수준에서만 수행.
> 2. 기존 실험 결과를 100퍼센트 신뢰하지 말고, 다시한번 검토할 필요가 있음.
>   - 예를들어 control_hz가 10일때 제일 잘되었다고 해서 반드시 control_hz를 10으로 하기 보다, 다시 한번 검토 후 수행.
> 3. 모든 의사 결정에는 명확한 근거가 있어야함.
>   - 근거가 없을 경우 다시 로봇 실험을 하는 것도 허용.
>   - 다만, 이 경우 로봇 실험을 제외한 것들은 모두 다 할 것.
> 4. 작업을 codex, agy의 장단점에 맞게 분배하여 진행.
> 5. 커뮤니티 활성화.
> 6. 계획 문서 수립 완료 후 luckkim123@postech.ac.kr로 메일 보낼것.
> (추가) 다른 머신에 작업을 맡길 경우 orca의 orchestration 기능 활용.

Every held-or-changed knob below argues against THIS text. The one place this program departs from
the record is that the record says "재학습은 여전히 정당화되지 않는다 — A 가 먼저다" (`finding/137` §11); the
user's objective makes retraining the goal, so item A becomes Phase 0's first gate rather than a
precondition for planning.

## Diagnosis — what the record establishes

**D-1. The pitch failure is a deploy-configuration gap, and thrusters cannot restore it.**
The incumbent teacher (`teacher_iter_budget/trpo_iterbudget_s30_260805_012813/model_9998.pt`,
git `598db899` on `exp/koopman-marine-obs`, dirty tree = registry files only) learned pitch from the
vertical thrusters (My authority 2×0.145 m×50 N = 14.5 N·m) and roll from the arm (16.62 N×0.13 m ≈
2.2 N·m vs horizontal-thruster roll 1.4 N·m). On the robot `thruster_scale=0` removed pitch's
actuator: T4 roll +14.80° (98.7 %), pitch +0.14° (0.9 %), θ2 span 5–7° on pitch steps vs 23–25° on
roll. With m3 DEAD the live TAM's (Fz, My) rows collapse to rank 1 on m0, and the mixer's
`reallocate()` keeps Fz and drops My — so even with thrust ON, pitch is the arm's job.
[EVIDENCE: vault `finding/137` §2–§5; live TAM printed in the codex inventory §3; `deployed_tam.json`]

**D-2. The incumbent never trained for that plant.** Fault DR was ON (`fault.enable: true`,
`thruster_fail_prob 0.1`, health U(0, 0.5), severity under DORAEMON, `use_privileged_fault_obs
false`) — a single effectively-dead channel ≈0.5 %/episode, two simultaneously 1/30 000. The
`fault_severity` dim reached Beta(1,1) only after iteration 7748, so even the fully-open box exposes
the policy to the real (m3+m4) pattern in ~0.003 % of episodes. `thruster_fixed_health` exists and IS
honored on the training reset path (`_reset_idx → _reset_physics → sample_thruster_health →
set_thruster_health`), so training on the real actuator set is a config change, not code.
[EVIDENCE: `deployed_env.yaml:fault`, `iter_budget/README.md` Part 1, vault `notes/2026-08-24-fault-tolerant-allocation-analysis.md` §5, codex inventory §4]

**D-3. Latency is the one apply-before-retrain item.** The incumbent trained `control_delay_steps
(0,0)`; the robot's observations were 1.2 (attitude) to 4.7 (joints) control steps stale in August.
Board fixes since then: IMU 100 Hz (`80ab138`), joints 50 Hz (`_loop_hz:=50`, verified 08-26), so the
remaining staleness is ≈1 step. `(0,3)` was trained (E1-latdr) and stalled DORAEMON (return 197 vs lb
250, success 0.09). Range `(0,1)` was user-approved 2026-08-14 for the next from-scratch round, with
a PAIRED (same seed, with/without) ~500-iteration cost gate because two seeds of the incumbent config
already straddle alpha (R30 0.469 / R31 0.536 vs 0.5). Z4 sweep on a delay-free policy: att ss_error
0.630 → 1.474 → 3.239 → 5.604° for 0/1/2/3 injected steps.
[EVIDENCE: `posts/finding/264` incl. 08-14/08-15 updates; `posts/finding/266`; vault `finding/065` §1]

**D-4. The attitude plant does NOT need retuning.** Net buoyancy 16.62 N vs sim 17.11 N (3 %,
percentile 46 of the training distribution); restoring stiffness K 7.76 vs 6.10 N·m/rad is percentile
81 under the `cog/cob_offset_z` DR; curvature saturates the same direction. Roll DC gain 148 °/m
(3 % scatter). [EVIDENCE: vault `finding/136`, `notes/2026-08-25-night-reanalysis.md` §0-5]

**D-5. Actuation deadband is handled on the DEPLOYMENT side, consistently.** Sim `thrust_deadband
0.075` is inert (`enable_thrust_curve=False` → identity); the board mixer's `undeadband()` inverts the
measured ESC deadband (45 counts of 300, D=0.15; real value 0.16, asymmetric −0.167/+0.150). The
policy therefore sees an approximately linear actuator in both worlds. The remaining unmodeled term
is the thrust-curve SHAPE (quadratic vs linear) with zero DR coverage — blocked on a T200 bench that
does not exist (decision/209 item 3). Literature (see §Traceability) finds no work that both models
deadband in sim and inverts it at deployment; it recommends picking one lane. This program keeps the
deployment lane. [EVIDENCE: `marinelab-core/thruster.py:_thrust_command`, `posts/decision/209`, vault `finding/135` §7]

**D-6. "10 Hz was best" is n=1 and confounded.** The only stable joint-only RL runs were 10 Hz
(41.8 s on 08-13; 195 s on 08-26, tripped). 50 Hz runs were short and predate the IMU 100 Hz /
joint 50 Hz fixes. Loop-rate mismatch was excluded as the oscillation cause (`finding/065`). No
literature compares "decimate a 50 Hz policy" vs "retrain at 10 Hz"; the one measured ablation
(Gangapurwala et al. 2023, ANYmal) shows lower training rates tolerate more latency (50 Hz → 50 ms,
10 Hz → 90 ms) without losing success, but also that resampling a component at a mismatched rate
silently broke it. Conclusion: the rate question needs a controlled measurement, not a default.
[EVIDENCE: vault `resume-brief` §3; `finding/064`·`065`; §Traceability R4]

**D-7. Budget, machines, seeds.** 4096 envs: RTX 4070 ≈ 3.3–3.6 s/iter (11.3 GB), 5000 iter ≈ 5 h,
10000 ≈ 9.6 h; DGX GB10 ≈ 5.56 s/iter at 4096 (10000 ≈ 15.4 h), 18.1 s/iter at 16384, 34.7 s/iter
at 32768 (83 GB of 121 GB). DORAEMON saturates 21/21 dims at ≈7748 iterations (step_interval 250 ×
~30 expansions) regardless of env count; 5000 iterations leaves 0/21 saturated, and 5000→10000 cut
hard-DR att_norm ss_error 1.012→0.660 and its dispersion 2.378→0.652. Seed floor at `none`: 56 %
peak-to-peak on roll ss_error across 3 seeds (corrected plant) → single-seed verdicts are
undecidable; paired-seed design is mandatory. The standing "machine isolation" caveat (+109 %
same-config same-seed cross-machine on roll ss_error) rests on ONE pair, which is inside that seed
floor (a same-seed run on a different GPU is not a paired run) — see `[DECISION-REQUIRED: dgx-trained-deployable]`.
[EVIDENCE: `iter_budget/README.md`; `posts/finding/001`; `posts/decision/236` (2026-07-23 update); `posts/decision/048` caveat; `posts/finding/183`; `teacher-final-replicate/PLAN.md` lever table]

**D-8. Everything else the record closed stays closed.** `imu_yaw_offset +102`, frame `+x=3시·+y=12시`,
`thruster_order [3,2,4,0,5,1]`, signs identity on m0/m1/m2/m5, m3 DEAD, m4 excluded, J1/J2 homing,
θ2 hard window REMOVED (methodology violation, `decision/061`), manipulability constraint never
binding, THR_FILTER_DT 0.02. [EVIDENCE: vault `resume-brief` §2]

## What this program is, and what it is not

It IS: one teacher retrain whose plant CONFIGURATION matches the robot that exists (m3 dead, m4
muted, ≈1-step latency), with every other knob held at the incumbent's as-run value so the result is
attributable. It is NOT plant-v2 (hydro/added-mass/thrust-curve corrections, `decision/209`) — those
stay gated on bench measurements that do not exist; it is NOT a reward or constraint redesign; and it
adds NO hard clamps, latches or rule-based shaping anywhere in training (constraint 1 of the
Objective). Robot-damage prevention stays where it already is — deployment-side guards
(`joint_current_max_ma` 1000–1200, `start_att_max_deg` 45, J1 cable-wrap rail 6π, J2>π abort,
`launch_driver:=false`) — and none of them enters the training environment.

## Phase 0 — evidence gates (desk; zero training GPU-hours; all on marinelab via Orca)

Each gate has a pre-registered readout. None launches training.

| # | Gate | Command / method | Pre-registered readout | Effect |
|:--|:--|:--|:--|:--|
| G0-A | Does the incumbent have an arm-pitch fallback? (`finding/137` item A) | `eval.py static --checkpoint <model_9998> --fault_fixed_health 1,1,1,0,0,1 --doraemon-dr-from <incumbent run>` with the attitude STEP trajectory (`build_step_trajectory`, `--att-amp-deg 15`), 64 envs, seed 42; compare to the same eval with health `1,1,1,1,1,1` | pitch step tracking at `none`: if ≥ 80 % of the healthy run → fallback exists and the retrain's pitch argument (D-1) drops to "robustness"; if < 50 % → D-1 confirmed | decides how §Predicted outcome is phrased, not whether the program runs |
| G0-B | Rate/latency sensitivity of the incumbent in sim | `--control-delay 1` and `2` at all levels (Z4 repeat on the incumbent; the recorded sweep is on `trpo_buoyanchor`) | reproduce the superlinear degradation (≈2×/5× at d=1/2) | sizes the delay-DR benefit; feeds `[DECISION-REQUIRED: control-rate]` |
| G0-C | Is a fixed-health training config feasible under DORAEMON? | 2-seed × 500-iteration probe with `fault.thruster_fixed_health=[1,1,1,0,0,1]`, `control_delay_steps=[0,1]`, all else incumbent; PAIRED against the same seeds without the two changes | `Train/mean_reward` and `DORAEMON/success_rate` trajectories: proceed if the paired deficit is < the R30↔R31 seed gap (13.4 return points) at iteration 500; otherwise apply the changes one at a time and find the culprit. Also read the `thruster_util` constraint margin (J_C/d_k): it was 0.82–0.93 of budget with 6 thrusters (`posts/decision/234`) and four live channels may push it to binding | gate for Phase 3 launch (this is the `finding/264` revised gate, option b) |
| G0-D | DGX parallel-seed throughput | On ksm-nas: one 4096-env run for 100 iterations alone, then two concurrently; record s/iter and `free -m` peak | choose 2 parallel seeds if slowdown ≤ 1.5×, else serial | sizes Phase 3 wall-clock |
| G0-E | Constraint activation check | read the incumbent `launch.log` / TB tags for the 10 constraint margins; confirm `num_constraints` is synced at runtime (the deployed `agent.yaml` serializes `num_constraints: 0`) | 10 `Constraint/*` tags present | pre-launch sanity for Phase 3 (a config that silently dropped constraints would be a different algorithm) |
| G0-F | Board-side one-liners (no robot) | add `/rl/command` to `albc_rl_fieldtest.launch` record list (`finding/137` item F); confirm `thruster_sign` default is NOT identity in the fieldtest launch or document the mandatory arg | bag contains setpoints in the next tank run | vault-side, registered by pointer |
| G0-G | **m0/m3 motor identity** (dry, robot out of water, 5 min, operator) — the record conflicts: `posts/finding/255` (2026-07-05) measured "vertical pair = ONE motor, dual ESC", `deployed_tam.json` (2026-08-11) records m0 ok / m3 DEAD as separate channels, `finding/137` §7 flagged it and left it open | trace the two vertical ESC leads to the motor(s); if one motor, note which ESC actually drives it | two motors → fixed health `[1,1,1,0,0,1]` is the right model (m0 alone, My = +0.145·u0). ONE motor → the sim's differential My row is unphysical and `[1,1,1,0,0,1]` would teach a pitch moment that does not exist; the honest model is m0 with `My = 0` (TAM row edit) — see `[DECISION-REQUIRED: vertical-motor-identity]` | blocks Phase 1's fixed-health vector until answered; both branches are one config line |

## Phase 1 — the retrain configuration (delta vs incumbent, one row per knob, with grounds)

| Knob | Incumbent (as-run) | This program | Ground |
|:--|:--|:--|:--|
| `fault.enable` | `true` | `true` | held |
| `fault.thruster_fixed_health` | `null` (Bernoulli) | `[1,1,1,0,0,1]` — see `[DECISION-REQUIRED: fault-config]` for whether the 4 live channels keep sampled degradation | D-1/D-2: the policy must learn arm-pitch under a rank-1 vertical set; training exposure today is 0.003 %. Literature: RL FTC work trains a dedicated policy for a known permanent underactuated configuration (§Traceability R3). This is plant fidelity, not a rule — no clamp, no shaping |
| `randomization.control_delay_steps` | `(0,0)` | `(0,1)` | D-3 (`finding/264`, user-approved 08-14); board rates now make ≈1 step the whole residual; `(0,3)` measured to stall |
| `decimation` / control rate | 4 → 50 Hz | 4 → 50 Hz (held) — see `[DECISION-REQUIRED: control-rate]` | D-6: changing it ripples through 8 rate-coupled constants (codex §1/§15-b) and no measurement yet justifies a value; the rate question is measured on the robot with the SAME policy first |
| `thrusters.thrust_deadband` / `enable_thrust_curve` | 0.075 / False (inert) | held | D-5: deployment-lane compensation; curve blocked on bench |
| `randomization.*` DR ranges, `max_thrust_scale (0.85,1.15)` | as-run | held byte-identical | comparability to the incumbent; plant-v2 is out of scope |
| `doraemon` (`kl_ub 0.12`, `performance_lb 250`, `step_interval 250`, `alpha 0.5`) | as-run | held | recalibration protocol (`decision/063`) says widening the box requires re-tuning both; we do not widen the box. Fixed-health may lower attainable return → G0-C measures it; if it fails, `performance_lb` becomes a decision, not a silent edit |
| reward / constraints (10 terms) | as-run (`k_bias −2.0`) | held | constraint 1 of the Objective: no new shaping; `manipulability_cost` stays soft (never bound before) |
| `observation_noise_model` | white + per-episode bias | held — see `[DECISION-REQUIRED: obs-noise-color]` | one sim-only ablation (HuB) favors colored noise; no measurement on this robot; YAGNI unless the user opts in as a screening arm |
| `use_privileged_fault_obs` | `false` | `false` | with a fixed fault pattern there is nothing to infer; FaultDR-AB already rejected it (H2) |
| obs 72D, network, TRPO hyper-params, `num_steps_per_env 64`, `entropy_coef_per_dim`, `min_std_per_dim` | as-run | held | attributability; every lever in this family was tried and refuted (`teacher-final-replicate/PLAN.md` lever table) |
| `num_envs` | 4096 | 4096 | 16384 measured inside seed noise at 11× compute; DGX's value here is parallel seeds, not envs |
| `max_iterations` | 5000 (resumed, 9998 total) | 10000 from scratch | saturation at ≈7748; 5000 leaves 0/21 dims open (D-7) |
| seeds | 30 (single) | 30 and 31 (≥2) — see `[DECISION-REQUIRED: seeds-and-budget]` | seed floor 56 % p2p; the R30/R31 straddle |
| code | `598db899` | current `exp/koopman-marine-obs` HEAD (`2eedcd0`, +40 config / +56 env lines since 598db899, all Koopman/ablation additions dormant behind `koopman_module_path=""` and arm flags) | same lineage; verified `598db899` is an ancestor |

Mixer implication (robot side, registered by pointer in the vault PLAN): a policy trained on the
dead set must be deployed with `thruster_sign:=[1,1,1,0,0,1]` and `fault_reallocate=false` —
reallocation would move the plant AWAY from the training distribution — see
`[DECISION-REQUIRED: reallocate-with-new-policy]`.

## Parameter coupling

### Tier 1 — follows mechanically; nothing to set

| Key | Incumbent | This program | Note |
|:--|:--|:--|:--|
| `episode_length_s` 30 → steps | 1500 | 1500 | `decimation` held, so step counts hold [DERIVED] |
| `hist_stride` 3 → 60 ms, `vel_cmd_resample_steps` 250 → 5 s | same | same | rate held [DERIVED] |
| `state_space` | 28 | 28 | `use_privileged_fault_obs` held false |
| `observation_space` | 72 | 72 | `use_bias_ema_obs` held |
| DelayBuffer allocation | none | history 1, per-env lag ∈ {0,1} redrawn at reset | consequence of `(0,1)`; RNG stream shifts → comparisons vs the incumbent are distribution-level, never per-env paired (`finding/264` note 2) |

### Tier 2 — real coupling; a decision is required

| Coupling | Why it is real | Marker |
|:--|:--|:--|
| Fixed dead channels lower the attainable episode return → DORAEMON's `performance_lb 250` may become infeasible (the E1-latdr stall class) | `performance_lb` was calibrated on the healthy plant (p25 of the return distribution) | `[DECISION-REQUIRED: fault-config]` (G0-C measures it; if the paired probe fails, the user chooses between a fixed-health fraction < 100 % and an `lb` re-calibration — never a silent edit) |
| Delay DR shifts the env RNG stream and adds 1 privileged dim's meaning (normalized delay) | breaks per-env pairing with any `(0,0)` run | `[DECISION-REQUIRED: delay-range]` |
| Control rate change would re-time 8 constants | codex §1 | `[DECISION-REQUIRED: control-rate]` |
| DGX vs workstation as the training machine of the DEPLOYED teacher | standing caveat vs its n=1 evidence | `[DECISION-REQUIRED: dgx-trained-deployable]` |
| Parallel seeds on one GB10 share compute | s/iter unknown until G0-D | `[DECISION-REQUIRED: seeds-and-budget]` |
| Whether m0's `My = 0.145` row is physical depends on the m0/m3 motor identity (G0-G); with a single motor the fixed-health model must also zero that row | a spurious pitch moment in sim is a sim-to-real gap the retrain would CREATE | `[DECISION-REQUIRED: vertical-motor-identity]` |
| Four live thrusters carry the whole wrench → `thruster_util` (budget 0.40, already 0.82–0.93 of budget on the healthy plant) may bind and the policy may under-use thrust | binding is measured, not assumed; tightening/loosening budgets to compensate is out (halving budgets cost −54 % reward, `posts/finding/052`) | read in G0-C; escalates only if it binds (`[DECISION-REQUIRED: fault-config]` covers the fallback) |

### Tier 3 — no coupling to the variables under test; leave byte-identical

All DR ranges, `doraemon` cfg, reward cfg, constraint cfg, network sizes, TRPO cfg, `num_steps_per_env`,
`save_interval`, `decimation`, `thrusters` cfg, hydro cfgs, `att_cmd_rp_range`, `initial_joint_pos_range`.

## Phase 2 — marinelab 5000-iteration screening (optional, user's own words: "필요할 경우")

Purpose: attribute the two changes before committing DGX time. Each arm = 4096 envs, 5000 iterations,
RTX 4070 (GPU0) ≈ 5 h, eval on the RTX 4060 (GPU1) with `--doraemon-dr-from` anchored on the
incumbent; 5000-iteration arms are compared ONLY to each other at matched iteration (their box is
unsaturated by construction; they are screening, never deployable).

| Arm | One variable vs S0 | Reads |
|:--|:--|:--|
| S0 | incumbent config, seed 30, from scratch, 5000 iter | control (the paper suite's `full_method` arm may serve if its `env.yaml` matches — verify key-by-key, `decision/006`) |
| S1 | + `thruster_fixed_health [1,1,1,0,0,1]` | pitch tracking with health `1,1,1,0,0,1` at eval (the arm-pitch question) + `Train/mean_reward` deficit |
| S2 | + `control_delay_steps (0,1)` (on top of S1) | delay cost, paired seed |
| S3 (only if G0-B/robot A/B show a rate cliff) | `decimation 8` (25 Hz) with the 8 constants re-timed | rate robustness at eval delays 0/1/2 |
| S4 (only if opted in) | + OU-colored obs noise | attitude ss_error at hard |

Skip rule: if G0-C's 500-iteration paired probe clears with margin, S1/S2 are redundant and Phase 3
starts directly — the screening exists to de-risk, not to delay.

## Phase 3 — DGX final teacher (ksm-nas)

- Branch: `exp/koopman-marine-obs` at the marinelab HEAD after the 10 unpushed commits are pushed
  (or fetched directly) — `[DECISION-REQUIRED: push-marinelab-branch]`. ksm-nas's clone is on
  `main@1062dc2` (2026-08-03) and must be moved to this branch; `main` is NOT an ancestor of it.
- Launch guards (all measured, `dgx-final-scaleup/HANDOFF-DGX.md`, `launch_armD.sh`): `TERM=xterm`,
  `--headless`, `fault.enable=True` (fixed health makes this mandatory), `free -m` abort > 102 400 MiB,
  artifact check (a `model_N.pt` past its due time) instead of exit code, no `CVD` trap.
- Runs: seeds 30 and 31, 4096 envs, 10000 iterations, `--run_group teacher_realplant_2026_09`, all
  Phase-1 overrides via Hydra (`env.fault.thruster_fixed_health=[1,1,1,0,0,1]`,
  `env.randomization.control_delay_steps=[0,1]`), parallel if G0-D allows.
- Monitoring (verified tag names): `Train/mean_reward`, `DORAEMON/success_rate`, `DORAEMON/mode`,
  `Policy/mean_noise_std`, all 10 `Constraint/*` margins; the iteration-500 abort gate uses the
  paired G0-C trajectory as its reference, never a saturation-time band (vault
  `feedback_handoff_healthy_band_timepoint`). Fixed-schedule EVALS at iterations 2500 / 5000 / 7500 /
  10000 on the fixed-health exam (TB is blind to intra-run eval regressions: a 34 % none-level
  degradation moved every TB metric < 1 %, `posts/finding/297`); best-checkpoint tracking follows.
- Launch is queued with `omx queue-launch`, fired by the user. Nothing here auto-fires.

## Phase 4 — selection, distillation, export

1. Re-score incumbent + every candidate checkpoint (best-checkpoint tracking, DORAEMON authors'
   prescription) on ONE machine (the workstation RTX 4060 eval GPU) in one batch, `--doraemon-dr-from`
   the incumbent, `--fault_fixed_health 1,1,1,0,0,1` as the primary exam (the robot that exists) plus
   healthy `1,1,1,1,1,1` as the secondary; decide at `hard`, never at `none`; per-env paired floors
   (0.10° ss_error, 1.6 pp survival) only where `dr_*` arrays match; `ood` re-derived per run is not
   comparable — use `--ood-scale` if an OOD read is wanted.
2. Pre-registered success: on the fixed-health exam, pitch ss_error at `hard` within 2× of roll, and
   roll not worse than the incumbent's healthy-exam roll beyond the paired floor. Failure to reach
   this is a result, not a reason to add shaping.
3. Distill GRU (C3 recipe: GRU 128/head 64, `dagger_mix=select`, β 0.5, λ 1.0, 2048 envs × 1000
   iter) AND TCN fallback from the selected teacher; `decision/263` showed C3 does not transfer
   across teachers, so the student is re-validated in-loop (`analysis/eval.py` student mode) rather
   than assumed.
4. Export packs (`export_deploy_pack.py`), parity atol 1e-5 in the container, obs 72D unchanged so
   the board port (`deploy/72d-inc9998-gru`) needs weight files only; re-run `test_deploy_constants.py`.

## Phase 5 — robot (tank), pre-registered, in the vault PLAN by pointer

1. Same-policy control-rate A/B FIRST with the INCUMBENT pack (no retrain needed): joint-only,
   `control_hz` 50 vs 10, roll ±15° steps, ≥2 runs each, alternating order, bag with `/rl/command`;
   readout: settle time and 0.3–0.7 Hz ripple amplitude. This closes D-6 with data, whichever way.
2. New pack, joint-only: T4 protocol with roll AND pitch ±15°; pre-registered pitch: θ2 span ≥ 15°
   on a pitch step and ≥ 50 % tracking (the incumbent gave 5–7° / 0.9 %).
3. New pack, thrusters: `thruster_sign:=[1,1,1,0,0,1]`, `fault_reallocate=false`, `thruster_scale`
   0.05 → 0.1 → 0.3 (vault T10), `rosparam get` of both args logged at start.
4. Guards unchanged (deployment side only): current cap 1000–1200 mA, `start_att_max_deg` 45,
   `launch_driver:=false`, J2 > π abort.

## Work split

| Who | What | Ground / rule |
|:--|:--|:--|
| Claude (this session) | decisions, gate readouts, verdicts, plan/community writes | omo: decision and verdict never delegated |
| codex (`develop`, ground 1) | the ≤10-line fault-mask change if `[DECISION-REQUIRED: fault-config]` picks option A; launch scripts; eval wrappers; Hydra override syntax check | settled plan, mechanical |
| agy (`explore`, ground 2) | long-log and bag digests, report drafting from `summary.json` sets, cross-run table assembly | 1M-context reading; keep each call < 5 min |
| Orca orchestration | every remote step: `worker-start --on marinelab` for G0-A/B/C/E and Phase 2/4; ksm-nas via `[DECISION-REQUIRED: ksm-nas-orca]` | user instruction; supervised loop with `worker_done`, verify `worker-read --source transcript` |
| hq community | `decision` post opening this program (marinelab), `handoff` pointer post (vault), one `finding` per gate readout | user instruction 5 |

## Backlog reconciliation (open leads, all named; none dropped silently)

| Lead | Disposition here |
|:--|:--|
| `finding/264` control_delay (0,0) — needs-apply-before-retrain | APPLIED: `(0,1)` in Phase 1, gate G0-C |
| `decision/209` plant-v2 batch (buoy added mass, buoy damping, thrust curve, arm actuator form; obs+4) | DEFER — all gated on bench measurements (T200 curve, XW540 step) that do not exist; explicitly NOT in this retrain; named in the launch ack |
| `finding/163` accumulator reset asymmetry (board reseeds from constant) | board-side fix, no training impact; carried to Phase 5 checklist |
| `finding/198` J2 winding on land / rates | closed by hardware (rates fixed, unwrap guards); rate question → Phase 5 step 1 |
| `finding/296` M3 per-dim return decomposition | DEFER — needs per-env return logging that eval does not write; not required for this line |
| `decision/263` C3 non-transfer across teachers | CARRIED: Phase 4 step 3 re-validates the student |
| `decision/061` eval anchor rule | APPLIED in Phase 4 |
| vault `finding/135` ESC deadband / no proportional band (T10 premise) | robot-side; not a training change (D-5); Phase 5 step 3 will meet it |
| vault `finding/137` items A–F | A → G0-A; B → answered (`fault.enable: true`); C (vertical row measurement) → real-side, DEFER; D (m0/m3 same motor?) → real-side visual check before Phase 5; E (R4 bag) → agy digest task; F → G0-F |
| `dgx-final-scaleup` §8 Q1 machine isolation | → `[DECISION-REQUIRED: dgx-trained-deployable]` |
| E-lat, E-obs, E-t200 (closeout roster) | E-lat subsumed by Phase 1 `(0,1)`; E-obs superseded (obs72 decided); E-t200 DEFER (bench) |
| `posts/finding/255` (07-05, "vertical pair = one motor, dual ESC") vs `deployed_tam.json` (08-11, m0 ok / m3 DEAD) — unresolved conflict | → G0-G + `[DECISION-REQUIRED: vertical-motor-identity]`; the fixed-health vector is not final until this is answered |
| `posts/decision/030` velocity_limit_sim 3.1 vs `delta_scale 0.10` (5 rad/s demand → target runaway) — recorded as a retrain item | HELD: both sides (sim `_joint_pos_targets`, board `np_policy.py`) integrate identically and unbounded (`posts/finding/163`: not a sim-to-real gap); changing `delta_scale` would be a board change too and a new variable. Arm-pitch training raises arm demand, so runaway frequency is READ in the fixed-health eval (`applied action` channel), not clamped |
| `posts/decision/127` (08-05) control-delay as a "gen-2 requirement" incl. per-sensor staleness modeling | SUPERSEDED in range by `finding/264` (08-14, `(0,1)`); the per-sensor split is now moot for the board (joints 50 Hz) and stays out of scope |
| `posts/decision/155` / `197` / `253` needs-apply-before-retrain (horizontal TAM rewrite; vertical Fz/My redesign; IMU 45°/pitch-negation; TAM moment-arm / max_thrust DR band) | horizontal rewrite APPLIED (`3bb042b`, incumbent trained on it); max_thrust band ADOPTED (`(0.85,1.15)`); IMU offset closed on the ROBOT side (+102°, consumer-side rotation) — sim frame unchanged by design; vertical row → G0-G / item C |
| `posts/decision/219` / `234` / `finding/141` — real robot has 2 faulted thrusters while `thruster_util` trends into binding (93.2 % at extend8k); m4 loss halves the pure-yaw ceiling (11.5 N·m) | READ in G0-C (`thruster_util` margin); budgets are NOT retuned to compensate (`finding/052`: halving budgets → −54 % reward); yaw-rate tracking on the fixed-health exam is a pre-registered secondary readout |
| `posts/decision/299` XY body-offset DR (arm-tip buoy pose disturbance) must not be pruned | HELD — all DR ranges byte-identical |
| `posts/decision/179` reward retune only after a post-fix baseline; `performance_lb` recalibration if returns change | HONORED — no reward change; `lb` recalibration is a listed fallback under `[DECISION-REQUIRED: fault-config]`, never silent |
| `posts/decision/140` (07-27) fault-DR ADOPT + privileged fault obs REJECTED | HONORED — fault DR stays on the live channels under option A; privileged obs stays false |

## Risks

- Fixed-health training may make `performance_lb 250` infeasible → G0-C catches it before any long run.
- Four live thrusters may drive `thruster_util` to binding (0.82–0.93 of budget already on six) → the
  policy may under-use thrust for yaw; read the margin in G0-C and the yaw-rate exam in Phase 4; do NOT
  loosen the budget to compensate (`finding/052`).
- If m0/m3 are one motor (G0-G), the `[1,1,1,0,0,1]` model keeps a pitch moment (`My = 0.145·u0`) the
  robot cannot make → the retrain would CREATE a gap; G0-G is therefore a hard prerequisite of Phase 1.
- Training pitch through the arm may teach the policy to also use m0 (Fz/My coupling 0.145) → heave
  drift in the tank; the `thruster_util` constraint and `k_thr` penalty discourage it but do not
  forbid it; read `Fz` usage in the fixed-health eval (`applied action` channel) before Phase 5.
- A DGX-trained teacher is a departure from the recorded caveat; mitigated by one-machine re-scoring
  and ≥2 seeds; residual risk is stated, not hidden.
- Student distillation is the measured bottleneck of the shipped artifact (every student 2.5–3.1° hard
  roll dispersion regardless of teacher); this program does not fix that and does not claim to.
- Orca on ksm-nas is not paired today; a local supervised worker over ssh loses nothing but adds one
  hop of failure (Mac must stay up).

## Predicted outcome

Most likely: G0-A shows the incumbent has NO arm-pitch fallback (θ2 span in sim mirrors the 5–7°
seen in the tank), G0-C clears with a paired deficit inside the seed gap, and the retrained teacher
tracks pitch through the arm on the fixed-health exam at `hard` with ss_error within 2× of roll while
roll stays inside the paired floor of the incumbent's healthy exam. Delay DR `(0,1)` costs < 5 % return
(the Z4 curve says d=1 is the cheap step). The tank then shows pitch steps with θ2 spans ≥ 15° — the
first pitch tracking this robot has produced under RL.

Plausible null: pitch through a 2.2 N·m arm against a 6.10–7.76 N·m/rad restoring stiffness is
authority-limited (±14.5° at θ2 150° per T1), so a pitch step of 15° may settle near the envelope
edge; that would be a physics ceiling, not a training defect, and the paper-side story would shift
to "attitude within the arm envelope".

Failure mode to watch: fixed dead channels drop attainable return below `performance_lb` → DORAEMON
mode −2 from the start (the E1-latdr signature). Tell: `DORAEMON/success_rate` < 0.5 at iteration 250
in BOTH seeds with the paired control above it.

## Decisions for the user

1. `[DECISION-REQUIRED: dgx-trained-deployable]` — Allow a DGX-trained teacher to be THE deployed
   model? The record forbids it on a +109 % cross-machine term measured once (same seed on a
   different GPU ≠ a paired run; the seed floor is 56 % p2p). Recommend: yes, conditional on
   one-machine re-scoring and ≥2 seeds. Alternative: train the final on the workstation (2 seeds
   serial ≈ 19 h) and use ksm-nas only for screening/probes.
2. `[DECISION-REQUIRED: fault-config]` — (A) fixed `[1,1,1,0,0,1]` mask AND sampled degradation on the
   4 live channels (≈10-line change in `faults.py`: apply the mask after Bernoulli sampling; keeps the
   fault curriculum alive) — recommended; (B) fixed health only, config-only, fault DR effectively off;
   (C) mixture p·fixed + (1−p)·Bernoulli. Also decides the fallback if G0-C fails (fraction < 100 % vs
   `performance_lb` re-calibration).
3. `[DECISION-REQUIRED: control-rate]` — Hold 50 Hz training and settle the rate on the robot with the
   same policy (Phase 5 step 1) — recommended; or add the 25 Hz screening arm S3 now.
4. `[DECISION-REQUIRED: delay-range]` — `(0,1)` (recommended, user-approved 08-14) vs `(0,2)`.
5. `[DECISION-REQUIRED: seeds-and-budget]` — 2 seeds × 10000 iterations (≈15.4 h each on the DGX;
   parallel if G0-D shows ≤ 1.5× slowdown) — recommended; or 3 seeds.
6. `[DECISION-REQUIRED: reallocate-with-new-policy]` — Deploy the new policy with `fault_reallocate=false`
   and `thruster_sign:=[1,1,1,0,0,1]` (changes the vault D4 default). Recommend: yes.
7. `[DECISION-REQUIRED: ksm-nas-orca]` — Pair ksm-nas as an Orca environment (`orca serve` inside the
   `seungmin-dev` container, needs install) or drive it from a local Orca-supervised worker over ssh
   (no install; Mac must stay up). Recommend: local worker now, pairing when convenient.
8. `[DECISION-REQUIRED: push-marinelab-branch]` — Push the 10 unpushed `exp/koopman-marine-obs` commits
   from marinelab so ksm-nas can fetch them (or fetch over ssh from the workstation). Recommend: push.
9. `[DECISION-REQUIRED: obs-noise-color]` — Keep white+bias (recommended) or add arm S4 (OU-colored
   noise) to screening.
10. `[DECISION-REQUIRED: paper-comparability]` — Acknowledge the new teacher is a deployment line
    outside the RA-L 7-arm suite (different plant configuration); no paper table is re-run here.
11. `[DECISION-REQUIRED: vertical-motor-identity]` — Operator answers G0-G (are m0 and m3 one motor with
    two ESCs, as `finding/255` measured on 2026-07-05, or two motors, as `deployed_tam.json` implies?).
    Two motors → fixed health `[1,1,1,0,0,1]` as planned. One motor → also zero m0's `My` entry in
    `_BASE_ALLOCATION_MATRIX` (a factual correction of one number, not a rule) so sim cannot pitch with
    a motor the robot does not have. Recommend: answer before G0-C runs; both branches cost one line.

## Traceability — external sources consulted (2026-09-02)

- R1 deadband: BlueRobotics T200 guide (1475–1525 µs neutral); MarineGym (arXiv 2503.09203) models a
  dead-zone; 6-DOF UVMS paper (arXiv 2512.13359) uses a fixed ±5 N band, not randomized; spacecraft RL
  (arXiv 2508.19164) measured a failed deployment-side deadband compensation; classical marine control
  (Whitcomb & Yoerger 1999) links dead-zones to limit cycles. No RL work does both sim-model and
  deployment-inverse → pick one lane (this program: deployment lane).
- R2 latency: Tan et al. 2018 (arXiv 1804.10332) obs latency 3–19 ms at 150–200 Hz; MMDR (arXiv
  2109.14549) proprio delay DR [0, 40 ms] at 25 Hz with per-modality independent sampling, +90 %
  real-world improvement; "Learning to Swim" (arXiv 2410.00120) skipped action-delay DR citing
  instability. Supports a narrow `(0,1)`-class range with a paired gate.
- R3 permanent faults: satellite RL (arXiv 2505.00165) trains a dedicated underactuated-case policy;
  quadrotor RL-FTC (arXiv 2505.08223, 2603.10714) infers faults from history; no RL work substitutes
  an arm/moving mass for a lost thruster → our arm-pitch transfer is unverified in the literature.
- R4 control rate: Gangapurwala et al. ICRA 2023 (arXiv 2209.14887) latency tolerance 50 ms @ 50 Hz vs
  90 ms @ 10 Hz, 10 Hz not worse in success; resampling a 200 Hz component at 10 Hz produced near-zero
  gradients (caution against decimation without retraining); no decimate-vs-retrain comparison exists.
- R5 noise & curriculum: HuB (arXiv 2505.07294) OU-colored noise beat uniform in sim (67.18 vs 69.45 mm);
  DORAEMON (arXiv 2311.01885) α = 0.5, best-checkpoint tracking, infeasible ranges destabilize;
  no DORAEMON/ADR follow-up for underwater/aerial found; no published "iterations to saturate" norm.
