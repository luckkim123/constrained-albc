# Program: retrain-simtoreal-2026-09 — fault-tolerant attitude teacher retrain (generalized fault DR + action-delay DR), rebuilt from the evidence ledger

**Status: REVISION 3 (2026-09-03) — rebuilt from primary sources. NOT approved, NOT launched, nothing queued.**
Launches only via `omx queue-launch`, fired by the user. Robot steps only with the operator.

> ## Why this revision exists (read first)
>
> The 2026-09-02 plan (Round 1 + Round 2 merged, then FROZEN by `handoff/304`) changed its claims each time the user
> pushed on it, because it was written from digests and cited posts it had not read to their last Update. This revision
> was built the other way round: **every load-bearing claim was first re-scored against both stores** (vault 140 posts +
> marinelab 304 posts, read to the last `## Update`) — `review/306` carries the full 31-claim ledger — and the plan below
> cites that ledger line by line. The previous text is kept beside this file as `PLAN.md.bak-round2-frozen` for diffing.
>
> **What the ledger changed (all in `review/306`, with the closing finding `finding/305`):**
> 1. The "vertical TAM on the wrong axis" lead is **refuted by the artifact** — the pitch diagnosis of `vault:finding/137` stands (`finding/305` §1).
> 2. HARD-GATE `decision/197` re-scored: item 1 applied; item 2's premise (one motor) refuted, only the **moment magnitude** is unmeasured; item 3 (IMU frame) **closed on the robot side by measurement**; item 4 max_thrust band applied, moment-arm band open (`finding/305` §2).
> 3. Nine numbers/claims of the frozen plan were wrong or unsourced (thrust-ON bags exist and are unanalyzed; no J2>π guard exists; `thruster_sign` default is identity; "6–8 %" was the 5k arm not the incumbent; `thruster_util` 0.805–0.943; `performance_lb` 250 is not p25; C3 non-transfer was RETRACTED; DGX 5.41 s/iter; 1/30,000 vs 0.09 % are different events) — each corrected where it is used below.
>
> **What did NOT change:** the user's constraints and decisions (§1), the FTC framing, generalized fault DR, `(0,1)` action delay, workstation final, held constraints/rewards/DR box, 50 Hz.

## 1. Objective — user, verbatim (2026-09-02, Mac session)

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

Later user statements that bind this plan (same session, 2026-09-02 evening; recorded in `decision/301` comments, `handoff/303`, `handoff/304`, vault memory): faults must be trained as a **distribution** (FTC strengthening), never a plant with the dead thrusters glued off; **no special mass on the deployed (m3,m4) pattern** (generalized fault DR); the final teacher trains on the **workstation** (recorded departure from "ksm-nas"; ksm-nas = screening/probes only); the incumbent's 10 IPO constraints stay **unchanged and unstrengthened**; the paper framing is "fault-tolerant attitude control validated on hardware with real failures", not "the robot is broken". The user also asked whether the policy could take over depth / yaw / XY — that is `[DECISION-REQUIRED: scope]` in §10, not decided here.

## 2. Diagnosis — what the record establishes (each line names its source; corrected numbers in bold)

**D-1. Pitch failure = deploy-configuration gap; thrusters cannot restore it with m3 dead.** The incumbent learned pitch from the vertical thrusters (My 2 × 0.145 m × 50 N = 14.5 N·m) and roll from the arm (16.62 N × 0.13 m ≈ 2.2 N·m vs horizontal-thruster roll 1.4 N·m); joint-only T4 gave roll 98.7 % / pitch 0.9 % with the arm following its commands within 1–3°. [`vault:finding/137` §2–§5] The vertical pair sits on the sim ±x axis = 3 h/9 h exactly as the robot has it, and m0 alone produces pitch with roll unchanged — the "wrong axis" lead is refuted. [`finding/305` §1; `deployed_tam.json`; codex ground-4 check in `review/306` §C] With m3 DEAD the live (Fz, My) rows are rank 1 and `reallocate()` keeps Fz and drops My, so pitch is the arm's job whether reallocation is on or off. [`vault:finding/137` §5] **Not yet measured:** the thrust-ON repeat of the same staircase (`10-19-06`, 145 s) is unanalyzed — G0-H below tests §5's prediction on data instead of code reading. [`vault:finding/137` §12, `vault:finding/141`]

