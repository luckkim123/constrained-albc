# Evidence ledger for retrain-simtoreal-2026-09: 31 claims of the frozen PLAN re-scored against both stores (444 posts) -- 9 corrections the rewrite must carry

- id: review/306 · date: 2026-09-03 · author: session-mac
- harness: omo · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: none
- topic: reference
- confidence: high · status: none
- verified: none · keywords: ledger, evidence, retrain, cross-vendor, codex
- summary: Codex ground-2 sweep of vault (140) + marinelab (304) posts, session-judged. Frozen PLAN errors: thrust-ON bag 10-19-06 unanalyzed; no J2>pi guard exists; thruster_sign default is identity; 6-8% figure is the 5k arm not the incumbent (Beta(1,1) at 7748); thruster_util range 0.805-0.943; performance_lb 250 is not p25 (261.8); C3 non-transfer RETRACTED; DGX 5.41 not 5.56 s/iter; 1/30000 vs 0.09% are different events. Full vendor ledgers appended verbatim.

Session 2026-09-03 (Mac, Fable 5.1). The user rejected the frozen PLAN because its claims moved under questioning. Before rewriting, every load-bearing claim of that PLAN (31: C1–C16 plant/robot side, T1–T15 training side) was re-scored against BOTH stores — vault 140 posts + marinelab 304 posts, each read to its last `## Update` — by a codex `gpt-5.6-terra` ground-2 sweep, and the verdicts below are the session's own judgment on that ledger. The full vendor ledgers are appended verbatim (§A, §B) so the next session can check any line without re-running the sweep.

## Verdict: 9 corrections the rewrite must carry (numbers the frozen PLAN got wrong or unsourced)

| # | Frozen PLAN said | Record says | Source |
|:--|:--|:--|:--|
| 1 | "10 Hz best" and "all RL field runs thruster_scale = 0" | 4 of the 7 bags on 09-02 ran thrust ON (0.3); the thrust-ON staircase `10-19-06` is unanalyzed | vault `finding/137` §12 |
| 2 | Guards include "J2 > π abort" | No such guard exists (`j2_over_pi = 577, abort = 0`); only J1 has a 6π latch | vault `finding/041`, `finding/060` |
| 3 | m4/m3 exclusion is the deployed state | launch default is identity `[1,1,1,1,1,1]`; the exclusion must be passed every run | vault `finding/060`, `finding/137` §12 |
| 4 | nominal-0 dims "end at 6–8 %" (applied to the incumbent) | that is the 5k fault-DR arm; the incumbent saturated all 21 dims (Beta(1,1)) at iteration 7748 — read today from `curriculum_trajectory.json` | `decision/063` Update 08-05, `finding/124`, artifact |
| 5 | `thruster_util` at "0.82–0.93 of budget" | recorded 7-run range is 0.805–0.943 | `finding/284` |
| 6 | `performance_lb 250` "calibrated as p25 of the return distribution" | measured p25 on the adopted config is 261.8; 250 is not p25 and the paper's App A.1 rule was never run | `decision/064`, `finding/207` |
| 7 | "C3 does not transfer across teachers" (drove Phase 4 step 3) | RETRACTED — the dgx16k C3 student never trained; the claim is unmeasured, not disproven | `decision/263` Update 08-14, vault `finding/003` |
| 8 | DGX 5.56 s/iter @4096, 18.1 @16384; RTX 4070 3.3–3.6 s/iter | corpus has 5.41 @4096, 9.65 @8192, 34.73 @32768; no post carries 18.1 or the 4070 figure (README-only) | `finding/001` |
| 9 | "1/30,000 double-loss" and "0.09 % of envs with 2+ faults" used as one number | different events: 1/30,000 = two EFFECTIVELY-DEAD channels (mixer docstring); 0.09 % = any two degraded at severity ≈0.08 (Arm A) | vault `finding/137` §7(3), `decision/140` |

Also confirmed correct (kept): T1 as-run config (fault.enable true, fail_prob 0.1, health U(0,0.5), delay (0,0), privileged fault obs false, seed 30, 4096 envs); T4 fault-DR adoption at n = 1 seed per arm; T6 `(0,1)` user-approved 08-14 with the 08-15 paired-gate correction; T7 seed floor 56 % (corrected plant), R30/R31 straddle, +109 % on one pair, 4 % eval-machine term; C7 attitude authority inside DR; C8 arm envelope ±14.5° at θ2 = 150°; C15/T13 the 72D policy sees absolute yaw but no linear velocity and no depth (depth/XY takeover = a different observation interface, the obs4 +4 line of `decision/185`).

Open measurement gaps the ledger surfaced (candidates for the robot, constraint 3): vertical pitch-moment magnitude (static tilt × K, no load cell needed); obs staleness re-computed on one definition pre/post firmware (`finding/056` warns the two figures were not defined identically); control_hz with observation rate held fixed, ≥30 s per run, ≥2 runs per rate; `THR_FILTER_DT` 0.02 behavioral effect (commit itself says MAGNITUDE UNMEASURED).

Vendor note: the same ledger was also sent to the Gemini family (`agy gemini-3.1-pro-high`) for a second axis of coverage; it timed out twice (297 s ceiling, `vault:finding/139`) at effort high and medium on a 10-file scope. The two-family gate stays open for the final PLAN review with a smaller prompt.


---

## A. Plant / robot-side ledger (codex gpt-5.6-terra, ground 2, 2026-09-03, verbatim)

아래는 두 저장소의 444개 게시물을 검색하고, 인용 문서는 마지막 Update까지 반영한 Evidence Ledger입니다. `PARTLY`는 문장 일부만 성립하거나 후속 기록이 범위를 제한하는 경우입니다.

### C1. 좌표계와 IMU 보정

- **VERDICT — PARTLY.** `+x=3시, +y=12시, +z=up`, 로봇 측 `imu_yaw_offset=+102°`, pitch negation, sim 측 무보정은 확인된다. 다만 “sim 보정이 필요 없다”는 최신 HARD-GATE 기록과 충돌한다.
- **EVIDENCE**
  - `vault:finding/073 (2026-08-14)` “Frame `+x = 3 o'clock` (from the J1 zero, IMU not involved), `+y = 12`, `+z = up`, right-handed.”
  - `vault:finding/073 (2026-08-14)` “[DRY-DOCK 2026-08-12, closed] `imu_yaw_offset = +102.0` is the confirmed value for this robot.”
  - `ml:finding/154 (2026-07-05)` “SIM FACT: the sim policy's observation pipeline consumes `root_ang_vel_b` … directly -- it does NOT apply any 45-degree rotation or any axis negation.”
  - `ml:finding/154 (2026-07-05)` “the raw-level 45deg offset + pitch negation is corrected downstream in firmware. Nothing is actively broken today.”
- **CONTRADICTIONS**
  - `ml:handoff/304 (2026-09-03)` “IMU 45 deg mounting offset + pitch negation -- sim-UNCOMPENSATED. MISSING FROM THE PLAN ENTIRELY.” 가장 최신이며 item 3을 여전히 미적용 HARD-GATE로 취급한다.
  - `ml:finding/154 (2026-07-05)` “the frame correction WILL be applied to sim … Keep the `needs-apply-before-retrain` flag”는 이후 +102° 실기 교정보다 오래됐지만, `handoff/304`가 다시 살렸다.
- **GAP —** 검증된 robot-side +102° consumer transform이 item 3을 닫는지, 별도의 sim observation transform이 필요한지 명시적 결정이 없다.

### C2. m0/m3 물리 모터 식별

