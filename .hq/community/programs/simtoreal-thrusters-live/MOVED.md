# Program: simtoreal-thrusters-live — MOVED (2026-08-14)

**이 프로그램의 정본은 더 이상 여기에 없다.**

정본: vault `0_Project/in_progress/albc/.omx/programs/simtoreal-thrusters-live/PLAN.md`
(`/Users/kimseungmin/ksm_Obsidian/...`, git tracked).

이전 시점 sha256 `d25b5fc92faee17419be46b818482a9907c94651a8466dcf5123a87c690d0ce8`,
1462 줄로 양쪽 일치를 확인한 뒤 옮겼다. 이전 정본은 이 디렉터리의
`PLAN.md.moved-20260814` 에 그대로 남아 있다 (읽기 전용 기록).

## 왜 옮겼나 — 두 저장소의 경계

경계는 **무엇을 바꾸는 실험인가** 다.

| 저장소 | 담는 것 | 산출물 |
|:---|:---|:---|
| vault `albc/.omx` | **로봇을 바꾸는 실험** — 캘리브레이션, 배포 상수, 펌웨어, 수조, 실해역 | 배포 상수, ROS/펌웨어 커밋 |
| marinelab `.omx` (여기) | **정책을 바꾸는 실험** — 학습, DR, distill, eval | 체크포인트 |

이 저장소의 프로그램 8개 중 실기는 이것 하나였고, 나머지 7개는 전부 학습이다.
실기 세션은 로봇 옆(Mac)에서 도는데 정본만 SSH 너머에 있었던 것이 분리 이유다.

## 경계를 넘는 항목은 어떻게 하나

실기에서 나왔지만 **학습에 반영해야 하는** 것(예: `control_delay_steps=(0,0)`,
m3 사망 fault DR 커버리지, 추진기 정적 이득 갭)은 vault 에서 발견하고 **여기 wiki 에
`status: needs-apply-before-retrain` 으로 등록만** 한다.

양쪽에 사본을 두지 말 것. vault 좌표계 노트 §11 이 이 PLAN 을 "1345 줄" 이라 적어둔 채
낡아 있었던 것이 사본 방식의 실패 사례다.

## 실기 지식 wiki

2026-08-14 이전의 실기 지식은 **이 저장소 wiki 에 그대로 있다** — 옮기지 않았다.
링크 그래프가 학습 쪽 페이지와 얽혀 있어 일부만 떼면 참조가 끊어진다.

category `sim2real` 3건:
`calibrating_a_rotation_needs_two_points…` / `esc_deadband_and_the_six_channel_pwm…` /
`open_the_policy_winds_j2_on_land…`

앞으로 생기는 **로봇을 바꾸는** 지식만 vault root 에 쓴다.
