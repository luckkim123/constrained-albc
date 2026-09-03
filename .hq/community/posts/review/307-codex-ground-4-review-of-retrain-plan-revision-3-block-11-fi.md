# Codex ground-4 review of retrain PLAN revision 3: BLOCK, 11 findings -- 8 confirmed and folded into revision 3.1 (R-1 identifiability, pair arithmetic, severity-integrated exposure, explicit gate thresholds, launch manifest), 2 rejected, 1 partly

- id: review/307 · date: 2026-09-03 · author: session-mac
- harness: omo · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: none
- topic: reference
- confidence: high · status: none
- verified: none · keywords: review, cross-vendor, codex, ground-4, retrain, plan
- summary: Different-family adversarial review of PLAN v3. Most consequential: R-1 static tilt cannot separate lever from thrust coefficient and must not auto-edit the plant (now decision 9); P(m3,m4 dead) was 0.20/0.41 not 0.41/0.66 %; exposure must integrate severity U(0,1) (P>=2 dead 1.1-4.1 %); G0 thresholds were ungrounded; commit not pinned. agy failed 3x so the two-family gate is NOT met. Reviewer output verbatim inside.

Ground-4 adversarial review of PLAN revision 3 by codex (gpt-5.6-terra, effort high, 2026-09-03), a different model family from the Claude session that authored it. Verdict: **BLOCK**, 11 findings. Session judgment and disposition (all folded into PLAN revision 3.1, committed the same day):

| # | Finding | Disposition |
|:--|:--|:--|
| 1 | R-1 static-tilt protocol does not control heave, contact, other actuators, drift; cannot separate lever from thrust coefficient; auto-editing the plant from it is unsafe | CONFIRMED — R-1 rewritten as a differential identification (free-floating, controllers off, arm fixed, dwell + steady-state + depth-abort criteria) whose output feeds a NEW user decision `vertical-moment` (PLAN §10 item 9); no automatic plant change |
| 2 | P(exactly m3,m4 dead) wrong for q = 0.05 / 0.075 (0.20 % / 0.41 %, not 0.41 / 0.66) | CONFIRMED — corrected |
| 3 | Severity at saturation is U(0,1), so exposure must be severity-integrated (P(>=2 dead) 1.13 / 2.42 / 4.09 %, ~2 / 4 / 7 per iteration) | CONFIRMED — corrected; exposure target restated on the integrated numbers |
| 4 | D-1 "thrusters cannot restore pitch" is untested while G0-H is pending | CONFIRMED — softened to "untested; pitch is the arm's job in the deployed configuration" |
| 5 | D-4 "plant needs no retune" collides with the open vertical moment | POSSIBLE — D-4 scoped to the arm-and-buoyancy plant |
| 6 | G0-A/B/C thresholds (80 %, 50 %, 13.4 points) ungrounded; 50-80 % band unhandled; G0-B has no benefit criterion | CONFIRMED — thresholds restated as pre-registered choices with an inconclusive band; G0-B given a 2x / 1.3x criterion; G0-C's cross-seed 13.4 replaced by a same-seed 5 % trajectory criterion |
| 7 | R-1-driven nominal change and S1c band not in the user decision list; G0-C ordering before fault-config | CONFIRMED — decision 9 added; G0-C explicitly waits for fault-config and seeds |
| 8 | "held byte-identical" vs current HEAD: needs pinned commit, config diff, dirty-tree, hashes | CONFIRMED — G0-J launch manifest added |
| 9 | GRU recipe and Phase 4 criteria lack sample sizes / floors / tie rule | POSSIBLE — Phase 4 given 64 envs x standard set, per-env pairing, 0.10 deg / 15-env floors, tie -> robot; GRU recipe kept as the shipped recipe, not as validated |
| 10 | Hidden hard constraint / special-cased fault pattern | REJECTED by the reviewer itself — none found |
| 11 | Missing: integrated exposure target, eval N/CI, commit manifest, valid R-1, tank pass/abort per thruster_scale step, GPU-hour budget | CONFIRMED except (e), which lives in the vault PLAN (T10 / section 3c) and is pointed to |

The Gemini family (agy) could not be run on this revision (three timeouts / flag mismatch on 2026-09-03), so the two-family gate is NOT met; this review is one family. Full reviewer output follows verbatim.

---

1. **CONFIRMED-DEFECT — §5/§7 R-1:** 가장 중대한 결함은 부정확한 R-1이 측정 결과에 따라 최종 학습 plant를 자동 변경한다는 점이다. `M=Kθ`는 동일한 arm/질량배치에서 자유 정적평형이고 외력·외부모멘트 및 다른 actuator 출력이 0일 때만 유효하다. 단일 수직추진기는 heave와 pitch를 동시에 만들며, free-floating 상태에서는 깊이 이동·유체항력·드리프트가 생긴다. wall push나 “operator holds”는 미지의 반력과 모멘트를 추가하므로 측정을 오히려 무효화한다. deadband, thrust curve, 실제 최대추력, mixer scaling까지 모두 `0.145 m`와 혼입된다. 현재 protocol은 arm 자세, attitude controller 상태, 다른 actuator 명령, drift 허용치, 접촉/테더 하중, steady-state 판정을 통제하지 않는다. 이 결과로 moment arm을 고치면 원인이 추력계수여도 기하를 왜곡한다.