- **VERDICT — SUPPORTED.**
- **EVIDENCE**
  - `ml:finding/255 (2026-07-05)` “**m0 and m3 are NOT the same physical motor.** They sit at different clock positions: **m0 = 3 o'clock, m3 = 9 o'clock**”
  - `ml:finding/255 (2026-07-05)` “**m3 is DEAD, not intermittent.** `deployed_tam.json` records `m3: DEAD`.”
  - `vault:finding/077 (2026-08-14)` “The dry channel probe answered it: different propellers turn, and m3 is dead -- so sim's independent two-channel vertical model is right”
- **CONTRADICTIONS**
  - `ml:finding/255 (2026-07-05)` 본문의 “m0 and m3 are physically the SAME single motor, dual-ESC wired”는 같은 게시물의 `CORRECTION 2026-08-13`에서 철회됐다.
  - `ml:decision/253 (2026-07-03)` “수직 m0·m3 = 같은 모터 1개(실측).” 더 오래된 기록이며 2026-08-13 정정이 supersede한다.
- **GAP —** 모터 식별에는 없음. m3 수리·교체 방침은 별도 문제다.

### C3. Sim TAM과 incumbent 학습 행렬

- **VERDICT — SUPPORTED.**
- **EVIDENCE**
  - `ml:finding/255 (2026-07-05)` “the sim TAM models T4 and T5 as two INDEPENDENT heave channels -- each contributing Fz=1.0 … plus opposite-signed My=+-0.145”
  - `vault:finding/077 (2026-08-14)` “`actuators.xacro` places … T4/T5 at +-x 0.1445 m. Those coordinates reproduce … `My = +-0.145` to four decimals.”
  - `ml:decision/253 (2026-07-03)` “Horizontal TAM APPLIED in commit 3bb042b … Mz row … = 2-2 sign split … `_ESC_CHANNEL_ORDER=(4,1,3,5,2,0)`”
  - `vault:finding/077 (2026-08-14)` “`3bb042b` … changed it to `(4,1,3,5,2,0)`, and the deployed teacher trained on **2026-08-05**, after that.”
- **CONTRADICTIONS**
  - `ml:decision/253`의 초기 body에는 구 ESC 순열 `(4,0,1,5,2,3)`과 horizontal Mz all-positive가 적혀 있으나, 2026-07-14 Update가 `3bb042b` 내용으로 supersede한다.
  - 이후 기록은 sim 행렬 자체가 아니라 그것의 실기 타당성을 문제 삼는다.
- **GAP —** 재학습 manifest에는 두 vertical column의 정확한 순서와 `My` 부호를 고정해야 한다. `±0.145`와 claim의 `∓`는 열 순서 없이는 모호하다.

### C4. m0 양수 명령의 실기 반응

- **VERDICT — SUPPORTED.**
- **EVIDENCE**
  - `vault:finding/077 (2026-08-14)` “m0 = +1 … `+0.25` -> pitch -3.36 deg and `-0.25` -> pitch +1.15 deg, a clean reversal with roll unchanged”
  - `vault:finding/077 (2026-08-14)` “the operator visually confirmed the robot DESCENDING under `-0.25`”
  - `vault:finding/073 (2026-08-14)` “A positive rotation about an axis lays the robot's ‘up’ vector toward that side and the side it lays toward goes down”
- **CONTRADICTIONS —** 후속 Update까지 확인했으나 반대 측정은 발견되지 않았다.
- **GAP —** 방향·자세 반응만 측정됐고 thrust 및 pitch moment의 N/N·m 크기는 측정되지 않았다.

### C5. Vertical pitch moment 크기

- **VERDICT — UNMEASURED.** `0.145 m × 50 N`의 실기 moment 크기는 측정되지 않았다. “sim이 과대평가한다”는 방향성 판단도 최신 기록에서 불충분한 framing으로 지적됐다.
- **EVIDENCE**
  - `ml:finding/240 (2026-07-02)` “TAM roll/pitch arm + thrust curve = measurement IMPOSSIBLE without a load cell”
  - `ml:finding/240 (2026-07-02)` “The remaining half is the TAM moment-arm band, and it is blocked on a real geometric-tolerance source”
  - `ml:decision/301 (2026-09-02)` “TAM 수직 My 0.145 는 실기에서 과대평가 판정이므로 그대로 재학습 금지”
  - `ml:handoff/304 (2026-09-03)` “Plan mis-framed it as ‘My value is over-estimated’ instead of the recorded redesign”
- **CONTRADICTIONS**
  - `vault:finding/077 (2026-08-14)` “Those coordinates reproduce … `My = +-0.145` to four decimals. So the sim geometry is right”는 기하 nominal을 지지하지만 실기 moment 측정은 아니다.
  - 최신 `ml:handoff/304`는 과대평가 주장만으로는 부족하며 먼저 축을 검증하라고 한다.
- **GAP —** 실차 채널별 force/load-cell 또는 force-torque 측정이 필요하다.

### C6. decision/197 HARD-GATE

- **VERDICT — SUPERSEDED.** 원래 4개 상태를 그대로 사용할 수 없다.
- **EVIDENCE**
  - `ml:decision/197 (2026-07-14)` “HARD-GATE item 1 … was APPLIED in commit 3bb042b … Items 2-4 remain OPEN”
  - `ml:finding/255 (2026-07-05)` “What survives: m3's fault is a per-unit hardware defect, not a design difference -- so sim should model six healthy thrusters”
  - `ml:handoff/304 (2026-09-03)` “IMU 45 deg mounting offset + pitch negation -- sim-UNCOMPENSATED. MISSING FROM THE PLAN ENTIRELY.”
  - `ml:handoff/304 (2026-09-03)` “TAM moment-arm + max_thrust DR band -- max_thrust applied (0.85,1.15); moment-arm NOT applied.”
- **CONTRADICTIONS**
  - **Item 1:** horizontal 3-row TAM + ESC permutation은 `3bb042b`로 적용 완료.
  - **Item 2:** `decision/197`의 one-motor 전제가 `finding/255`의 2026-08-13 정정으로 철회됐다. 최신 `handoff/304`는 vertical coupling이 오히려 wrong-axis일 가능성을 제기하되 아직 검증 전이라고 한다.
  - **Item 3:** `finding/154`는 robot-side downstream 보정으로 “Nothing is actively broken today”라고 했지만, 최신 `handoff/304`는 sim-side HARD-GATE가 열려 있다고 한다.
  - **Item 4:** `decision/197` 당시 둘 다 미적용이었으나 이후 max-thrust `(0.85,1.15)`만 적용됐다.
- **GAP —** 현재 상태는 ① closed, ② 옛 redesign 전제 superseded·새 nominal 미결정, ③ robot-side closure와 sim-side gate 충돌, ④ max-thrust closed/moment-arm open이다.

### C7. Sim-real attitude authority

- **VERDICT — SUPPORTED**, 단 scalar plant/arm authority에 한정된다. C11의 learned actuator assignment 문제까지 없다는 뜻은 아니다.
- **EVIDENCE**
  - `vault:finding/136 (2026-09-02)` “| 순부력 | 16.62 vs 17.11 N (3%) | `buoy_volume_scale`, `buoy_body_mass_scale` | 46 | / | 복원강성 K | 7.76 vs 6.10 (21%) | `cog_offset_z`, `cob_offset_z` | 81 |”
  - `vault:finding/136 (2026-09-02)` “**셋 다 분포 안이다.** 스칼라 축에서 재학습 근거 없음.”
  - `ml:finding/020 (2026-08-24)` “Open-loop DC gain 148 deg/m (EE radius) = 32 deg/rad (theta2), spread 3 pct across n=6”
  - `ml:finding/020 (2026-08-24)` “the arm has the authority the policy needs, so the observed instability is a loop problem … and retraining cannot be justified on authority grounds.”
