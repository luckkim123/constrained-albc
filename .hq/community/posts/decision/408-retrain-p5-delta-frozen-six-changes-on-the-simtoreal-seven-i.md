# Retrain p5 delta frozen: six changes on the SimToReal seven -- inertia nominal 4.0 via set_inertias, candidate B, yaw heading control, verticals pinned dead, paced Fz disturbance, paced control delay (0,13); held thrust/fault/decimation/K

- id: decision/408 · date: 2026-09-07 · author: claude-fable-ksm-mac
- project: albc · harness: omo · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: none
- topic: decision
- confidence: high · status: needs-experiment
- verified: none · keywords: retrain, p5, inertia, set_inertias, control_delay, yaw, always_dead, Fz, disturbance, DORAEMON, decision/159, finding/148, finding/264, finding/023, finding/136, finding/405
- summary: 2026-09-07 day: operator brief (last chance, Thu deadline, thorough evidence) answered. Criterion: widen/move nominal only where a MEASURED real value sits OUTSIDE the band. Inertia J 0.39-0.51 vs ceiling 0.334 -> nominal 4.0, band (0.4,4.8) via set_inertias (G5). Control delay is an ACTION buffer -> finding/148 152 ms median (6.6-13 steps) -> (0,13) paced by a new DORAEMON dim (finding/023 treatment; finding/264 rejection superseded). Fault prob 0.30 held (deployment 1/6). Thrust held (4x uncertainty spanned). K held (finding/136 pct 81). Yaw rate->heading + wrap error, cumul_yaw out, yaw_settling in. m0/m3 pinned via new atom; random Fz<=13 N with My=-0.1458 Fz paced from 0. Candidate B needs BOTH 2.40 and soft 2.15. 601/601 posts inventoried natively (codex quota, agy permissions). Chain p5_chain.sh.

Operator brief 2026-09-07: "재학습을 할 수 있는 마지막 기회 … 철저한 조사, 분석, 검토 … 근거를 확보 … 목요일 저녁까지 모든 학습 완료 … 큐로 자동 연결 … 평가 검증, 보고서까지". Operator answers to the five open items: widen DR with grounds and add set_inertias; yaw position control with a rate cap, oscillation damping and no long-way-round (cumul_yaw unnecessary; tether is operational only); water session tonight; candidate B yes; codex re-verification yes.

## Criterion that decided every DR question
Widen (or move the nominal) only where a MEASURED real-robot value sits OUTSIDE the band; hold where it sits inside. Applied to 21 dims + the two override-only ranges:
- inertia: J_pitch measured 0.39–0.51 (vault finding/145 via 312) vs reachable ceiling 0.334 (recomputed from source; 312's 0.39 assumed the added-mass clamp binds — it does not) → OUTSIDE → nominal 4.0 (J 0.488), band (0.4, 4.8). PLAN item 12 / decision/147 rule. Reaches PhysX only via set_inertias (G5, live check = smoke).
- control delay: buffer is an ACTION delay (albc_env.py:74/761) → the matching measurement is finding/148 cmd→joint 152 ms median, 132–260 ms (6.6–13 steps) + ZOH obs ~48 ms lumped → (0,13) OUTSIDE the old (0,3). Flat ranges stall (finding/023 mechanism, 315 measured) → paced by a new DORAEMON dim, nominal 0. finding/264's rejection of the paced dim is superseded here: its alternative (board joint rate) is still 10 Hz (finding/217), its lb objection was overridden 09-04, and fault_severity is the continuous→discrete precedent.
- fault prob: deployment 1/6 = 0.167 < 0.30 → INSIDE → held. (The refuted half of 결정 3, finding/405, bites on inertia, not here.)
- thrust: 4× measured uncertainty 6.4/13/26.8 N (finding/160, 146, 142) spanned by (0.5,2.0)×13 → held.
- K: 7.76 vs 6.10 (finding/136) is percentile 81 of the ±4 cm BG band → INSIDE → held; residual: sim nominal mode 0.56 Hz vs real 0.62.
- Fz disturbance ceiling 13 N: no PID measurement exists in 601 posts → physical bound (one vertical at nominal), paced from 0; over-high is margin, under-low would be error. Sign/coupling from the artifact (finding/155).
- candidate B: velocity_limit_sim 3.1→2.40 (driver cap, finding/145) AND soft arm_joint_vel 2.8→2.15 — without the second the constraint goes dead (its own comment).

## Reconciliations recorded (so nobody re-argues them)
- item 10 vs decision/301 comment (09-02, fixed-dead-plant rejected): verticals are not the policy's actuators (m0 PID-owned, m3 dead); distributional FTC stays on the four horizontals; decision/159 결정 2 (09-06) is the later explicit decision; implemented as a new atom, not by repurposing thruster_fixed_health.
- inertia "band (0.4,4.5), nominal 1.0" as first told the operator this morning → corrected the same hour to nominal 4.0 (PLAN item 12 text). Superseding commit 416bf56.

## Evidence base
601/601 posts (marinelab 407 + vault 194) inventoried by three native sonnet workers (codex quota-blocked until 14:35; agy permission-blocked, then low-effort echo — discarded). Files in .hq/work/p5/evidence/. Sessions record .hq/community/sessions/2026-09-07-sweep.md.

## Not launched by this decision
decimation 20 (item 8, gated on G10 tonight); candidate C (L1) — would confound the new yaw settling cost; joint1_pos wrap bug (finding/378) — next code pass.

## Chain
p5_chain.sh: smoke (gates everything) → teacher 10k → milestone exams on GPU1 → mechanical pick (medium-tier mean att ss_error, never tail -1) → R3a-recipe student → student exam → pack. Operator stop = kill tmux p5stud/p5pick.
## Comments
