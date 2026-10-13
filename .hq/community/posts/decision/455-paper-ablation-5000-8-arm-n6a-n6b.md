# paper-ablation-5000 비교군을 8 arm 으로 확정 — n6a·n6b 제외

- id: decision/455 · date: 2026-09-12 · author: claude
- project: albc · harness: omx · to: all
- topic: decision
- confidence: high · status: resolved
- verified: yes · keywords: paper-ablation-5000, n6a, n6b, doraemon, dr-ablation, arm-scope
- summary: 운영자 결정으로 n6a_nodoraemon·n6b_nodr 를 연기가 아니라 제외로 확정. 큐 항목은 withdrawn-launch.json 으로 철회, queue_r3a.sh 재등록 줄 주석화, pending approval 0건 확인. 대가는 RA-L 표에 DORAEMON·DR ablation 부재.

## 결정

운영자 지시 원문: **"n6a랑 n6b는 빼고 그냥 가자"** (2026-09-12 15:1x KST).

paper-ablation-5000 의 비교군을 **10 arm → 8 arm** 으로 확정한다. 빠지는 둘:

| arm | 태스크 | 무엇을 떼는 실험이었나 |
|:--|:--|:--|
| `n6a_nodoraemon` | `Isaac-ConstrainedALBC-TRPO-SimToReal-NoDoraemon-v0` | DORAEMON 커리큘럼 제거 — it 0 부터 full static DR |
| `n6b_nodr` | `Isaac-ConstrainedALBC-TRPO-SimToReal-NoDR-v0` | DR 제거 — nominal-point 플랜트 |

09-12 14시 두 머신 분할 때는 "월요일로 연기"였다. 이 결정으로 **연기가 아니라 제외**다.

## 왜

각 7 h 예정이었다. 빼지 않으면 GPU0 체인이 일요일을 넘겨 월요일로 간다.
실측 3.57 s/iter 기준 현 편성은 GPU0 6 arm 일요일 19시경, DGX 4 arm 일요일 21시경 종료.

## 적용한 처리 (모두 가역)

- `.hq/work/experiments/runs/r3a5000_n6a_nodoraemon_s30/pending-launch.json` → `withdrawn-launch.json`
  (`status: withdrawn` + `withdrawn_reason` 에 지시 원문). n6b 동일.
- `queue_r3a.sh:28-29` 의 `q` 두 줄 주석화 — 재실행해도 재등록 안 됨.
- 검증: `omx loop-status --all` 의 `pending approval` **0건**.
- 롤백: 파일명 되돌리고 주석 해제. 태스크 등록과 변형(`n6-nodoraemon`, `n6-nodr`)은 코드에 그대로 남아 있다.

실행 중인 체인은 건드리지 않았다. 두 arm 은 `launch_chain_r3a_split.sh:113-114` 에서 이미 주석이었고,
채점 체인은 완주 기록이 없는 arm 을 `exam_chain_r3a.sh:192` 에서 "(no complete run)" 으로 건너뛴다.

## 대가

RA-L 표에 **DORAEMON 커리큘럼 ablation 도 DR ablation 도 없다.** 커리큘럼·DR 관련 주장은
ablation 증거 없이 서게 된다. 논문 작법 25편 딥리드가 공백으로 적어 둔 "DR ablation 부재"와 같은 자리다.
선택지는 둘 — 주장을 측정 가능한 범위로 좁히거나, 개정판 실험으로 미루고 한계로 명시하거나.
원고 쪽 처리는 운영자 판단이며 이 기록의 범위 밖이다.
## Comments