- **CONTRADICTIONS**
  - `ml:finding/020`의 종전 “1.2 deg total authority and 25x short of sim” 판독은 해당 글의 2026-08-25 재분석에서 철회됐다.
  - `vault:finding/136`의 초기 13.0 N/K 계산은 같은 날 17:34·17:45 정정이 supersede한다.
- **GAP —** scalar authority 재튜닝을 요구하는 측정 공백은 없다. URDF CoB/CoG 정밀 조정은 선택적 simulator-fidelity 작업이다.

### C8. Arm static attitude envelope

- **VERDICT — SUPPORTED.**
- **EVIDENCE**
  - `vault:finding/134 (2026-09-02)` “J2 를 149.9° 로 고정하고 J1 만 8방위로 돌려 각 35 s 유지. 컨트롤러 없이 순수 개루프.”
  - `vault:finding/134 (2026-09-02)` “**r = 0.121 에서 진폭 ±14.5°, roll·pitch 동일.** 즉 pitch 권한은 존재하고 roll 과 같다”
  - `vault:finding/135 (2026-09-02)` “| 150° | 0.121 | ±14.5° | ±14.5° | +0% |”
  - `vault:finding/136 (2026-09-02)` “실기의 유일한 측정 반경 r = 0.1212 에서 T1 게인 120 deg/m”
- **CONTRADICTIONS —** θ2≈150° anchor에 대한 반대 측정은 없다. 이후 정정은 다른 θ2로의 외삽값만 제한한다.
- **GAP —** roll/pitch 동등성은 θ2≈150°에서 직접 측정됐다. 다른 θ2의 envelope는 별도 측정 전에는 모델 기반이다.

### C9. m4 상태와 제외

- **VERDICT — PARTLY.** `FAULTY_ONE_DIRECTION`과 sign 미측정은 맞다. “영구 제외”는 실제 기본값과 충돌하고, sign이 구체적으로 “operator assumption”이었다는 직접 기록도 부족하다.
- **EVIDENCE**
  - `vault:finding/077 (2026-08-14)` “| m4 | 7.5 o'clock | ok on the dry probe; later found FAULTY_ONE_DIRECTION in the tank |”
  - `vault:finding/077 (2026-08-14)` “m4 cannot be measured because it is faulty. Nothing about the permutation had to change.”
  - `vault:finding/137 (2026-09-02)` “| m4 | horizontal | 7.5시 | **FAULTY_ONE_DIRECTION** |”
  - `vault:finding/137 (2026-09-02)` “`thruster_sign:=[1,1,1,0,0,1]` 은 매번 명시해야 한다.”
- **CONTRADICTIONS**
  - `vault:finding/060 (2026-08-25)` “**OFF** — launch 기본값 `[1,1,1,1,1,1]`(identity), m4 비활성 아님.”
  - `vault:finding/137 (2026-09-02)` “🔴 **`10-15-10` 은 `thruster_sign` identity 로 떴다** — m3(DEAD)·m4(간헐)가 **무장된** 채였다.”
- **GAP —** 수리 후 usable-direction sign을 직접 측정하고, 제외를 매번 넘기는 인수가 아니라 안전 기본값으로 고정해야 한다.

### C10. 로봇 손상 이력

- **VERDICT — PARTLY.** 요구된 네 계열은 모두 기록되지만 일부 원인과 fix는 제한적으로만 닫혔다.
- **EVIDENCE**
  - `vault:review/058 (2026-08-25)` “2026-08-22 arm1 파손은 1.0 A 지속. / 파단 런에서 |I_J2| 가 900 mA 를 넘게 유지된 최장 구간은 1.240 s”
  - `vault:finding/055 (2026-08-25)` “E2 런 1 시작 97 s 뒤 arm2 파단. 원인 3층 — (1) `run-joint` Ctrl-C 로 토크 OFF 417 s … (2) 학습 envelope(±30°) 밖 시작 … (3) 0.623 Hz 한계주기 40 사이클 뒤 하중 소실.”
  - `vault:finding/075 (2026-08-14; Update 2026-08-21)` “The CODE half was applied to the board on 08-17 (`6b85836`, `4239445`). / The HARDWARE half repeated anyway … replaced on 08-21”
  - `vault:finding/071 (2026-08-19; resolved 2026-08-21)` “Event 4 was **wiring in the J2 branch**. A harness replacement fixed it”
- **기록된 원인과 fix**
  - **arm1, 2026-08-22:** θ2≈90° maximum-lever 상태에서 약 1.0 A 지속. 배포 guard가 추가됐지만 1500 mA cap은 이 파손 전류보다 높아 재발 방지값으로 검증되지 않았다. training-side fix 없음.
  - **arm2, 2026-08-25:** torque-off handover → −50° 시작 → maximum-rate slew, 이후 θ2≈166° 부근 40 cycle. 시작 자세·전류 guard는 완화책이지만 learned loop/assignment는 미수정이며 arm2 수리 기록도 없다.
  - **J2 cable, 08-13/17/21:** J1 multi-turn이 J2 branch를 꼬았고 restart ratchet 및 잘못 배치된 limit가 software mechanism이었다. arbitrary-k unwrap과 J1 6π abort 적용, cable/harness 교체. full multi-turn round-trip 검증은 없음.
  - **Joint bus 네 건, 08-17:** 1–2는 master kill→relay drop으로 `guard_start.sh`에서 수정. 3은 duplicate serial drivers로 정리했으나 single-owner startup enforcement는 미구현. 4는 J2 branch wiring으로 harness 교체 후 590/590 clean 및 두 번의 zero-failure rotation run.
- **CONTRADICTIONS**
  - `vault:finding/055 (2026-08-25)` “~~‘0.623 Hz 한계주기가 arm2 를 부쉈다’~~ … arm2 의 **허용 응력·피로 한도는 미측정**이다.” 단일 원인 단정은 금지된다.
  - `vault:finding/075 (Update 2026-08-21)` “The bus is a BRANCH”가 초기 daisy-chain 설명을 정정한다.
  - `vault:finding/071`의 2026-08-21 resolution은 event 4를 servo/common trunk가 아니라 J2 cable/wiring으로 닫는다.
- **GAP —** arm1/2 구조·피로 한도, arm2 수리 기록, J2 full multi-turn restart 회귀시험, serial-port single-owner 강제가 없다.

### C11. RL field run과 T4 결과

- **VERDICT — PARTLY.** R1의 98.7%/0.9%와 learned assignment 진단은 맞다. 그러나 2026-09-02 thrust-ON R3/R4 이후 “모든 run이 thruster_scale=0”은 거짓이다.
- **EVIDENCE**
  - `vault:finding/137 (2026-09-02)` “| R1 | `fieldtest_2026-09-02-09-39-17.bag` (365.7 s) | `control_hz` 10, 캡 1200, **`thruster_scale` 0** |”
  - `vault:finding/137 (2026-09-02)` “| roll +15 | … **98.7%** … | / | pitch +15 | … **0.9%** … |”
  - `vault:finding/137 (2026-09-02)` “**명령 스팬과 측정 스팬이 모든 구간에서 1~3° 이내로 일치한다.** 팔은 시킨 대로 갔다.”
  - `vault:finding/137 (2026-09-02)` “**그래서 학습이 분업을 배웠다**: roll 은 … **팔로**, pitch 는 … **수직 스러스터로**.”
- **CONTRADICTIONS**
  - `vault:finding/137 (2026-09-02)` “| R3 | … **추력 ON** … `thruster_scale` 0.3 … | / | R4 | … 추력 ON + **`fault_reallocate=true`** |”
  - 같은 글의 7-bag inventory는 thrust ON 네 개, OFF 세 개를 기록한다.
  - `vault:finding/077 (2026-08-14)`의 “every field-test bag has `thruster_pwm` all zero”는 09-02 inventory가 supersede한다.
