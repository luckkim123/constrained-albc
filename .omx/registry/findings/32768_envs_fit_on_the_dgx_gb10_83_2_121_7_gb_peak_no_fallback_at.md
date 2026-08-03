---
title: "32768 envs FIT on the DGX GB10 (83.2/121.7 GB peak, no fallback) at 34.73 s/iter, but per-doubling cost is degrading (1.78x -> 1.90x) and a 200-iter probe cannot see DORAEMON at all (step_interval 250)"
tags: ["scaling", "dgx", "gb10", "throughput", "memory", "doraemon", "num-envs", "e2"]
created: 2026-07-30T08:15:48.169652
updated: 2026-07-30T08:15:48.169652
sources: []
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# 32768 envs FIT on the DGX GB10 (83.2/121.7 GB peak, no fallback) at 34.73 s/iter, but per-doubling cost is degrading (1.78x -> 1.90x) and a 200-iter probe cannot see DORAEMON at all (step_interval 250)

MEASURED 2026-07-30 on the DGX (seungmin-dev, NVIDIA GB10, aarch64, 121 GB unified memory) by the
E2 scaling pilot `trpo_scale32768_pilot_260730_151337`, group `dgx_scale_32768`, at
constrained-albc 9ef4cf644b3f8677b5b1fe4e8355fb30e24202dd (main) + marinelab
a1d8b2f9451bfe6fac59a12a80caad42a9e284e8 (main) -- i.e. the ADOPTED plant (`max_thrust_scale`
(0.85, 1.15) verified from the run's own dumped `params/env.yaml`, `fault.enable: false`).
200 iterations, `num_steps_per_env` 64, `step_interval` 250, `max_kl` 0.005 -- teacher recipe
otherwise UNCHANGED. exit_code 0.

THIS IS A THROUGHPUT/FEASIBILITY PROBE, NOT A COMPARISON-BEARING RUN. It trains on a plant with six
open `needs-apply-before-retrain` leads (the added-mass one fires at runtime: `HydrodynamicsModel(base):
Marginal added mass stability` at M_a/I_rigid 0.87 surge/sway, 0.91 roll/pitch, 0.94 yaw against the
0.8 threshold). Do NOT read these numbers as a plant-correct baseline, and do not compare the policy
against workstation-trained anchors (machine isolation: +109% roll ss_error, same config same seed).

## 1. 32768 envs FITS on GB10 -- the 16384 fallback did not fire

- peak unified-pool used: 83,170 MiB of 124,610 MiB -> 41,440 MiB (40.5 GB) headroom
- peak per-process GPU: 69,207 MiB (67.6 GB)
- baseline before launch: 5,609 MiB used / 119,000 MiB available

INSTRUMENT NOTE: `nvidia-smi` reports `Memory-Usage: Not Supported` and `memory.total/used = [N/A]`
on GB10 -- it is unified memory, so any handoff step that says "peak VRAM from nvidia-smi" is not
executable as written. Two working substitutes: `nvidia-smi --query-compute-apps=pid,used_memory`
DOES work (per-process only), and `free -m` sampling captures the whole pool, which is the honest
instrument because GPU allocation and host RSS come out of the same 121 GB.

## 2. Throughput: 34.73 s/iter, and the per-doubling cost is degrading

Steady state (first 10 iterations discarded; iteration 1 = 40.55 s warmup, the rest immediately flat):
mean 34.726 s, median 34.720 s, min 34.560 s, max 35.150 s, stdev 0.065 s, n=190. Total wall clock
6,951 s (115.9 min) for 200 iterations.

Against the two prior DGX points (5.41 s/iter @4096, 9.65 s/iter @8192):

| num_envs | s/iter | per-doubling factor | samples/s | s per env per iter |
|---:|---:|---:|---:|---:|
| 4096 | 5.41 | -- | 48,455 | 1.321e-3 |
| 8192 | 9.65 | 1.784x | 54,330 | 1.178e-3 |
| 32768 | 34.73 | 1.897x (geometric, over 2 doublings) | 60,384 | 1.060e-3 |

Scaling is still sub-linear (linear would be 2.000x per doubling) but the margin is thinning:
1.784x -> 1.897x. The practical consequence is that an 8x batch buys only 1.25x sample throughput
(48.5k -> 60.4k samples/s). A fixed-iteration 5000-iter run at 32768 would take 5000 x 34.73 s =
48.2 h, inside the 42-54 h band that was extrapolated before the pilot.

## 3. DORAEMON: the curriculum NEVER STEPPED -- 200 iterations is below the instrument's resolution

`step_interval` is 250 iterations and the pilot ran 200, so no expansion was possible by construction.
Confirmed three independent ways: `DORAEMON/kl_step` = 0.0000 for all 200 iterations; every
`DORAEMON/mean/*` and `DORAEMON/std/*` is bit-flat across all 200; `curriculum_trajectory.json`
holds exactly one record and it is the `iter: 0` snapshot (Beta a=b=15 on the 17 two-sided dims,
a=b=1 on the four one-sided dims).

- `DORAEMON/success_rate`: 0.0000 -> 0.0020 (max 0.0040), still ~0 as expected at iteration 200 of a
  5000-iteration recipe
- `DORAEMON/mode`: -3.0, logged once (n=1). The enum is NOT defined anywhere under
  `constrained_albc/` -- the tag is composed dynamically (`{f"DORAEMON/{k}": v for k, v in
  metrics.items()}` in `envs/_core/runners/on_policy_doraemon_runner.py:98`) and only READ by
  `.omx/profile/analyze_training.py:994`. Semantics unresolved; irrelevant to the no-expansion
  verdict, which three other signals already settle.
- `DORAEMON/buffer_size` 2000 (full) throughout; `DORAEMON/total_episodes` 34,141 -> 326,187

Optimisation itself is healthy: `Train/mean_reward` -16.95 -> 152.29 (max 164.46), `Policy/entropy`
8.50 -> -2.40 monotone.

CONSEQUENCE FOR THE NEXT PROBE: any run intended to answer "does the curriculum stay healthy at
32768 envs" needs >= 250 iterations to see one expansion and realistically >= 500 for a trend. A
200-iteration probe measures throughput and memory only.

## 4. Launch mechanics on this box (they differ from the container)

`/isaac-sim/python.sh` does not exist on the DGX -- there is no Docker there and Isaac Sim is a
source build. The raw interpreter `~/workspace/isaaclab/_isaac_sim/kit/python/bin/python3` lacks
numpy when invoked directly. The one working launcher is
`TERM=xterm ~/workspace/isaaclab/isaaclab.sh -p scripts/train.py ...` (TERM must be set or the
script dies on `'ansi+tabs': unknown terminal type` over SSH); it preserves cwd, so running it from
the constrained-albc root lands output in that tree. `CUDA_VISIBLE_DEVICES` pinning is a no-op here:
GB10 is a single GPU.

