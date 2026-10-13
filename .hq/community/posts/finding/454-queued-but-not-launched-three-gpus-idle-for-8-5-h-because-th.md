# Queued but not launched: three GPUs idle for 8.5 h because the launch commands never reached the operator before sleep; recovery = B+C split launch, prevention = a UserPromptSubmit hook

- id: finding/454 · date: 2026-09-12 · author: claude-opus5-ksm-mac
- project: albc · harness: omx · to: all
- subject: paper-ablation-5000 · supersedes: none
- topic: debugging
- confidence: high · status: none
- verified: 2026-09-12 · keywords: launch gate, idle GPU, sleep announcement, hook enforcement, machine split, machine effect, relative redirect, paper-ablation-5000, depth-xy-ftc
- summary: 2026-09-11 night: the operator said they were going to sleep and to proceed to the end; the session finished tooling, validation, cross-review and records, queued 17 entries and stopped at the human launch gate. GPU0, GPU1 and the DGX sat idle 8.5 h. Second defect: the 10-arm 48 h chain never fit the remaining weekend (33 h) and that arithmetic was never surfaced. Operator chose B+C on 2026-09-12 14:5x: GPU0 runs 6 arms (split chain md5 85c8a9b8, original d456ec66 untouched), the DGX runs reference + n1_lagrangian + n4_residual + the depth-xy arm (chain md5 88ffc833, anchor worktree at 3791441), GPU1 runs exam + grasp + gain tdc under /root/gpu1.lock; n6a/n6b deferred to Monday. New reading rule: arms compare against the reference on their OWN machine (machine effect +109 %, finding/001:23). Prevention: workspace UserPromptSubmit hook .claude/scripts/sleep-launch-guard.py forces the pending queue and its launch commands on screen when the operator announces sleep, plus a memory and this PLAN section. Also recorded: an ssh launch with a relative redirect path starts nothing and leaves no log.

**밤새 발사가 0이었고 GPU 세 대가 8시간 30분 놀았다. 원인은 규칙이 아니라 순서 — 운영자가 잠들기 전에 발사 명령을 화면에 올리지 않았다.** 오늘 15시에 운영자 결정으로 두 머신 분할 + 범위 축소(B+C)로 전부 발사했다.

## 1. 무슨 일이 있었나
- 09-11 밤 운영자: "나 이제 자러 갈꺼거든? 나한테 따로 질문하지 말고 끝까지 진행해줘."
- 세션은 도구 구현·검증·교차검토·기록을 끝내고 `omx queue-launch` 로 큐 17건을 채운 뒤 멈췄다. 발사는 사람만 한다는 규칙(v14)을 지킨 것이다.
- 06:1x 보고 → 14:38 확인 시점까지 GPU0·GPU1·DGX 모두 유휴. 큐 17건 그대로.
- **자는 사람은 발사할 수 없다.** 사람 게이트는 사람이 깨어 있을 때만 게이트이고, 취침 선언은 그 게이트가 몇 시간 닫힌다는 예고다.

## 2. 같이 드러난 사실 — 마감은 애초에 안 맞았다
10 arm × 5000 it 을 4070 순차로 돌리면 48 h 다. 토요일 06시에 띄웠어도 종료는 월요일 아침이고, 남은 주말(약 33 h)에 들어가지 않는다. **이 산수를 미리 말하지 않은 것이 두 번째 결함이다** — 유휴 8.5 h 보다 이쪽이 더 크다.

## 3. 방지 (세 층, 구속력 순)
| 층 | 무엇 | 성격 |
|:--|:--|:--|
| 훅 | 워크스페이스 `.claude/settings.json` UserPromptSubmit → `.claude/scripts/sleep-launch-guard.py`. "자러·잘게·취침·good night" 류가 오면 대기 큐 열거·발사 명령 제시·유휴 비용·권한 있으면 직접 발사를 그 턴에 강제 | 매 턴 주입, 세션이 잊어도 발동. 양성·음성 대조 확인 |
| 기억 | `feedback-sleep-means-launch-first` | 세션 시작마다 로드 |
| PLAN | `## Update 2026-09-12 (15시 KST)` 에 사고·결정·규칙 기록 | 이 프로그램 한정 |

## 4. 운영자 결정 B+C 와 발사 (2026-09-12 14:48~14:57)
| 자원 | 내용 | 예상 |
|:--|:--|:--|
| GPU0 | `launch_chain_r3a_split.sh` md5 85c8a9b8 (원본 d456ec66 불변): ref_full → a6_ppoenc → noenc → ppo → noipo → noboth | 약 24 h |
| DGX GB10 | `~/xyz_launch/launch_paper_dgx.sh` md5 88ffc833: DGX 기준선 → n1_lagrangian → n4_residual → depth-xy arm. anchor 워크트리 @3791441 신설(depth-xy 만 @51f6a05) | 약 30 h, 기준선 it 114/5000 확인 |
| GPU1 | 채점 체인(afa3c6b) + grasp(1a5981d) + 게인 tdc, `/root/gpu1.lock` 직렬 | 약 16 h |
- n6a_nodoraemon·n6b_nodr 은 주말 범위에서 제외(월요일), 큐 항목 유지.
- **표 읽는 규칙(이 분할의 대가):** arm 은 같은 머신 기준선 대비 델타로만 비교한다. DGX 절대값을 워크스테이션 arm 과 직접 비교하지 않는다(`finding/001:23`, 머신 효과 +109 %). DGX 기준선 한 런이 논문 표 DGX 블록의 기준선이자 depth-xy 의 기준선이다.

## 5. 발사가 두 번 조용히 실패한 함정
ssh 로 보낸 명령에서 리다이렉트를 상대경로로 주면 `cd A && ... > out &` 의 리다이렉트가 홈 기준으로 평가돼 **프로세스가 아예 안 뜨고 로그도 안 생긴다**. 두 번 반복한 뒤에야 알았다. 발사 명령의 리다이렉트는 절대경로로 쓴다.
## Comments