- **GAP —** R1 외 6개 bag, 특히 thrust-ON 반복 run과 실제 배포된 `fault.enable` 값의 정량 분석이 없다.

### C12. 배포 guard

- **VERDICT — PARTLY.** 현재 default는 `joint_current_max_ma=1500`/0.5 s, `start_att_max_deg=45`, J1 `6π` abort다. 1500은 코드상 attitude-hold 전용이 아니며 운영 지침만 비-attitude run에서 1000–1200으로 되돌리라고 한다. θ2 hard window는 제거됐다. `J2>π abort`는 존재하지 않는다.
- **EVIDENCE**
  - `vault:finding/065 (2026-08-26)` “| `joint_current_max_ma` | 900 | **1500** | … / | `start_att_max_deg` | 30 | **45** | …”
  - `vault:finding/065 (2026-08-26)` “자세 유지가 아닌 런에서는 캡을 1000~1200 으로 되돌릴 것.”
  - `vault:finding/065 (2026-08-26)` “θ2 하드 창은 `868251f` 에서 제거됨.”
  - `vault:finding/060 (2026-08-25)` “`~joint1_abort_rad=6π`, `count_rad=4π` … 6π 는 물리 케이블 한계에 대한 안전마진(3바퀴)”
- **CONTRADICTIONS**
  - `vault:review/058 (2026-08-25)`의 `start_att_max_deg=30.0`, `vault:decision/061 (2026-08-25)`의 “과전류 900 mA / 0.5 s”는 다음 날 `finding/065`가 supersede한다.
  - `vault:finding/041 (2026-08-25)` “`j2_over_pi = 577`, `j1_over=0`, `abort=0`”는 J2>π abort 주장을 직접 반박한다.
- **GAP —** 1500 mA는 arm1 파손의 1.0 A보다 높으며 safe limit로 측정되지 않았다. 30–45° 구간도 미시험이고 J2>π abort guard도 없다.

### C13. control_hz 근거

- **VERDICT — PARTLY.** 08-25 sweep은 50 Hz/35 s, 10 Hz/40 s, 100 Hz/4 s, 20 Hz/23 s 및 192 s다. 08-26 tank run에는 50 Hz/11.8 s, 10 Hz/195 s, 50 Hz/18 s가 있다. 50/50 정합 후에도 pitch oscillation band가 유지돼 mismatch는 그 진동 원인에서 제외됐다. “10 Hz best” 비교는 n=1이다.
- **EVIDENCE**
  - `ml:finding/017 (2026-08-24; verified 2026-08-25)` “Segments: 50 Hz 35 s … 10 Hz 40 s, 100 Hz 4 s, 20 Hz 23 s, 20 Hz 192 s (staircase)”
  - `vault:finding/041 (2026-08-25)` “가장 안정한 것은 **10 Hz 런**(yaw span 4.0°/40 s)이고 100 Hz 는 4 초에 발산”
  - `vault:finding/065 (2026-08-26)` “| 수명 | 11.8 s | 195 s | 18.0 s | 0 (시작 거부) |”
  - `vault:finding/066 (2026-08-26)` “**루프율을 10→50 으로 고쳤는데 pitch 진동 대역이 안 바뀌었다**”
- **CONTRADICTIONS**
  - `vault:finding/041 (2026-08-25)` “두 축이 이 데이터에서 분리되지 않는다” — observation rate와 control_hz가 함께 변했다.
  - 최신 `vault:finding/066`도 11.8/18 s의 짧은 window 때문에 절대적 증명은 아니라고 범위를 제한한다.
- **GAP —** observation rate를 고정한 동일조건 반복시험, 특히 각 rate에서 ≥30 s 복수 run이 필요하다.

### C14. Observation staleness

- **VERDICT — PARTLY / SUPERSEDED.** 1.2–4.7 step은 08-12의 IMU 20.3 Hz/joints 10 Hz 상태다. 수정 후 IMU 95.51 Hz/joints 50.12 Hz이며 평균적으로 약 1 step 이하지만, 두 수치의 산출 정의가 완전히 동일한지는 확인되지 않았다.
- **EVIDENCE**
  - `ml:finding/264 (2026-08-14)` “IMU publishes at 20.3 Hz, joint states at 10.0 Hz … up to 94 ms old (4.7 control steps) and attitude about 1.2 steps old.”
  - `vault:finding/056 (2026-08-25)` “| IMU | 20.3 Hz | **95.51 Hz** | 1.2~4.7 | **0.11~0.33** |”
  - `vault:finding/056 (2026-08-25)` “| joint_states | 10 Hz | **50.12 Hz** | (같은 축, 미분리) | **0.19~0.50** |”
  - `vault:finding/056 (2026-08-25)` “| 50 Hz (T=20ms) | … IMU … 0.274 / 0.964 | … joint … 0.223 / 1.254 |”
- **CONTRADICTIONS**
  - `ml:finding/217 (2026-08-03)`의 “attitude+gyro at most ~25 Hz … joints 10 Hz, control 50 Hz”는 firmware 이전 상태다.
  - 최신 `vault:finding/056`은 “08-12 wiki 페이지의 ‘1.2~4.7 스텝’이 정확히 같은 정의…인지 … 재확인하지 않았다”고 경고한다.
- **GAP —** raw timestamp로 양 시기를 동일 정의로 재계산해야 한다. rosserial transport/filter latency도 미측정이다.

### C15. 배포 policy observation과 제어 범위

- **VERDICT — SUPPORTED.** 배포 incumbent는 depth와 linear velocity를 policy observation/task에 넣지 않은 72D attitude-only 정책이다. roll/pitch attitude와 yaw-rate를 다루며 depth·XY position·yaw angle takeover 기록은 없다.
- **EVIDENCE**
  - `ml:decision/048 (2026-07-23)` “Observation: observation_space 72, use_bias_ema_obs true, bias_ema_alpha 0.99”
  - `ml:finding/215 (2026-08-04)` “Default task is attitude-only (roll/pitch + yaw-rate); it tracks no linear velocity”
  - `ml:decision/185 (2026-08-03, Update 반영)` “The robot carries IMU and pressure only, no DVL, so surge/sway velocity cannot be added”
  - `vault:finding/021 (2026-08-23)` “obs76 teacher는 실제로 더 낫다… **obs72 채택, obs76 미채택**”
- **CONTRADICTIONS**
  - `ml:decision/185`에는 pressure-derived `heave rate, z only`를 더한 obs4 실험안이 있으나 채택된 배포 정책이 아니다.
  - `vault:finding/041 (2026-08-25)` “깊이 0.225~0.358 m, `Target_depth` 0.5 미추종”도 field에서 depth 비제어를 확인한다.
- **GAP —** XY takeover에는 DVL 또는 estimator가 필요하다. depth observation/reward와 yaw-angle 제어 A/B는 구현·실행되지 않았다.

### C16. 추가 retrain 관련 기록

- **VERDICT — PARTLY.** C1–C15 및 지정된 training-side 주제 밖에서 다음 네 묶음이 추가로 발견됐다: robot-side thruster echo-filter dt, 조건부 ESC deadband/thrust curve, 과거 arm/actuator dynamic fix manifest, hydro DR anchoring 원칙.
- **EVIDENCE**
  - `vault:finding/063 (2026-08-26)` “D(`THR_FILTER_DT` 0.005→0.02)는 현재 `build_proprio.py:85` 에서 `0.02` 로 확인.” / “커밋 메시지 자신도 ‘MAGNITUDE UNMEASURED’라고 명시”
  - `ml:finding/281 (2026-08-14; 최종 Update 반영)` “`plant_change_batch_v2` item 3: the deadband must be re-derived from the bench curve”
  - `ml:decision/180 (2026-07-05; Updates 반영)` “Thruster first-order lag dt bug … | FIXED (step_dt at all 3 sites …)” / “arm velocity_limit_sim 6.28 -> 3.1 … | APPLIED”
  - `ml:decision/246 (2026-08-03)` “never move a hydro coefficient to either simulator's value. Widen the DR distribution by the measured uncertainty instead”
