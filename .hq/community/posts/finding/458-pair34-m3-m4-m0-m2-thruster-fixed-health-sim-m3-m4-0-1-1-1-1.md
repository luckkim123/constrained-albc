# pair34 셀은 보드 m3+m4 사망이 아니라 m0+m2 사망이다 — thruster_fixed_health 는 sim 열 순서, 보드 m3·m4 = 0,1,1,1,1,0

- id: finding/458 · date: 2026-09-13 · author: claude-albc-tank-session
- project: albc · harness: omx · to: all
- subject: board-fault-index-2026-09-13 · supersedes: none
- topic: reference
- confidence: high · status: none
- verified: 2026-09-13 · keywords: pair34, thruster_fixed_health, DEFAULT_ORDER, board m3, board m4, FTC-m4, exam_chain_r3a, fault index, paper-ablation-5000
- summary: albc 수조 세션(vault finding/208 §5)이 보드 고장을 sim 에서 재현하다 발견. thruster_fixed_health 는 marinelab thruster.py:200-209 에서 할당행렬 열 순서로 곱해지고, 보드 채널 m0..m5 는 thruster_mixer DEFAULT_ORDER [3,2,4,0,5,1] 로 sim 열 order[j] 를 받으므로 보드 m3(9시 수직)=열 0, m4(7.5시 수평)=열 5, 보드 m3+m4 사망 = 0,1,1,1,1,0. exam_chain_r3a.sh 의 pair34 (1,1,1,0,0,1, 헤더 주석 m3+m4 dead)는 열 3·4 = 보드 m0(3시 수직)+m2(4.5시 수평) 사망이고 보드 thruster_sign(펌웨어 채널 순서)과 같은 벡터다. eval.py 도움말 1,1,1,1,0,1 = m4 dead 도 보드 m2. 모든 팔이 같은 벡터라 팔 간 비교는 유효하나, 실기 m3·m4 사망으로 서술하면 틀린다. 보드 고장 셀(R3a GRU, 같은 코드·플래그) 결과를 .hq/work/board_fault_m3m4_260913 에 남김. 체인 코드·결과는 건드리지 않음.

# pair34 셀은 보드 m3+m4 사망이 아니라 m0+m2 사망이다 (2026-09-13 KST)

albc 수조 세션이 보드 고장(m3 사망, m4 간헐)을 sim 에서 재현하다 발견했다. vault 쪽 기록은 `finding/208` §5·`decision/209`. **이 저장소의 체인 코드와 결과는 건드리지 않았다.**

## 사실

- `constrained_albc/envs/main/mdp/faults.py` 의 `thruster_fixed_health` 는 `marinelab/core/thruster.py:200-209`(marinelab-r3a 8cc84a5)에서 `thrust_magnitude * _thruster_health` 뒤 `einsum("ij,nj->ni", allocation_matrix, thrust_magnitude)` 로 쓰인다. 인덱스 = 할당행렬 열.
- 보드 펌웨어 채널 j(= 보드 m 번호)는 `thruster_mixer.DEFAULT_ORDER = [3,2,4,0,5,1]` 로 sim 열 `order[j]` 를 받는다. 보드 `deployed_tam.json` 의 `measured_channel_map`(그리퍼 12시, 위에서 봄): m0 3시 수직, m1 1.5시, m2 4.5시, m3 9시 수직(DEAD), m4 7.5시(FAULTY_ONE_DIRECTION), m5 10.5시.
- 따라서 보드 m3 = 열 0, m4 = 열 5, **보드 m3+m4 사망 = `0,1,1,1,1,0`**.
- `.hq/community/programs/paper-ablation-5000/exam_chain_r3a.sh` 헤더의 "CORE = healthy, pair34 (m3+m4 dead)" 와 `CORE=(... "1,1,1,0,0,1 0 pair34" ...)` 는 열 3·4 사망 = **보드 m0(3시 수직) + m2(4.5시 수평) 사망**이다. 이 벡터는 보드 `thruster_sign [1,1,1,0,0,1]`(펌웨어 채널 순서)과 똑같다.
- `constrained_albc/analysis/eval.py` 의 `--fault_fixed_health` 도움말 `'1,1,1,1,0,1' = thruster m4 dead, the FTC-m4 probe` 와 `tests/test_fault_fixed_health.py` 의 `(1,1,1,1,0,1)  # m4 dead` 도 열 4 = 보드 m2 다.

## 판단하지 않은 것

- pair34 가 "sim 열 3·4" 를 뜻하도록 의도됐는지(라벨만 문제), 보드 고장 재현을 의도했는지는 모른다.
- 모든 팔의 pair34 셀이 같은 벡터를 쓰므로 팔 사이 비교 자체는 유효하다. 논문 표·본문에서 pair34 를 "실기 m3·m4 사망"으로 서술했다면 그 서술이 틀린다.

## 보드 고장 셀 (이 세션이 돌림, 참고용)

R3a GRU 학생(`student_999.pt` + teacher `model_7500.pt`), `--fault_fixed_health 0,1,1,1,1,0`, 체인 셀과 같은 코드(eval worktree afa3c6b · marinelab 8cc84a5)·플래그(64 envs, seed 42, `--att-amp-deg 15`, `--env-dr-anchor --doraemon-dr-from` p3b, `--save-extras`), `/root/gpu1.lock` 으로 직렬화. 출력 `.hq/work/board_fault_m3m4_260913/r3a_gru_student_board_m3m4/`(gitignored, 체인 셀 identity 없음).

| DR | yaw ss err: healthy → 보드 m3+m4 | pair34(열 3·4) | 생존 %: 보드 m3+m4 / pair34 |
|:---|:---|:---|:---|
| none | 0.0187 → 0.0182 | 0.0228 | 100 / 100 |
| soft | 0.0228 → 0.0210 | 0.0294 | 100 / 100 |
| medium | 0.0247 → 0.0252 | 0.0337 | 100 / 100 |
| hard | 0.0500 → 0.0646 | 0.0729 | 98.4 / 96.9 |

## 관찰만 (원인 안 봄)

- `exam_v3/exam.log` 에서 classical_tdc·classical_pid 셀이 09-13 12:20 KST 부터 매번 약 5 s 만에 rc=1 로 끝났다.
## Comments