**D-2. The incumbent trained faults as a distribution, but complete loss had measure zero and double loss was rare.** As-run: `fault.enable true`, `thruster_fail_prob 0.1`, health `U(0, 0.5)`, `use_privileged_fault_obs false`, per-channel i.i.d. Bernoulli with the DORAEMON `fault_severity` scalar multiplying the fail probability (`sample_thruster_health`, `severity * cfg.thruster_fail_prob`). [`deployed_env.yaml:fault`, `envs/main/mdp/faults.py:27-55`, `decision/140`] A health of exactly 0 is not representable (continuous U(0,0.5)). **The incumbent's `fault_severity` reached Beta(1,1) at iteration 7748 and stayed there to 9998** (artifact `curriculum_trajectory.json`, read 2026-09-03; the "6–8 % of range" figure is the 5k fault-DR arm, `finding/273`, not the incumbent). [`finding/305` §2] The "1/30,000" double-loss figure (mixer docstring) and the "0.09 % of envs" (Arm A at severity ≈0.08) are different events and neither derivation is in the record; this plan uses the closed-form exposure in §5 and a unit test, not those numbers. [`review/306` T2]

**D-2b. The lever is the sampler shape, not the severity schedule.** E-ftc1 raised the severity endpoint 2.50× and made m4-dead fault rejection 2.9–5.5× WORSE at every level. [`decision/238`, `finding/273` Update 07-29] Fault DR itself was adopted at 5–12× less m4-dead degradation with zero terminations (n = 1 seed per arm); privileged fault obs was not adopted on that n = 1 fixed-pattern eval. [`decision/140`] `decision/140` evaluated m4-only because "the real robot has one vertical motor" — that premise is refuted, so **vertical faults belong in the exam** (m3 dead IS the robot). [`finding/305` §2]

**D-3. Action latency is the one apply-before-retrain config item; observation staleness is closed by firmware.** Pre-firmware obs age was 1.2–4.7 control steps (IMU 20.3 Hz / joints 10 Hz); post-fix IMU 95.5 Hz / joints 50.1 Hz → 0.11–0.50 step, **with the caveat that the two figures were not computed on one definition** (`vault:finding/056`). `control_delay_steps` delays the ACTION and was trained (0,0); (0,3) stalled DORAEMON (return ≈197 vs lb 250, mode −2); **(0,1) is user-approved (2026-08-14)** with the gate corrected on 08-15 to a PAIRED same-seed with/without comparison, because two seeds of the incumbent config already straddle alpha (R30 0.469 / R31 0.536). Z4 sweep: att ss_error 0.630 → 1.474 → 3.239 → 5.604° for 0/1/2/3 injected steps. The real command→actuator response time is unmeasured. [`finding/264` incl. Updates 08-14/08-15, `finding/266`, `vault:finding/056`]

**D-4. The attitude plant needs no retune on the scalar axes.** Net buoyancy 16.62 N vs sim 17.11 N (3 %, DR percentile 46); restoring stiffness K 7.76 vs 6.10 N·m/rad (percentile 81); arm open-loop DC gain 148°/m (3 % scatter); arm static envelope ±14.5° at θ2 = 150°, equal on roll and pitch. [`vault:finding/136`, `vault:finding/134`, `finding/020`] So the retrain is justified by FTC + deploy/TAM alignment, not by an authority gap.

**D-5. Actuation deadband is compensated on the deployment side and stays there.** Sim `thrust_deadband 0.075` is inert (`enable_thrust_curve false`); the mixer inverts the measured ESC deadband (45 of 300 counts). The thrust-curve SHAPE (quadratic vs linear, 2.0–4.65× gap) has zero DR coverage and is blocked on a T200 bench that does not exist. [`deployed_env.yaml`, `finding/281`, `finding/283`, `decision/209` item 3]