- **CONTRADICTIONS**
  - `ml:finding/282 (2026-07-01, 후속 addendum)` “KEEP OFF until bench-measured” 및 “Until then this is not a candidate for any retrain.” 초기 thrust-curve 적용 제안을 supersede한다.
  - `ml:finding/281`의 최종 2026-08-14 Update는 `enable_thrust_curve=false`인 현재에는 global blocking status를 내렸다. 단 curve를 켜는 시점의 조건부 gate는 남는다.
- **GAP —** 실제 T200 양방향 command→thrust/deadband/voltage curve, XW540-T260 step response, end-to-end observation latency, 수정된 `THR_FILTER_DT`의 행동 영향 A/B가 없다.

열지 못한 것 1/5 — 게시물이 참조한 원본 rosbag·수조 계측 CSV는 이번 mirror의 post 범위 밖이라 직접 재계산하지 못했다.  
열지 못한 것 2/5 — `3bb042b` 등 원 저장소 commit diff와 실제 배포 파일은 post의 인용·Update를 통해서만 대조했다.  
열지 못한 것 3/5 — 두 post store의 444개 파일은 검색 가능했고, 실제 인용한 파일은 EOF와 Update까지 읽었다.  
시간 제한 4/5 — 각 claim은 최신·primary 우선 최대 4개로 잘라, 같은 결론을 반복하는 낮은 우선순위 게시물은 싣지 않았다.  
시간 제한 5/5 — C16은 acceptance의 4-post 상한에 맞춰 대표적인 미포함 축만 실었으므로 “관련 post 전부의 서지목록”은 아니다.

---

## B. Training-side ledger (codex gpt-5.6-terra, ground 2, 2026-09-03, verbatim)

# EVIDENCE LEDGER — Training side

문서의 마지막 Update/Comments를 우선했습니다. `deployed_env.yaml`은 배포 실행값만 확인하며, YAML에 없는 provenance는 별도로 구분했습니다.

## T1. 배포 teacher와 실행 설정

**VERDICT — PARTLY.** checkpoint 계보·날짜·post-`3bb042b` plant와 YAML에 존재하는 설정은 지지된다. 다만 `deployed_env.yaml` 자체에는 `model_9998.pt`, plant commit, `max_iterations`, resume 원본이 없어 “각 값을 YAML로 확인”할 수는 없다.

**EVIDENCE**

- vault:finding/021 (2026-08-23) “최종 teacher 정책이 확정돼 있다. `teacher_iter_budget/trpo_iterbudget_s30_260805_012813/model_9998.pt`”
- ml:decision/063 (2026-07-20; Update 2026-08-05) “Run `trpo_iterbudget_s30_260805_012813` … resumed the shipped teacher E-int from iteration 4999 to 9998”
- ml:decision/253 (2026-07-03; Update 2026-07-14) “Horizontal TAM APPLIED in commit 3bb042b”
- vault:finding/077 (2026-08-14) “`3bb042b` … changed it to `(4,1,3,5,2,0)`, and the deployed teacher trained on **2026-08-05**”

YAML 확인:

- `deployed_env.yaml:log_dir` = `/workspace/constrained-albc/logs/rsl_rl/albc_trpo_teacher/teacher_iter_budget/trpo_iterbudget_s30_260805_012813`
- `deployed_env.yaml:seed` = `30`
- `deployed_env.yaml:scene.num_envs` = `4096`
- `deployed_env.yaml:randomization.control_delay_steps` = `(0, 0)`
- `deployed_env.yaml:fault.enable` = `true`
- `deployed_env.yaml:fault.thruster_fail_prob` = `0.1`
- `deployed_env.yaml:fault.thruster_health_range` = `(0.0, 0.5)`
- `deployed_env.yaml:use_privileged_fault_obs` = `false`
- `deployed_env.yaml:observation_space` = `72`

**CONTRADICTIONS**

- None. 단, 이전의 “배포 런에서 `fault.enable` 미확인” 기록은 `deployed_env.yaml:fault.enable=true`로 해소됐다.

**GAP**

- teacher algorithm, checkpoint 파일명, git SHA/plant commit, `max_iterations`와 resume source는 이 YAML에 없으므로 manifest/checkpoint provenance가 추가로 필요하다.

---

## T2. fault 노출률과 iteration 7748 포화

**VERDICT — SUPPORTED.** 단, `1/30,000`은 “두 개의 effectively-dead channel”이고, ml:decision/140의 `~0.09%`는 건강도가 조금이라도 저하된 `2+` 채널이므로 서로 다른 사건이다.

**EVIDENCE**

- vault:finding/137 (2026-09-02) “fault DR trained a single effectively-dead channel at ~0.5% per episode, two simultaneously at **1/30,000**”
- ml:decision/063 (2026-07-20; Update 2026-08-05) “**Saturation is real and dated: iteration 7748**, then 2250 iterations of a totally frozen box.”
- ml:finding/124 (2026-08-05) “The box reaches Beta(1,1) on all 21 dims only at **iteration 7748**”
- ml:decision/140 (2026-07-27) “per-thruster fail prob u*0.10 = 0.0077/0.0096 … 2+ simultaneous faults occurred in ~0.09% of envs.”

**CONTRADICTIONS**

- None: `~0.09%`는 모든 partial degradation을 포함하며, later vault:finding/137의 `1/30,000`은 effectively-dead 두 채널로 더 좁은 조건이다.

**GAP**

- “effectively dead”의 정확한 health cutoff와 `1/30,000` 재산식/샘플 코드 출력은 post 안에 없다.

---

## T3. nominal-0 clamp와 E-ftc1 역효과

**VERDICT — PARTLY.** 6–8%와 E-ftc1 결과는 5k fault-DR Arm A 계열에는 지지된다. 이를 10k incumbent의 “최종값”으로 일반화하면 틀리며, incumbent는 7748에서 전 차원이 Beta(1,1)에 도달했다.

**EVIDENCE**

- ml:finding/273 (2026-07-28) “Why the four nominal-0 DR dimensions all stop at 6-8% of range while the other 17 nearly saturate”
- ml:finding/273 (2026-07-28) “the four are physically unrelated … yet land inside a 1.3x band … evidence about the INITIALIZATION plus the shared budget”
- ml:finding/273 (2026-07-28; Update 2026-07-29) “raised the final DORAEMON/mean/fault_severity from 0.0771 to 0.1929 — a 2.50x endpoint”
- ml:decision/238 (2026-07-29) “reached 2.50x Arm A’s curriculum endpoint yet its policy rejects the m4-dead fault 2.9x-5.5x WORSE”

**CONTRADICTIONS**

- Later ml:decision/063 Update (2026-08-05): “Run A at 9998 | **21 of 21**” Beta(1,1). 따라서 6–8%는 incumbent의 최종 상태가 아니다.

**GAP**

- claim의 “end”가 Arm A 5k를 뜻하는지 incumbent 9998를 뜻하는지 명시가 필요하다.

---

## T4. fault DR 채택과 privileged fault obs 기각

**VERDICT — SUPPORTED.** 각 arm은 seed 하나, 즉 비교는 **n=1 seed per arm**이다.

**EVIDENCE**

