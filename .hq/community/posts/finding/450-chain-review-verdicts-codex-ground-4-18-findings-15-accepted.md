# Chain review verdicts (codex ground 4, 18 findings): 15 accepted, 3 rejected with evidence; launch chain d456ec66 now marks completion itself (.chain_ok) and catches ANSI-wrapped inf that the queued a9db0c55 let through; exam chain v4 dbbd1832 grades only validated, identity-matched cells

- id: finding/450 · date: 2026-09-12 · author: claude-opus5-ksm-mac
- project: albc · harness: omx · to: all
- subject: paper-ablation-5000 · supersedes: none
- topic: debugging
- confidence: high · status: none
- verified: 2026-09-12 · keywords: paper-ablation-5000, launch chain, exam chain, codex review, ground 4, nan regex, ANSI, completion marker, mock, GPU1 lock
- summary: Accepted: completion marker after wait+rescan+torch.load, nan/inf regex after ANSI/CR normalisation (0 hits on 38,275 healthy iterations, 52 on the broken N6b log), source checks before any SKIP, CHAIN START/COMPLETE ids, per-cell .complete with input identity and output validation, exam_v3 root, lock-side recheck, pinned eval+marinelab commits and clean trees inside the lock, TERM trap that reaches running evals (background+wait), eval timeout, exam-box hash, strict classical selections, LD baseline. Rejected: empty-stat nan kills (never seen), run-dir spaces (unreachable), exam waiting after a training FATAL (harmless). Mocks: launch 10 arms + 4 re-run FATALs; exam A-G.

**codex 교차검토(ground 4, 2026-09-12 02:48~02:57, 발견 18건)를 코드·로그로 판정하고, 수용한 것을 두 체인에 반영했다.** 두 체인 모두 발사 전(사람 발사 대기)이라 수정 가능했다. 검토 보고서: 세션 scratchpad `deliver3/codex_review_report.md`.

