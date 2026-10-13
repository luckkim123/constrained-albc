# Handoff — depth-xy-ftc-2026-09

Paste as-is into the session that fires the runs. Self-contained: everything needed is here or produced by the commands below.

## Objective (carried from PLAN.md, verbatim)

> (2026-09-12 04:3x KST, 사용자) "근데 궁금한게 지금은 학습이 자세라 제어만 하는데 여기에 xyz 제어까지 추가해도 되는거 아니야? 기존 제어기들이 제어하는 방식 정도로만 하면 dvl이 없는 로봇이어도 가능할 것 같은데? 이것도 해봐줄 수 있어? 이건 병렬로 하기 위해 ksm nas에서 하자. 주말중에 전부 실험해봐야하니깐"
>
> Scope answer (05:0x): "추천대로 하되 모델이 z축 스러스터의 값도 보면 좋을 것 같네. 아 그리고 고장 제어도 여전히 추가해주고." — z closed loop + xy open loop. Comparison answer: "DGX 에서 자세만 기준선도".

## Hard rules

1. Launch EXACTLY ONE chain, the one below: it runs the depth-xy arm, then the attitude-only reference, serially on the DGX. Nothing else is pre-approved.
2. If a knob looks wrong, a pin FATALs, or the gate fails, STOP and report. Do not edit the chain or the tree to get past it.
3. Never set CUDA_VISIBLE_DEVICES on the DGX. Never edit a running chain script.

## Held decisions

| knob | held at | alternative considered | why held | what it costs |
|:--|:--|:--|:--|:--|
| DORAEMON return | excludes `depth_tracking` and `xy_force_tracking` | include them and re-tune `performance_lb` | the arm and the reference pace their curricula on the same return (operator's same-DGX reference) | the curriculum does not slow down when depth or xy tracking is poor |
| `performance_lb` | 200 (anchor SimToReal) | re-tune for the larger return | follows from the row above | none beyond that row |
| fault DR | p 0.30, dead 0.5, severity DORAEMON dim | pin m3 dead | operator "고장 제어도 여전히"; FTC is a distribution, never a pinned plant | the arm never trains on a guaranteed dead vertical |
| xy command scale | u_xy x 8 N | larger force | leaves the `thruster_util` average budget 0.40 room for attitude and depth | the xy command covers about 22 % of horizontal authority |
| depth command range | start depth +- 0.5 m | wider | the tank band is 0.205-0.890 m | no deep-water profile |
| everything else | anchor SimToReal (3791441) | p5 delta (`decision/408`) | keeps the DGX reference comparable to the paper arms | the p5 plant changes are not in either run |

## Predicted outcome

Reference: curriculum health like the p3b canary; its attitude numbers differ from the workstation reference by the machine effect (`finding/001:23`) — not a result. Arm: depth hold within about 0.05 m at none/soft, worse at hard; attitude at hover within the reference's noise floor at none, with a cost while horizontal thrust is commanded; force tracking at none/soft. A null (the policy under-realizes the xy command) is a real possibility and is a result.

## Steps

1. On the Mac: `ssh -o BindAddress=192.168.10.17 ksm-nas` (the plain alias is refused by the Mac's route).
2. `git -C ~/workspace/constrained-albc-xyz rev-parse HEAD` must print `51f6a052fad210b52bd22b4336ecc412b5ef239b`; `git -C ~/workspace/marinelab-xyz rev-parse HEAD` must print `8cc84a54540f9fd06a835efc3f33d117dd8b2a84`; both `git status --short` empty; `nvidia-smi --query-compute-apps=pid --format=csv,noheader` empty; `md5sum ~/xyz_launch/launch_depthxy_dgx.sh` starts with `7fcd9f72`.
3. `EXPECT_HEAD=51f6a052fad210b52bd22b4336ecc412b5ef239b nohup bash ~/xyz_launch/launch_depthxy_dgx.sh > ~/xyz_launch/chain.out 2>&1 &`
4. Within 10 min `~/xyz_launch/chain.out` shows `GATE ok arm`. Every 500-1000 it: `/usr/bin/python3 ~/xyz_launch/watch_depthxy_dgx.py` — a STALL SIGNATURE line is a report-to-operator event.
5. After `END arm` and `END ref`: exams per PLAN "Eval schedule".

## Reporting

All numbers are screening measurements unless the plan says otherwise. Report measurements, never adoption conclusions. Queue entries: `depthxy_dgx_arm_s30`, `depthxy_dgx_ref_s30`.