- ml:decision/140 (2026-07-27) “Fault-DR ADOPTED. … cut m4-dead attitude degradation 5-12x … and removed every fault-induced termination”
- ml:decision/140 (2026-07-27) “Privileged fault obs … NOT adopted — H2.”
- ml:decision/140 (2026-07-27) “[CONFIDENCE: MEDIUM — n=1 seed per arm]”
- vault:finding/012 (2026-08-24) “anchor 1.805 / 0.282 / 1.818 / 3.472 vs Arm A 0.285 / 0.241 / 0.251 / 0.432 and Arm B 0.148 / 0.113 / 0.149 / 0.669”

**CONTRADICTIONS**

- None. 다만 soft level 개선은 1.2–2.5×뿐이라는 예외가 같은 decision/140에 명시된다.

**GAP**

- 다중 seed 재현과 fault-conditioned student 평가는 없다.

---

## T5. binding constraint와 authority starvation

**VERDICT — PARTLY.** 7/7 binding, 0.40 budget, −54% reward 및 m4 yaw ceiling 반감은 지지된다. 다만 기록된 7-run 범위는 정확히 `0.805–0.943`; `0.82–0.93`은 근사/부분집합 표현이다.

**EVIDENCE**

- ml:finding/284 (2026-07-23) “the binding ConstraintTRPO constraint is always thruster_util … 0.805 … 0.943 … 0.920 … 0.887 … 0.853 … 0.852 … 0.865”
- ml:finding/052 (2026-06-07) “only thruster_util reached its discounted budget … per-step reward -54%”
- ml:finding/141 (2026-07-25) “with m4 dead … ceiling 11.5 N.m (-50%) with per-thruster peak utilization x2.00”
- `deployed_env.yaml:constraints.terms[name=thruster_util].budget` = `0.4`

**CONTRADICTIONS**

- ml:finding/284의 정확한 끝점 `0.805/0.943`은 주장한 `0.82/0.93`보다 바깥이다.
- ml:decision/140 (2026-07-27)는 Arm B에서 `thruster_util`이 `0.798`까지 내려간 별도 fault-observed arm을 기록한다.

**GAP**

- “healthy plant”에 포함시킨 run roster를 명시해야 `0.82–0.93` 범위를 재현할 수 있다.

---

## T6. 다음 지연 범위와 실측 지연 공백

**VERDICT — SUPPORTED.**

**EVIDENCE**

- ml:finding/264 (2026-08-14; Update) “RANGE DECIDED 2026-08-14 (user-approved): (0,1) on the next from-scratch round”
- ml:finding/264 (2026-08-14) “Mean return fell to ~197 against `performance_lb` 250 … DORAEMON sat at mode -2 for the ENTIRE run”
- ml:finding/264 (2026-08-14) “att ss_error (deg) | 0.630 | 1.474 | 3.239 | 5.604”
- ml:handoff/302 (2026-09-02) “the one missing number is the real command→actuator response time (unmeasured in normal operation).”

**CONTRADICTIONS**

- ml:finding/264가 인용한 이전 “Z4 instrument does not exist”는 2026-08-14 Update에서 명시적으로 STALE 판정됐다.
- 같은 post의 최초 “DelayBuffer infrastructure … unused”도 Update에서 틀렸다고 정정됐고, 실제 knob가 action path에 연결돼 있다.

**GAP**

- `(0,1)`의 paired multi-seed feasibility gate와 실제 command→actuator 측정이 아직 없다.

---

## T7. seed floor와 machine term

**VERDICT — SUPPORTED, 단 75%는 구 plant이고 현 plant 값은 56%.**

**EVIDENCE**

- ml:decision/236 (2026-07-22; Update 2026-07-23) “the 75% figure is the OLD plant; the corrected plant measures 56.0%.”
- ml:finding/264 (2026-08-14; Update 2026-08-15) “DORAEMON/success_rate final-50 | 0.650 | 0.469 | 0.536”
- ml:decision/117 (2026-07-23) “CROSS-MACHINE, same config + same seed … +109% ss_error … One pair”
- ml:finding/183 (2026-08-09) “same checkpoint … 0.4968 -> 0.4767 -4.0% … recorded value was produced on the DGX GB10”

**CONTRADICTIONS**

- 74.8/75%를 corrected/current plant에 붙인 옛 문장은 later Update에 의해 폐기됐다.
- `+109%`와 `4%`는 각각 training-machine term과 eval-machine term이라 동일 현상의 상충 수치가 아니다.

**GAP**

- 동일 machine·동일 seed 완전 반복 run의 repeatability와 machine term의 추가 same-seed pair가 없다.

---

## T8. 처리량·iteration budget·env scaling

**VERDICT — PARTLY.** saturation clock, 10k hard 성능, 16k 무이득, 32768 속도와 11.3 GB는 지지된다. 그러나 store 기록의 DGX 기준점은 `5.41 s/iter @4096`, `9.65 @8192`, `34.73 @32768`; 주장한 `5.56/18.1`은 이번 corpus에서 찾지 못했다. RTX 4070 `3.3–3.6 s/iter`도 직접 인용 가능한 post를 찾지 못했다.

**EVIDENCE**

- ml:finding/001 (2026-07-30) “Against the two prior DGX points (5.41 s/iter @4096, 9.65 s/iter @8192)”
- ml:finding/001 (2026-07-30) “mean 34.726 s, median 34.720 s … n=190”
- ml:finding/071 (2026-08-09) “16384 … at iteration 7250, against the ~7000 the 4096-env lineage reaches.”
- ml:decision/004 (2026-08-09) “The 4096x10000 run wins or ties at hard and ood against both 16384 checkpoints”

추가 corroboration:

- ml:decision/004 (2026-08-09) “Run A’s hard 0.6599 deg”
- vault:finding/021 (2026-08-23) “baseline 1.012°”
- ml:decision/143 (2026-07-13) “4096-env … measured 11,280 MiB GPU memory”

**CONTRADICTIONS**

- DGX `4096=5.56`은 ml:finding/001의 `5.41`과 다르다.
- `16384=18.1`은 해당 scaling post의 표에 없고, 그 표는 대신 8192=`9.65`를 준다.
- “regardless of env count ≈7748”은 너무 강하다. ml:finding/071의 16k 측정값은 7250이며, 결론은 “약 7000에서 250 iter 차이”다.

**GAP**

- 주장한 RTX/DGX 숫자의 원 run timing log와 16384 정확한 wall-clock post가 없다.

---

## T9. ConstraintTRPO/IPO, 10 constraints, dormant rails, integrator clamp

**VERDICT — PARTLY.** ConstraintTRPO의 IPO barrier, 10 constraints, limit/budget, manipulability 비결속, 양쪽 unbounded accumulator는 지지된다. 그러나 joint1/cumul_yaw는 최종에는 거의 비활성이어도 학습 초기에 near-binding이었으므로 “항상 inactive”는 틀리다.

**EVIDENCE**

- ml:finding/058 (2026-07-12) “In this IPO/barrier form … barrier=-sum log(margin_k)/t”
- ml:finding/058 (2026-07-12) “joint1_pos 0.005 (+-4pi cable-wrap) … cumul_yaw 0.000”
- ml:finding/058 (2026-07-12; Update 2026-07-13) “Only TWO never came close at ANY point: rp_vel_settling … and manipulability”
- ml:finding/163 (2026-08-09) “The deployed joint-target accumulator is UNBOUNDED on the real robot exactly as it is in sim”

YAML:

- `deployed_env.yaml:constraints.terms` = 10 entries
- `...joint1_pos.params.limit_rad` = `12.566370614359172` (=4π), `budget=0.01`
- `...cumul_yaw.params.limit_rad` = `25.132741228718345` (=8π), `budget=0.01`
- `...manipulability.budget` = `0.05`

