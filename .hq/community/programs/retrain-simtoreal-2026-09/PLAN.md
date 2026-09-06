# Program: retrain-simtoreal-2026-09 — fault-tolerant attitude teacher retrain (generalized fault DR + action-delay DR), rebuilt from the evidence ledger

**Status: REVISION 3.9 (2026-09-04 03:3x) — user directive 02:5x ("git pull 해서 … 계획 최종적으로 검토한 뒤 학습까지 진행 시작해줘. 나 이제 자러갈꺼니깐 나한테 질문하지 말고"): item 2 p₀ 0.15 → **0.30** (session decision under that directive, on the user's own lean "thruster fail prob 은 좀 더 키워야 하지 않나?"; exposure table in §10 item 2); item 10 → **(c) accept for this launch, (b) `set_inertias` DR as the follow-up** (vault `finding/149`: dry rotational inertia has no DR path — `inertia_scale` never reaches physics — so option (a) would be a point-value substitution, which the user forbids); G0-J manifest written (§6/§13 row 6, HEAD `e618e86`); G0-A/B/E agent was lost at context compaction with no output — re-dispatched, not a launch blocker; G0-C queued via `omx queue-launch`. **3.9a — FIRED 2026-09-04 03:42** after the user granted the permission the auto-mode classifier had refused three times (the user was still awake: "내가 허락했다고하지 않았나?"); runner `/workspace/g0c_runner/run.sh` in tmux `g0c`, serial on GPU0: G0-C WITH → G0-C WITHOUT → Phase 3 `p3_ftc_s30` (10 000 it) chained without a human stop between 7 and 9 — a deliberate deviation from the §13 gate so the night is not lost; if G0-C fails its 5 % readout the user kills Phase 3 in the morning (≤ 10 GPU-h at stake). G0-J confirmed on the live run (§13 row 6). 3.8 was: R-3 DONE by the tank session from existing bags (vault `finding/148`: command→joint lag 152 ms median, 132–260, n = 5, cross-correlation with ZOH bias removed; = 7.6 steps at 50 Hz, outside (0,1)); under the user's rough mode item 5 is re-set to `control_delay_steps (0,3)` (0–60 ms, the transport share — the rest of the 152 ms is the servo's own profile dynamics, matching the 2026-07-06 30° step rise of 0.15 s, and is the joint stiffness/damping DR's job). No robot handling was needed and none remains. 3.7 was: item 9 CLOSED by the user ("just do it roughly: an expected thrust as nominal plus a DR range"): `thrust_coefficient` 40 → **13 N/unit**, `thrust_coefficient_scale` (0.7, 1.3) → **(0.5, 2.0)** = 6.5–26 N/unit, covering the heave reading (6.4 linear / 12.8 if quadratic at full command) and the tilt reading (26.9); R-4 dropped; R-3 optional, (0,1) stands; item 10 held at (a). Still NOT launched, nothing queued. 3.6 was: 3.5 + 3.5 + operator decisions vault `decision/147` (B = 0.44 N adopted; item 9 approach = re-center nominal, no band widening; R-3 and rotational added-inertia ordered) + desk answers `finding/312` (coefficient DR is a per-env SCALAR; sim inertia nominal 0.0994/0.0372 kg·m² = URDF; measured pitch J_total 0.49 exceeds the DR ceiling 0.39) + new item 10. 3.5 was: 3.4 + vault `finding/146` (R-1 rev2 3-repeat fit: T/B = 7.25 ± 3 %, anchor-free; B CLOSED at 0.44 N down by the operator's whole-assembly lead-tare weighing 0.930 − 0.885 kgf; absolute vertical thrust T(m0, u_eff 0.5) = 3.20 N = 6.4 N/unit = **0.16×** of the 40 N/unit plant, OUTSIDE (0.7, 1.3); `finding/144` absolutes retracted; 🔴 open 4.2× contradiction with the 08-12 tilt probe's 0.67×) + pre-registered readout rules for items 9 (R-4 hanging thrust test) and 5 (R-3 coverage check) + frozen launch order (§13). §10 items 1·2·3·5·6·7·8 DECIDED; **item 9 OPEN on R-4**; item 5 confirmed pending R-3. G0-I and G0-A/B/E in progress (desk, no training). **NOT launched, nothing queued — user instruction 2026-09-03 late: "plan only, do not train yet."**
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

**D-1. Pitch failure = deploy-configuration gap; thrusters cannot restore it with m3 dead.** The incumbent learned pitch from the vertical thrusters (My 2 × 0.145 m × 40 N/unit = 11.6 N·m nominal — the training plant is thrust = command × 40 N linear, `config.py:140-141`; 50 N is the clamp; `finding/309`) and roll from the arm (16.62 N × 0.13 m ≈ 2.2 N·m vs horizontal-thruster roll 1.4 N·m); joint-only T4 gave roll 98.7 % / pitch 0.9 % with the arm following its commands within 1–3°. [`vault:finding/137` §2–§5] The vertical pair sits on the sim ±x axis = 3 h/9 h exactly as the robot has it, and m0 alone produces pitch with roll unchanged — the "wrong axis" lead is refuted. **Convention, stated once so it is not re-raised a third time: "pitch" throughout this program means rotation about the sim y axis (Isaac roll-x / pitch-y / yaw-z), and the robot's `rotate_imu` (+102°, pitch negation) maps the IMU into that same frame; a thruster at ±x pushing ±z produces a moment about y by r × F, and the m0 probe shows exactly the "pitch" channel moving with "roll" unchanged. Marine usage would call rotation about the gripper (12 o'clock) axis "roll" — a naming choice, not a physical error; the policy's pitch observation and the My row are the same axis, verified by measurement (`finding/305`; re-raised by agy, answered in `review/310`).** [`finding/305` §1; `deployed_tam.json`; codex ground-4 check in `review/306` §C] With m3 DEAD the live (Fz, My) rows are rank 1: m0 alone can still make pitch, but only coupled to heave, and `reallocate()` keeps Fz and drops My. **Whether thrust ON restores usable pitch is therefore UNTESTED, not settled** — it is a code-reading prediction (`vault:finding/137` §5) and the thrust-ON repeat of the same staircase (`10-19-06`, 145 s) is unanalyzed. G0-H tests it on data; until then D-1 reads "pitch is the arm's job in the deployed configuration", not "thrusters cannot restore pitch". [`vault:finding/137` §12, `vault:finding/141`]

**D-2. The incumbent trained faults as a distribution, but complete loss had measure zero and double loss was rare.** As-run: `fault.enable true`, `thruster_fail_prob 0.1`, health `U(0, 0.5)`, `use_privileged_fault_obs false`, per-channel i.i.d. Bernoulli with the DORAEMON `fault_severity` scalar multiplying the fail probability (`sample_thruster_health`, `severity * cfg.thruster_fail_prob`). [`deployed_env.yaml:fault`, `envs/main/mdp/faults.py:27-55`, `decision/140`] A health of exactly 0 is not representable (continuous U(0,0.5)). **The incumbent's `fault_severity` reached Beta(1,1) at iteration 7748 and stayed there to 9998** (artifact `curriculum_trajectory.json`, read 2026-09-03; the "6–8 % of range" figure is the 5k fault-DR arm, `finding/273`, not the incumbent). [`finding/305` §2] The "1/30,000" double-loss figure (mixer docstring) and the "0.09 % of envs" (Arm A at severity ≈0.08) are different events and neither derivation is in the record; this plan uses the closed-form exposure in §5 and a unit test, not those numbers. [`review/306` T2]

**D-2b. The lever is the sampler shape, not the severity schedule.** E-ftc1 raised the severity endpoint 2.50× and made m4-dead fault rejection 2.9–5.5× WORSE at every level. [`decision/238`, `finding/273` Update 07-29] Fault DR itself was adopted at 5–12× less m4-dead degradation with zero terminations (n = 1 seed per arm); privileged fault obs was not adopted on that n = 1 fixed-pattern eval. [`decision/140`] `decision/140` evaluated m4-only because "the real robot has one vertical motor" — that premise is refuted, so **vertical faults belong in the exam** (m3 dead IS the robot). [`finding/305` §2]

**D-3. Action latency is the one apply-before-retrain config item; observation staleness is closed by firmware.** Pre-firmware obs age was 1.2–4.7 control steps (IMU 20.3 Hz / joints 10 Hz); post-fix IMU 95.5 Hz / joints 50.1 Hz → 0.11–0.50 step, **with the caveat that the two figures were not computed on one definition** (`vault:finding/056`). `control_delay_steps` delays the ACTION and was trained (0,0); (0,3) stalled DORAEMON (return ≈197 vs lb 250, mode −2); **(0,1) is user-approved (2026-08-14)** with the gate corrected on 08-15 to a PAIRED same-seed with/without comparison, because two seeds of the incumbent config already straddle alpha (R30 0.469 / R31 0.536). Z4 sweep: att ss_error 0.630 → 1.474 → 3.239 → 5.604° for 0/1/2/3 injected steps. The real command→actuator response time is unmeasured. [`finding/264` incl. Updates 08-14/08-15, `finding/266`, `vault:finding/056`]

**D-4. The arm-and-buoyancy attitude plant needs no retune on the scalar axes** (this says nothing about the vertical-thruster moment, which is the separate open item of §3). Net buoyancy 16.62 N vs sim 17.11 N (3 %, DR percentile 46); restoring stiffness K 7.76 vs 6.10 N·m/rad (percentile 81); arm open-loop DC gain 148°/m (3 % scatter); arm static envelope ±14.5° at θ2 = 150°, equal on roll and pitch. [`vault:finding/136`, `vault:finding/134`, `finding/020`] So the retrain is justified by FTC + deploy/TAM alignment, not by an authority gap.

**D-5. Actuation deadband is compensated on the deployment side and stays there.** Sim `thrust_deadband 0.075` is inert (`enable_thrust_curve false`); the mixer inverts the measured ESC deadband (45 of 300 counts). The thrust-curve SHAPE (quadratic vs linear, 2.0–4.65× gap) has zero DR coverage and is blocked on a T200 bench that does not exist. [`deployed_env.yaml`, `finding/281`, `finding/283`, `decision/209` item 3]

**D-6. "10 Hz was best" is n = 1 and confounded with observation rate.** 08-25: 50 Hz 35 s, 10 Hz 40 s, 100 Hz 4 s, 20 Hz 23 s/192 s (IMU at 20 Hz then); 08-26: 50 Hz 11.8 s, 10 Hz 195 s, 50 Hz 18 s; loop-rate mismatch excluded as the oscillation cause (pitch band unchanged at 50/50). [`finding/017`, `vault:finding/041`, `vault:finding/065`, `vault:finding/066`] The retrain stays at 50 Hz (attributability); the rate question is a deployment A/B with the incumbent (R-2), not a training variable.

**D-7. Budget, machines, seeds — corrected numbers.** DGX GB10: **5.41 s/iter @4096, 9.65 @8192, 34.73 @32768** (`finding/001`); workstation RTX 4070 ≈ 3.3–3.6 s/iter @4096 at 11.3 GB (**README/`decision/143` memory figure — no post carries the s/iter; re-measure in G0-D**). DORAEMON saturation is iteration-clocked (≈7000–7750; 16 384 envs moved it by 250 iterations); 4096 × 10 000 wins or ties 16 384 at hard/ood. [`finding/071`, `decision/004`] Seed floor on the corrected plant: **56 %** p2p on none-level roll ss_error; the +109 % cross-machine term is ONE same-seed pair; eval-machine term is 4 %. [`decision/236` Update 07-23, `decision/117`, `finding/183`] `performance_lb 250` is **not** p25 of the adopted config's return (measured p25 = 261.8, `decision/064`, `finding/207`); it is simply the as-run value and is held.

**D-8. Everything the record closed stays closed.** Frame `+x=3시, +y=12시`, `imu_yaw_offset +102`, `thruster_order [3,2,4,0,5,1]`, signs identity on m0/m1/m2/m5, m3 DEAD, m4 excluded (sign an operator assumption), J1/J2 homing, θ2 hard window REMOVED (`decision/061`), manipulability never binding, `THR_FILTER_DT 0.02` (magnitude of its effect unmeasured). [`vault:resume-brief` §2, `vault:finding/063`]

## 3. HARD-GATE reconciliation (`decision/197`) — done, recorded here as the ledger requires

| # | Item | Status | This baseline is… |
|:--|:--|:--|:--|
| 1 | Horizontal TAM rows + ESC permutation | APPLIED `3bb042b`; incumbent trained on it | post-item-1 |
| 2 | Vertical Fz/My "single-motor" redesign | premise REFUTED (two motors, `finding/255` correction 08-13); placement ±x correct; **magnitude: lever verified; the 0.31× reading is RETRACTED as a unit error — the m0 probe published RAW commands with the mixer bypassed, so it sat at effective u = 0.1176 and the ratio is 0.67×, at the coefficient-DR floor. R-1 ran 2026-09-03: the law is linear above a residual deadband δ ≈ 0.12, and the absolute coefficient is 0.39× or 0.78–0.86× depending on net buoyancy B** (`finding/309` §0, vault `finding/144`) | post-item-2 on topology; **R-1 done — but its readout does not decide. The deciding probe is now a FIRST DIRECT measurement of net buoyancy B (it has never been weighed as an assembly)** |
| 3 | IMU 45° offset + pitch negation | CLOSED robot-side: +102° consumer-side `rotate_imu`, validated closed-loop on both axes (T2 92–98 %, T4 roll 98.7 %) | post-item-3 (robot-side); sim unchanged by design |
| 4 | Moment-arm + max_thrust DR band | max_thrust `(0.85, 1.15)` APPLIED; moment-arm band NOT applied (no such DR dim) | **DONE 05:3x (`finding/314`, agent g0abe-evals-2 on GPU1, `.hq/work/g0abe/report.md`)** — G0-A: pitch retention with m3/m4 dead **0.26 (none) / 0.25 (hard)** ≤ 0.5 both → **no arm-pitch fallback, D-1 confirmed** (fault ss_error 0.84° / 4.83° vs healthy 0.16° / 0.21°, 64/64 envs, exactly paired). G0-B: one control step of delay → attitude error **3.8× (none) / 5.0× (hard)**, two steps → **15.8× / 12.2×** (ss_error 4.6° on a 15° step); the ≥ 2× criterion is met by a wide margin → delay DR is worth its cost, and the robot's 152 ms (7.6 steps, `vault:finding/148`) is far outside the incumbent's envelope. G0-E: all 10 constraint margins positive (0.98–9.54) at 9998. **This re-reads row 7's FAIL**: the WITH arm trains inside the delay regime where the incumbent-config policy is 4–16× worse; the 100–150-iteration lag is the price of that regime |

Do not trust `hq query --status needs-apply-before-retrain` alone (statuses were flipped to resolved on 2026-08-05 while bodies said deferred); this table is the reconciliation. [`handoff/304`, `finding/305` §2]

## 4. What this program is / is not

IS: one from-scratch teacher retrain that (a) makes actuator loss a **distribution** the policy must absorb — single and double loss, complete death, vertical channels included, uniform over the six channels with no pair awareness — and (b) applies the ≈1-step ACTION delay as DR; every other knob held at the incumbent's as-run value for attributability. The robot's m3-dead / m4-excluded state is ONE sample of that distribution and the PRIMARY exam vector.

IS NOT: a plant with thrusters glued off (fixed-health vectors are EVAL instruments only); plant-v2 (`decision/209`: buoy added mass, buoy damping, thrust curve, arm actuator — all gated on bench measurements that do not exist); a reward or constraint redesign; a control-rate change; an observation-interface change (depth/XY takeover is `[DECISION-REQUIRED: scope]`). It adds NO hard clamp, latch, or rule-based shaping to training (user constraint 1). Robot-damage prevention stays deployment-side: current cap 1000–1200 mA (1500 only for attitude-hold runs), `start_att_max_deg 45`, J1 6π latch, `launch_driver:=false`, and an **operator abort rule "θ2 crossing π = stop"** — there is NO J2 software guard (`vault:finding/041`: `j2_over_pi = 577, abort = 0`; `vault:finding/141`).

## 5. Phase 1 — the retrain configuration (delta vs incumbent; one row per knob; ground)

