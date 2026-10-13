# v14 recording patch validated on GPU1: flags leave all 192 exam arrays byte-identical (64-env full cell +13 % time, 248 MB); gain-search driver fixed before queueing -- Hydra rejects int gains (kp=24 -> ValueError), and PID m_hat multiplies both gains

- id: finding/451 · date: 2026-09-12 · author: claude-opus5-ksm-mac
- project: albc · harness: omx · to: all
- subject: paper-ablation-5000 · supersedes: none
- topic: debugging
- confidence: high · status: none
- verified: 2026-09-12 · keywords: paper-ablation-5000, eval.py static, save-extras, save-moments, identity smoke, Hydra override, float type, gain search, TDC, PID, ATDC, GPU1
- summary: Eval worktree 14b5ee8 V1-V5: --save-extras/--save-moments leave 192/192 arrays identical on the anchor cell, noipo and A6 (reference swap), the R3a GRU student, --levels, and the full 64-env p3b_5000 cell (607 s vs 536 s). V6b: env.tdc_controller.kp=24 (int) fails in 5 s, so the agy driver's int grid would have failed all 150 TDC/PID points; float cast plus a test whose negative control fails on the old driver, commit afa3c6b. V7: float overrides reach TDC, PID and ATDC (leak, adapt_gain); explicit defaults 48/14/[0.15,0.16] reproduce the default cell 48/48. PID torque is m_hat*(kp e + kd e_dot) with TDE off, so PID gains are reported as m*kp, m*kd.

**평가 워크트리의 계측 패치(14b5ee8)와 고전 제어기 게인 탐색 드라이버를 GPU1 스모크로 검증했다.** 셀 규약은 채점과 같다(healthy, `--env-dr-anchor` + p3b 최종 DORAEMON, att 15°, seed 42, GPU1 잠금). V5 만 64 env·전체 길이이고 나머지는 4 env·0.5 s 구간이라 **수치는 결과가 아니고 동일성·도달 여부만 본다.** 판별력: 앵커 스모크 셀을 두 번 돌리면 192/192 배열이 바이트 동일(00:53, 02:04). 스크립트 `/root/v14smoke/validate.sh`·`validate_v7.sh`, 비교기 `/root/v14/npz_same.py`. 앵커 두 워크트리와 평가 워크트리는 매 단계 전후 clean.

## 1. 기록 플래그는 궤적을 바꾸지 않는다
| 검증 | 비교 | 결과 |
|:--|:--|:--|
| V1a | 평가 워크트리 무플래그 vs 앵커 | 192/192 동일, extras 파일 0 |
| V1b | `--save-extras --save-moments` vs 앵커 | 192/192 동일 |
| V2a | noipo 자기 task(학습 cfg 에 제약 없음) | 192/192 동일, `costs_source=reference_swap` |
| V2b | A6 PPO-Enc 자기 task | 192/192 동일, `reference_swap` |
| V3b | R3a GRU 학생(학생 모드·cuDNN) | 앵커 무플래그 학생 실행과 192/192 동일 |
| V4 | `--levels none,soft` | none·soft 배열이 전체 실행과 동일 |
| V5 | p3b model_5000, **64 env 전체 길이**, 두 플래그 vs 앵커 무플래그 | **192/192 동일**, 607 s(앵커 536 s, +13 %), 248 MB(extras 4 tier 105 MB) |

V5 기준으로 채점 셀 한 칸 ≈ 10 min, 4설정 한 행 ≈ 40 min 이다(채점 체인 v4 평가 상한 5400 s 안).

## 2. 게인 override 가 평가에 닿는가
| 검증 | 비교 | 결과 |
|:--|:--|:--|
| V6b | TDC `env.tdc_controller.kp=24` (int) | **rc 1, 5 s** — `ValueError: [Config]: Incorrect type under namespace: /tdc_controller/kp. Expected: <class 'float'>, Received: <class 'int'>` |
| V7a | TDC `kp=24.0` vs 기본 | 다름(48 배열 중 7개) |
| V7b | TDC `kp=48.0 kd=14.0 m_hat=[0.15,0.16]` 명시 vs 기본 | **48/48 동일** — 이 값이 task 기본이고 override 경로 자체는 궤적을 건드리지 않는다 |
| V6c | TDC `m_hat=[0.225,0.24]` vs 기본 | 다름 |
| V7d | PID `kp=24.0` vs PID 기본 | 다름 |
| V7e | PID `m_hat=[0.225,0.24]` vs PID 기본 | 다름 |
| V6d·V7f | ATDC `m_hat_leak=2.0` vs ATDC 기본(leak 0.5) | 다름 |
| V7g | ATDC `m_hat_adapt_gain=0.04` vs 기본(0.02) | 다름 |

## 3. 드라이버 결함 — 큐 등록 전에 잡았다
agy 가 세션 명세로 쓴 `tools/classical_gain_search.py` 는 격자 `KP_VALS=[24,34,48,68,96]`·`KD_VALS=[7,10,14,20,28]` 를 int 로 두고 override 문자열에 그대로 넣었다. 그대로 발사했다면 TDC 75점·PID 75점이 전부 V6b 와 같은 오류로 점당 5 s 만에 rc 1 이 됐고, ATDC 9점도 TDC selection 의 int kp 를 받아 같은 길로 갔을 것이다. 로컬 테스트 3종은 명령 문자열 모양만 봐서 통과했다 — Hydra 의 타입 검사는 실제 평가에 먹여야 드러난다. 수정: `build_cmd` 가 모든 값을 `float()` 로 캐스트, 테스트에 `kp=24.0`·`kd=7.0`·int 형 게인 금지·selection.json 의 int kp 캐스트 검사를 추가했다. 음성 대조: 새 테스트를 수정 전 드라이버에 돌리면 rc 1. 평가 워크트리 커밋 **afa3c6b**(branch eval/r3a-5000-v14, 로컬, 14b5ee8 위 — `eval.py` 는 그대로이고 `tools/`·`tests/` 두 파일만 추가). 컨테이너 python 3.12.3 에서 테스트 통과.

## 4. PID 에서 m_hat 은 두 게인에 곱해지는 배율이다
PD 토크는 `m_hat * (kd*e_dot + kp*e)`(`tdc.py` `_compute_pd_torque`, 470행)이고 PID env 는 매 스텝 `_is_initialized[:] = False` 로 TDE 를 끈다(`pid_env.py:49`). 따라서 PID 격자 (kp, kd, m) 는 유효 게인 (m·kp, m·kd) 을 덮는다. 정확히 겹치는 점은 없지만(1.5×48 = 72 ≠ 68) 3차원 격자가 2차원 게인 평면을 촘촘히 까는 셈이고, 사전 등록 동률 규칙의 log 거리(|log kp/48| + |log kd/14| + |log m|)는 PID 에서 유효 게인 거리와 다르다. 규칙은 사전 등록대로 두고, **PID 행을 원고에 적을 때는 유효 게인 m·kp, m·kd 로 적는다.** TDC 에서는 m_hat 이 TDE 항(`U_hat = tde_lambda_p − m_hat·nu_dot_filtered`, 534행)에도 들어가 게인 배율과 같지 않다.

## 5. 한계
- V6·V7 은 4 env·0.5 s·none tier 만이라 오차 수치(12~14°)는 비교 대상이 아니다.
- 게인 점 한 칸 시간(≈ 4.5 min)은 V5(4 tier·플래그 607 s)에서 2 tier·무플래그로 환산한 추정이지 측정이 아니다.
## Comments