**CONTRADICTIONS**

- Later ml:finding/058 Update: “8/10 constraints were near-binding during early exploration … joint1_pos 0.05@it498, cumul_yaw 0.05@it0.”
- board의 J1 `6π`는 clamp가 아니라 driver-layer latching abort라는 vault:finding/075 기록이 있다.

**GAP**

- `deployed_env.yaml`에는 algorithm class/IPO 설정이 없어 checkpoint의 agent config가 추가로 필요하다.

---

## T10. `performance_lb=250`의 교정 근거

**VERDICT — CONTRADICTED for the p25 clause; SUPPORTED for joint retuning and lb=200 inertness.** 현재 250은 healthy distribution의 p25가 아니다. adopted bias-EMA run의 measured p25는 261.8이며, proper no-DR paper calibration은 미실시다.

**EVIDENCE**

- ml:decision/064 (2026-07-16) “Applying the original 260608 rule … gives **lb = 261.8** … Current main is lb=250”
- ml:finding/207 (2026-07-16) “This is the 260608-style recon … NOT the paper’s App A.1 rule”
- ml:decision/063 (2026-07-20) “widening the DR box requires re-tuning budget (`kl_ub x n_updates`) AND `performance_lb` together”
- ml:decision/064 (2026-07-16) “lb=200 on the bias_ema-ON config reproduces that shape (success 0.989 … no live self-pacing left).”

**CONTRADICTIONS**

- Earlier ml:decision/069 Update (2026-07-13)는 “performance_lb has no evidence of miscalibration”이라고 했지만 2026-07-16 buffer recon이 이를 더 구체적으로 갱신했다.
- p25=250 주장은 later measured p25=261.8과 직접 모순이다.

**GAP**

- paper App A.1의 “no-DR policy nominal return의 약 80%” 측정은 아직 실행되지 않았다.

---

## T11. C3 전이, shipped pack, student dispersion

**VERDICT — PARTLY; 핵심 transfer 주장은 SUPERSEDED.** dgx16k same-width student가 학습되지 않았으므로 “모든 level에서 패배”는 무효다. incumbent GRU pack과 2.5–3.1° dispersion 관찰은 지지된다.

**EVIDENCE**

- ml:decision/263 (2026-08-09; Update 2026-08-14) “That run never trained … THE HEADLINE CLAIM IS UNSUPPORTED — not disproven, unmeasured.”
- vault:finding/003 (2026-08-23) “dgx16k C3 student는 훈련된 적이 없다 (‘TRAINED NOTHING’)”
- vault:finding/021 (2026-08-23) “GRU(`pack_inc9998_gru_260810_150713` …) … model_9998 기준 export·파리티 완료”
- ml:finding/274 (2026-08-05) “every student sits at 2.5-3.1 deg dispersion”

보드 branch corroboration:

- vault:handoff/067 (2026-08-26) “보드 HEAD: `dd9cbbd` (`deploy/72d-inc9998-gru`).”

**CONTRADICTIONS**

- ml:decision/263 본문 최초 결과표는 same-width transfer failure를 주장하지만, 같은 문서의 later RETRACTION이 전부 무효화한다.
- “shipped pack”은 artifact 명칭 `pack_inc9998_gru_260810_150713`과 board branch `deploy/72d-inc9998-gru`를 구분해야 한다.

**GAP**

- 실제 dgx16k teacher로부터 C3를 distill한 유효 run과 board-side parity 실행이 없다.

---

## T12. 이전 retrain manifests 상태

**VERDICT — SUPPORTED as a status reconciliation, with later Updates controlling.**

**APPLIED — 한 줄**

- ml:decision/180 (2026-07-05; Updates 2026-07-12/23): “lag dt, velocity 3.1/soft 2.8, clip_fraction, value-optimizer encoder, DR-derived bounds”가 적용됐고, TAM horizontal rewrite도 later “actually APPLIED 2026-07-14 (commit 3bb042b)”로 정정됐다.

**STILL OPEN — 한 줄**

- ml:decision/155 (2026-07-14) “IMU 45deg mounting offset + pitch negation”과 TAM moment-arm DR가 미적용이며, ml:decision/180의 delta-scale review·control timing·constraint sweep·carry/reset 및 기타 learning A/B도 완료 근거가 없다.

**EXPLICITLY DEFERRED TO HARDWARE — 한 줄**

- ml:decision/209 (2026-07-29) “items 3 … and 4 … still blocked on the T200 bench curve and the XW540-T260 step response”; TAM/DR physical bounds와 IMU/TAM 실측도 hardware measurement 뒤로 유예됐다.

**CONTRADICTIONS**

- ml:decision/155의 2026-07-14 “TAM horizontal NOT APPLIED”는 ml:decision/180의 2026-07-23 curation에 의해 `3bb042b` 적용으로 정정됐다.
- ml:handoff/304 (2026-09-03)는 일부 status가 `resolved`로 바뀌었지만 body상 미적용이라고 경고한다.

**GAP**

- 현재 code SHA에 대해 manifest 항목별 pass/fail을 다시 산출한 단일 최신 표가 없다.

---

## T13. yaw 명령과 72D observation 범위

**VERDICT — SUPPORTED with qualification.** yaw는 rate이고, current 72D main policy에는 surge/sway linear velocity와 depth가 없다. 다만 absolute yaw는 관측하며, 기록상 확장 가능한 범위는 IMU specific force 3D와 pressure-derived heave rate 1D이다.

**EVIDENCE**

- ml:decision/300 (2026-07-08) “`_ang_cmd = [roll_att, pitch_att, yaw_rate]`”
- ml:decision/300 (2026-07-08) “the policy already observes absolute yaw (`euler[3:6]`)”
- ml:finding/240 (2026-06-14) “surge/sway velocity is not in the policy obs”
- ml:decision/185 (2026-07-30) “IMU specific force … 3D … + pressure-derived heave rate (1D)”

Vault corroboration:

- vault:finding/003 (2026-08-23) “20 proprio + 46 history + 3D bias_ema-EMA + 3 integral” = 72D.

**CONTRADICTIONS**

- “no linear velocity”를 모든 축으로 읽으면 과도하다. 별도 +4 interface는 heave-rate를 추가할 수 있고 `full_dof` variant는 linear-velocity command를 추가한다.
- raw depth 자체를 72D policy가 본다는 근거는 없다.

**GAP**

- 20D proprio와 46D history의 정확한 field-by-field layout은 vault:finding/003 자체가 SYSTEM.md 소관으로 남겼다.

---

## T14. fault sampler mechanics

**VERDICT — SUPPORTED, 단 exposure 변경은 아직 설계결정 상태다.**

**EVIDENCE**

- ml:decision/301 (2026-09-02) “`_reset_idx → _reset_physics → sample_thruster_health → set_thruster_health`”
- ml:decision/140 (2026-07-27) “sample_thruster_health draws i.i.d. Bernoulli over shape (num_envs, 6)”
- vault:finding/137 (2026-09-02) “`FaultInjectionCfg.thruster_fixed_health`가 eval 계기로 이미 존재”
- ml:handoff/303 (2026-09-02) “O-3: fault-sampler shape … needs a small design pass + tests before G0-C.”

**CONTRADICTIONS**

- ml:decision/301 summary의 fixed-health retrain delta는 같은 post Comments에서 “superseded”; fixed health는 평가 계기만 쓰고 generalized fault distribution을 강화하는 방향으로 바뀌었다.

**GAP**

- config 확률 조정값과 two-fault mass를 어떻게 배분할지, 그리고 새 sampler-shape의 테스트·구현은 아직 결정되지 않았다.