2. **CONFIRMED-DEFECT — §5 노출 산술:** 고정된 `q`와 6개 i.i.d. 채널에서 정확한 값은 다음과 같다.

| q | P(≥1 dead) | P(≥2 dead) | P(exactly m3,m4 dead) |
|---:|---:|---:|---:|
| 0.05 | 26.4908% | 3.2774% | **0.2036%** |
| 0.075 | 37.3602% | 6.8868% | **0.4118%** |
| 0.10 | 46.8559% | 11.4265% | 0.6561% |

첫 두 pair 값 0.41%/0.66%가 틀렸다. 공식 `q²(1−q)^4` 자체는 맞다.

3. **CONFIRMED-DEFECT — §2/§5:** `4096×64/1500=174.763`, 따라서 “≈175 resets/iteration”은 모든 episode가 1500 step이고 정상상태 평균이라는 조건에서 맞다. 조기 termination이 있으면 실제 reset 수는 증가한다. 고정-q double-loss 기대치는 각각 5.73/12.04/19.97회로 “6–20”도 반올림상 맞다. 그러나 saturation이 `Beta(1,1)`—즉 severity가 균등분포—라면 severity=1 값을 매 reset에 적용할 수 없다. 공유 severity를 적분하면 P(≥2)는 약 1.131%/2.418%/4.086%, 즉 1.98/4.23/7.14회/iteration이다. 계획의 “once curriculum saturates 6–20”은 잘못된 해석이다.

4. **CONFIRMED-DEFECT — §2 D-1/§6 G0-H:** D-1은 “thrusters cannot restore pitch”라고 확정하지만, posts와 G0-H는 thrust-ON bag이 미분석이라 이 명제가 아직 시험 대상이라고 한다. Rank-1은 pitch 불가능을 뜻하지 않고 heave와의 결합을 뜻한다. 진단은 “복원 여부 미확정”으로 낮춰야 한다.

5. **POSSIBLE — §2 D-4:** “attitude plant needs no retune”은 vertical effective moment가 미측정이고 ≥20% 수정 가능하다는 §3/§5와 양립하기 어렵다. 인용된 buoyancy, stiffness, arm envelope는 vertical-thruster calibration까지 닫지 못한다.

6. **CONFIRMED-DEFECT — §6 G0-A/B/C:** 통과 기준 80%, 50%, 13.4점은 근거가 없다. 특히 서로 다른 seed의 최종 격차를 iteration-500 intervention 허용손실로 쓰는 것은 통계적·인과적 근거가 아니다. 50–80%의 G0-A 결과 처리도 비어 있고, G0-B는 “재현”만 요구해 `(0,1)`의 편익을 결정하지 못한다.

7. **CONFIRMED-DEFECT — §5/§8/§10:** R-1 결과에 따른 nominal 수정과 S1c DR band의 폭·분포·채택 기준이 사용자 결정 목록에 없다. 이는 명시되지 않은 plant knob 변경이다. `fault-config` 결정 전 G0-C 구현/launch가 서술된 순서도 고쳐야 한다.

8. **CONFIRMED-DEFECT — §4/§5/§9:** “§5 delta only/모든 다른 knob 유지”와 incumbent commit 대신 current HEAD 사용은 충돌한다. ancestor 확인만으로 dormant 여부가 보장되지 않는다. 정확한 commit, config diff, dirty-tree 상태, artifact hashes를 launch guard로 고정해야 한다.

9. **POSSIBLE — §9:** GRU 128/head 64 및 distillation hyperparameters의 근거로 제시된 자료는 단지 종전의 “transfer failure”를 철회할 뿐, 이 recipe의 채택을 지지하지 않는다. Phase-4의 `2×`, “paired floor”, “no collapse” 역시 episode 수, 신뢰구간, aggregate rule이 없어 선택 규칙으로 실행 불가능하다.

10. **REJECTED — §5–§9 사용자 hard-constraint 위반 주장:** training fault는 균등 채널 분포이며 real pair는 eval에만 쓰인다. unchanged IPO constraints는 사용자의 후속 지시에 의해 명시적으로 유지된다. iteration abort는 학습 shaping이 아니고 deployment guards는 파손 방지용이다. 따라서 숨은 clamp나 m3/m4 특혜는 발견되지 않았다.

11. **CONFIRMED-DEFECT — §9 및 전체:** 빠진 필수 항목은 (a) severity를 적분한 실제 exposure 목표, (b) eval episode 수·CI·동률/불일치 처리, (c) 고정 commit/config manifest, (d) 유효한 vertical-moment 식별 protocol, (e) 각 thruster-scale 단계의 tank pass/abort/recovery 기준, (f) G0/optional screening/final을 합친 총 GPU-hour 예산이다.

**Verdict: BLOCK.** R-1이 식별할 수 없는 값을 이용해 최종 plant를 자동 수정하는 것이 최우선 차단 사유다. 그 protocol, severity-integrated exposure, G0-C/Phase-4 기준, launch commit을 고정하기 전에는 10k retrain이나 R-1 tank session을 승인하면 안 된다.
## Comments
