# v14 B1-B5 code facts, and training-end J_Ck / adaptive threshold / Lagrangian lambda recovered from existing TB tags: in the R3a teacher lineage the IPO adaptive threshold engaged only in the first few percent of iterations and never after it 2050

- id: finding/449 · date: 2026-09-12 · author: claude-opus5-ksm-mac
- project: albc · harness: omx · to: all
- subject: paper-ablation-5000 · supersedes: none
- topic: technique
- confidence: high · status: none
- verified: 2026-09-12 · keywords: v14, A1, B1, B2, B3, B4, B5, F-2, F-8, F-11, F-18, F-22, IPO, adaptive threshold, barrier, J_Ck, Lagrangian, tensorboard, p3b
- summary: B1 IPO-off arms get no cost penalty (fixed k_tau/k_thr/k_s/k_bias only); B2 Table II values are D_k, d_k = 100 D_k; B3 alpha = barrier_alpha 0.05; B4 46D = 10x3 + 8x2; B5 F_bu 26.2 N is gross buoyancy of a separate link. TB Constraint/viol = J-d and margin = d^i-J give J, d^i and activity exactly every iteration; N1 lambda replays from viol. p3b: active in <=4 percent of its 0-2092 iterations (only constraints whose J/d crossed 1-alpha), 0 of 10 constraints ever active over 2050-9999 (max J/d 0.91).

**v14 AC 요청 B1~B5 의 코드 사실과, A1 중 "학습 종료 시점 J_Ck·적응 threshold" 를 기존 TB 로그에서 새 계산 없이 읽는 방법.** 줄번호는 앵커 워크트리 `/workspace/constrained-albc-r3a`(anchor/r3a-5000 @ 3791441) 기준 — 비교군 10런과 같은 코드.

## B1~B5 (코드 판독)
| # | 답 | 근거 |
|:--|:--|:--|
| B1 IPO 끈 arm 보상에 제약 비용이 들어가나 | **안 들어간다.** 비용은 `extras["costs"]` 로만 나가고 보상은 reward manager + 종료 벌점. noipo·noboth·A6(PPO-Enc) 은 `constraints.terms=[]` 라 비용을 계산조차 안 한다. PPO arm 은 계산하지만 PPO 가 안 읽는다. 단 모든 arm 보상에 고정 벌점 k_tau −0.01, k_thr −0.35, k_s −0.1, k_bias −2.0 이 있다 | `albc_env.py:1400-1412`, `config_noconstraint.py:29`, `config_simtoreal.py:155` |
| B2 Table II "Threshold d_k" 0.01–0.40 | 그 값은 스텝 예산 **D_k** 다. 알고리즘이 `d_k = D_k/(1−γ_c)`, γ_c 0.99 → d_k = 100·D_k | `constraint_trpo.py:147-150`, 러너 auto-sync `constraint_encoder_runner.py:48-54` |
| B3 적응 threshold α | `d_k^i = max(d_k, J_Ck + α·d_k)`, **α = barrier_alpha 0.05**(알고리즘 기본 0.02 를 cfg 가 덮음). log-barrier t = 100 은 별도 | `constraint_trpo.py:320-322`, `rsl_rl_ppo_cfg.py:228` |
| B4 교사 history 46D | 추종 특징 10(관절 4 + 몸체 6) × 3 스텝 + 행동 8 × 2 스텝 = 30 + 16, 제어 3 스텝마다 기록 → 과거 0.18 s | `config.py:518-526`, `albc_env.py:1220-1223` |
| B5 부력체 질량·부력 | F_bu 26.2 N 은 부력체 **총부력**(무게 9.1 N, 순 +17.1 N). 부력체는 별도 강체 링크(m 0.93 kg)라 플랜트의 ROV 몸체 관성에는 안 들어간다. `albc.py:124` 주석 "main 88.1" 은 옛 부피 기준으로 낡음 | marinelab `albc.py:104-113,124` @ 8cc84a5, finding/443 |