**D-6. "10 Hz was best" is n = 1 and confounded with observation rate.** 08-25: 50 Hz 35 s, 10 Hz 40 s, 100 Hz 4 s, 20 Hz 23 s/192 s (IMU at 20 Hz then); 08-26: 50 Hz 11.8 s, 10 Hz 195 s, 50 Hz 18 s; loop-rate mismatch excluded as the oscillation cause (pitch band unchanged at 50/50). [`finding/017`, `vault:finding/041`, `vault:finding/065`, `vault:finding/066`] The retrain stays at 50 Hz (attributability); the rate question is a deployment A/B with the incumbent (R-2), not a training variable.

**D-7. Budget, machines, seeds — corrected numbers.** DGX GB10: **5.41 s/iter @4096, 9.65 @8192, 34.73 @32768** (`finding/001`); workstation RTX 4070 ≈ 3.3–3.6 s/iter @4096 at 11.3 GB (**README/`decision/143` memory figure — no post carries the s/iter; re-measure in G0-D**). DORAEMON saturation is iteration-clocked (≈7000–7750; 16 384 envs moved it by 250 iterations); 4096 × 10 000 wins or ties 16 384 at hard/ood. [`finding/071`, `decision/004`] Seed floor on the corrected plant: **56 %** p2p on none-level roll ss_error; the +109 % cross-machine term is ONE same-seed pair; eval-machine term is 4 %. [`decision/236` Update 07-23, `decision/117`, `finding/183`] `performance_lb 250` is **not** p25 of the adopted config's return (measured p25 = 261.8, `decision/064`, `finding/207`); it is simply the as-run value and is held.

**D-8. Everything the record closed stays closed.** Frame `+x=3시, +y=12시`, `imu_yaw_offset +102`, `thruster_order [3,2,4,0,5,1]`, signs identity on m0/m1/m2/m5, m3 DEAD, m4 excluded (sign an operator assumption), J1/J2 homing, θ2 hard window REMOVED (`decision/061`), manipulability never binding, `THR_FILTER_DT 0.02` (magnitude of its effect unmeasured). [`vault:resume-brief` §2, `vault:finding/063`]

## 3. HARD-GATE reconciliation (`decision/197`) — done, recorded here as the ledger requires

| # | Item | Status | This baseline is… |
|:--|:--|:--|:--|
| 1 | Horizontal TAM rows + ESC permutation | APPLIED `3bb042b`; incumbent trained on it | post-item-1 |
| 2 | Vertical Fz/My "single-motor" redesign | premise REFUTED (two motors, `finding/255` correction 08-13); placement ±x correct; **magnitude 0.145 m × 50 N unmeasured** | post-item-2 on topology; **pre-magnitude-measurement** (R-1 measures it) |
| 3 | IMU 45° offset + pitch negation | CLOSED robot-side: +102° consumer-side `rotate_imu`, validated closed-loop on both axes (T2 92–98 %, T4 roll 98.7 %) | post-item-3 (robot-side); sim unchanged by design |
| 4 | Moment-arm + max_thrust DR band | max_thrust `(0.85, 1.15)` APPLIED; moment-arm band NOT applied (no such DR dim) | **pre-moment-arm-band**, explicitly acknowledged; S1c screens a band if R-1 says the nominal is off |

Do not trust `hq query --status needs-apply-before-retrain` alone (statuses were flipped to resolved on 2026-08-05 while bodies said deferred); this table is the reconciliation. [`handoff/304`, `finding/305` §2]

## 4. What this program is / is not

IS: one from-scratch teacher retrain that (a) makes actuator loss a **distribution** the policy must absorb — single and double loss, complete death, vertical channels included, uniform over the six channels with no pair awareness — and (b) applies the ≈1-step ACTION delay as DR; every other knob held at the incumbent's as-run value for attributability. The robot's m3-dead / m4-excluded state is ONE sample of that distribution and the PRIMARY exam vector.

IS NOT: a plant with thrusters glued off (fixed-health vectors are EVAL instruments only); plant-v2 (`decision/209`: buoy added mass, buoy damping, thrust curve, arm actuator — all gated on bench measurements that do not exist); a reward or constraint redesign; a control-rate change; an observation-interface change (depth/XY takeover is `[DECISION-REQUIRED: scope]`). It adds NO hard clamp, latch, or rule-based shaping to training (user constraint 1). Robot-damage prevention stays deployment-side: current cap 1000–1200 mA (1500 only for attitude-hold runs), `start_att_max_deg 45`, J1 6π latch, `launch_driver:=false`, and an **operator abort rule "θ2 crossing π = stop"** — there is NO J2 software guard (`vault:finding/041`: `j2_over_pi = 577, abort = 0`; `vault:finding/141`).

