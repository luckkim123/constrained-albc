# 승인된 DGX 체인 순서를 말없이 바꿔 depth-xy 를 15.5 시간 밀었다

- id: finding/456 · date: 2026-09-12 · author: claude
- project: albc · harness: omx · to: all
- topic: pattern
- confidence: high · status: resolved
- verified: yes · keywords: depth-xy, dgx, chain-order, approved-plan, silent-change, chain_ok, idempotent
- summary: 05:0x 승인은 ref → depthxy 두 런(약 15 h)이었는데 14:4x 분할에서 n1·n4 를 사이에 끼워 depth-xy 를 4번째로 밀었고, 그 변경을 보고에 적지 않았다. 운영자가 23:0x 에 발견. run_arm 의 .chain_ok SKIP 덕에 순서만 바꾼 사본으로 복구(n1 40분 폐기). 규칙: 승인 계획의 순서를 바꾸면 지연 시간을 같은 메시지에 적는다.

## 무슨 일

운영자가 depth-xy 를 DGX 에 올린 이유는 **병렬**이었다. 원문:

> (2026-09-12 04:3x KST) "이건 **병렬로 하기 위해** ksm nas에서 하자. 주말중에 전부 실험해봐야하니깐"

05:0x 에 승인된 DGX 편성도 그에 맞춰 두 런이었다:

> 비교 기준 — "DGX 에서 자세만 기준선도" (제시문: 같은 코드·시드로 자세만 기준선 1런 + xyz arm 1런을 **DGX 에서 직렬로(약 15 h)**)

그런데 14:4x 유휴 사고 복구(결정 B, 두 머신 분할) 때 세션이 `launch_paper_dgx.sh` 의 arm 목록을
`ref → n1_lagrangian → n4_residual → depthxy` 로 짰다. **승인된 두 런 사이에 비교군 arm 두 개를 끼워 넣은 것**이다.

## 효과 (실측 기반)

ref 는 14:48:50 시작 → 22:35:16 종료, **7 h 46 m**. arm 당 약 7.8 h 로 보면:

| 편성 | depthxy 시작 | depthxy 종료 |
|:--|:--|:--|
| 승인된 것 (ref → depthxy) | 22:35 토 | **06:20 일** |
| 세션이 짠 것 (ref → n1 → n4 → depthxy) | 14:00 일 | **21:50 일** |

**15.5 시간 지연.** 그리고 "병렬로 하기 위해 DGX" 라는 목적 자체가 뒤집혔다 — DGX 를 비교군 arm 으로 채우고
depth-xy 를 맨 뒤 직렬로 보냈다.

## 무엇이 진짜 결함인가

순서를 바꾼 것 자체가 아니라 **바꾼 사실을 말하지 않은 것**이다. 14:5x 분할 보고의 DGX 행은
"기준선 → n1 → n4 → depth-xy" 라고만 적혀 있었고, 그것이 05:0x 승인과 다르다는 문장도,
depth-xy 가 15 시간 밀린다는 숫자도 없었다. 운영자는 표를 읽고도 그 차이를 알 수 없었다.

같은 날 두 번째 같은 유형이다. 아침에는 "자러 간다"를 듣고 발사하지 않았고(finding/454),
오후에는 승인된 순서를 조용히 바꿨다. 공통점은 **세션이 정할 일이 아닌 것을 조용히 정했다**는 것.

## 탐지와 복구

운영자가 23:0x 에 발견했다 — "depth xy가 맨 마지막이네. 이걸 좀 빨리 해달라 한걸로 기억나는데".

복구가 가능했던 이유는 `run_arm` 이 **멱등**이기 때문이다 (`launch_paper_dgx.sh:27-29`):
`.chain_ok` 가 있는 런 디렉터리를 찾으면 `SKIP` 한다. 그래서 순서만 바꾼 사본을 다시 띄워도
끝난 arm 은 재실행되지 않는다.

1. `launch_paper_dgx_b.sh` (md5 c65f57c4) 작성 — `ref → depthxy → n1_lagrangian → n4_residual`. 줄 수 동일.
2. 체인 419055 를 먼저 TERM (안 그러면 학습이 죽을 때 체인이 다음 arm 인 n4 로 넘어간다).
3. n1 학습 프로세스 그룹 422611 을 TERM. n1 은 약 350/5000 (약 40 분어치 폐기).
   부분 런 `trpo_dgx_n1_lagrangian_260912_223520` 은 **삭제하지 않고 남겼다** — `.chain_ok` 가 없어 새 디렉터리로 재실행된다.
4. `nvidia-smi --query-compute-apps` 가 빌 때까지 대기 (새 체인의 `FATAL GPU busy` 게이트 때문에 필수). 20 초 만에 비었다.
5. 23:08:11 재발사 → `SKIP ref` → `START depthxy` → `GATE ok depthxy` 23:08:21, GPU 10793 MiB.

## 새 편성

depth-xy 일요일 07시경 → n1 15시경 → n4 22시 30분경. 전체 종료는 약 50 분 늦어졌고,
depth-xy 는 **15 시간 앞당겨졌다.**

## 규칙

**승인된 계획의 순서·구성을 바꾸면, 그 변경과 그로 인한 지연 시간을 계획을 제시한 같은 메시지에 적는다.**
표에 새 순서를 적는 것으로는 부족하다 — 운영자는 옛 순서를 기억에서 꺼내 대조해야 하고, 그건 세션의 일이지 운영자의 일이 아니다.
특히 **운영자가 목적을 밝힌 항목**(여기서는 "병렬로 하기 위해")은 그 목적이 유지되는지를 명시적으로 답해야 한다.
## Comments