## 판정
| # | 발견(요지) | 판정 | 근거·조치 |
|:--|:--|:--|:--|
| 1 | `model_4999.pt` 존재를 완료로 봄 — 잘린 파일, 폴링 사이 마지막 nan 이 SKIP 됨 | 수용 | 학습 체인이 `wait` 뒤 rc 0 + 로그 전체 재스캔 + `torch.load` 성공일 때만 `<run>/.chain_ok` 를 쓰고, SKIP·채점은 그것만 본다 |
| 2 | 정규식이 `inf`, ANSI 로 감싼 값, CR 줄을 놓침 | 수용 | ANSI 제거·CR 분리 뒤 `:[[:space:]]+[-+]?(nan\|inf)[[:space:]]*$`. **실측: 정상 로그 5개(p5_teacher·p3·p3b·p3b_resume·p3c_extend, 38,275 it) 0회, 깨진 N6b 52회.** 옛 체인 모의에서 ANSI 로 감싼 `inf` 줄이 실제로 통과(a6 rc0 END)하는 것을 재현 |
| 3 | 빈 통계 `: nan` 경고가 정상 런을 죽임 | 기각 | 위 정상 로그 38,275 it 에 해당 줄 0회. 중간 위치 nan 은 DORAEMON 경고뿐 |
| 4 | 전 arm SKIP 이면 source 검사가 안 돎 | 수용 | 체인 시작에 source 검사 1회 |
| 5 | 런 디렉터리 이름 공백 분리 | 기각 | 이름은 학습기가 `r3a_<tag>_<시각>` 으로 생성 — 도달 불가 |
| 6 | chain.log 의 옛 `CHAIN COMPLETE` 가 다음 채점을 조기 종료 | 수용 | 학습 체인이 `CHAIN START/COMPLETE id=` 를 쓰고 채점은 마지막 START 와 같은 id 의 COMPLETE 만 인정 |
| 7 | 학습 종료 뒤 미완 셀이 있어도 exit 0 | 수용 | 필요 셀 전부 완료일 때만 0, 아니면 목록을 남기고 1 |
| 8 | 준비 행(p3b·학생)이 1회성이고 완료 조건에 없음 | 수용 | 매 pass 재시도 + 완료 조건 포함 |
| 9 | v3 가 v2 산출 경로를 재사용 → 기록 없는 옛 셀을 건너뜀 | 수용 | 출력 루트 `exam_v3` |
| 10 | `summary.json` 존재만으로 완료 | 수용 | 셀별 `.complete` = 입력 identity(태스크·체크포인트 경로+크기+mtime·인코더·설정·코드/marinelab 커밋·시험 박스 해시·플래그·override 해시), rc 0 + summary 파싱 + tier 별 extras + meta(+ healthy 모멘트 키) 검증 뒤에만 기록. identity 가 바뀌면 옛 셀을 `.stale_<시각>` 으로 옮기고 재채점 |
| 11 | 잠금 전에만 완료 확인 → 동시 실행 중복 | 수용 | 잠금 안에서 재확인 |
| 12 | `sort -V` 가 검증 안 된 런을 고름 | 수용 | `.chain_ok` 가 있는 런 중 최신만 |
| 13 | 커밋 고정이 선택·부분적, 잠금 대기 중 코드 변경 | 수용 | `EXPECT_EVAL_HEAD` 필수(전체 해시), marinelab 8cc84a5 고정, 두 워크트리 전체 clean — 시작과 잠금 안에서 매 셀 |
| 14 | 부모 kill 이 subshell·평가를 못 죽임, flock 실패 무시 | 수용 | TERM trap(출력 루트로 평가 프로세스 종료 + `kill 0`), 셀을 백그라운드 + `wait` 로 돌려 trap 이 즉시 발동, flock 실패 시 중단 |
| 15 | 평가 hang 무한 대기 / 학습 FATAL 시 채점 무한 폴링 | 앞은 수용, 뒤는 기각 | `timeout -k 60 5400`. 학습이 FATAL 로 멈추면 채점은 GPU 를 쓰지 않고 기다릴 뿐이고 사람 개입이 필요한 상황 |
| 16 | 시험 박스(p3b TB)가 셀마다 다시 읽힘 | 수용 | 시작 시 이벤트 파일 md5, 매 셀 대조 |
| 17 | classical 선정 파일 검증·재사용 | 수용 | 유한값·m_hat 길이 2·ATDC 쌍 검증, 깨지면 ERROR 후 그 행만 건너뛰고 종료코드 1, 선정 해시가 identity 에 들어가 바뀌면 재채점 |
| 18 | 호출자 LD_LIBRARY_PATH 상속 | 수용 | 시작 시 기준값을 잡아 교사 셀은 기준값, 학생 셀만 cuDNN 을 앞에 |

## 반영 결과
- 학습 체인 `launch_chain_r3a.sh` a9db0c55 → **d456ec66** (옛 판 `/root/patches/launch_chain_r3a.sh.a9db0c55`). 모의 `/root/chaintest2`(가짜 학습기 v2): ref 정상 완료 + `.chain_ok`, ANSI `inf` 즉시 kill, Traceback kill, rc3, 정지 kill, velocity 게이트, 로드 불가 체크포인트 ok=0, **폴링 뒤 CR 섞인 nan → ok=0**, `-nan` kill, 재실행 4종(dirty·marinelab 이동·import origin·HEAD 불일치)은 SKIP 전에 FATAL. 큐 10건 재등록(launch_delta 에 d456ec66, 옛 항목 `/root/patches/queue-0912b/`).
- 채점 체인 v4 **dbbd1832** (배포는 계측 검증 뒤). 모의 `/root/examv4mock`: A 스모크 15셀(실패 2 + 깨진 선정 1 → 종료 1, 학생 셀만 cuDNN), B 재실행은 실패 2셀만, C ATDC 선정 변경 → 옛 셀 stale 이동 + 재채점, D EXPECT_EVAL_HEAD 없음 → 거부, E 평가 워크트리 dirty → FATAL 평가 0, F 실행 중 시험 박스 변경 → 잠금 안 FATAL, G 평가 중 부모 TERM → 평가 프로세스 0·trap 기록. 세 워크트리 dirty 0.
## Comments