## 5. Phase 1 — the retrain configuration (delta vs incumbent; one row per knob; ground)

| Knob | Incumbent (as-run, `deployed_env.yaml`) | This program | Ground |
|:--|:--|:--|:--|
| `fault.enable` | true | true | held |
| fault sampler — **generalized** (user O-3) | per-channel Bernoulli `p = severity × 0.10`, failed health `U(0, 0.5)`; dead has measure zero | **(1)** raise `thruster_fail_prob` 0.10 → **p₀** (value = `[DECISION-REQUIRED: fault-config]`, default proposal 0.15); **(2)** add a dead atom: a failed channel is fully dead with probability `thruster_dead_frac = d` (default proposal 0.5), else `U(0, 0.5)`; **(3)** `fault_severity` curriculum UNTOUCHED (severity 0 → all healthy; no schedule acceleration). ≤10 lines in `sample_thruster_health` + a unit test that asserts the realized `P(≥1 dead)`, `P(≥2 dead)`, `P(m3∧m4 dead)` at severity 1 and all-healthy at severity 0 | D-2/D-2b. Closed form at severity 1 with q = p₀·d: `P(≥1 dead) = 1−(1−q)^6`, `P(≥2 dead) = 1−(1−q)^6−6q(1−q)^5`, `P(exactly m3,m4 dead) = q²(1−q)^4`. q = 0.05 → 26.5 % / 3.3 % / 0.41 %; q = 0.075 → 37.4 % / 6.9 % / 0.66 %; q = 0.10 → 46.9 % / 11.4 % / 0.66 %. With ≈175 resets per iteration at 4096 envs (1500-step episodes, 64 steps/iter) that is 6–20 double-loss episodes per iteration once the curriculum saturates — learnable, versus measure-zero today. Uniform over channels: (m3,m4) gets no special mass (user decision) |
| realized exposure (pre-registered readout) | unmeasured | log per-episode dead-count histogram at the severity the run actually reaches; target: `P(≥2 dead)` ≥ 1 % over the last 2000 iterations | the whole FTC premise is exposure; if the curriculum starves it, raising the severity FLOOR is a DECISION (re-opens E-ftc1), never a silent edit |
| `fault.thruster_fixed_health` | null | null in training; exam vectors in Phase 4 only | user: faults are a distribution |
| vertical TAM `My` row | `±0.145` (geometry from `actuators.xacro`, reproduces to 4 decimals) | **held at 0.145** unless R-1 measures a ≥20 % deviation; then the nominal is corrected to the measured value before Phase 3. A moment-arm DR band is screening arm S1c, not the main line | `finding/305`: placement correct, magnitude unmeasured; "over-estimated" has no number in the record (`vault:finding/137` §7(2)) — a plan must not encode a direction with no measurement |
| `randomization.control_delay_steps` | (0, 0) | **(0, 1)** | D-3, user-approved 08-14; `(0,3)` measured to stall |
| `decimation` / control rate | 4 → 50 Hz | 4 → 50 Hz | D-6; rate is a deployment A/B (R-2) |
| `thrust_deadband` / `enable_thrust_curve` | 0.075 / false | held | D-5 |
| DR ranges incl. `max_thrust_scale (0.85, 1.15)`, `doraemon` (`kl_ub 0.12`, `performance_lb 250`, `step_interval 250`, `alpha 0.5`) | as-run | held byte-identical | comparability; `decision/063`: widening the box needs joint re-tuning — we do not widen it. If G0-C shows the heavier fault mass drops return below lb, that is `[DECISION-REQUIRED: fault-config]` fallback, not a silent lb edit |
| reward / 10 IPO constraints | as-run | held; **nothing strengthened** (user O-1). `thruster_util` (budget 0.40; 0.805–0.943 of budget across 7 runs, `finding/284`) is read in G0-C as the O-2 readout | constraint 1; `finding/052`: halving budgets −54 % reward |
| `use_privileged_fault_obs` | false | false on the main line; S1b screens true | rejection was n = 1 on a fixed pattern (`decision/140`) |
| obs 72D, network, TRPO hyper-params, `num_envs 4096` | as-run | held | attributability; 16 384 bought nothing (`decision/004`) |
| `max_iterations` | 5000 resumed to 9998 | 10 000 from scratch | saturation ≈7000–7750 (`finding/071`) |
| seeds | 30 | 30 (final); paired probe = seed 30 with/without | `[DECISION-REQUIRED: seeds]` — see §10 |
| code | `598db899` (`exp/koopman-marine-obs`) | current HEAD of the same branch (`2eedcd0`+), Koopman/ablation additions dormant | same lineage; verify ancestor before launch |

