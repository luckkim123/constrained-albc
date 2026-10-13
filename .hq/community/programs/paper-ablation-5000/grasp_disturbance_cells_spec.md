# grasp-step chain: disturbance cells (operator request, move-test note §4-5(a) decided in §8-1 2026-09-12 00:xx)

Request (vault `10-19_Projects/11_Research/01_albc/03_notes/2026-09-11-move-test-thruster-ownership-design.md:189,292`):
"marinelab 파지 계단 proposal 의 (0,0) 고정 경로에 외란 종류(pitch 모멘트 계단, yaw 회전)를 더해 요청". Never reached the
marinelab session through a handoff; found 2026-09-12 05:1x. Not in grasp commit 1a5981d.

Design (to implement on eval/grasp-step after the depth-xy queue):
- `eval.py static --hold-zero-cmd` + `--pitch-moment-step MY --event-step K`: body-frame My on the base link from step K on,
  re-added every physics substep after `_apply_action` (generalize `_install_yaw_torque_injector`, eval.py:776-807: the
  composer is a SET, so a one-shot add is overwritten), gated by `episode_length_buf >= K` per env.
  MY = 1.9 N.m: the depth PID's worst pitch injection with m0 alone, |My| = 0.1458 x Fz, Fz <= 13 N (decision/408,
  finding/154/155). Sign both ways as two cells (+MY, -MY).
- `--yaw-rate-step R --event-step K`: in hold mode set targets["yaw_rate"][K:] = R, roll/pitch stay 0. R = 0.3 rad/s (inside the
  trained +-0.5 rad/s range, config.py:532).
- Readout: `grasp_step_readout.py --event-step K` for non-payload events (the payload trace has no step), same pre-registered
  metrics (peak deviation, settling from the peak, pre/post steady state, survival); instrument check = alive at K.
- Chain rows unchanged; new cells row x {pitch_plus, pitch_minus, yaw_rot}, tiers soft,medium,hard, K = 750.
- Validation: smoke like K0-K6 (flags off identity, one 64-env cell per new flag, readout rc).

Constraint found 2026-09-12 05:3x: `r3a5000_grasp_v1` is queued with `EXPECT_GRASP_HEAD=1a5981d` and the chain FATALs when the
grasp worktree HEAD moves. Implement the disturbance cells on a NEW branch/worktree from 1a5981d (e.g. `eval/grasp-disturb`,
`/workspace/constrained-albc-grasp-dist`) with its own chain pin, never as a commit on eval/grasp-step while that entry is pending.