## A1 학습 측: TB 에 J_Ck 태그는 없지만 대수로 복원된다
- 러너가 기록하는 것: `Constraint/viol/<k>` = J_Ck − d_k, `Constraint/margin/<k>` = d_k^i − J_Ck, `Constraint/barrier_penalty`(`constraint_encoder_runner.py:341-345`; 값은 `constraint_trpo.py:456-463`). J_Ck = 배치 평균 GAE 비용 리턴(≥0 클램프). 러너 docstring 은 cost_return·d_k 도 기록한다고 적었지만 코드는 안 한다.
- 따라서 **J_Ck = viol + d_k, d_k^i = margin + J_Ck, 적응 활성(d_k^i > d_k) ⇔ viol + margin > 0 ⇔ J_Ck > (1−α)·d_k.** 매 iteration 기록된다(p3b r2050: 7950 점 = 2050..9999).
- N1 Lagrangian 의 λ_k 는 TB 에도 체크포인트에도 없다(`_last_lambdas`, `_nu` 는 일반 텐서). 그러나 쌍대 갱신이 `nu += lr·(J_Ck − d_k)`, `nu ≥ −20`, `λ = softplus(nu).clamp(max)`(`constraint_lagrangian.py:93,113-116`)이고 그 입력이 기록된 viol 과 같은 값이라, **λ 궤적은 TB viol 을 재생해 복원된다** — 큐에 오른 N1 설정을 바꿀 필요가 없다.
- 판독기: `/root/v14/a1_train_costs.py <run_dir> [--window N] [--json]` (Isaac python, tensorboard 만 사용). 체인 arm 이 끝나면 각 run dir 에 돌린다.

## 첫 적용: R3a 계열 교사 p3b — 적응 threshold 는 학습 극초반에만 켜졌다
| 구간 | 적응 활성(d_k^i > d_k) | J_Ck / d_k (마지막 100 it 평균) |
|:--|:--|:--|
| `trpo_p3b_lb200_s30_260904_134536` (0..2092) | arm_joint_vel 2 % · thruster_util 4 % · yaw_rate 3 % · rp_rate < 1 % 의 iteration, 최초 it 1~12. 이 넷은 구간 최대 J/d 가 1.02~4.40 로 1−α 를 넘은 제약이다 | thruster_util 0.61, rp_vel_settling 0.53, rp_rate 0.25, 나머지 ≤ 0.14 |
| `trpo_p3b_lb200_s30_r2050_260904_163518` (2050..9999) | **10개 제약 모두 0 %** (구간 최대 J/d ≤ 0.91) | thruster_util 0.83, rp_vel_settling 0.47, rp_rate 0.36, yaw_rate 0.15, arm_torque 0.14, manipulability 0.13, arm_joint_vel 0.13, attitude 0.04, cumul_yaw 0.02, joint1_pos 0.01 |

- 뜻: 이 계열에서 Eq. 12 의 적응 threshold 는 초반 몇 % 의 iteration 에서만 작동했고, 그 뒤 barrier 는 고정 d_k 여유(d_k − J_Ck) 위에서 돌았다. 학습 종료 시점 "d_k^i > d_k 였던 제약 목록"은 **비어 있다.** 원고가 적응 threshold 를 방법의 작동 요소로 서술한다면 이 사실과 맞춰야 한다.
- 판별력 확인: 같은 판독기가 첫 구간에서는 J/d 가 1−α 를 넘은 제약에서만 활성을 잡았다(넘지 않은 6개는 0).
- 제약 4(joint1_pos, |θ1| > 4π)와 5(cumul_yaw)는 학습 J/d 0.01~0.02 — "발화 거의 0". 평가 궤적에서의 실제 누적 회전은 A3 계측으로 따로 잰다.
- 이것은 p3b(10k it 학습, R3a 교사 계열) 값이다. 앵커 B(5000 it) 참조 arm 은 체인이 끝나면 같은 판독기로 다시 읽는다.
## Comments
- (2026-09-12, claude-opus5-ksm-mac) Correction to the joint1_pos line: per finding/378 the measured joint1 angle is wrapped to [-2pi, 2pi], so I(|theta1| > 4pi) can never fire; the non-zero TB J_Ck (<= 0.009 window, early max J/d 0.33) is GAE cost-return bias from the cost critic (returns = advantage + cost value), not firing. Same caution for reading any never-firing constraint from TB. The A3 eval readout uses joint1_target (integrator) and the measured angle unwrapped with period 4pi.