## 6. Phase 0 — gates that need no robot (desk / eval / one training probe)

| # | Gate | Method | Pre-registered readout | Decides |
|:--|:--|:--|:--|:--|
| G0-A | Does the incumbent have an arm-pitch fallback? | `eval.py static --checkpoint model_9998 --fault_fixed_health 1,1,1,0,0,1 --doraemon-dr-from <incumbent>` with the attitude STEP trajectory (`--att-amp-deg 15`), 64 envs, seed 42; compare to health `1,1,1,1,1,1` | pitch step tracking at `none`: ≥ 80 % of healthy → fallback exists (D-1 becomes "robustness"); < 50 % → D-1 confirmed | how §9 is phrased, not whether the program runs |
| G0-B | Incumbent delay sensitivity | `--control-delay 1` and `2` at all levels | reproduce the superlinear Z4 curve on the incumbent | sizes the (0,1) benefit |
| G0-C (**training launch, `omx queue-launch`**) | Feasibility + cost of the two changes | **paired**: seed 30, 500 iterations, WITH (fault sampler p₀,d + delay (0,1)) vs WITHOUT, same machine; unit test of the sampler passes FIRST | proceed if the paired return deficit at iter 500 < 13.4 points (R30↔R31 seed gap); `thruster_util` margin is the O-2 readout — if it binds, escalate | Phase 3 launch |
| G0-D (**GPU probe**) | Workstation throughput | 100 iterations alone, then two concurrent; s/iter, VRAM | replaces the unsourced 3.3–3.6 s/iter | Phase 3 wall-clock |
| G0-E | Constraint activation read | 10 `Constraint/*` margins from the incumbent's TB; note `joint1_pos`/`cumul_yaw` were near-binding EARLY (`finding/058` Update) | observational only | pre-launch sanity |
| G0-F | Board one-liners | add `/rl/command` to the fieldtest record list; make `thruster_sign` a mandatory launch arg or log `rosparam get` at start | next bag carries setpoints and sign | vault-side, by pointer |
| **G0-H** (new) | Does thrust ON restore pitch? (D-1 §5 prediction) | analyze bag `10-19-06` with `~/albc_diag/t4_step_analyze.py`, separating reallocation on/off by `Fz` usage (no `fault reallocation:` log exists) | pitch tracking with thrust ON vs the 0.9 % joint-only baseline; heave drift | whether D-1's "arm must do pitch" holds on data. Needs the board reachable (was not on 09-03) |
| **G0-I** (new) | Sampler exposure unit test | implement §5 (1)(2) behind two config values; test asserts the closed-form numbers ± 0.5 pp at severity 1 and all-healthy at severity 0 | test green | gates G0-C |

G0-G (m0/m3 motor identity) is DROPPED — answered by `finding/255`'s correction and `deployed_tam.json`.

## 7. Phase 0-R — robot measurements allowed by constraint 3 (none blocks the desk gates)