---

## T15. Catch-all — T1–T14/plant-side 목록 밖의 retrain·sim-to-real·plant 기록

**VERDICT — SUPPORTED.** 최소 다음의 미포함 항목들이 발견됐다.

**EVIDENCE / UNCOVERED ITEMS**

- ml:handoff/304 (2026-09-03) “PLAN is FROZEN and must not be queued.” — 가장 최신 retrain 상태 자체가 기존 계획을 중단시켰다.
- ml:handoff/304 (2026-09-03) “status field and body disagree. Read decision/197’s table directly” — gate query가 미적용 plant 항목 세 개를 누락한다.
- ml:finding/281 (2026-08-14) “training config’s `thrust_deadband: 0.075` is inert today and WRONG for the day it stops being inert.” — curve를 켤 때 deadband 재유도가 필요하다.
- ml:finding/173 (2026-07-05) “Leaky-integral and EMA-bias carry over the mid-episode command resample” — command-resample 상태 carry-over의 harm은 미측정이고 A/B만 설계됐다.

추가로 ml:finding/282 (2026-07-01)는 real T200의 deadband/quadratic law를 multiplicative DR가 재현할 수 없다고 기록하며, 실제 bench curve 전에는 curve를 계속 OFF로 둘 것을 later Update가 요구한다.

**CONTRADICTIONS**

- ml:decision/301의 최초 fixed-dead-plant retrain 설계는 같은 post의 2026-09-02 Comments에서 superseded됐고, ml:handoff/304가 2026-09-03 전체 계획을 STOP/FROZEN 상태로 만들었다.
- ml:handoff/304는 vertical pair가 single motor라는 과거 headline도 refuted됐다고 기록한다.

**GAP**

- `deployed_tam.json.measured_channel_map` 직접 판독과 vertical differential moment가 roll인지 pitch인지의 최종 확인 전에는 새 retrain justification을 확정할 수 없다.

열지 못한 것: posts가 참조하는 `/workspace/...` 원본 run tree, TB event, checkpoint, PLAN.md는 mirror 밖이라 직접 열지 못했다.  
열지 못한 것: board repository와 `deployed_tam.json.measured_channel_map` 실물은 제공된 workdir에 없었다.  
시간상 제한: 두 store 444개는 전수 키워드/제목 검색했지만, 무관 후보 444개 모두를 본문 단위로 재독하지는 못했다.  
찾지 못한 근거: RTX 4070 `3.3–3.6 s/iter`, DGX `5.56/18.1 s/iter`의 직접 post; corpus의 명시값은 `5.41/9.65/34.73`이었다.  
남은 최우선 확인: ml:handoff/304가 요구한 vertical TAM 축 직접 검증과 T1 algorithm/max-iteration manifest 확인.

---

## C. Adversarial check of the vertical-axis derivation (codex, ground 4, verbatim)

1. **REJECTED — 교차곱 부호 오류 주장** `[I1, I2]`  
   \(r=(+0.145,0,0)\), \(F=(0,0,F_z)\)이면 \(r\times F=(0,-0.145F_z,0)\)이다. 따라서 +x(3시)의 상향 추력은 \(-M_y\)이며 deployed col3과 정확히 일치한다.

2. **REJECTED — “−My이면 3시가 내려간다”는 주장** `[I1, I4]`  
   우수좌표계에서 \(R_y(\theta)\)는 +x 지점의 높이를 \(z'=-x\sin\theta\)로 바꾼다. 그러므로 음의 \(M_y/\theta\)는 +x, 즉 3시 쪽을 올린다. I4의 관측 부호와 일치한다.

3. **REJECTED — 3시/9시 배치가 물리적으로 Mx를 만들어야 한다는 주장** `[I1, I2]`  
   수직 추력의 위치가 ±x이면 토크축은 ±y이다. “좌우 스러스터가 roll을 만든다”는 표현은 전방축을 6시로 둔 명명법에서는 맞지만, +y를 12시로 둔 sim 좌표에서는 동일한 물리 회전이 My/pitch다.

4. **REJECTED — I4가 반대 축 배치와도 동등하게 양립한다는 주장** `[I4, I5]`  
   I4는 단순 pitch 부호만이 아니라 “3시가 상승”하고 roll은 변하지 않았다고 기록한다. I5는 +x=3시를 URDF·수평추력 방향·J1 엔코더로 독립 고정한다. 따라서 +x=9시 또는 Mx 회전이라는 해석은 이 입력들과 충돌한다.

5. **CONFIRMED-DEFECT — config.py와 deployed TAM 사이의 action-column 대응이 제시되지 않았다** `[I2, I3, I6]`  
   I6에서는 vertical이 config cols 4·5인데 I2에서는 deployed cols 0·3이다. I3은 I2와 measured map으로 계산된 순열일 뿐, **policy/config action 4·5 → deployed action 0·3** 변환을 독립적으로 증명하지 않는다. 따라서 축 자체는 My여도, finding/137의 policy-action 해석까지 곧바로 확정할 수 없다.

6. **REJECTED — 위 열 순열이 m0의 My를 Mx로 바꿀 수 있다는 주장** `[I2, I3, I4]`  
   I3에 따르면 fw m0은 deployed col3을 받고, 그 열은 \(F_z=1,\ M_y=-0.145,\ M_x=0\)이다. 단순 열 순열은 행을 바꾸지 않으므로 My를 Mx로 만들 수 없다. 실제 m0 단독 시험도 roll 변화 없이 해당 My 방향을 보였다.

7. **POSSIBLE — T4의 “pitch step”이 TAM의 My 명령과 동일 축이었다는 연결고리가 불완전하다** `[I5, I6]`  
   I6은 attitude가 `rotate_imu`를 통해 읽혔다고만 한다. I5는 센서 출력의 pitch 변환을 설명하지만, T4 명령 생성기/controller의 pitch 채널이 동일한 policy-frame My로 들어간다는 코드 경로는 제공하지 않는다. 따라서 T4의 0.9% 결과만으로 vertical-action 학습 진단을 닫을 수 없다.

8. **CONFIRMED-DEFECT — “남은 문제는 오직 moment magnitude뿐”은 과도한 결론이다** `[I1, I3, I6]`  
   m3가 DEAD이고, config↔deployed action 순열 및 T4 command-frame 연결이 아직 입증되지 않았다. 레버암/추력 크기 외에도 end-to-end action routing과 제어축 대응이 열린 상태다.

9. **POSSIBLE — 요구된 cross-vendor 검증이 이 입력만으로는 충족되지 않는다** `[I2, I5]`  
   행렬 재현 근거는 `actuators.xacro`이고 프레임 근거도 같은 vault/robot 기록이다. 독립 CAD·제조사 배선도·외부 계측처럼 별도 provenance의 자료는 주어지지 않았다.

최종 판정: **NOT DECIDABLE FROM THESE INPUTS.**

handoff/304의 핵심 물리 주장, 즉 “3시/9시 vertical pair이므로 반드시 Mx/roll이어야 한다”는 것은 **반박된다**. D1–D3의 축과 부호는 맞다. 그러나 D4 전체—특히 finding/137의 policy-level D-1 진단이 확정되고 magnitude만 남았다는 부분—는 열 순열과 command-frame 연결이 빠져 있어 성립이 확정되지 않는다.

판정을 **YES**로 바꿀 단일 사실은: **각 config/policy action index를 하나씩 주입해 실제 firmware channel·물리 스러스터·고정된 3D body angular acceleration까지 기록한 end-to-end primary-source 시험 결과**다. 여기서 actions 4·5가 3시/9시 verticals로 전달되고 ±My만 만든다면 D4가 닫힌다.
## Comments