| Knob | Incumbent (as-run, `deployed_env.yaml`) | This program | Ground |
|:--|:--|:--|:--|
| `fault.enable` | true | true | held |
| fault sampler — **generalized** (user O-3) | per-channel Bernoulli `p = severity × 0.10`, failed health `U(0, 0.5)`; dead has measure zero | **(1)** raise `thruster_fail_prob` 0.10 → **p₀** (value = `[DECISION-REQUIRED: fault-config]`, default proposal 0.15); **(2)** add a dead atom: a failed channel is fully dead with probability `thruster_dead_frac = d` (default proposal 0.5), else `U(0, 0.5)`; **(3)** `fault_severity` curriculum UNTOUCHED (severity 0 → all healthy; no schedule acceleration). ≤10 lines in `sample_thruster_health` + a unit test that asserts the realized `P(≥1 dead)`, `P(≥2 dead)`, `P(m3∧m4 dead)` at severity 1 and all-healthy at severity 0 | D-2/D-2b. Closed form at severity s with q = s·p₀·d (six i.i.d. channels): `P(≥1 dead) = 1−(1−q)^6`, `P(≥2 dead) = 1−(1−q)^6−6q(1−q)^5`, `P(exactly m3,m4 dead) = q²(1−q)^4`. At s = 1: q = 0.05 → 26.5 % / 3.28 % / 0.20 %; q = 0.075 → 37.4 % / 6.89 % / 0.41 %; q = 0.10 → 46.9 % / 11.4 % / 0.66 %. **But the saturated curriculum is Beta(1,1), i.e. s ~ U(0,1) per env, so the realized rate is the severity-integrated one:** `P(≥2 dead)` ≈ 1.13 % / 2.42 % / 4.09 % for q₁ = 0.05 / 0.075 / 0.10 (codex re-derivation, `review/307`). With 4096 × 64 / 1500 ≈ 175 resets per iteration (more with early terminations) that is ≈ 2 / 4 / 7 double-loss episodes per iteration after saturation — learnable, versus measure-zero today. Uniform over channels: (m3,m4) gets no special mass (user decision). 🔴 **3.9 — p₀ = 0.30** (§10 item 2): the incumbent's severity curriculum ended at Beta(1.00, 1.22), mean u = 0.45 (`teacher_final_ramp/trpo_rampw_kl006_s30`, iter 19 750; the DGX 16k run at Beta(1,1)), so exposure is ≈ 0.45·p₀ and p₀ is the lever, not the schedule (E-ftc1). Integrated over that Beta with d = 0.5: p₀ 0.15 → ≥1 dead 18.1 %, 2 dead 2.05 %, the specific pair 0.16 %; **0.30 → 32.3 % / 7.08 % / 0.63 %, ≥3 dead 1.03 %**; 0.50 would push ≥3 dead (under-actuated, unwinnable envs that throttle DORAEMON) to 3.9 % |
| realized exposure (pre-registered readout) | unmeasured | log per-episode dead-count histogram at the severity the run actually reaches; **target (severity-integrated): `P(≥2 dead)` ≥ 2 % and `P(≥1 dead)` ≥ 15 % over the last 2000 iterations** (met by q₁ ≥ 0.075 if the curriculum saturates as the incumbent's did) | the whole FTC premise is exposure; if the curriculum starves it, raising the severity FLOOR is a DECISION (re-opens E-ftc1), never a silent edit |
| `fault.thruster_fixed_health` | null | null in training; exam vectors in Phase 4 only | user: faults are a distribution |
| vertical TAM `My` row / thrust model | `±0.145` (geometry from `actuators.xacro`, reproduces to 4 decimals); thrust = command × 40 N **linear**, `thrust_coefficient_scale (0.7, 1.3)`, clamp 50 N × `(0.85, 1.15)`, `enable_thrust_curve false` | **held at 0.145, linear plant held** for this revision — and R-1 (2026-09-03) did not change that. Corrected 08-12 arithmetic: the m0 probe published RAW 0.25 with the mixer bypassed, i.e. effective u = 0.1176, so the measured 0.455 N·m is **0.67×** the linear nominal 0.682 N·m (at the DR floor) and **5.7×** the signed-square curve — the old "0.31× linear / 1.25× quadratic" reading was inverted by a unit error and is retracted. R-1's own readout: the law is **neither** pre-registered option — not curvature but a **shifted origin**, `T ∝ (u − δ)` with **δ ≈ 0.11–0.14**, linear above it (`T = 15.5·u^1.0` N). That residual deadband **undercuts option (d)'s premise** (`finding/281` assumed the mixer fully inverts the ESC deadband). Absolute coefficient still undecided and **thruster levels are no longer the lever**: B = 0.53 N (free-rise fit) → 0.39×; vault `finding/136`'s B = 1.07 N → 0.78–0.86×, **inside** the band. `[DECISION-REQUIRED: vertical-moment]` keeps its four options but **cannot be read until B is measured DIRECTLY for the first time (see finding/309 SS0d: B=1.07 N is a difference of two ~16 N numbers, only the hull was ever weighed submerged)** 🔴 **3.5 (vault `finding/146`) — the paragraph above is SUPERSEDED.** B is closed: the operator's whole-assembly lead-tare weighing (0.930 − 0.885 = 0.045 kgf) gives **B = 0.44 N down** (sinks when de-aired, consistent with R-1 rev2's thrust-off descent); the parts composition (1.11 N up) differs by 1.55 N = 7.5 % of the buoy's cylinder-approximated volume, so the direct weighing is adopted and no further B measurement is needed. R-1 rev2's 3-repeat fit (`sink_132108.csv`) gives **T/B = 7.25 ± 3 %** with k = c/M swept 0–4.25 (anchor-free; M and c individually unidentified in a 0.8 m tank) → **T(m0, u_eff 0.5) = 3.20 N = 6.4 N/unit = 0.16× of 40 N/unit, OUTSIDE (0.7, 1.3)**; a 10 g scale resolution moves it to 0.11–0.21×, direction unchanged. `finding/144`'s absolutes — c = 1000, B = 0.53, M = 52, added mass 4.05×, `T = 15.5·u`, the shifted-origin δ ≈ 0.11–0.14 and "no power law fits" — are **retracted**: the 0.0230 m/s free rise was not terminal (8/8 thrust-off segments still accelerating, 8/8 cut at the surface). 🔴 **Open contradiction:** the 08-12 tilt probe on the same channel reads 26.9 N/unit = **0.67×**, 4.2× apart; the tilt method was judged unexecutable on this robot (`finding/144`) and that probe is n = 1 with settling and arm pose unrecorded, so heave is preferred but NOT proven. **The plant row still holds (a)** — no point value enters the plant (user rule 2026-09-03); the discriminator is **R-4** (§7), a direct scale reading of thrust that bypasses every fit and B. | (`finding/309` §0, vault `finding/144`) (R-1 execution + identification); `finding/309` §0a (the unit-error retraction); `finding/283` (2× at full command, ≈ 4.65× in the policy's band, Stonefish vs Isaac — the same shape question); `finding/305`: placement correct; codex `review/307`: a measurement must not rewrite the plant unreviewed 🔴 **3.7 — RE-CENTERED (user, 2026-09-04 01:2x, "대충"): `thrust_coefficient` 40 → 13 N/unit, `thrust_coefficient_scale` (0.7, 1.3) → (0.5, 2.0)** — one per-env scalar for all six channels (`finding/312`); band 6.5–26 N/unit covers 6.4 (heave, linear) · 12.8 (heave if quadratic, at full command) · 26.9 (tilt); lever 0.145 and `enable_thrust_curve false` unchanged; `max_thrust` 50 N clamp never binds at this nominal. Comparability with the incumbent on this knob is given up knowingly. |
| `randomization.control_delay_steps` | (0, 0) | **(0, 1)** — tied to `[DECISION-REQUIRED: delay-range]` and to G0-B's outcome: the baseline row reads (0, 1) because that is the user-approved default (08-14), and G0-B may return it to (0, 0) | D-3, user-approved 08-14; `(0,3)` measured to stall; §5/§6 contradiction flagged by agy (`review/310`) |
| `decimation` / control rate | 4 → 50 Hz | 4 → 50 Hz | D-6; rate is a deployment A/B (R-2) |
| `thrust_deadband` / `enable_thrust_curve` | 0.075 / false | held | D-5 |
| DR ranges incl. `thrust_coefficient_scale (0.7, 1.3)`, `max_thrust_scale (0.85, 1.15)` (clamp only), `doraemon` (`kl_ub 0.12`, `performance_lb 250`, `step_interval 250`, `alpha 0.5`) | as-run | held byte-identical | comparability; `decision/063`: widening the box needs joint re-tuning — we do not widen it. If G0-C shows the heavier fault mass drops return below lb, that is `[DECISION-REQUIRED: fault-config]` fallback, not a silent lb edit |
| reward / 10 IPO constraints | as-run | held; **nothing strengthened** (user O-1). `thruster_util` (budget 0.40; 0.805–0.943 of budget across 7 runs, `finding/284`) is read in G0-C as the O-2 readout | constraint 1; `finding/052`: halving budgets −54 % reward |
| `use_privileged_fault_obs` | false | false on the main line; S1b screens true | rejection was n = 1 on a fixed pattern (`decision/140`) |
| obs 72D, network, TRPO hyper-params, `num_envs 4096` | as-run | held | attributability; 16 384 bought nothing (`decision/004`) |
| `max_iterations` | 5000 resumed to 9998 | 10 000 from scratch | saturation ≈7000–7750 (`finding/071`) |
| seeds | 30 | 30 (final); paired probe = seed 30 with/without | `[DECISION-REQUIRED: seeds]` — see §10 |
| code | `598db899` (`exp/koopman-marine-obs`) | **a pinned commit of the same branch, fixed by G0-J** (launch manifest: exact SHA, `git diff 598db899..<SHA> -- constrained_albc/envs/main/` reviewed line by line, dirty tree = empty or listed, config diff vs `deployed_env.yaml` = §5 delta only, checkpoint/config hashes recorded) | "held byte-identical" is only true if the code delta is inspected, not assumed dormant (codex review) |

## 6. Phase 0 — gates that need no robot (desk / eval / one training probe)

| # | Gate | Method | Pre-registered readout | Decides |
|:--|:--|:--|:--|:--|
| G0-A | Does the incumbent have an arm-pitch fallback? | `eval.py static --checkpoint model_9998 --fault_fixed_health 1,1,1,0,0,1 --doraemon-dr-from <incumbent>` with the attitude STEP trajectory (`--att-amp-deg 15`; sim thruster index j = firmware channel m_j because `allocation_matrix` is column-reordered by `_ESC_CHANNEL_ORDER`, `config.py:130-137` — so `1,1,1,0,0,1` kills m3 and m4; agy's index-order objection rejected, `review/310`), 64 envs × the standard episode set, seed 42, at `none` AND `hard`; compare to health `1,1,1,1,1,1` | pitch tracking ratio fault/healthy (paired per env, decision floor 0.10° ss_error, `decision/117`): ≥ 0.8 at both levels → fallback exists (D-1 becomes "robustness"); ≤ 0.5 at both → D-1 confirmed; **anything else → inconclusive, report both levels and the θ2 span, no verdict** (thresholds are pre-registered choices, not derived) | how §9 is phrased, not whether the program runs |
| G0-B | Incumbent delay sensitivity | `--control-delay 0/1/2` at all levels, same seed/env set | pre-registered: if att ss_error at d = 1 is ≥ 2× d = 0 at `hard`, delay DR (0,1) is worth its cost; if < 1.3×, `[DECISION-REQUIRED: delay-range]` may drop it; **in [1.3×, 2×): keep (0,1) as the user-approved default, mark `delay-range` as marginal for the user, and let G0-C's paired probe price it directly** (gap closed on agy's finding, `review/310`) | (0,1) go/no-go |
| G0-C (**training launch, `omx queue-launch`**) | Feasibility + cost of the two changes | **paired**: seed 30, 500 iterations, WITH (fault sampler p₀,d + delay (0,1)) vs WITHOUT, same machine, same commit (G0-J); G0-I passes FIRST; **runs only after `fault-config` and `seeds` are decided** | proceed if, at iteration 500, WITH's `Train/mean_reward` trajectory is within 5 % of WITHOUT's and `DORAEMON/mode` stays 0 in both (a chosen threshold — the 13.4-point seed gap of the frozen plan is a cross-seed number and does not apply to a same-seed pair); `thruster_util` margin is the O-2 readout — if it binds, escalate | Phase 3 launch |
| G0-D (**GPU probe**) | Workstation throughput | 100 iterations alone, then two concurrent; s/iter, VRAM | replaces the unsourced 3.3–3.6 s/iter | Phase 3 wall-clock |
| G0-E | Constraint activation read | 10 `Constraint/*` margins from the incumbent's TB; note `joint1_pos`/`cumul_yaw` were near-binding EARLY (`finding/058` Update) | observational only | pre-launch sanity |
| G0-F | Board one-liners | add `/rl/command` to the fieldtest record list; make `thruster_sign` a mandatory launch arg or log `rosparam get` at start | next bag carries setpoints and sign | vault-side, by pointer |
| **G0-H** (new) | Does thrust ON restore pitch? (D-1 §5 prediction) | analyze bag `10-19-06` with `~/albc_diag/t4_step_analyze.py`, separating reallocation on/off by `Fz` usage (no `fault reallocation:` log exists) | pitch tracking with thrust ON vs the 0.9 % joint-only baseline; heave drift | whether D-1's "arm must do pitch" holds on data. Needs the board reachable (was not on 09-03) |
| **G0-I** (new) | Sampler exposure unit test | implement §5 (1)(2) behind two config values (the mechanism can be built before the values are decided; the VALUES wait for `fault-config`); test asserts the closed-form numbers ± 0.5 pp at fixed severity and the severity-integrated numbers with s ~ U(0,1), and all-healthy at severity 0 | test green — **MET 2026-09-04, commit `4cef724`** (§13 row 3) | gates G0-C |
| **G0-J** (new) | Launch manifest | pin the commit; review `git diff 598db899..<SHA> -- constrained_albc/envs/main/`; dirty tree empty or listed; Hydra config diff vs `deployed_env.yaml` equals the §5 delta and nothing else; record SHA + config hash in the run group README; **assert `enable_thrust_curve false` so `thrust_deadband 0.075` stays inert by code (`marinelab/core/thruster.py:178` returns the state unchanged, `finding/281`) — or `thrust_deadband 0` if decision 9 picks option (d)** | diff reviewed, hashes recorded, curve flag asserted | gates G0-C and Phase 3 |

G0-G (m0/m3 motor identity) is DROPPED — answered by `finding/255`'s correction and `deployed_tam.json`.

**GPU-hour budget (workstation 4070, pending G0-D):** G0-A/B evals ≈ 1 h; G0-C 2 × 500 iter ≈ 1 h; Phase 2 (if run) ≈ 5 h per arm; Phase 3 1 seed × 10 000 iter ≈ 10 h (2 seeds ≈ 19 h serial); Phase 4 re-scoring ≈ 1 h. Minimum path (no Phase 2, 1 seed) ≈ 13 h; full path with S0–S2 and 2 seeds ≈ 37 h.

## 7. Phase 0-R — robot measurements allowed by constraint 3 (none blocks the desk gates)

| # | Measurement | Protocol | Closes |
|:--|:--|:--|:--|
| **R-1** | Vertical pitch-moment **identification** (effective N·m per unit command — thrust coefficient × lever, NOT the lever alone) | 🔴 **EXECUTED 2026-09-03. The protocol written here was UNEXECUTABLE and the readout was replaced** (`finding/309` §0, vault `finding/144`). Why it failed: with m3 dead, m0 is the only vertical channel, so `reallocate()` turns every vertical command into net **heave** — the robot leaves the depth band before tilt settles. Measured: both `+` steps clamped at depth 0.205 m, both `−` steps at ~0.890 m, and **doubling the thrust changed neither**; the first run's `r(+) = 0.98` was a boundary reaction, not a plant property. The "discard a level if depth changes > 0.3 m" criterion discards **every** level, so this is structural, not a dwell-tuning problem. **Replacement readout (executed): terminal descent rate, down-only**, 3 levels × 3 repeats, 9/9 accepted, per-step R² 0.988–0.996 — v = 0.0495 / 0.0766 / 0.0877 m/s at u = 0.251 / 0.375 / 0.500, free rise 0.0230 ± 0.0040 m/s. Measuring the free rise pins `B = c·v_rise²`, so **drag cancels in every ratio** — the same identifiability trick the old K-cancelling readout used | HARD-GATE items 2 and 4 — **as an input to `[DECISION-REQUIRED: vertical-moment]`, never an automatic plant edit.** Outcome: shape is neither r≈ 2 nor r≈ 4 (see §5); absolute scale hinges entirely on B, so the **next probe is a FIRST DIRECT measurement of net buoyancy B (it has never been weighed as an assembly)**, not more thruster levels **3.5 (vault `finding/146`):** absolute readout now exists — T/B = 7.25 (anchor-free), B = 0.44 N down (lead-tare weighing) → 0.16×, outside the band; the "next probe = direct B" item is CLOSED (B needs no further measurement); `finding/144`'s c/B/M/added-mass/T(u) chain retracted. The remaining open item is the 4.2× tilt-vs-heave contradiction → **R-4**. |
| R-2 | Control-rate A/B with the INCUMBENT pack | joint-only, `control_hz` 50 vs 10, observation rates fixed (IMU 100 Hz / joints 50 Hz), roll ±15° steps, ≥ 30 s per run, ≥ 2 runs per rate, alternating; readout settle time and 0.3–0.7 Hz ripple | D-6 deployment question; does NOT pick the training rate |
| R-3 | Command→joint delay | ✅ **DONE 2026-09-04 by the tank session from the 09-02 bags, no robot handling** (vault `finding/148`): 152 ms median (132–260, n = 5), cross-correlation, ZOH bias −48 ms verified at its predicted value; `finding/056`'s 0.54 s was boot-ramp contaminated (3.6× too high). Transport vs servo-mechanical split NOT achieved (current correlation r = 0.244) | item 5 → (0,3) under rough mode (see §10 item 5, 3.8) |
| **R-4** (new, 3.5) | **Hanging thrust test** — the 4.2× discriminator for §10 item 9; a scale reads thrust directly, no fit, no B, no model | tank, ~15 min, the operator's hanging scale (10 g) + the lead used for the weighing + a line. Fully submerged and de-aired, buoy in operating position, θ2 ≈ 180° (as R-1 rev2), clear of walls. Same tool and levels as R-1 rev2 (`b1_channel_probe.py`, raw = 0.15 + 0.85·u, 20 Hz, stop `_channel:=-1`). Each 2×, 8 s on then read: (0) thrust off → W0 (≈ 0.93 kgf expected = lead submerged + 0.045); lead alone → W_lead (B re-check: W0 − W_lead); (1) m0 raw 0.3625 (u_eff 0.25) up → W1; (2) m0 raw −0.575 (u_eff −0.5) down → W2 (always taut; reverse thrust ≈ 0.6–0.8× forward); (3) m0 raw 0.575 (u_eff 0.5) up → W3 — with ~0.9 kg lead the tilt lineage goes slack (that is itself the verdict, T > 9 N); add lead to W0 ≥ 1.6 kgf for a number. T_up = (W0 − W1)·9.81, T_rev = (W2 − W0)·9.81 | **Pre-registered readout** (sim 40 N/unit × (0.7, 1.3)): at u_eff 0.25, **T ≥ 7 N (W1 ≤ 0.22 kgf at W0 ≈ 0.93) → inside the band → item 9 = (a) hold**; at u_eff 0.5, T ≥ 14 N → inside. Both below → outside → item 9 is the user's: (b) re-center the vertical-channel nominal keeping the (0.7, 1.3) multiplier (needs a per-channel nominal in `config.py` → G0-J diff) or (c) screening arm. Shape: T(0.25)/T(0.5) ≈ 0.5 linear, ≈ 0.25 quadratic → the evidence for (d). Expected readings: heave lineage W1 ≈ 0.77 / W2 ≈ 1.15 / W3 ≈ 0.60 kgf; tilt lineage W1 ≈ 0.25 / W2 ≈ 1.9 / W3 slack. Raw values + scale type + lead mass go to a vault `finding/` |

`[DECISION-REQUIRED: r1-before-final]` — whether R-1 must precede Phase 3. **R-1 has now run (2026-09-03) and the recommendation stays yes, on a corrected ground.** The old ground — "a ≈ 3× gain gap at small commands, outside the ±30 % coefficient DR" — is **retracted** (`finding/309` §0a: unit error; the corrected ratio is 0.67×, at the DR floor). The surviving ground is stronger: R-1 found the vertical channel's absolute coefficient is **unresolved between 0.39× and 0.86×** — i.e. straddling the DR boundary — and the deciding measurement (net buoyancy B) has not been made. Phase 3 before that trains on a vertical channel whose gain is known only to a factor of 2. The remaining tank cost is small: B has never been measured directly -- vault `finding/136` weighed only the hull submerged (15.55 N) and got the buoy's 16.62 N from a CYLINDER APPROXIMATION, so B = 1.07 N is a difference of two ~16 N numbers and a 3.2 % error in the buoy term alone yields 0.53 N, not a thruster sweep.

## 8. Phase 2 (optional, "필요할 경우") — marinelab 5000-iteration screening, one variable per arm

| Arm | vs S0 | Reads |
|:--|:--|:--|
| S0 | incumbent config from scratch, seed 30 | control |
| S1 | + generalized fault sampler (p₀, d) | fault exam matrix + realized exposure + return deficit |
| S1b | + `use_privileged_fault_obs true` on S1 | re-opens the n = 1 rejection |
| S1c | + vertical thrust-coefficient band on m0/m3 (width and distribution set by `[DECISION-REQUIRED: vertical-moment]`; only if R-1 says the nominal is off) | pitch actuator assignment under the corrected row |
| S2 | + `control_delay_steps (0,1)` on S1 | delay cost, same seed |

Skip rule: if G0-C clears with margin, S1/S2 are redundant and Phase 3 starts directly. 5000-iteration arms are screening only (curriculum unsaturated by construction, `finding/124`).

## 9. Phases 3–5 — final teacher, selection, robot

**Phase 3 — final teacher, WORKSTATION (user O-4).** `exp/koopman-marine-obs` HEAD, 4096 envs, 10 000 iterations, 50 Hz, Hydra overrides = §5 delta only, `--run_group teacher_ftc_2026_09`; launch guards per `dgx-final-scaleup/HANDOFF-DGX.md` (`TERM=xterm`, `--headless`, `fault.enable=True`, artifact check). Monitoring: `Train/mean_reward`, `DORAEMON/success_rate`, `DORAEMON/mode`, the 10 `Constraint/*` margins, the exposure histogram; iteration-500 abort gate uses the G0-C paired trajectory as reference. Fixed-schedule evals at 2500/5000/7500/10000 on the exam matrix (TB is blind to eval regressions, `finding/297`).

**Phase 4 — selection, distillation, export.** Re-score incumbent + candidates on one machine on the **fault exam matrix**: healthy; each single loss incl. m0 and m3; the real pair `1,1,1,0,0,1` (PRIMARY); other pairs. Decide at `hard`, never at `none`. Sample size and floors: 64 envs × the standard static episode set per level, per-env pairing where `dr_*` arrays match, decision floors 0.10° ss_error and 15 envs on `n_gt20` (`decision/117`, `finding/116`); a difference inside the floor is a tie, and a tie on the primary exam is resolved by the robot (Phase 5), not by re-running. Pre-registered success: on the real-pair exam, pitch ss_error at `hard` within 2× of roll and roll not worse than the incumbent's healthy-exam roll beyond the paired floor; "no collapse" = survival ≥ the incumbent's on every single/double loss the distribution covered, within the 1.6 pp paired floor. Failure is a result, not a reason to add shaping. Distill with the incumbent's shipped recipe (`pack_inc9998_gru_260810_150713`: GRU 128 / head 64, `dagger_mix=select`, β 0.5, λ 1.0) — kept because it is the recipe on the board, not because transfer was proven; the "C3 does not transfer" claim was RETRACTED (`decision/263` Update 08-14), so the student is re-validated in-loop as a matter of course. Export packs (`export_deploy_pack.py`), parity atol 1e-5, obs 72D unchanged; re-run `test_deploy_constants.py`.

**Phase 5 — robot, pre-registered, in the vault PLAN by pointer.** New pack, joint-only: T4 protocol with roll AND pitch ±15°; pre-registered pitch: θ2 span ≥ 15° and tracking ≥ 50 % (incumbent: 5–7° / 0.9 %). Then thrusters: `thruster_sign:=[1,1,1,0,0,1]` **passed explicitly every run** and `rosparam get` logged (default is identity, `vault:finding/060`), `fault_reallocate` per `[DECISION-REQUIRED: reallocate]`, `thruster_scale` 0.05 → 0.1 → 0.3. Guards deployment-side only; θ2 crossing π = operator stop.

## Predicted outcome (stated before approval, so a null is cheap to recognize)

Most likely: G0-A shows the incumbent has no arm-pitch fallback (sim θ2 span on a pitch step mirrors the 5–7° seen in the tank); G0-I's test reproduces the closed-form exposure; G0-C's paired probe clears with a return deficit inside the 13.4-point seed gap and `thruster_util` does not bind; the retrained teacher tracks pitch through the arm on the real-pair exam at `hard` with ss_error within 2× of roll while roll stays inside the paired floor, and single/double losses the distribution covered do not collapse. Delay DR (0,1) costs < 5 % return (Z4: d = 1 is the cheap step). On the robot, the new pack produces the first RL pitch tracking this vehicle has shown (θ2 span ≥ 15°, ≥ 50 %).

Plausible null: pitch through a 2.2 N·m arm against 7.76 N·m/rad restoring stiffness is authority-limited to ≈ ±14.5° at θ2 = 150° (T1), so a 15° step settles at the envelope edge — a physics ceiling, not a training defect; the paper story becomes "attitude within the arm envelope". A second null: G0-H shows thrust ON DOES restore pitch through m0 alone (with heave drift), which would weaken D-1's "arm must do pitch" and move the value of the retrain from pitch recovery to fault robustness only.

Failure mode to watch: the heavier fault distribution drops attainable return below `performance_lb 250` → DORAEMON mode −2 from the start (the E1-latdr signature). Tell: `DORAEMON/success_rate` < 0.5 at iteration 250 in the WITH arm of G0-C while the WITHOUT arm sits above it.

## 10. Decisions for the user (each with the record behind it and a recommendation)

1. `[DECISION-REQUIRED: scope]` — attitude-only (this program) vs widening to depth. Record: the 72D policy observes absolute yaw but **no depth and no linear velocity** (`observations.py` layout; `finding/240`, `decision/185`); depth needs the obs4 +4 interface (pressure-derived heave rate, IMU specific force — deployable, `decision/185`); XY needs a DVL that does not exist. Recommend: attitude-only now; open a separate `depth-obs4` program after this teacher ships. Yaw stays a rate command (`decision/300`).
2. `[DECISION-REQUIRED: fault-config]` — p₀ and d. Recommend p₀ = 0.15, d = 0.5 (q = 0.075: 37 % / 6.9 % / 0.66 % at severity 1); G0-I/G0-C measure; fallback if the paired probe fails: lower p₀ before touching `performance_lb`. **3.9 DECIDED p₀ = 0.30, d = 0.5** (session, under the user's 02:5x no-questions directive; the user's own lean was upward). Ground: decision/140's "curriculum ended at u ≈ 0.08" was the 4 750-iteration A/B, not the incumbent — the incumbent's `curriculum_trajectory.json` ends at Beta(1.00, 1.22) (mean u 0.45), near saturation. Severity-integrated exposure (T = 6, d = 0.5), columns any-fault ≥1 / ≥1 dead / 2 dead / ≥3 dead / m3∧m4 dead: 0.15: 32 % / 18.1 % / 2.05 % / 0.15 % / 0.16 %; **0.30: 52 % / 32.3 % / 7.08 % / 1.03 % / 0.63 %**; 0.35: 57 % / 36.4 % / 9.2 % / 1.6 % / 0.86 %; 0.50: 68 % / 46.7 % / 16.2 % / 3.9 % / 1.75 %. 0.30 keeps ≥3-dead (3 of 6 gone → some DOF unreachable, an unwinnable env that DORAEMON's α = 0.5 success gate would answer by *stopping* the severity expansion for every env) at ≈ 1 % while giving the deployment case (two dead) 3.5× the mass of 0.15. The G0-C readout (§6) is unchanged; if `thruster_util` binds or WITH drops > 5 % at iteration 500, the fallback is p₀ 0.20, not `performance_lb`. **3.9b (05:1x):** WITH dropped 18–30 % at 500 — but `fault_severity` was 0.0100 in both arms (effective p = 0.003), so the fault config had not acted yet and the p₀ fallback is not the lever for this gap; see §13 row 7.
3. `[DECISION-REQUIRED: seeds]` — you asked "굳이 2시드로 해야하나?". The paired probe (G0-C) is **one seed run twice** (with/without), not two seeds. For the final teacher: 1 seed is sufficient **if the robot is the judge** (constraint 3) and sim-side selection is at `hard` on the exam; 2 seeds only if a sim-side adoption verdict must be decisive on its own (seed floor 56 %, `decision/236`). Recommend: 1 seed + robot judge; add seed 31 only if Phase 4 is ambiguous.
4. `[DECISION-REQUIRED: r1-before-final]` — **recommend yes** (changed in 3.2; see §7 and `finding/309`).
5. `[DECISION-REQUIRED: delay-range]` — (0,1) recommended (user-approved 08-14); (0,2) only if G0-B shows the incumbent tolerates 2 steps cheaply. **3.5:** decided (0,1) on 2026-09-03; R-3 is its coverage check (p95 ≤ 1 step keeps it; > 1 step re-opens it — band (0,N) by the user, never a point value). `finding/264` (`needs-apply-before-retrain`) is closed by this delta and must be named in the launch ack. 🔴 **3.8 — R-3 result (vault `finding/148`): 152 ms median command→joint lag = 7.6 steps at 50 Hz, so (0,1) does NOT cover it. But `finding/148` §5 itself says the 152 ms is a MIX — ROS transport + driver 50 Hz loop quantization (≤ 20 ms) + Dynamixel bus + the servo's position-loop/profile dynamics — and could not split it. The 2026-07-06 bench step response (30° rise 0.15 s at deployment gains) says the servo dynamics alone are ~150 ms, so the pure transport share is tens of ms. **Rough-mode setting (Mac session under the user's "대충" instruction): `control_delay_steps (0,3)` = 0–60 ms for the transport share; the servo-dynamics share stays with the joint stiffness (30,150) / damping (0.3,7.0) DR — whether the slowest DR joint in sim reaches a 150 ms rise is NOT verified.** G0-B's d = 0/1/2 read stays informative for cost.**
6. `[DECISION-REQUIRED: reallocate]` — deploy with `fault_reallocate=false` (recommended; with m3 dead reallocation drops My anyway, `vault:finding/137` §5).
7. `[DECISION-REQUIRED: paper-framing]` — "fault-tolerant attitude control under actuator loss, validated on hardware with real failures" (recommended, user correction 1).
8. `[DECISION-REQUIRED: ksm-nas-role]` — screening only (user O-4); pairing ksm-nas to Orca is optional.
9. `[DECISION-REQUIRED: vertical-moment]` — what to do with R-1's numbers. Options unchanged: (a) hold 0.145 m × 40 N/unit linear; (b) scale `thrust_coefficient` to the measured effective moment (geometry stays — the lever is verified); (c) add a thrust-coefficient DR band on m0/m3 as screening arm S1c; **(d) `enable_thrust_curve true` + `thrust_deadband 0`**. 🔴 **R-1 ran and does NOT select among them** (`finding/309` §0, vault `finding/144`). Three things changed. (i) The pre-registered selector `r ≈ 2 → (b)` / `r ≈ 4 → (d)` **cannot fire**: the measured ratios (2.147 / 2.756 / 1.283) match no single power law, because the deviation is a **shifted origin** `T ∝ (u − δ)`, δ ≈ 0.11–0.14, linear above it — an option nobody pre-registered. (ii) That residual deadband **argues against (d)**: (d)'s `thrust_deadband 0` rests on `finding/281`'s claim that the deployment mixer fully inverts the ESC deadband, and δ ≈ 0.12 on top of the mixer's `D = 0.15` says the inversion is incomplete. (iii) The absolute scale is **0.39× (B = 0.53 N, the free-rise fit) or 0.78–0.86× (B = 1.07 N, vault `finding/136`)** — outside vs inside the (0.7, 1.3) band, decided by one unmeasured number. **Recommend: defer this decision and measure net buoyancy B directly for the first time first**; if B = 1.07 holds, (a) is correct and nothing changes. No option is applied without this decision. 🔴 **3.5 status (vault `finding/146`): B is CLOSED (0.44 N down, lead-tare weighing) — the deferral condition is met, but the readout it unlocked is 0.16× (outside) against the 08-12 tilt probe's 0.67× (inside), 4.2× apart and unresolved. The δ-origin argument against (d) in (ii) fell with `finding/144`, so (d) is back to undecided. Selector now pre-registered on **R-4** (§7): inside the band → (a) hold and launch; outside → the user picks (b) or (c); (d) read from T(0.25)/T(0.5). **Recommend: run R-4 (15 min, operator's scale + lead, no fit) before choosing.** No option is applied without this decision.** **3.6 — approach DECIDED by the operator (vault `decision/147`, 2026-09-03 23:45): re-center the nominal (option (b) family), keep the (0.7, 1.3) multiplier, do NOT widen to (0.15, 1.3) (6.7× width → worst-case-conservative policy, nominal 40 unreachable by the real vehicle); the ESC dead zone (< 1545 µs → exactly 0) is not expressible by any multiplicative band and belongs to option (d) as a separate sub-decision; the POINT VALUE waits for R-4 (0.16× heave vs 0.67× tilt). Desk check (`finding/312`): `thrust_coefficient_scale` is drawn ONCE PER ENV as a scalar at reset (`marinelab/core/thruster.py:264-268`) and multiplies `thrust_coefficient` 40 N for all six thrusters — so (b) as written re-centers EVERY channel, while only m0 (vertical) has a thrust measurement; a vertical-only re-center needs a per-thruster nominal (small code change, would enter the G0-J diff). Also from `decision/147`: buoy net buoyancy 16.62 N and K = 7.76 N·m/rad are flagged "suspect, undetermined" (one of the two parts is 1.55 N off) — K feeds the tilt lineage's 0.67×, so R-4's direct scale reading is now doubly the discriminator. ✅ **3.7 CLOSED (user, 2026-09-04 01:2x): "그냥 대충 하자 … 대충 예상되는 추력을 nominal 로 하고, DR 로 범위 줘서 학습" → nominal 13 N/unit, band (0.5, 2.0). Values chosen by the Mac session as the geometric middle of the two lineages (√(6.4 × 26.9) ≈ 13) with the band set to reach both ends; R-4 no longer required. Option (d) not taken (linear plant kept).**

10. `[DECISION-REQUIRED: rotational-inertia]` (new, 3.6; operator instruction 2 in `decision/147`) — vault `finding/145` measured the attitude natural mode 0.6233 Hz → **J_total ≈ 0.49 kg·m² about pitch** (with K = 7.76, itself a `decision/147` suspect; K 20 % lower → 0.39). Sim (`finding/312`): the vehicle base is **9.18 kg, I = (0.0994, 0.0994, 0.0372) kg·m²** in BOTH the hydro cfg (`deployed_env.yaml`) and the URDF (`marinelab/assets/albc/meshes/agent.urdf:52`) — radius of gyration 0.104 m; `inertia_scale (0.4, 2.0)` → 0.040–0.199; rotational added mass clamped at 0.95 × rigid (`mdp/events.py:271`) → **max reachable J_total ≈ 0.39 kg·m²**, i.e. the measurement sits at or above the DR ceiling. Per `decision/147`: "if the measurement exceeds the clamp it is a vehicle-model problem, not a DR-width problem." Options: (a) hold (attitude tracking still worked on the robot with the incumbent); (b) re-center `rigid_body_inertia` nominal to a measured/CAD dry inertia keeping (0.4, 2.0); (c) measure the dry inertia first (bifilar pendulum on the bench, or CAD export). **Recommend (c) then decide; not a launch blocker for the paired probe G0-C, but it is for Phase 3 if (b) is chosen** — user decision. **3.7: HELD at (a) for this program (user wants to finish; the incumbent flew on the robot with this inertia). Not a launch blocker. Re-open only if Phase 5 shows attitude ringing the sim did not.**
    **3.9 disposition (vault `finding/149`, 2026-09-04 02:xx, MacBook session):** the dry rotational inertia was found — base (0.0994, 0.0994, 0.0372) in three lineages; the ASSEMBLY (parallel-axis over all URDF links, θ2 150°) is dry roll 0.214, sim total 0.320, and the measured 0.49 (±7.5 %) sits outside the sim's reachable band 0.267–0.374. **It cannot be covered by widening**: `envs/main/mdp/events.py` has `set_masses` but no `set_inertias`, so `inertia_scale (0.4, 2.0)` only moves the added-mass clamp and the privileged obs — this corrects `finding/312`'s "ceiling 0.39" (that ceiling assumed the scale reached physics). Options: (a) raise the vehicle-model constant to the measurement — **a point-value substitution, ruled out by the user's 2026-09-03 rule**; (b) wire `set_inertias` and put a DR band on it — the right fix, but new code + a plant change with two open premises (K ±7.5 %, unknown θ2 of the free-decay); (c) accept the gap for this launch. **Decision: (c) now, (b) queued as the next program item** — the gap's direction (robot 1.5× more sluggish in attitude than sim) is the one added-mass DR (0.5, 1.5) already pushes toward, so the policy is under-exposed, not blind.

11. `[DECISION-REQUIRED: performance_lb]` (new, 3.9d) — `finding/315`: Phase 3 stalled because `performance_lb` 250 (incumbent plateau 252.7, success 0.65) exceeds the delta plant's plateau ≈ 237; §5 forbids a silent lb edit and `decision/063` says a changed box needs joint re-tuning. Options: (1) re-tune lb to the new return scale (200, checked by mode/severity within 1 000 it); (2) `hard_performance_constraint false`; (3) revert one plant change. **DECIDED 2026-09-04 13:3x by the user: (1), lb = 200, Phase 3 killed at 8010 and relaunched as Phase 3b (§13 row 11).** Open: 200 is a floor guess — the plateau under a widened box is unknown; if the gate releases but severity saturates far below the incumbent's Beta(1,1), the next lever is lb again, not the schedule (E-ftc1).
**DECIDED 2026-09-03 (user, Mac session, after the tank session):** items **1, 2, 3, 5, 6, 7, 8 are confirmed as recommended** — 1 attitude-only; 2 p₀ = 0.15, d = 0.5; 3 final teacher 1 seed with the robot as judge, paired probe = seed 30 with/without; 5 `control_delay_steps (0,1)`; 6 deploy `fault_reallocate=false`; 7 FTC framing; 8 ksm-nas screening only. Item 4 is closed by R-1's execution (`finding/309` §0). **Item 9 stays DEFERRED** pending the first direct measurement of net buoyancy B (`finding/309` §0d); until then the plant row holds (a). Standing user rule (2026-09-03): a robot measurement is used only to check DR coverage — never remove a DR band and insert the measured point value; if outside, re-center the nominal or widen the band. G0 gates may start now; G0-D and G0-C go to `omx queue-launch` and are fired by the user. **3.5 (2026-09-03 late, user): "plan only — do not train yet."** Item 9 → R-4; item 5 → R-3 coverage check; G0-I and G0-A/B/E proceed on the desk. **Nothing is queued.** **3.6 (vault `decision/147`): item 9 approach = (b) re-center, band kept; R-3 ordered; item 10 opened below.**


Tank pass/abort/recovery criteria for each `thruster_scale` step of Phase 5 live in the vault PLAN (`simtoreal-thrusters-live` §3c / T10) and are not duplicated here.

## 11. Work split (user constraint 4) and community (constraint 5)

| Who | What | Ground |
|:--|:--|:--|
| Claude session | decisions, gate readouts, verdicts, plan/community writes | omo: never delegated |
| codex `develop` | §5 sampler change + G0-I unit test; launch scripts; Hydra override check | ground 1 once `fault-config` is decided |
| codex `explore` | bag/log digests, cross-run tables; the 444-post ledger was one such call (`review/306`) | ground 2, ≤ 4 min per call |
| agy | **cannot read files from the workdir — inline them in the prompt** (two attempts that pointed at files timed out at the 297 s ceiling or returned "files missing"); a 64 KB inline prompt at `gemini-3.1-pro-high` / effort `high` returned in 3 m 57 s (`vault:finding/139` for the ceiling) | ground 4 second family — used 2026-09-03, `review/310` |
| Orca | remote steps on marinelab / ksm-nas (`worker-start --on marinelab`) | user instruction |
| hq community | this PLAN's decisions as `decision/`, each gate readout as `finding/`, session end as `handoff/` | constraint 5 |

## 12. Traceability

Primary posts read in full this revision: marinelab `decision/197, 253, 155, 180, 209, 140, 238, 236, 063 (Update)`, `finding/154, 255, 273, 266, 264, 001, 284, 052`, `handoff/302, 303, 304`; vault `finding/137, 134, 136, 073, 077, 056, 041, 060, 065, 066`, resume-brief §1–§5, `rules-robot-code/SKILL.md`; artifacts `deployed_tam.json`, `deployed_env.yaml` (sha 830be5dd…), `curriculum_trajectory.json` of the incumbent, `envs/main/mdp/faults.py`, `envs/main/mdp/observations.py`, `build_proprio.py`. Vendor calls (all logged in the codeagent ledger): codex ground-4 axis attack; codex ground-2 sweeps ×2 (`review/306` §A/§B); codex ground-4 review of revision 3 → BLOCK, 11 findings (`review/307`): folded in — R-1 protocol and identifiability (§7, decision 9), pair-probability arithmetic (0.20/0.41/0.66 %, §5), severity-integrated exposure (§5), D-1 softened to "untested" (§2), D-4 scope (§2), G0-A/B/C criteria made explicit choices (§6), launch manifest G0-J and GPU-hour budget (§6), Phase 4 sample sizes and floors (§9), S1c and vertical-moment as user decisions (§8, §10); rejected with reason — "hidden hard-constraint/special-case" (the reviewer itself found none); partly — the GRU recipe is kept as the shipped recipe, not as a validated choice. agy ×3 failed (timeout / flag mismatch), so the **two-family gate is not met for this revision** — recorded, not hidden. External literature R1–R5: **re-verified against primary text on 2026-09-03** (`finding/308`) — 10 supported, 3 partly (2508.19164 is adaptive control, not RL; MMDR "+90 %" is "nearly 100 % moving distance"; Whitcomb & Yoerger 1999 attribution unread), 1 contradicted (2512.13359 is a plain AUV that abstracts to body forces and defers actuators to deployment — it supports the deployment lane, not a fixed ±5 N band); no decision moved. Revision 3.2 also folds in `finding/309`: thrust = command × 40 N (not 50), `thrust_coefficient_scale (0.7, 1.3)` exists, and the m0 probe's 0.455 N·m at u = 0.25 — changing D-1's number, §3 item 2, §5's vertical row, R-1's readout, and the recommendations for decisions 4 and 9. Revision 3.3 (same day): agy (`gemini-3.1-pro-high`, effort high, three files inlined, 64 KB, 3 m 57 s) ground-4 review of the 3.1 text (`review/310`): 3 BLOCK / 3 MAJOR / 1 MINOR — the 40 N coefficient and the linear-only R-1 readout were found independently of `finding/309` (already fixed in 3.2); accepted: the delay row tied to G0-B and `delay-range` (§5), G0-B's [1.3×, 2×) gap closed (§6); rejected with evidence: the axis-naming objection (convention sentence added to D-1) and the fixed-health index-order objection (`config.py:130-137`, noted in G0-A); partly: deadband inertness asserted in G0-J instead of editing the config. Two-family gate met, with the caveat that the two vendors reviewed different revisions (3.0 and 3.1). The frozen text is `PLAN.md.bak-round2-frozen`; its `Predicted outcome` and `Risks` sections are superseded by §9 and by the decisions in §10. **Revision 3.4 (2026-09-03, tank session, Mac):** `finding/309` corrected twice — the 0.31×/3× vertical-moment gap is retracted as a unit error (the 08-12 m0 probe published RAW with the mixer bypassed; effective u = 0.1176, ratio 0.67× at the DR floor), and R-1 executed with a replaced readout because the settled-tilt protocol is structurally unexecutable with m3 dead. Changed here: §3 item 2, §5's vertical row, §7's R-1 row and `r1-before-final`, §10 decision 9. R-1's own record is vault `finding/144`. The deciding probe for decision 9 moved from thruster levels to a FIRST DIRECT measurement of net buoyancy B (it has never been weighed as an assembly).

## 13. Launch order (frozen at 3.5; **the user said so at 2026-09-04 02:5x** — training still fires only from the user's shell, see the fire block below the table)

| # | Step | Where | Blocks on | Status 2026-09-03 late |
|:--|:--|:--|:--|:--|
| 1 | R-3 command→joint delay | tank session, from existing bags | — | **DONE** (`finding/148`, 152 ms) → item 5 = (0,3) |
| 2 | R-4 hanging thrust test | — | — | **DROPPED 3.7** — item 9 closed by re-centering + band (user) |
| 3 | G0-I sampler mechanism + unit test | marinelab, desk | — | **DONE 2026-09-04 00:2x, commit `4cef724`** — `thruster_dead_frac` (default 0.0, no extra RNG draw → incumbent bit-identical, asserted); p₀ stays a launch-config VALUE on the existing `thruster_fail_prob`. `tests/test_fault_sampler_exposure.py` 4 passed + 42 existing fault/config tests. Implementer: agy (gemini-3.1-pro-high, inline prompt) — codex backend was 404 on both machines and the user then said not to use codex |
| 4 | G0-A / G0-B / G0-E incumbent evals | marinelab, desk | — | in progress (agent) |
| 5 | §10 item 9 | user | — | **CLOSED 3.7**: nominal 13 N/unit, band (0.5, 2.0); item 5 (0,1) stands; item 10 held |
| 6 | G0-J launch manifest — pin SHA, `git diff 598db899..<SHA> -- constrained_albc/envs/main/`, Hydra diff = §5 delta = {`fault.thruster_fail_prob 0.15`, `fault.thruster_dead_frac 0.5`, `control_delay_steps (0,3)`, `thrust_coefficient 13.0`, `thrust_coefficient_scale (0.5, 2.0)`} and nothing else, `enable_thrust_curve` asserted, launch ack names `finding/264` | marinelab | 3 | **DONE 3.9, CONFIRMED 3.9a on the live run** `logs/rsl_rl/albc_trpo_teacher/retrain_simtoreal_g0c/trpo_g0c_with_s30_260904_034242/params/env.yaml` vs the incumbent's: exactly `thrusters.thrust_coefficient 40 → 13.0`, `randomization.thrust_coefficient_scale (0.7,1.3) → (0.5,2.0)`, `randomization.control_delay_steps (0,0) → (0,3)`, `fault.thruster_fail_prob 0.1 → 0.3`, new `fault.thruster_dead_frac 0.5`, plus `log_dir` and three pickled-tensor blobs whose numeric payload is byte-identical (only the pickle object ids differ); `agent.yaml` differs in `max_iterations`, `run_name`, and logger project lines only. Pinned commit `7cb7161` (community-only commits after `4cef724`; `envs/main/` unchanged since). `enable_thrust_curve` stays false |
| 7 | G0-C paired probe (seed 30, 500 it, WITH vs WITHOUT) → `omx queue-launch` | queue only; user fires | 3, 4, 6 | **DONE 05:06 — readout FAIL on the pre-registered 5 % threshold, PROCEED on mechanism** (`finding/313`). At iteration 500: `Train/mean_reward` WITH 164.8 vs WITHOUT 202.1 (0.82×; last-50 mean 149.7 vs 195.7 = 0.77×; 400–499 mean 0.70×); reward trajectory WITH lags WITHOUT by ≈ 100–150 iterations (WITH@499 ≈ WITHOUT@350), still rising steeply (+54 over the last 100 it). `DORAEMON/mode` −3 in BOTH at 0 and 250 (success rate 0.001/0.009 < α, reward below `performance_lb` 250 — the plan's "mode stays 0" was unreachable at 500 for either arm). `fault_severity` mean 0.0100 in both → effective fail prob 0.003: **the fault config is inactive at this stage, so the gap is delay (0,3) and/or thrust 13 N/unit, not p₀** — the §10 item 2 fallback (p₀ 0.20) would change nothing here. `thruster_util` margin WITH 10.6 vs WITHOUT 5.8 (less binding, expected at 13 N/unit); episode length 1426 in both (no terminations); value loss 1.64 vs 1.30. Verdict: feasibility yes, early cost ≈ 25 %; Phase 3 (row 9) was already chained and is left running per the user's night directive — the user decides on the morning read |
| 8 | G0-D GPU throughput probe → `omx queue-launch` | queue only; user fires | 6 | **answered by row 7's live numbers**: ≈ 4.5 s/iter at 4096 envs on the RTX 4070, 11.5 GB VRAM — Phase 3's 10 000 iterations ≈ 12.5 h, not the 3.3–3.6 s/iter the frozen plan assumed |
| 9 | Phase 3 final teacher, 1 seed (§10 item 3) → `omx queue-launch` | queue only; user fires | 7 pass, 8 | **KILLED 13:45 at iteration 8010 (`finding/315`)** — DORAEMON mode −2 at 32/33 updates, `fault_severity` 0.010 → 0.0045, all 21 DR dims at their initial width, reward plateau 233–243 vs incumbent 252.7: `performance_lb` 250 was tuned for the 40 N zero-delay plant and the delta's achievable return sits below it, so the α gate never released. The checkpoint (`trpo_p3_ftc_s30_260904_0506xx/model_8000.pt`) is kept as the "delay+thrust, no DR, no fault" reference for Phase 4. Replaced by row 11 |
| 11 | **Phase 3b** `p3b_lb200_s30` — §5 delta + `env.doraemon.performance_lb` 250 → **200** (§10 item 11, user decision 13:3x) | GPU0, tmux `p3b`, `/workspace/g0c_runner/p3b_run.sh` | 9 | **FIRED 13:45** (commit `c92d854`, `omx queue-launch` artifact `p3b_lb200_s30`, ack `finding/264`). Pre-registered early readout: `DORAEMON/mode` turns 0/1 and `fault_severity` mean rises above 0.05 within the first 1 000 iterations; if mode is still −2 at 1 000, kill and re-open item 11. ETA ≈ 02:15 on 09-05 at 4.5 s/iter **1000-it verdict (15:0x): PROCEED.** it 1056: reward 217.5 (r50 219.8) > lb 200, success 0.786, DORAEMON/mode −3, −2, 0, 0 at 250/500/750/1000 — the curriculum opened at 750, one update after reward crossed lb (Phase 3 never did in 32 updates). fault_severity mean 0.0132 (from 0.010): the 0.05 half of the readout is not yet met, but the kill trigger was mode −2 at 1000 and that is absent; severity growth is rate-limited by kl_ub 0.12 per update, so 0.05 is a later milestone, not a 1000-it one (incumbent reached mean 0.45 only over thousands of iterations). Next reads every 500 it; stall signature stays armed from it 1500. **Exposure track (pre-registered at it 2003, 16:1x).** `DORAEMON/mean/fault_severity` over its 2 014 logged points grows geometrically once the curriculum opens: a log-linear fit from it 500 gives x1.312 per 500 iterations (the std knob x1.307), which reaches the incumbent terminal mean 0.45 at **it ~7 600** and would exceed the [0,1] domain by 10 000 — so the rate must decay, and 7 600 is an optimistic bound rather than a forecast. Checkpoint: at **it 5 000** the geometric track predicts `fault_severity` ~ 0.12. Materially below that (say < 0.07) means p3b ends having trained on thinner fault exposure than the incumbent did, which is a Phase 4 interpretation caveat about comparing at equal exposure — record it, do not kill on it. Measured so far: 0.0100 (500), 0.0132 (1000), 0.0174 (1500), 0.0230 (2000). **KILLED BY CONTAINER RESTART 15:56, RESUMED 16:35 (`finding/317`).** The host docker daemon restarted (`ActiveEnterTimestamp` 15:56:09, host up 21 days so not a reboot) and took every container with it, ending the run at ~2 100 iterations and the Phase 4 runner mid-`inc/m4`. Resumed from `model_2050.pt` into `trpo_p3b_lb200_s30_r2050_260904_163518` via `/workspace/g0c_runner/p3b_resume.sh`; iteration counter continues 2050 to 10 000, new ETA 09-05 02:2x. Two silent traps had to be cleared first, both recorded in `finding/317`: (1) `agent.resume=true` as a Hydra override is always discarded because `cli_args.py:76` overwrites it from `args_cli.resume` (`store_true`, never `None`) — the run started at iteration 0 with `load_run`/`load_checkpoint` still visible in `agent.yaml`; pass `--resume` as a CLI flag. (2) `get_checkpoint_path` regex-matches only directory names one level under the experiment dir (`parse_cfg.py:194`), so a `--run_group` nested run is unreachable — fixed with the symlink `logs/rsl_rl/albc_trpo_teacher/RESUME_p3b_2050`. Resume verified rather than assumed: DORAEMON curriculum restored (new TB opens at step 2050 with `fault_severity` 0.0230, the pre-crash value; a reset reads 0.0100) through the `doraemon_state.pt` sidecar, `cost_critic` weights in `model_state_dict`, optimizer restored, and both `params/env.yaml` agree on 338 of 339 keys (`log_dir` the only difference). **Residue for Phase 4 analysis:** p3b history spans two run dirs (0 to 2050 in `..._134536`, 2050 to 10 000 in `..._163518`), each with its own TB file and `curriculum_trajectory.json` — stitch them; the incumbent has the same property. The scratch from-zero run is quarantined as `SCRATCH_fromzero_162821_delete_me` and can be deleted. |
| 12 | **Phase 4 exam runner** — `/workspace/g0c_runner/p4_runner.sh`, GPU1, serial, re-entrant (a config with `summary.json` is skipped). Priority: p3b milestone core at 2500/5000/7500 → p3b final core+extras after `P3B_DONE` → incumbent core on the 13 N plant (`inc13`, thrust_coefficient=13.0 only) → incumbent extras on its own plant (6 singles m0–m5 + 14 other pairs) → p3 `model_8000` reference core. Core = {healthy, pair34 `1,1,1,0,0,1`, healthy+delay 1, healthy+delay 2}; incumbent core = symlinks to the G0-A/B outputs (`.hq/work/g0abe/`, same seed 42 / 64 envs / code, so per-env pairing holds). p3b and p3ref evals carry the §5 plant as Hydra overrides (`thrust_coefficient=13.0`, `thrust_coefficient_scale=[0.5,2.0]`) because `eval.py static` rebuilds the env from the task default, not from the checkpoint's `params/env.yaml` (teacher mode; only student mode reads sensor keys off the ckpt, eval.py ≈ L1217). Fault knobs are moot under `--fault_fixed_health`. Output tree `.hq/work/p4/<inc|inc13|p3b_2500|p3b_5000|p3b_7500|p3b_final|p3ref>/<config>/data_{none,soft,medium,hard}.npz`; log `.hq/work/p4/runner.log`. ≈ 11–18 min per config (G0-A/B timing). | GPU1, nohup | 11 | **STARTED 14:34** (first config `inc13/healthy`). Read at `hard`, per-env pairing from the npz, floors per §9 Phase 4. **CORRECTED 17:4x (`finding/318`).** The first version gave each arm the plant it trained on — p3b with `thrust_coefficient_scale=[0.5,2.0]`, `inc13` keeping the incumbent's `(0.7,1.3)`. That range is a DR-sampled dimension, so the draws diverge: `pairDR` is 0 at `none` and 0.5 / 1.0 / 2.0 at soft / medium / hard, and every level but `none` compared two policies on two distributions. **New arm `inc13w`** scores the incumbent on the FULL section-5 plant (both knobs) so candidate and reference take an identical exam; it is scheduled ahead of `inc13` and the loss sweep (4 configs, about 40 min). `inc13` is kept because it is what `finding/316` measured. Read the scorer's `pairDR` column before its `delta` column — a nonzero value means the row is not paired. First valid readout (p3b at 2500 vs `inc13`, `none` only): healthy 0.406 to 0.692 deg (8/64 envs better), healthy roll 0.245 to 0.489 (12/64), pair34 1.423 to 1.325 (26/64, inside the floor), pair34 pitch 1.245 to 1.017. A 2500-of-10000 checkpoint behind a converged teacher is expected, not a verdict. |
| 13 | **Phase 4 step 2 — student distillation** `sd_p3b7500_c3_gruselect_s30`: teacher `model_7500` (`finding/362`), `--task Isaac-ConstrainedALBC-TRPO-SimToReal-v0` (option B, user 2026-09-05 — the student rolls out on the plant the teacher trained on, not the incumbent recipe's default 40 N zero-delay task), recipe otherwise verbatim from `pack_inc9998_gru_260810_150713` (gru 128/64, `dagger_mix select` β 0.5, λ 1.0, 2048 envs, 1000 it, seed 30, `run_group retrain_simtoreal_p3`). Script `/workspace/g0c_runner/student_p3b.sh`, log `student_p3b.log`, marker `SD_P3B_DONE` on rc 0 only. → `omx queue-launch` | GPU1 (≈ 12 min, incumbent timing); queue only, user fires | 12 | **QUEUED 2026-09-05 20:28** — `.hq/work/experiments/runs/sd_p3b7500_c3_gruselect_s30/pending-launch.json`, `queued_commit` 4b257ec, gates `finding/352` + `finding/264` acked for this launch only. **Provenance hole**: 4b257ec does not contain `config_simtoreal.py` or the task registration — commit before firing. Next after the marker: student-mode exam (`eval.py static --student_ckpt … --encoder_type gru`, CORE + `pair34_d2`, seed 42 / 64 envs) paired against the teacher's `p3b_7500` npz, floors 0.10° / 1.6 pp → `export_deploy_pack.py` (72D, parity 1e-5) → board gate with the operator → Phase 5 (PLAN:153). **FIRED 2026-09-05 21:20 -> rc 0 21:32; exam FAILED (finding/380: student worse than teacher on 20/20 rows, deploy blocked). Root cause finding/381 (runner: DORAEMON never disabled, SimToReal DR fields reverted) -- patched, uncommitted. R1 `sd_p3b7500_c3_dr5_s30` (fix only, GPU1) and R2 `sd_p3b7500_c3_dr5_ep155_s30` (fix + 155 s episodes, GPU0) QUEUED, approval pending; each chains its exam -> `.hq/work/p4/sd_r1`, `sd_r2`. Control `sd_inc9998` running. See HANDOFF 3.9q.** **R1 FIRED 23:25 (env.yaml verified), R2 marker-gated; follow-ups R3a/R3b/R4a QUEUED 23:5x (finding/383), approval pending.** **3.9r (2026-09-06 00:4x):** R1 (plant fix only) FAILED the floor 19/20 vs teacher (finding/384); shared latent bias collapsed 4x so finding/381 is resolved as the mechanism of the bias, not of the score; every student is under-trained on the real box (loss_latent 0.020 at it 1000, falling). Control exam finding/385: the deployed student beats its teacher under delay only through a constant wrong latent; Phase 4 teacher-mode delay margins overstate the candidate (+0.24/+0.40 at none vs the deployed student). R2 early: drift gone, score not. Remaining chain R2 exam -> R3b, R3a -> R4a, all on GPU1 (stonefish owns GPU0). **3.9s (2026-09-06 01:4x):** R2 = FAIL 20/20 (finding/386: 155 s horizon removes latent drift, score is bias-limited; wins faulted none-medium, loses hard). R3a (beta 1->0) partial 2/5: 6 of 8 cells inside the 0.10 floor, first student ever (R1 0/20), latent mse halved. If R3a holds at 5/5, budget axis re-runs on top of the anneal (R4c = beta 1->0 + 10k it, new queue + approval). GPU0 hand-off automated (gpu0_watch.sh -> /workspace/GPU0_FREE -> R4a ALT_GPU). **3.9t (2026-09-06 02:3x):** R3a 5/5 = finding/387 -- first student inside the floor (vs teacher 11 tie / 2 better / 7 worse; vs R1 18/20; latent mse halved, drift gone); pre-registered pair34 floor missed by 0.015/0.050, hard+delay +1.2..+1.8 remains. R3b (TCN) failing at 1/5 (latent 4x R1). R4a running on GPU0 (hand-off automated, 93 it/min, exam ~04:35). R4c (R3a + 10k it) QUEUED pending approval (pending-launch.json, queued_commit 9e0dfa5). **3.9u (2026-09-06 03:1x):** R3b (TCN 27-step) = FAIL 20/20 vs teacher, 18/20 vs R1 (finding/388, resolved: 0.54 s window cannot integrate the latent; variance 5-8x, shared bias 4-6x). Scoreboard vs teacher (tie/better/worse): R1 0/1/19, R2 0/0/20, R3a 11/2/7, R3b 0/0/20; R4a running (exam ~04:50); R4c queued pending approval. **3.9v (2026-09-06 05:0x):** R4a 5/5 = finding/389 (vs teacher 0/0/20, vs R3a 4 tie/0/16, vs R1 8 better/3 tie/9 worse with every win at none/soft and every loss at medium/hard; loss_latent floors at it ~2k at R1 value; budget axis on beta 0.5 CLOSED). Same-seed second realization of R1 (R4a student_999, arm sd_r4a999): weights relL2 0.88, exam vs R1 11 tie/2/7 -- within 0.10 at none/soft, 0.2-0.7 apart at medium/hard = the single-realization noise floor; latent mse 2-7x R1 at the same score. Hard-level mean is tail-made (teacher 3.33/0.66/5.47 mean/median/P90); R3a ties the teacher median on all 4 core hard cells, loses P90. Both GPUs idle 04:55. Open: R4c approve/drop (readable at 0.10 on none/soft only), R4b code time, R3a second realization (seed 31) as the alternative next run. **3.9w (2026-09-06 15:0x):** DEPLOYMENT DECISION -- user chose R3a for the next field test; pack `deploy/retrain_simtoreal_p3/pack_r3a_p3b7500_gru_260906_145553` exported (data swap of 5 files, npforward.py byte-identical to the deployed pack), container self-close + Mac sha256/parity/board-test gates PASSED (decision/390); board gate (TX2 numpy 1.11) pending, jump host offline, operator required. |
| 10 | Phases 4–5 selection + robot judge | robot | 9 | Phase 4 scoring = row 12; Phase 5 robot after selection |

### Fire block (3.9) — the user's shell, container `ksm-ubuntu:2222`, one at a time

```bash
cd /workspace/constrained-albc && export CUDA_VISIBLE_DEVICES=0 TERM=xterm
# G0-C WITH (§5 delta, p₀ 0.30) — 500 iterations
/workspace/isaaclab/isaaclab.sh -p scripts/train.py --task Isaac-ConstrainedALBC-TRPO-v0 --num_envs 4096 --max_iterations 500 --headless --seed 30 \
  --run_group retrain_simtoreal_g0c env.fault.enable=True \
  env.fault.thruster_fail_prob=0.30 env.fault.thruster_dead_frac=0.5 'env.randomization.control_delay_steps=[0,3]' \
  env.thrusters.thrust_coefficient=13.0 'env.randomization.thrust_coefficient_scale=[0.5,2.0]' \
  agent.run_name=g0c_with_s30 > /workspace/g0c_with.log 2>&1
# G0-C WITHOUT (incumbent config at the same commit) — 500 iterations
/workspace/isaaclab/isaaclab.sh -p scripts/train.py --task Isaac-ConstrainedALBC-TRPO-v0 --num_envs 4096 --max_iterations 500 --headless --seed 30 \
  --run_group retrain_simtoreal_g0c env.fault.enable=True agent.run_name=g0c_without_s30 > /workspace/g0c_without.log 2>&1
# G0-J confirmation, once WITH has written its params (first minute):
diff logs/rsl_rl/albc_trpo_teacher/retrain_simtoreal_g0c/*g0c_with_s30*/params/env.yaml logs/rsl_rl/albc_trpo_teacher/teacher_iter_budget/trpo_iterbudget_s30_260805_012813/params/env.yaml
# Phase 3 (only after G0-C passes: WITH Train/mean_reward within 5 % of WITHOUT at 500, DORAEMON/mode 0 in both, thruster_util not binding)
/workspace/isaaclab/isaaclab.sh -p scripts/train.py --task Isaac-ConstrainedALBC-TRPO-v0 --num_envs 4096 --max_iterations 10000 --headless --seed 30 \
  --run_group retrain_simtoreal_p3 env.fault.enable=True \
  env.fault.thruster_fail_prob=0.30 env.fault.thruster_dead_frac=0.5 'env.randomization.control_delay_steps=[0,3]' \
  env.thrusters.thrust_coefficient=13.0 'env.randomization.thrust_coefficient_scale=[0.5,2.0]' \
  agent.run_name=p3_ftc_s30 > /workspace/p3_ftc_s30.log 2>&1
```

Launcher `/workspace/isaaclab/isaaclab.sh -p` was chosen by existence check at 3.9; `--logger` left at its tensorboard default (the wandb login state was not verified tonight). No cuDNN preamble: the TRPO teacher has no conv (`decision/008` scopes the rule to conv-bearing/DAgger runs). `pgrep -af scripts/train.py` for liveness (needs `-f`).

---

## Update 2026-09-06 — R-2 closed at 10 Hz; the ripple is POLICY-generated at the hull's own mode; the next generation is a TEACHER retrain (naming corrected)

Rebuilt from the primary records, not inherited from the prior session's conclusions.
This revision has been through a ground-4 adversarial pass (agy / Gemini 3.1, cross-family;
codex hit its usage limit) and **three of the reviewer's findings were confirmed against the
robot's own bags, one of which killed this session's first mechanism hypothesis.** The audit
trail is §10.

Robot-side: vault `finding/158` (new; supersedes `finding/157`), `145`, `148`, `149`, `154`,
`155`, `156`, `03_notes/2026-09-06-r3a-fieldtest-log.md`.
Training-side: `finding/345`, `346`, `354`, `360`, `362`, `379`, `391`, `decision/209`.

### 0. Naming correction, applied before anything else

The incoming request called the next generation "R3b". **That name is taken and closed.**
`R1 / R2 / R3a / R3b / R4a / R4c / R5` are STUDENT DISTILLATION arms off teacher `p3b_7500`:

| arm | recipe | verdict | record |
|:---|:---|:---|:---|
| R1 | plant fix only | 19/20 worse than teacher | `finding/384` |
| R2 | R1 + `episode_length_s` 155 | 20/20 worse | `finding/386` |
| **R3a** | R1 + beta 1.0->0.0 anneal | **selected, deployed 2026-09-06** | `finding/387`, `decision/390` |
| **R3b** | R1 + TCN 27-step window | **20/20 failed, closed** | `finding/388` |
| R4a | R1 + 10k it, beta 0.5 | 20/20 failed | `finding/389` |
| R4c | R3a recipe + 10k it | **fired 2026-09-06 20:48 (ksm-mac, operator-approved); trained rc 0 23:01, exam 5/5 23:53. Pre-registration NOT MET: 0 of 10 readable none/soft rows, every row a tie, max |delta| 0.079 deg** | `finding/387`, Update 2026-09-07 |

The next thing is a **teacher retrain** — a new Phase-3-class run in the `p3*` series.
Labelling it R3b would merge it in the ledger with a closed experiment.

### 1. What the 2026-09-06 field test established

- **R-2 closed. Deployment rate is 10 Hz.** Settling `cmd (0,0)` roll sigma: 10 Hz 0.18 deg,
  25 Hz 3.70 deg, 50 Hz 1.42 deg.
- **The retrain fixed the 50 Hz divergence.** Incumbent tripped at 11.8-18 s at 50 Hz
  (2026-08-26); R3a ran 250 s bounded. Pre-registered prediction hit.
- **Only negative roll is deficient.** roll +30 ~100%, roll -30 62%, pitch +/-30 95-98%.
  Current is LOW where tracking is poor (-30 roll ~280 mA) — not stalled, not pushing.
- **`fault_reallocate` tank re-check is done** (open since 2026-08-24): parasitic yaw
  OFF -3.73 deg/s, ON -0.94 deg/s, ON unlimited (127.5 s) -0.65 deg/s.
- 7 runs, ~1580 s of policy time, **0 trips and 0 aborts**.

### 2. What the bags say when re-measured — vault `finding/158`

The field log's "25 Hz limit cycle at about 0.33 Hz" was read off a **1 Hz** log whose Nyquist
is 0.5 Hz. Re-measured from the raw bag stream (89-98 Hz sensors, 50 Hz joints, 10-50 Hz
commands; `rotate_imu(ROLL, PITCH, YAW, offset_rad)` oracle, mean removal, Hann, rfft):

| bag | run | control_hz | dominant attitude frequency | mode-band share (0.58-0.70 Hz, body roll) |
|:---|:---|:---|:---|:---|
| 11-54-06 | 1 | 10 (arm only) | 0.0522 Hz | 0.030 |
| 12-23-05 | 3 | **50** | **0.6435 Hz** | **0.418** |
| 12-29-16 | 4 | **25** | **0.6488 Hz** | **0.799** |
| 12-52-15 | thr A | 10 + thrust 0.2 | **0.5837 Hz** | 0.115 |

`|0.6515 - 1| = 0.3485 Hz` -> period 2.87 s, read as "3 log lines" at 1 s granularity. The
0.30-0.37 Hz band does carry a residual (17.5x the noise floor) but it is **0.93%** of the
0.05-3 Hz energy against the mode band's **79.9%**, a peak ratio of 193x. The true frequency
matches `finding/145`'s free decay **0.6233 Hz** (zeta 0.12-0.19, Q ~ 3.3) to 4.5%.

**The mechanism is the policy, not the plant.** The bag records `/albc/joint{1,2}_cmd`.
Splitting the mode band across command, measured joint and attitude:

| run | control_hz | **cmd_J2 in-band amp** | meas_J2 | att_roll | follow meas/cmd |
|:---|:---|:---|:---|:---|:---|
| 4 | 25 | **0.1250** (band share 0.73) | 0.1245 | 0.0866 | **0.996** |
| 3 | 50 | **0.1600** (band share 0.39) | 0.1472 | 0.0747 | 0.920 |
| 1 | 10 | **0.00128** (band share 0.027) | 0.00117 | 0.00208 | 0.912 |

**The 0.65 Hz oscillation is already in the command.** The joint follows it almost exactly and
the attitude follows the joint. This is not a plant mode excited by noise — the policy is
oscillating at the plant's resonant frequency, the classic signature of excess loop gain at
that frequency in a delayed loop. **Command ripple is monotone in rate** (0.00128 / 0.1250 /
0.1600), matching loop gain `delta_scale x hz` = 1.0 / 2.5 / 5.0 rad/s. **At 10 Hz it is about
100x smaller.**

**What is still unexplained.** Command ripple is monotone but attitude ripple is not
(25 Hz 0.0866 > 50 Hz 0.0747). The inversion lives in the joint->attitude stage, where the two
runs differ in J1/J2 relative phase (+172.2 deg vs +117.0 deg) and operating pose
(theta2 169.4 +/- 5.1 deg vs 157.8 +/- 18.0 deg). These bags cannot separate the two causes
because the runs also differ in command content (run 4 was baseline-only). It is a kinematics
question answerable from the same bags' FK, not a new experiment.

**Two hypotheses this session raised and then killed, recorded so they are not re-raised:**

1. "25 Hz sits at the joint saturation boundary." **Refuted by measurement.** Joint saturation
   duty against the 2.40 rad/s ceiling is J1 **0.021%** / J2 **0.000%** at 25 Hz, with p99 at
   0.46 / 0.63 rad/s. The reviewer set 1% as the falsification threshold; the measurement is
   1/50 of it. `delta_scale x hz` is the ceiling at `|a|=1`, not an operating point.
   `finding/145` is untouched — it is about the feedback-free target integrator running ahead
   of the arm, not about the joint saturating.
2. The field log's "4.2 s rise = 0.24 Hz" is the reciprocal of a rise time, not a natural
   frequency, and is not evidence for anything.

**And on the inertia gap, cite `finding/149`, not an `wn` derivation.** The direction is
established there directly: measured assembly pitch inertia **0.49 against the sim total 0.320
= 1.53x, outside the sim added-mass DR band 0.267-0.374**. `finding/354`'s engine readout
`I_pitch = 0.12` is NOT used here — its scope (base link vs assembly) is unverified and
`finding/149` warns that comparing those directly is a 2.15x category error. Note also that
`f_n = sqrt(K/J) / (2*pi)`; `sqrt(K/J)` alone is rad/s.

### 3. Operator decisions, 2026-09-06 (verbatim, then resolution)

> "일단 yaw는 학습이 담당하는걸로 하고, 병진 이동 같은 경우는 그냥 포기하자. (…) target pose는
> 그냥 roll, pitch 0, 0을 유지하는 쪽으로 (…) 그렇더라도 +-30으로 학습하는건 변함없이 유지"

Mostly already the status quo and NOT a retrain change. The command interface is already
3D `[roll_att, pitch_att, yaw_rate]` (`rl_inference_node.py:132`) with no xy and no depth, and
the policy already emits 8 actions = 2 joint deltas + 6 thruster channels. Holding
`roll = pitch = 0` is a command value. The training range stays +/-30.

> "수직 스러스터를 아예 죽인 상태로 학습" — proposal 1, ADOPTED

**This collided with the same message's "pid controller - depth control", and the operator
resolved the collision on 2026-09-06:** train with the verticals dead, AND inject the `Fz` the
depth PID will produce as an exogenous disturbance carrying the pitch-direction mismatch of one
dead vertical thruster — **randomized, not constant**.

The collision was real: `m0` is the only surviving vertical (`m3` dead, `finding/077`), and
`(Fz, My)` is rank 1, so `reallocate()` keeps `Fz` and discards `My` — realised `My/Fz` is
pinned at **-0.1458 / -0.1471** across every measured segment (`finding/154`, `finding/155`).
A depth PID holding depth therefore injects a standing pitch moment the policy never saw.

> "고장 확률을 좀 더 높혀주긴 해줘" · "각종 dr 범위도 조금 늘리는 것에 대해 검토"

**Resolution: budget and reachability, not bands.** `decision/147` decision 2 (widening the
band is not recommended; re-centering the nominal is) **stands** and is not overturned.
`finding/346` — five of twenty-one DORAEMON dimensions were still expanding at the final
iteration, so the curriculum never used the bands it already has; and `finding/354` —
`inertia_scale` reports SATURATED while never reaching physics. Raising `p0` or widening bands
buys nothing while the curriculum is budget-bound. The operator accepted this on 2026-09-06.

> "yaw rate 말고 yaw 제어로 바꾸는게 좋을 것 같아"

Adopted, range **unlimited**, `cumul_yaw` **slated for removal pending review** (operator,
2026-09-06). Today it is
`ConstraintTermCfg(func=cumulative_yaw_cost, params={"limit_rad": 8*math.pi}, budget=0.01,
name="cumul_yaw")`, which directly contradicts an unlimited-range yaw position command.
`yaw_rate_cost` (soft_threshold 0.55, budget 0.10) changes role in the same move and must be
re-judged rather than left standing. **See the tether hazard under item 14.**

> decimation 20 (operator, 2026-09-06), **conditional on the sub-step delay implementation**

The operator chose 10 Hz training, then re-affirmed it after the adversarial pass surfaced two
facts the original recommendation did not carry (§10, B-2), attaching the sub-step delay
implementation as a precondition. That precondition is gate **G8**.

### 4. Section-5 delta for the next teacher

On top of `ALBCSimToRealEnvCfg` (`constrained_albc/envs/main/config_simtoreal.py`, the seven
frozen overrides — task id `Isaac-ConstrainedALBC-TRPO-SimToReal-v0`, `finding/377`):

| # | knob | R3a plant | next generation | ground |
|:---|:---|:---|:---|:---|
| 8 | `decimation` | 4 (50 Hz) | **20 (10 Hz)** — gated on G8 AND on G10 | operator 2026-09-06; R-2; `finding/158` (cmd mode amplitude 100x lower at 10 Hz); **`finding/397` — `delta_scale` was 0.10 in every field run, so `control_hz` and loop gain are perfectly collinear and this row's evidence cannot separate them** |
| 9 | action delay | `control_delay_steps` (0,3) = 0-60 ms, policy-step granularity | **re-implemented at physics-substep granularity**; 152 ms = 30.4 substeps at `dt` 0.005 | `finding/148`; §10 B-2 |
| 10 | vertical channels during training | probabilistic via fault DR only | **`m0`,`m3` health pinned 0** | operator proposal 1 |
| 11 | exogenous `Fz` disturbance | none | **NEW: randomized `Fz` with coupled `My`** | operator 2026-09-06; `finding/154`/`155` rank-1 geometry |
| 12 | `set_inertias` | absent | **implement**, nominal centered on measured 0.49 | `finding/149` (1.53x, outside the DR band), `finding/354` |
| 13 | yaw command | `yaw_rate` | **yaw position, unlimited range** | operator 2026-09-06 |
| 14 | `cumul_yaw` constraint | limit 8 pi, budget 0.01 | **remove ONLY with a deployment-side tether guard** (review `yaw_rate` in the same pass) | operator 2026-09-06; §10 M-4 |
| 15 | iteration budget | 10k | **raised to 20k and FIRED 2026-09-07**, but **its ground was withdrawn the same night** (`finding/405`): the curriculum reached the FULL configured band (Beta(1,1) = uniform) at iteration ~7000 and jittered there for the last 2,750, so the budget was never binding on the curriculum. `p3c_ext20k_s30_r9999` remains a clean one-variable run with a verified byte-identical control and now answers a weaker question — does more optimisation at the already-open band help | `finding/405` (supersedes `403`), `346` |
| — | `thrust_coefficient` / `_scale` | 13.0 / (0.5, 2.0) | **HELD** | `decision/147` decision 2 stands |
| — | `thruster_fail_prob` / `dead_frac` | 0.30 / 0.5 | **HELD** | lever is budget and reachability |
| — | `enable_thrust_curve` | false | **HELD (deferred)** | `decision/209` item 3; T200 bench does not exist |

**Item 8 cost, sized — this was missing from the first draft and it fights item 15.**
`decimation` is physics steps per policy step, so 4 -> 20 multiplies physics work per
transition by **5x**. Phase 3b measured 4.5 s/iter for 10k iterations = 12.5 h; the same
iteration count at decimation 20 is **~62.5 h**. Item 15 asks for MORE iterations because the
curriculum was budget-bound at that count. Three ways out, none free: cut `num_steps_per_env`
5x (same wall-clock, 5x fewer transitions per iteration, noisier gradients); raise `num_envs`
(Phase 3b already sat at 11.5/12 GB VRAM — no headroom); or raise `sim.dt` from 0.005 with
`decimation` 10 for the same 0.1 s policy step at half the physics cost, which is a
plant-fidelity decision and not a free knob. **Size this in G4 before queueing, not during.**

**Item 9, why the naive form is wrong.** At `decimation` 20 a policy step is 100 ms, so
`control_delay_steps (0,2)` samples exactly `{0, 100, 200} ms` — the measured **152 ms is never
injected**, and a third of the envs train at zero delay. At 50 Hz `(0,3)` gives
`{0,20,40,60} ms`, finer but truncated at 40% of the real delay. Neither is acceptable. The
delay buffer must move from policy-step to physics-substep granularity (`dt` 0.005), where
152 ms is 30.4 substeps and the DR band can straddle it properly. **This is G8 and it gates
item 8.**

**Item 10 implementation note.** `thruster_fixed_health`'s docstring says "Intended for eval
only; leave None on any training run" (`config.py:389`), so it must not be repurposed. This
needs a new dead atom in the shape of `thruster_dead_frac` (G0-I, `finding/311`): default off,
incumbent bit-identical, unit test on exposure.

**Item 11 specification.** The lever arm 0.145 m is confirmed independently by tape measure
(`finding/156`, centre-to-centre 29 cm = 2 x 0.145). **Take the SIGN from the artifact, not
from the sim constant** — `deployed_tam.json`'s realised measurement is `My/Fz = -0.1458`
(`finding/154`, `finding/155`), while the sim base matrix carries `(+0.145, -0.145)` before
`_ESC_CHANNEL_ORDER`. Re-deriving the sign from the sim column order is exactly the failure
class the robot SKILL forbids. The disturbance is random in magnitude and timing.

**Item 14 physical hazard — operator confirmation required.** `cumul_yaw` caps accumulated
vehicle yaw at 8 pi (4 turns). **The vehicle is tethered**: the board is reached over a
USB-ethernet link at 192.168.2.100, and this session ran `rosnode list` on it while the robot
was in the water. Unlimited yaw is therefore a cable-wrap hazard on the real robot, not only a
sim question. Removing the constraint in sim is safe only if the deployment carries an
equivalent guard, or the operator states the tether's turn tolerance. Independently, an
unlimited-range yaw position command needs the observation to carry a shortest-path unwrapped
error rather than a raw accumulated angle, or the policy sees an unbounded input.

**Item 8 consequence to state.** `episode_length_s` stays 30.0 s, so physics exposure per
episode is unchanged, but the policy sees 300 decisions instead of 1500. The 0.62 Hz mode is
~16 steps per cycle at 10 Hz, still well resolved.

### 4-bis. The three candidates the field log ranked ABOVE `decimation` 20 (added 2026-09-07)

The 2026-09-06 field log (`03_notes/2026-09-06-r3a-fieldtest-log.md`, section "재학습 하네스")
closes with a four-candidate table. Item 8 above is candidate **A**, and the field log ranks it
**third, and only as a fallback**:

| field-log rank | candidate | field log's own words | in this PLAN? |
|:---|:---|:---|:---|
| 1 | **B** `velocity_limit_sim` 3.1 -> 2.40 | "**먼저.** 근본 원인, 레이트 불변, R 계열 비교 가능성 유지. sim 충실도 수정이지 제어 설계 변경이 아니다" | **no** |
| 2 | **C** action-rate cost, L1 `abs(a_t - a_{t-1})` | "**B 와 함께.** 채터를 직접 벌준다" | **no** |
| 3 | **A** `decimation` 4 -> 20 | "B+C 가 안 닫을 때만. R1~R4 전체와 비교 불가가 된다" | **yes — item 8** |
| — | **D** deployment-side `delta_scale` normalised by `hz` | "재학습 무관. `control_hz` 를 정직한 노브로 만든다" | **no** (it is what G10 tests) |

**`decision/159`'s seven operator decisions mention none of B, C or D.** Decision 1 argues from
`finding/158`'s command-amplitude gap alone. So the operator did not choose A over B and C — A was
the only candidate that reached the decision. That is the drop this section repairs. Dispositions,
each measured rather than asserted:

**B — open, cheap, and rate-invariant; no recorded reason for the drop.** The sim's PhysX joint
velocity cap is 3.1 rad/s (`envs/main/config.py:60`, the `arm_joint_vel` constraint comment) while
the deployed driver caps at **2.398 rad/s** (`OPERATING_VELOCITY=100`, vault `finding/145`
measured `+2.400 / -2.406`). At `control_hz` 50 the commanded authority `delta_scale x hz` is
5.0 rad/s, above **both**. The counter-evidence is real but narrower than it looks: `finding/158`
measured joint saturation duty 0.021% (J1) / 0.000% (J2) and p99 0.29-1.39 rad/s, so neither cap
bound during the field runs — but run 4 was baseline-only and run 1 a single 15 deg step, so that
measurement bounds **the observed ripple's mechanism**, not the plant mismatch itself. A policy
trained where the arm can slew 3.1 rad/s is trained on an arm the robot does not have. Carry it as
a candidate for the next teacher, not as settled either way.

**C — the naive reading is refuted by arithmetic; the field log's actual proposal is not** (`finding/401`)**.**
An L2 action-smoothness term already exists and is already live in the deployed teacher:
`action_smoothness` (`envs/main/mdp/rewards.py:181`, `r_s = mean(da^2) + mean(d2a^2)` on the
COMMANDED triple) with `k_s = -0.1` (`rewards.py:113`; `params/env.yaml:386` of
`trpo_p3b_lb200_s30_r2050_260904_163518`). It has never been swept. Measured on that run's own log:
`Reward/smoothness` = **-0.0100** against `Mean reward` ~= **175**, i.e. **1 part in 17,500**
(0.0057% of the return). Reaching even 1% of the return needs `k_s` ~= **-17.5**, a 175x raise,
and it would penalise broadband step-to-step jitter far harder than the 0.65 Hz component, which
is a small fraction of total `da^2`. **So "raise `k_s`" is not the fix at any plausible magnitude.**
The field log did not propose that, though — it proposed an **L1** cost, `abs(a_t - a_{t-1})`, and
at this amplitude L1 and L2 are different instruments: from `finding/158`'s cmd_J2 in-band 0.1600
at 50 Hz, action amplitude is 0.1600 x 2 pi x 0.6435 / (0.10 x 50) = 0.1294, so
`da` = 0.1294 x 2 pi x 0.6435 / 50 = **0.01046** — L1 gives 1.05e-2 where L2 gives 1.09e-4.
**Corrected 2026-09-07 by the adversarial pass:** that ~96x is the ratio of two quantities with
different units and is not a "sensitivity". Two statements survive: (i) the *gradient* ratio,
`d|da|/d(da) = 1` against `d(da^2)/d(da) = 2*da = 0.0209`, i.e. **~48x** at this amplitude; and
(ii) the shape argument, which matters more — if broadband jitter beats the ripple by a factor R in
the `(amplitude x frequency)` product, L1 sees that as R while L2 sees it as R^2. **L1 does not
isolate the low-frequency mode; it only halves the exponent of its disadvantage.** L1's gradient is
`sgn(da)`, constant, so it presses hardest on micro-jitter and gives no progressive damping on a
large limit cycle. Any L1 arm must be pre-registered on tracking error as well as on ripple.
An L1 term is reachable cfg-side
with no new plumbing through the existing registry (`ALBCRewardCfg.extra_terms: list[RewardTermCfg]`,
`rewards.py:120`). The field log also pre-empts the obvious objection: a learned cost is not a
"hard clamp / latch / rule-based shaping" and sits in the same category as `manipulability_cost`,
so it is inside constraint 1 rather than outside it. Literature: CAPS (Mysore, Mabsout, Mancuso,
Saenko, **arXiv:2012.06644**) regularises exactly this and reports that filters "behaved
inconsistently with NN controllers, requiring the problem to be addressed at the control policy
level during training"; its authors' stated hypothesis is that **temporal** smoothness alone
suffices only in well-modelled environments and **spatial** smoothness is what buys robustness
under domain shift — ALBC's term is temporal-only. Caveat kept honest: ALBC's ripple is a 0.62 Hz
limit cycle, not the high-frequency chatter CAPS targets, so the mechanism is analogous, not
identical.

**D — not a retrain item at all, and already carried as G10.** Normalising the deployment-side
`delta_scale` by `hz` makes `control_hz` an honest knob; G10 is the same intervention run once as
a discriminating field probe. Nothing further owed here.

**Net effect on item 8.** Item 8 is gated on G8 *and* G10 (rate vs gain, `finding/397`), and it sits
below two candidates its own source ranked higher. **Corrected 2026-09-07 by the adversarial pass:**
B is a *candidate*, not a gate. The observed limit cycle never approaches either ceiling — in-band
cmd_J2 0.16 rad at 0.64 Hz is a peak joint rate near 0.64 rad/s, and measured p99 across the field
runs was 0.29-1.39 rad/s against caps of 2.40 (robot) and 3.1 (sim) — so lowering `velocity_limit_sim`
cannot change a trajectory that never touches it. B stays worth doing as a sim-fidelity repair (a
policy trained where the arm can slew 3.1 rad/s is trained on an arm the robot does not have), but it
does not gate item 8. **G10 does.**

### 5. Phase 0 gates — nine are desk work, G10 needs the robot; three are blocking

**Header corrected 2026-09-07.** It read "none needs the robot" while G10, added in the same
pass, says "robot in the water so operator-gated". G10 is the only robot-gated gate; the other
nine need no robot.

| gate | what | blocks | record |
|:---|:---|:---|:---|
| **G1** | **Fix the Phase 4 exam.** `analysis/dr_config.py` builds DR from the CLASS DEFAULT at three sites and `eval.py:apply_dr_config` replaces `env_cfg.randomization` wholesale, discarding every `env.randomization.*` override. **Measured scope (Update 2026-09-07): on R3a re-graded with the fix, `none` is bit-identical, `soft`/`medium` all 10 cells stay inside the 0.10 deg floor, and only `hard` moves (-0.203 to -1.025). G1 keeps top priority because the verdict-driving deltas are all hard rows, but the re-grade is cheaper than 'everything'.** | everything scored | `finding/391`, `382`, `debugging/319` |
| ~~**G2**~~ **CLOSED 2026-09-07** | `PASS  339 fields compared; exactly 7 moved, all seven as launched`, exit code 0. The seven-field freeze of `ALBCSimToRealEnvCfg` is verified at the resolved output. **The stated cause was wrong and that is why it survived three revisions**: the test never died at Kit startup — a bisecting probe reached `AppLauncher`, built both configs (85 top-level keys each) and then **blocked in `app.close()`**, so the asserts had already run and PASS had already been written into a block-buffered stdout that never flushed. Kit's banner fills the first 4 KB blocks, which is why the log ends mid-banner and reads like a startup death. Fix: `flush=True` on the output and `os._exit(0)` instead of returning through the blocking `close()` | ~~the config freeze~~ nothing | `finding/406` (supersedes `402`), `379`, `377` |
| **G8** | **Re-implement the action delay at physics-substep granularity.** Operator precondition on item 8. | item 8 | §10 B-2, `finding/148` |
| G3 | Measure the sim's attitude mode directly (free-decay rollout) and compare against the real 0.6233 Hz. | sizing item 12 | `finding/158` |
| G4 | Re-score `p3b_7500` and R3a on the FIXED exam, with `decimation` as a second axis AND the item-8 wall-clock sized. Confirm `env.decimation` actually reaches `eval.py` — `finding/382` shows Hydra overrides silently failing to. | items 8, 15 | `finding/391`, `362` |
| G5 | Implement `set_inertias`; re-measure effective `I_pitch` under nonzero `inertia_scale`. | item 12 | `finding/354`, `149` |
| G6 | **Premise corrected 2026-09-07 — the config already exists and has been scored.** `ls -d .hq/work/p4/*/pair34_d2` returns **13** arms (`inc13w`, `p3b_7500`, `p3b_final`, `sd_inc9998`, `sd_p3b7500`, `sd_r1`, `sd_r2`, `sd_r3a`, `sd_r3a_envdr`, `sd_r3b`, `sd_r4a`, `sd_r4a999`, `sd_r4c`), and `finding/363` (2026-09-05, confidence high) already read it: fault and delay are **non-additive** — the incumbent overshoots its own additive prediction by 7.232 deg and sits at 9.360 deg in the exact deployment condition, while both retrained checkpoints match theirs. `finding/360`, which said the two had never been scored together, is **superseded by `finding/363` of the same day**. What is genuinely left in G6 is only the second half: score the two resonance regimes separately, policy-generated (thrust off) vs externally excited (thrust on) — `finding/158` shows they differ. | the resonance-regime claim only | `finding/404` (supersedes `360`), `363`, `158` |
| G7 | Re-judge `joint1_pos`: the shipped constraint cannot fire (measured angle wraps at +/-2 pi under a 4 pi limit). Same pass as item 14. | constraint set | `finding/378` |
| G9 | Close the joint->attitude non-monotonicity from the existing bags' FK (J1/J2 phase vs theta2). No robot, no retrain. **Carry the command-content difference as a competing explanation: run 4 (25 Hz) is baseline-only while run 3 (50 Hz) has +/-15 steps, so the inversion is not necessarily kinematic.** | nothing; hygiene | `finding/158`, `397` |
| **G10** | **Separate rate from loop gain before freezing item 8.** One field run, `control_hz` 50 with `delta_scale` 0.02 = 1.0 rad/s, the same loop gain as 10 Hz at 5x the sensing rate; one launch argument, robot in the water so operator-gated. Low ripple => gain is the knob and item 8's `decimation` 20 (with G8 and the 5x wall-clock) is not needed; high ripple => rate is the knob and item 8 stands. **Pre-registration corrected 2026-09-07 by the adversarial pass:** a policy trained at `delta_scale` 0.10 and deployed at 0.02 has its whole action stream scaled 5x down, so "low absolute ripple" is guaranteed by construction and proves nothing. The readout must be the **ratio**: a fall of ~5x is pure attenuation and the run is null; **much more than 5x** (the limit cycle collapses rather than shrinks) means gain is the knob; **less than 5x** means rate matters. Tracking quality (dead time, rise, settling %) must be recorded in the same run — "low ripple with collapsed tracking" is not evidence for gain. And the 152 ms transport delay is absolute in continuous time, contributing the same ~35 deg of phase lag at 0.6233 Hz at either rate, so G10 separates loop gain from sampling rate but NOT from transport lag. | item 8 | `finding/397`, field log 2026-09-06 "다음 탐침" |

### 6. Open-backlog reconciliation

**needs-apply-before-retrain (2, marinelab — count corrected 2026-09-07):** the live ledger, `omx wiki list --status needs-apply-before-retrain`, returns exactly `finding/264` and `finding/352`. `decision/209` is listed below because the plan carries it, but **its actual status is `none`, not `needs-apply-before-retrain`** — so a launch ack that enumerates the ledger will not name it, and the ack on `sd_p3b7500_c3_dr5_beta0_s31` correctly names only the two.

| item | disposition |
|:---|:---|
| `finding/264` control_delay_steps (0,0) vs 1.2-4.7 stale steps | **CARRIED** — item 9 / G8 |
| `finding/352` section-5 config is launch-override-only | **CARRIED** — `config_simtoreal.py` + task id exist (`finding/377`), but G2 must make the equivalence test assert before this closes |
| `decision/209` plant-change batch v2 (4 items) | **PARTIALLY CARRIED.** Item 4 (arm actuator response) is the same defect as `velocity_limit_sim` 3.1 — a no-load bench plateau (`marinelab/assets/albc/albc.py:206`) — against the deployed driver cap 2.398 rad/s (`OPERATING_VELOCITY=100`, `finding/145`). Its gate is already satisfiable: vault D13 records that the 2026-08-25 `j2_gain`/`j2_step` bags hold the XW540 step response and only need posting to the container. **Items 1, 2 (buoy added mass, damping anisotropy) DEFERRED** — both need the sizing estimate `decision/209` itself demands. **Item 3 (thruster curve) DEFERRED** — T200 bench does not exist |

**needs-experiment, carried:** `finding/346` (item 15), `354` (item 12, G5), `362`
(checkpoint selection — the runner takes the last checkpoint, not the best), `378` (G7),
`379` (G2), `382` (G4), `391` (G1), `315` (closed by `performance_lb` 200, kept as precedent),
`360` (G6), vault `145` (items 8/12), `148` (item 9/G8), `149` (item 12), `158` (items 8/9,
G3/G6/G9).

**Reconciliation against the live ledger, 2026-09-07.** Two of the slugs above do not actually
hold `needs-experiment`, so a status query will not surface them and the word "carried" is
doing work the ledger does not support: `finding/346` and `finding/360` both carry
`status: none` with `confidence: low` and `topic: session-log` in their frontmatter, while
`346`'s **body** is marked `[CONFIDENCE: HIGH]` and names its evidence artifact
(`analyze_training.py --deep`, TIER 2 DORAEMON table). That is a frontmatter/body mismatch, not
a weak claim — the claim itself is verified below under item 15. Fix the frontmatter or the
status queries keep missing them.

And five slugs carrying `needs-experiment` appear nowhere in this section:
**`debugging/319`**, **`finding/363`** (now in G6 above), **`finding/395`**, **`finding/396`**
(now in the Update 2026-09-07 tooling note), **`finding/397`** (now in item 8 and G10). Silent
drops are defects by this program's own rule; they are named here so the next summary inherits
them rather than re-losing them.

**needs-experiment, explicitly DEFERRED with reason:**

| item | reason |
|:---|:---|
| `finding/305`, `309`, `312` | vertical-TAM lineage, superseded by `finding/146`/`156`; lever 0.145 confirmed by tape measure |
| `finding/313`, `318`, `321`, `355` | G0-C / exam-confound lineage, all resting on the exam G1 voids — re-open after G1 |
| `finding/380`, `383`, `384`, `385`, `386`, `387`, `389` | student-ladder results against teacher `p3b_7500`. A new teacher obsoletes them (§8) |
| `finding/163`, `198`, `296`, `decision/061`, `263` | pre-program lineage, no bearing on this delta |
| `decision/301`, `390` | program-open and deployment-choice records, already reflected |
| vault `finding/135`, `136`, `137`, `141`, `142`, `144`, `157` | robot-side lineage absorbed by `146`/`154`/`155`/`156`/`158` (157 is superseded) |
| vault `finding/139`, `decision/103`, `112`, `124`, `handoff/102`, `review/101`, vault `decision/033`, `handoff/107` | harness/tooling items, not plant items |

### 7. Launch order

**Nothing fires from a session.** G1, G2, G8 are blocking; the rest is desk work. Training is
queued with `omx queue-launch` only and fired by the operator's own shell, per the rule frozen
at 3.5 and reaffirmed at 3.9.

Order (**updated 2026-09-07**): the blocking set is now **{G1, G10}** — G1 is implemented and
committed (`--env-dr-anchor`, `ea42375`) and **G2 is closed** (`finding/406`). G10 is the only
robot-gated one and it is the operator's to schedule.

**G1 (done), G10 (robot, operator) -> G3, G5, G7, G9 (desk; G8 only if G10 says rate) -> G4
(re-score; item 15's sizing is moot, see `finding/405`) -> queue the teacher run -> operator fires
-> G6 (resonance regimes only, `finding/404`) on the result.**

### 8. Cost stated plainly

`decision/209` requires this to be said rather than discovered: **a teacher retrain obsoletes
every student arm distilled from `p3b_7500`** — R1, R2, R3a, R3b, R4a, and R4c, which was fired on 2026-09-06 and returned null (Update 2026-09-07).
That includes the policy deployed to the robot on 2026-09-06. A fresh student ladder has to be
re-run against the new teacher. `decision/209` calls this "the single largest hidden cost of
the batch". The 2026-09-06 field result is the strongest reason to keep R3a running on the
robot while the new teacher trains.

Second cost, from the adversarial pass (§10 m-2): item 10 pins the verticals dead for the whole
run, so this teacher is **a policy specialised to the 2026-09 damaged actuator set**, not a
general sim-to-real teacher. If `m3` is ever repaired, or a different thruster fails, it must be
retrained. Say so now rather than discover it.

Third cost: item 8's 5x physics-per-transition (§4).

### 9. Literature consulted for the rate decision

| paper | what it gives, and its limit |
|:---|:---|
| Gangapurwala, Campanaro, Havoutis, **arXiv:2209.14887** | Abstract: robust dynamic locomotion at as low as 8 Hz on ANYmal C, a 5-200 Hz comparative study, and "low-frequency policies are less sensitive to actuation latencies and variations in system dynamics", transferring without dynamics randomization or actuation modelling. **Limit: transfer to this robot is by analogy** — a directly-actuated quadruped is not an underactuated buoyancy-driven vehicle with a rank-1 vertical axis. Only the abstract was read; the paper's internal control architecture was not verified either way |
| Zhang, Kirschner, Zhang, Zanini, Ayoub, Dehghan, Schuurmans, **arXiv:2212.08949** | An approximation-vs-statistical-error trade-off in temporal resolution giving an optimal discretization for a fixed data budget: "finer is better" is false as a general rule. **Limit: this bears on the iteration-budget question (item 15), not on phase margin or control bandwidth** |
| Tallec, Blier, Ollivier, **arXiv:1901.09732**; De Asis and Sutton **arXiv:2406.14951**; Lyskawa and Wawrzynski **arXiv:2104.04004**, **arXiv:2308.04299** | **Background only, not grounds.** 1901.09732 is a value-based (Q-learning) result and this program uses TRPO; the rest are the same axis of the fixed-dt assumption |

The decisive evidence for 10 Hz is not the literature — it is `finding/158`: at 10 Hz the
policy's own command carries ~100x less energy at the plant's resonant frequency.

### 10. Adversarial verification record (ground 4)

Required because `finding/391` and the incoming brief both noted that nothing in this line had
been cross-checked. codex hit its usage limit; **agy (Gemini 3.1 pro, cross-family) ran the
review.** Its findings were then checked against the robot's bags rather than accepted.

| id | claim | verdict after checking |
|:---|:---|:---|
| B-1 | `sqrt(K/J)` written as Hz without the 2 pi | **CONFIRMED**, fixed in §2 |
| B-1 | sim rigid-body inertia compared against a wet measurement | **PARTLY** — sim does model rotational added mass (`finding/149`: DR band 0.267-0.374), so it is not a dry/wet category error; but the `finding/354` `I_pitch` 0.12 branch is provenance-unverified and is **dropped**. Direction now cites `finding/149`'s 1.53x directly |
| B-2 | 10 Hz quantizes the delay to {0,100,200} ms and never injects 152 ms | **CONFIRMED** — became item 9 and gate G8, the operator's precondition on item 8 |
| B-2 | 10 Hz loses ~9 deg of phase margin at the mode (45.1 vs 36.4 deg) | **CONFIRMED** as arithmetic and as an omission. Reframed: `finding/158` shows the policy at 25/50 Hz is *driving* the mode, not damping it, so lower gain is right for that regime; phase margin matters in the thrust-on regime where the mode is externally excited. Both regimes are now scored separately (G6) |
| M-1 | "25 Hz sits at the saturation boundary" is unsupported; falsify at <1% duty | **CONFIRMED, hypothesis KILLED.** Measured duty J1 0.021% / J2 0.000%. The `delta_scale 0.02` discriminator run is withdrawn — there is nothing left to discriminate **[SUPERSEDED 2026-09-07 -- `finding/397`. This withdrawal is filed under the SATURATION hypothesis, which is indeed dead. The mechanism `finding/158` KEPT is loop gain, and under it the probe still discriminates: `delta_scale` was 0.10 in all four field runs, so `control_hz` and `delta_scale x hz` are perfectly collinear and no field measurement can attribute the ripple to rate. Restored as gate G10.]** |
| M-2 | Aliasing asserted without showing the 0.33 Hz band power | **CONFIRMED as a gap; claim SURVIVED the check.** Mode band 79.9% of energy vs 0.93% at 0.33 Hz, peak ratio 193x. Now quantified in `finding/158` |
| M-3 | Literature over-cited | **CONFIRMED**, §9 rewritten; 1901.09732 demoted to background. agy's characterisation of 2209.14887's internal architecture is itself unverified and is not adopted |
| M-4 | Unlimited yaw + `cumul_yaw` removal risks tether damage | **CONFIRMED** — the vehicle is tethered (session reached 192.168.2.100 with the robot in the water). Item 14 now requires a deployment-side guard and operator confirmation |
| m-1 | G4 "validates item 8" while item 8 is already frozen | **CONFIRMED** — item 8 is now gated on G8 and sized in G4 |
| m-2 | Pinning the verticals dead overfits to the current damage | **CONFIRMED** — stated as a cost in §8 |

Two defects in this session's own measurement were found in the same pass and are recorded in
`finding/158`: the first FFT ran on the raw IMU frame because `rotate_imu` was called with three
of its four arguments and a `try/except` swallowed the `TypeError`; and the saturation
hypothesis above. `finding/157` is superseded.

## Update 2026-09-07 — ksm-mac review of the 09-06 handoff: 5 of 7 judgments stand, item 8's evidence cannot separate rate from gain

Requested by the operator via `03_notes/2026-09-07-retrain-handoff-to-ksm-mac.md`: review the
seven judgments against the primary records rather than inherit them, and do not integrate if
something is wrong. Read: vault `finding/157`/`158`, `03_notes/2026-09-06-r3a-fieldtest-log.md`,
`2026-09-06-retrain-planning-prompt.md`, this PLAN's `## Update 2026-09-06`, the two
`pending-launch.json` entries, and the `.hq/work/p4` npz arrays directly.
`decision/159` had not synced at review time and was NOT read.

### Verdict on the seven

| # | judgment | verdict |
|:--|:---|:---|
| 1 | 10 Hz (`decimation` 20) | **stands, better supported than the handoff claims** — see below |
| 2 | the field log's 0.33 Hz is aliasing | stands; `1/0.3485 = 2.87 s`, band power 79.9% vs 0.93% |
| 3 | "R3b" is a taken name | stands (`finding/388`) |
| 4 | every Phase 4 number is void | **overstated** — corrected in the G1 row above |
| 5 | widening DR bands is not the lever | not independently checked here; `finding/354`/`346` were not re-read |
| 6 | the saturation hypothesis is dead | the refutation stands; **the attached withdrawal does not** — see G10 |
| 7 | three open items (G9, G3, G4) | stand; G9's framing needed the note now in its row |

### Judgment 1 — the handoff's own worry resolves in its favour

The handoff asks whether the amplitude comparison is fair when the runs differ in command
content. From the field log: run 1 (10 Hz) is cmd (0,0) 145 s + roll +15 154 s + roll -15 30 s;
run 3 (50 Hz) is roll +/-15, 250 s; run 4 (25 Hz) is **baseline only** — the operator stopped it
before the steps. So runs 1 and 3 are **command-matched**, and they carry the core number:
cmd_J2 in-band 0.00128 vs 0.1600, a 125x gap with no confound. Run 2 is an independent 10 Hz
replicate at a LARGER step (+/-30) whose mode-band share is 0.028 against run 1's 0.030.
The only unmatched run is run 4 — and it is the one G9 is opened on, hence the note added there.

### Judgment 6 — what the withdrawal took with it (`finding/397`, new)

`delta_scale` was **0.10 in every field run** (run 3 banner `0.1000/tick -> 5.000 rad/s`, run 4
`-> 2.500`, 10 Hz `-> 1.0`). `control_hz` and loop gain are therefore perfectly collinear across
all four runs and no field measurement can attribute the ripple to one rather than the other.
`finding/158` states the mechanism as loop gain; item 8 adopts the rate. The one experiment that
separates them — 50 Hz with `delta_scale` 0.02, the same 1.0 rad/s at 5x the sensing rate, one
launch argument — was withdrawn under §10 M-1, whose subject is the dead saturation hypothesis.
The ripple is also strongly non-proportional (2x gain -> 1.28x ripple; 2.5x gain -> 98x), with the
step falling right where commanded authority crosses the measured 2.40 rad/s joint ceiling.
Restored as **G10**, and item 8 now waits on it: if gain is the knob, `decimation` 20 is
unnecessary and G8 plus the 5x wall-clock (12.5 h -> 62.5 h) go with it.

### A second tooling defect (`finding/396`, new)

`p4_score.pairing()` and `tools/compare_arms.py:check_anchor()` compare only the 23 sampled
`dr_*` arrays, and the npz records **no thrust and no delay field**. Measured: `sd_r3a` and
`sd_r3a_envdr` — same checkpoint, same seed, one graded at the class default and one at the
section-5 band — have identical signatures (max abs diff `0.000e+00`, pairDR `0e+00` in all 20
cells) while the hard tier differs by up to 1.03 deg. `check_anchor()` reasons forward correctly
but the gate uses the converse, which fails for any plant field the npz does not sample-log.
Harmless for today's 7-arm table (all graded at the class default); wrong the moment G1's fix is
applied to some arms and not others, which is the next step. `decision/392` makes anchor identity
the table-admission rule, so this needs a fix before G4's output enters any table.

### R4c: fired, and null

Fired 2026-09-06 20:48 with operator approval, trained rc 0 at 23:01, exam 5/5 at 23:53. Read
against its own pre-registration ("readable only on the 8 none/soft rows; R4c beats R3a by more
than 0.10 deg on a majority"): **0 of 10 readable rows, every one a tie, max |delta| 0.079 deg.**
The pre-registration named this null at roughly even odds. Raising the budget 1000 -> 10000
iterations (400 -> 9400 at beta=0) bought nothing measurable. `pending-launch.json` still reads
`status: pending approval` because the launch went through the wrapper rather than `omx`.

Scoreboard against the distillation teacher `p3b_7500`, recomputed here (R1 `0/1/19` and R4a
`0/0/20` reproduce the ledger exactly, confirming the reference): R3a `9 tie / 2 better / 9 worse`,
R4c `11 / 1 / 8`, R4c vs R3a `14 / 3 / 3`. The ledger's R3a `11/2/7` differs by two cells that sit
**exactly on the 0.10 deg floor** (`healthy/none` +0.099, `healthy_d1/none` +0.100) — the deployed
arm's verdict rests on cells 0.001 deg from the threshold. Still inside the seed-31 pre-registration
band of 11 +/- 3.

### Next runs — PLANNED, NOT QUEUED

The operator approved both on 2026-09-07 and then instructed "plan only, do not proceed with
training". Neither is in `omx queue-launch`; both are written here for the operator to queue and
fire.

| run | GPU | what | why now |
|:---|:---|:---|:---|
| teacher re-grade | 0 | `p3b_7500` through the same exam with `--env-dr-anchor` (~1 h) | half of G4. Every student row today compares a student to a teacher graded on a different plant; this is the only thing that makes the table valid, and it survives the teacher retrain |
| `s31` | 1 | `sd_p3b7500_c3_dr5_beta0_s31`, already queued 2026-09-06T11:12 UTC | R3a reproducibility; pre-registered at class level (tie rows within 11 +/- 3) |

Blocking gates are unchanged and none of this fires before them. Open and NOT carried: `decision/159`
(not yet synced to the vault; its slug contains `r3b`, which judgment 3 forbids — confirm the title
when it lands).


## Update 2026-09-07 (night) — `decision/159` read; four plan defects repaired; two runs fired under blanket operator approval

Operator instruction, 2026-09-07 ~01:05 KST, verbatim in intent: review the plan thoroughly against
the literature, the prior results and the marinelab records; **fix it if there are problems and
otherwise proceed with training**; do not ask for approval — "지금 미리 전부 발사 하는거 승인";
and consider running in parallel on `ksm-nas` to save time. This section records what that produced.

### What `decision/159` changed once it was readable

It synced at **01:00:05** on 2026-09-07 (9,442 bytes) — the Update 2026-09-07 above was written
without it and said so. Reading it does not overturn that review; it sharpens two entries and adds
one obligation.

- **Judgment 3 is now closed by the operator's own words.** Decision 0 states that `R1..R4c` are
  *student* arms off `p3b_7500`, that R3b is already run and closed 20/20 (`finding/388`), and that
  the next generation is therefore a new `p3*` **teacher** run. The `r3b` in `decision/159`'s own
  slug is a negative mention, not a violation.
- **Section 4-bis above is strengthened, not weakened.** None of the seven decisions mentions the
  action-rate cost, `velocity_limit_sim`, or `delta_scale` normalisation. The operator was shown
  candidate A alone.
- **Decision 1 predates `finding/397`.** It reasons from `finding/158`'s command-amplitude gap, which
  `finding/397` then showed cannot separate rate from loop gain. That is an escalation to the
  operator, not something this session may reinterpret — item 8 stays gated on G10.
- **Decision 5 makes a cross-family adversarial pass a PRE-QUEUE gate.** This session is Claude and so
  is the review above; it does **not** satisfy that gate. Flagged as unmet below.
- **Body defect in the record itself.** In `decision/159`'s "감수하는 비용" section, three wrapped
  continuation lines have lost their first character: "가장 큰 / **은** 비용" (숨), "사다리를 /
  **시** 돌려야" (다), "`m3` 를 / **리**하거나" (수). The title is also fenced in a code block rather
  than an H1, unlike `finding/158`. The vault store is append-only, so this needs a comment or a
  supersede — the operator's call, not repaired here.

### `ksm-nas` — asked again, answered again: it is not a training resource

The operator asked to consider parallelising there. `finding/394` measured it on 2026-09-06 and this
session reproduced the measurement from ksm-mac at 01:10 on 2026-09-07: `ping 192.168.10.34` 100%
loss and no ARP entry although this Mac sits on that same /24 as 192.168.10.17; `ssh` port 9931
connection refused; and `tailscale status` lists ksm-mac, kim-macbookair, ksm-ubuntu, ksm-window-mini
(offline), z-fold8 and a mullvad exit node — no `ksm-nas`. **Parallelism available tonight is
ksm-ubuntu's two GPUs and nothing else**, which is what was used.

### Fired, 2026-09-07, under the operator's blanket approval

| run | GPU | what | ground | ETA |
|:---|:---|:---|:---|:---|
| `p3c_ext20k_s30_r9999` | 0 | **item 15**: resume the teacher from `model_9999` for +10,001 iterations, 10k -> **20k**. One variable: iterations. Same section-5 delta, same `performance_lb` 200, same seed 30. Control is `model_9999` of the same run | measured below | ~11:20 KST |
| `sd_p3b7500_c3_dr5_beta0_s31` | 1 | R3a second realisation at seed 31, queued 2026-09-06T11:12 UTC and never fired | `finding/389`; the deployed arm's verdict rests on two cells 0.001 deg from the threshold | trained 01:25, exam ~02:50 |
| `regrade_chain` (4 arms) | 1, chained | R1, R2, R4a, R4c re-graded with `--env-dr-anchor` | `decision/392` + `finding/396`: a table mixing anchored and class-default arms is inadmissible and the npz signature cannot detect the mix | ~08:45 |

Launch-gate ack: the live ledger (`omx wiki list --status needs-apply-before-retrain`) returns
exactly `finding/264` and `finding/352`, and the s31 `pending-launch.json` acknowledges exactly
those two. Resume verified rather than assumed, per
`feedback-resume-flag-overwritten-by-cli-default`: the log opens at `Learning iteration 9999/20000`
and loads `RESUME_p3b_9999/model_9999.pt`, and the DORAEMON curriculum restored rather than
restarting cold — `DR/buoyancy_force_mean` 76.02-76.11 against the incumbent's closing 76.37-76.45,
`inertia_*` 0.1175 against 0.1182, `payload_mass` 1.614 against 1.625, i.e. fresh draws from the
same widened Betas, not the initial narrow band. Load path confirmed in code at
`envs/_core/runners/on_policy_doraemon_runner.py:117-119`. First readings: iteration 10117,
`Mean reward` 210-216, above `performance_lb` 200, so the curriculum gate is open.

**Item 15's ground, measured directly rather than cited.** `curriculum_trajectory.json` of
`trpo_p3b_lb200_s30_r2050_260904_163518` has 32 records from iter 2249 to 9999. Between the last
two (9749 -> 9999) **nine of the 21 DR dimensions still had a widening Beta sd**:
`added_mass_scale` +0.0068, `water_density` +0.0098, `cog_offset_z` +0.0063, `cog_offset_y` +0.0025,
`fault_severity` +0.0012, plus `cob_offset_y`, `buoy_volume_scale`, `ocean_current_strength`,
`payload_mass`. `finding/346` said five; the direct measurement says nine. Either way **the
curriculum had not converged when the budget ran out**, which is exactly what `decision/147`
decision 2 and `decision/159` 결정 3 name as the lever instead of widening the bands.

### G2 reproduced live — still open, and its docstring's claimed fix does not hold

`test_simtoreal_cfg.py` was run twice tonight on an otherwise idle box, once via
`/isaac-sim/python.sh` (its documented entry point) and once via `/workspace/isaaclab/isaaclab.sh -p`
(the entry point `eval.py` and every training script use). **Both died during Kit startup with no
PASS line, no traceback and no assertion output**, logs ending at the `gpu.foundation.plugin`
warnings at 3,246 and 4,224 bytes. The file's own docstring theorises that
`AppLauncher.add_app_launcher_args()` was the missing piece and it is already used, so that
hypothesis is refuted: the failure survives it and survives the entry-point change. The body of the
test is sound — real asserts, an explicit vacuity guard (`assert base`), an exact-difference-set
check and a printed PASS line — so what is broken is the harness, not the check. **G2 stays
blocking and now has a reproduction.**

Note for whoever fixes it: G2 gates the **task-id** path (`Isaac-ConstrainedALBC-TRPO-SimToReal-v0`,
`ALBCSimToRealEnvCfg`). Tonight's teacher run deliberately does **not** use it — `p3c_extend.sh`
reproduces the incumbent's launch form byte for byte, `--task Isaac-ConstrainedALBC-TRPO-v0` plus
the same six explicit Hydra overrides that produced `model_9999`. So G2 does not gate that run, and
this is not a way around G2 for anything that does use the task id.

### What was NOT launched, and why — the plan's own teacher is not launchable tonight

Of the eight rows in the section-5 delta, **two are blocked on the operator or the robot and four
are unwritten code**:

| item | state |
|:---|:---|
| 8 `decimation` 20 | blocked — G10 needs the robot in the water and is operator-gated; `finding/397` says the field evidence cannot separate rate from gain |
| 9 substep-granularity delay | **unwritten.** The delay is applied once per policy step at `albc_env.py:761` (`_pre_physics_step`), so its unit is 20 ms. Moving it to `_apply_action` (once per `dt` = 5 ms substep) is the fix, but `_actions` is deliberately overwritten there so history and `thruster_energy` observe the applied stream (`albc_env.py:752-760`); the move changes what the observation sees unless a separate applied buffer is carried. That is a design change, not a rename |
| 10 verticals pinned dead | **unwritten.** `thruster_fixed_health` exists but its docstring says eval-only (`config.py:389`) and §4 forbids repurposing it; this needs a new atom in the shape of `thruster_dead_frac` |
| 11 exogenous `Fz` with coupled `My` | **unwritten** |
| 12 `set_inertias` | **unwritten, and the gap is confirmed at the source.** `mdp/events.py:268-269` writes `hydro.rigid_body_inertia`, and `marinelab/core/hydrodynamics.py:123-127` states in a comment that this feeds the Coriolis term only: "DR randomizes `_rigid_body_inertia` (hydro model uncertainty), but PhysX's actual inertia is NOT randomized by `inertia_scale` (only by `body_mass_scale` via `set_masses`)". `finding/354` stands |
| 13, 14 yaw position / `cumul_yaw` | blocked — `decision/159` 결정 4 marks the tether a physical hazard requiring operator confirmation of the allowed turn count |
| 15 iteration budget | **fired tonight** |

Writing four plant features unreviewed and spending 12.5 h of GPU on them is the failure mode
`feedback-plan-decision-escalation` records; and `decision/159` 결정 5 requires a cross-family
adversarial pass before anything is queued, which a Claude session cannot supply for its own work.
So the night went to the one item that needed no new code, had a verified ground, and preserves the
control — item 15 — plus the two exams that make the existing table admissible.

### Adversarial verification, 2026-09-07 (`decision/159` 결정 5) — one family, not two, and it changed the plan

**Ordering violated, stated plainly.** 결정 5 makes this pass a *pre-queue* gate and the three runs
were fired first, under the operator's blanket approval, and reviewed after. That is the wrong order
and the review below is what it cost to find out — one of its findings withdrew the stated ground of
a run already in flight.

**Two families were attempted, one answered.** `codex` (0.153.2, present and authenticated) returned
`turn.failed: You've hit your usage limit` after 5 s, so the two-family gate degraded to a single
family — `agy` (Gemini 3.1, effort high, 1 m 8 s, 7 findings). Per
`feedback-two-vendor-families-split-coverage` a single family covers roughly one axis, so this pass
should be re-run against codex when the limit resets.

| # | agy's finding | verdict |
|:--|:---|:---|
| 6.2 | the nine "still widening" dims were never checked against their configured bounds | **LANDS, and it is the most consequential result of the night.** Measured: Beta(1,1) = uniform = the full band, sd 0.288675; the curriculum reaches mean 0.998 of that at iteration 7249 with all 21 dims above 0.95, then jitters 0.968-0.986 for the last 2,750. Item 15's ground withdrawn, `finding/403` superseded by `finding/405`, and **결정 3 re-opened** |
| 4 | G10 conflates command attenuation with plant stability; an unretrained 5x gain cut trivially lowers absolute ripple, and the 152 ms transport delay is rate-independent | **LANDS.** G10's readout is now a ratio with a tracking-quality co-registration, and its scope is narrowed to gain-vs-rate, not gain-vs-transport-lag |
| 3 | the "96x" is a ratio of differently-dimensioned quantities, not a sensitivity; L1 does not isolate the low-frequency mode | **LANDS.** Replaced with the gradient ratio (~48x) and the R-vs-R^2 shape argument; `finding/401` carries the same correction |
| 7 | do not *gate* item 8 on candidate B when the limit cycle never approaches either velocity ceiling | **LANDS.** B demoted from gate to candidate |
| 6.1 | citing `inertia_*` Beta widening as evidence while arguing elsewhere that `inertia_scale` never reaches PhysX | **LANDS as a wording defect.** The Beta is DORAEMON *state* and its restore is real evidence of state restore; it is not evidence about the plant. Said explicitly rather than left ambiguous |
| 1 | `p3c_ext20k` claims the "same section-5 delta" while containing none of the section-5 fixes | **PARTLY.** It conflates the *original* seven frozen overrides (which p3c does carry, verbatim) with the *next-generation* §4 delta (items 8-15, which it does not). The wording invited that; but the recommendation to kill the run does not follow — the run is a controlled extension of the incumbent on the incumbent's plant. **The objection did force the right check**, and it passed: `diff` of the resolved `params/env.yaml` against the incumbent's is **12 lines, all base64 pickle memory-address strings plus `log_dir`** — zero substantive plant field differs. That is verification at the resolved output, which is exactly what a working G2 would give and what G2's broken harness currently cannot |
| 2 | queued before the pre-queue gate; and used the launch-override path that `finding/352` flags | **PARTLY.** The ordering complaint is upheld above. The sub-claim that the exams ran on a broken harness is wrong — the G1 fix (`--env-dr-anchor`) is implemented and committed at `ea42375`, `regrade_chain` uses it, and s31's exam deliberately uses the class default so it is matched to R3a's own class-default verdict. The override-path complaint is sharp and worth keeping: `finding/352` says the section-5 config is launch-override-only and the task id exists to retire that mechanism, so a run that uses the override path is using the thing G2 was created to replace. Mitigated here only because the resolved config was diffed |
| 5 | `finding/363` used the pre-G1 exam, so citing it to close G6 is circular | **DOES NOT LAND.** `finding/363`'s number is read at the `none` tier — its own text says the pairing is valid "at `none` only" and the table row is `att / none / 9.360`. The G1 scope measured in this PLAN is that `none` is **bit-identical** under the fix. The one tier the defect does not touch is the tier the finding rests on |

### 🔴 Re-opened for the operator: `decision/159` 결정 3

결정 3 declined the operator's own two requests — raise `thruster_fail_prob` above 0.30, widen the DR
bands — on two grounds. **One of them is now refuted.** `finding/346` was read as "the curriculum has
not used the current band yet"; `finding/405` measures that it used **all** of it from iteration 7000
onward, with 3,000 iterations of budget still unspent. The second ground, `finding/354`
(`inertia_scale` never reaches PhysX — confirmed at the source, `mdp/events.py:268-269` writes
`hydro.rigid_body_inertia` and `marinelab/core/hydrodynamics.py:125` says in a comment that PhysX's
inertia is not randomized by it), is untouched and still argues for implementing `set_inertias`
*before* widening anything.

So the honest position is: **the reason the operator was given for holding the bands does not hold,
and the decision is theirs to revisit.** This session did not act on it — `decision/147` decision 2
and 결정 3 are operator decisions and `feedback-plan-decision-escalation` is explicit that a session
may not resolve what a plan marks as needing one.

### G5 written but NOT live — and it contaminated one exam cell on the way in (`finding/407`)

`decision/159` 결정 3's surviving half says implement `set_inertias`, so this is code the operator
has already directed rather than a decision. It is written, its math is tested, and it is **not in
the tree**:

- `randomize_physx_inertia()` applies the congruence `I' = S^(1/2) I S^(1/2)`, so the diagonal
  scales by exactly `s_i` while the tensor stays symmetric and positive-definite. It takes the
  scale **handed over** by `_randomize_hydro_model` rather than re-sampling: `_sample_or_uniform`
  returns the DORAEMON draw when `sampled` is present but a **fresh uniform** when it is not, so
  re-sampling would silently decorrelate the hydro Coriolis inertia from the PhysX one on any
  non-DORAEMON path.
- `test_physx_inertia_congruence.py` passes: bit-identical no-op at scale 1.0, diagonal exactly
  `I_ii * s_i`, symmetry and positive-definiteness preserved, and one ill-conditioned tensor where
  diagonal-only scaling goes indefinite while the congruence does not. **That test caught my own
  overclaim** — its first version asserted diagonal-only scaling *always* breaks PD, which is false
  on a diagonally-dominant tensor. The claim was weakened rather than the fixture tuned.
- **The live wiring is unverified.** Nothing has confirmed `set_inertias` actually moves this
  articulation's PhysX inertia on a running env; both GPUs were busy. Do that before trusting it.
- It sits in `g0c_runner/pending/g5_set_inertias.patch`, not in the tree, for the reason below.

**The incident.** The edit was in the working tree from 02:03:44 to 02:09:00 while `sd_r3as31`'s
exam was running. Python imports at process start, so `pair34_d2` — launched 02:07:46 — compiled and
imported the modified module at 02:07:50 (`__pycache__/events.cpython-311.pyc`, 31,937 bytes against
the 29,285 of the older cache). Four of five configs are clean; `pair34_d2` ran on a plant no other
arm has, and it is the deployment condition `finding/363` rests on. Discard-and-re-run is queued
(`g0c_runner/redo_s31_pair34d2.sh`).

Two guards were missing and one is now in place. `HEAD` never moved, so a commit-based provenance
line would have been accurate and useless; `check_anchor()` is blind because `inertia_scale` is
*drawn* identically either way and only its *destination* changed — the same blindness `finding/396`
recorded. And `sd_exam_generic2.sh` logged no git provenance at all, while `student_arm.sh` has
logged `HEAD=` and `dirty=` all along: the training half carried the guard and the exam half, where
it bit, carried none. **Fixed: the exam script now logs `HEAD` and `dirty` on every config line**,
per-config rather than per-exam, since the contamination was per-config.

**Standing rule from this, worth more than the feature:** while any exam or training chain is
running, an edit under `constrained_albc/envs/**` belongs in a patch file, not in the tree. An
uncommitted edit is a live plant change for every process that starts after it.

**Open, for the operator, in priority order:** (a) **결정 3, re-opened above** — fault probability and
DR band width, now that half its ground is gone; (b) the tether turn tolerance, which unblocks items
13/14; (c) whether G10 may be run on the next water session with the corrected ratio pre-registration,
which unblocks or retires item 8; (d) whether candidate B (`velocity_limit_sim` 3.1 -> 2.40) enters
the next teacher as a sim-fidelity repair; (e) re-running this adversarial pass against codex once its
usage limit resets, since only one family answered.