| # | Measurement | Protocol | Closes |
|:--|:--|:--|:--|
| **R-1** | Vertical pitch-moment magnitude | m0 held at 2–4 command levels (mixer `undeadband` on), 30 s each, read steady pitch tilt θ and depth; `M = K·θ`, K = 7.76 N·m/rad (`vault:finding/136`); compare to sim `0.145 m × 50 N × u`. Pre-registered: within ±20 % → hold 0.145; outside → correct the nominal before Phase 3. Wall push is expected (rank-1 vertical axis) — operator holds | HARD-GATE items 2 and 4 |
| R-2 | Control-rate A/B with the INCUMBENT pack | joint-only, `control_hz` 50 vs 10, observation rates fixed (IMU 100 Hz / joints 50 Hz), roll ±15° steps, ≥ 30 s per run, ≥ 2 runs per rate, alternating; readout settle time and 0.3–0.7 Hz ripple | D-6 deployment question; does NOT pick the training rate |
| R-3 | Observation staleness on one definition | timestamp differences raw-vs-node for IMU and joints, same script as `finding/056` | D-3 caveat |

`[DECISION-REQUIRED: r1-before-final]` — whether R-1 must precede Phase 3 (recommended if the tank is available within the week; otherwise Phase 3 runs "pre-magnitude-measurement" as §3 records and S1c screens a band).

## 8. Phase 2 (optional, "필요할 경우") — marinelab 5000-iteration screening, one variable per arm

| Arm | vs S0 | Reads |
|:--|:--|:--|
| S0 | incumbent config from scratch, seed 30 | control |
| S1 | + generalized fault sampler (p₀, d) | fault exam matrix + realized exposure + return deficit |
| S1b | + `use_privileged_fault_obs true` on S1 | re-opens the n = 1 rejection |
| S1c | + vertical moment-arm band (only if R-1 says the nominal is off) | pitch actuator assignment under the corrected row |
| S2 | + `control_delay_steps (0,1)` on S1 | delay cost, same seed |

Skip rule: if G0-C clears with margin, S1/S2 are redundant and Phase 3 starts directly. 5000-iteration arms are screening only (curriculum unsaturated by construction, `finding/124`).

## 9. Phases 3–5 — final teacher, selection, robot

**Phase 3 — final teacher, WORKSTATION (user O-4).** `exp/koopman-marine-obs` HEAD, 4096 envs, 10 000 iterations, 50 Hz, Hydra overrides = §5 delta only, `--run_group teacher_ftc_2026_09`; launch guards per `dgx-final-scaleup/HANDOFF-DGX.md` (`TERM=xterm`, `--headless`, `fault.enable=True`, artifact check). Monitoring: `Train/mean_reward`, `DORAEMON/success_rate`, `DORAEMON/mode`, the 10 `Constraint/*` margins, the exposure histogram; iteration-500 abort gate uses the G0-C paired trajectory as reference. Fixed-schedule evals at 2500/5000/7500/10000 on the exam matrix (TB is blind to eval regressions, `finding/297`).

**Phase 4 — selection, distillation, export.** Re-score incumbent + candidates on one machine on the **fault exam matrix**: healthy; each single loss incl. m0 and m3; the real pair `1,1,1,0,0,1` (PRIMARY); other pairs. Decide at `hard`, never at `none`. Pre-registered success: on the real-pair exam, pitch ss_error at `hard` within 2× of roll and roll not worse than the incumbent's healthy-exam roll beyond the paired floor; no collapse on any covered loss. Failure is a result, not a reason to add shaping. Distill GRU (C3 recipe: GRU 128 / head 64, `dagger_mix=select`, β 0.5, λ 1.0) — **the "C3 does not transfer across teachers" claim was RETRACTED** (`decision/263` Update 08-14: that student never trained), so the student is re-validated in-loop as a matter of course, not because a transfer failure was measured. Export packs (`export_deploy_pack.py`), parity atol 1e-5, obs 72D unchanged; re-run `test_deploy_constants.py`.

**Phase 5 — robot, pre-registered, in the vault PLAN by pointer.** New pack, joint-only: T4 protocol with roll AND pitch ±15°; pre-registered pitch: θ2 span ≥ 15° and tracking ≥ 50 % (incumbent: 5–7° / 0.9 %). Then thrusters: `thruster_sign:=[1,1,1,0,0,1]` **passed explicitly every run** and `rosparam get` logged (default is identity, `vault:finding/060`), `fault_reallocate` per `[DECISION-REQUIRED: reallocate]`, `thruster_scale` 0.05 → 0.1 → 0.3. Guards deployment-side only; θ2 crossing π = operator stop.

## 10. Decisions for the user (each with the record behind it and a recommendation)

1. `[DECISION-REQUIRED: scope]` — attitude-only (this program) vs widening to depth. Record: the 72D policy observes absolute yaw but **no depth and no linear velocity** (`observations.py` layout; `finding/240`, `decision/185`); depth needs the obs4 +4 interface (pressure-derived heave rate, IMU specific force — deployable, `decision/185`); XY needs a DVL that does not exist. Recommend: attitude-only now; open a separate `depth-obs4` program after this teacher ships. Yaw stays a rate command (`decision/300`).
2. `[DECISION-REQUIRED: fault-config]` — p₀ and d. Recommend p₀ = 0.15, d = 0.5 (q = 0.075: 37 % / 6.9 % / 0.66 % at severity 1); G0-I/G0-C measure; fallback if the paired probe fails: lower p₀ before touching `performance_lb`.
3. `[DECISION-REQUIRED: seeds]` — you asked "굳이 2시드로 해야하나?". The paired probe (G0-C) is **one seed run twice** (with/without), not two seeds. For the final teacher: 1 seed is sufficient **if the robot is the judge** (constraint 3) and sim-side selection is at `hard` on the exam; 2 seeds only if a sim-side adoption verdict must be decisive on its own (seed floor 56 %, `decision/236`). Recommend: 1 seed + robot judge; add seed 31 only if Phase 4 is ambiguous.
4. `[DECISION-REQUIRED: r1-before-final]` — see §7.
5. `[DECISION-REQUIRED: delay-range]` — (0,1) recommended (user-approved 08-14); (0,2) only if G0-B shows the incumbent tolerates 2 steps cheaply.
6. `[DECISION-REQUIRED: reallocate]` — deploy with `fault_reallocate=false` (recommended; with m3 dead reallocation drops My anyway, `vault:finding/137` §5).
7. `[DECISION-REQUIRED: paper-framing]` — "fault-tolerant attitude control under actuator loss, validated on hardware with real failures" (recommended, user correction 1).
8. `[DECISION-REQUIRED: ksm-nas-role]` — screening only (user O-4); pairing ksm-nas to Orca is optional.

## 11. Work split (user constraint 4) and community (constraint 5)

| Who | What | Ground |
|:--|:--|:--|
| Claude session | decisions, gate readouts, verdicts, plan/community writes | omo: never delegated |
| codex `develop` | §5 sampler change + G0-I unit test; launch scripts; Hydra override check | ground 1 once `fault-config` is decided |
| codex `explore` | bag/log digests, cross-run tables; the 444-post ledger was one such call (`review/306`) | ground 2, ≤ 4 min per call |
| agy | ≤ 5 files per call at effort matching the model tier (`gemini-3.1-pro-high` needs `high`; `-low` needs `low`); 297 s ceiling (`vault:finding/139`) — timed out on 2026-09-03, so reserved for the final two-family review with a compact prompt | ground 4 second family |
| Orca | remote steps on marinelab / ksm-nas (`worker-start --on marinelab`) | user instruction |
| hq community | this PLAN's decisions as `decision/`, each gate readout as `finding/`, session end as `handoff/` | constraint 5 |

## 12. Traceability

Primary posts read in full this revision: marinelab `decision/197, 253, 155, 180, 209, 140, 238, 236, 063 (Update)`, `finding/154, 255, 273, 266, 264, 001, 284, 052`, `handoff/302, 303, 304`; vault `finding/137, 134, 136, 073, 077, 056, 041, 060, 065, 066`, resume-brief §1–§5, `rules-robot-code/SKILL.md`; artifacts `deployed_tam.json`, `deployed_env.yaml` (sha 830be5dd…), `curriculum_trajectory.json` of the incumbent, `envs/main/mdp/faults.py`, `envs/main/mdp/observations.py`, `build_proprio.py`. Vendor calls (all logged in the codeagent ledger): codex ground-4 axis attack; codex ground-2 sweeps ×2 (`review/306` §A/§B); agy ×3 failed (timeout / flag mismatch). External literature R1–R5 from the 2026-09-02 revision is **carried but not re-verified today**. The frozen text is `PLAN.md.bak-round2-frozen`; its `Predicted outcome` and `Risks` sections are superseded by §9 and by the decisions in §10.
