# Desk answers to decision/147: thrust-coefficient DR is a per-env scalar shared by all six thrusters; sim rotational inertia nominal = URDF 0.0994/0.0372 kg·m², measured pitch J_total 0.49 above the DR ceiling 0.39

- id: finding/312 · date: 2026-09-04 · author: session-mac-fable
- project: albc · harness: omo · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: none
- topic: reference
- confidence: high · status: needs-experiment
- verified: none · keywords: decision/147, thrust_coefficient_scale, per-env, rigid_body_inertia, URDF, added inertia, item 10
- summary: Container reads for the two items vault decision/147 left open. (1) thrust_coefficient_scale is drawn once per env as a scalar (marinelab/core/thruster.py:264-268) and multiplies the 40 N nominal for all six thrusters, resampled per episode — so item 9 option (b) as written re-centers every channel while only m0 is measured; vertical-only needs a per-thruster nominal (small code, G0-J diff). (2) Sim base inertia is 9.18 kg, (0.0994, 0.0994, 0.0372) kg·m² identically in deployed_env.yaml and agent.urdf:52 (radius of gyration 0.104 m); inertia_scale (0.4,2.0) + added-mass clamp 0.95×rigid give a max reachable J_total ≈ 0.39, below vault finding/145 measured 0.49 (0.39–0.41 if K is 20 % low) — vehicle-model candidate by the decision/147 rule; opened as PLAN §10 item 10, recommend measuring the dry inertia first. No plant value changed.

# Desk answers to decision/147: the thrust-coefficient DR is a per-env scalar (all six thrusters share one draw), and the sim's rotational inertia nominal is the URDF's 0.0994/0.0372 kg·m² — the measured pitch J_total 0.49 sits above the DR ceiling 0.39

2026-09-04 00:4x, Mac session, container reads. Two items vault `decision/147` left as "unverified / needs the container".

## 1. How the thrust-coefficient DR is applied (decision/147 ⚠️ "DR 적용 형태 미확인")

`marinelab/core/thruster.py:247-268` (`randomize_parameters`, called from `albc_env.py:1761-1766` at reset for the reset envs): `torch.rand(num_envs) * (hi − lo) + lo` — **one scalar per env**, multiplied onto `thrust_coefficient = 40.0` (`config.py:141`), applied to **all six thrusters of that env**, resampled per episode. `max_thrust_scale (0.85, 1.15)` scales the 50 N clamp separately. Consequences for §10 item 9:
- option (b) "re-center the nominal" as written moves EVERY channel; only m0 (vertical) has a thrust measurement (`finding/146`), horizontal channels have none;
- a vertical-only re-center needs a per-thruster nominal (a few lines; would enter the G0-J diff);
- per-thruster spread across an env does not exist today — every thruster in an env shares one coefficient.

## 2. Sim rotational inertia nominal (decision/147 instruction 2, "sim rigid_body_inertia nominal not found")

| source | mass | I (roll, pitch, yaw) kg·m² |
|:--|--:|--:|
| hydro cfg, incumbent `deployed_env.yaml:227-231` | 9.18 | (0.0994, 0.0994, 0.0372) |
| URDF `marinelab/assets/albc/meshes/agent.urdf:49-53` (base link, inertial origin z −0.05) | 9.18 | (0.0994, 0.0994, 0.0372) |
| buoy link (`deployed_env.yaml:270-274`) | 0.93 | (0.00278, 0.00278, 0.00336) |

Same numbers in both places, so there is one source. Radius of gyration √(0.0994/9.18) = **0.104 m** for a frame whose thrusters sit ~0.145 m off the pitch axis — small, and probably a hand-entered guess rather than CAD.

DR: `inertia_scale (0.4, 2.0)` (`config.py:193`, `events.py:268-269`) → rigid 0.040–0.199; rotational added mass nominal `added_mass[3:6] × 0.5` (`events.py:174`) and clamped at **0.95 × rigid** (`events.py:271`) → **max reachable J_total ≈ 0.199 + 0.189 = 0.39 kg·m²**.

Measured (vault `finding/145`): attitude mode 0.6233 Hz with K = 7.76 N·m/rad → J_total = K/(2πf)² ≈ **0.49–0.51 kg·m²**. K is a `decision/147` "suspect" (∝ buoy net buoyancy); K 20 % lower → 0.39–0.41. So the real total inertia sits **at or above the DR ceiling** even under the pessimistic K. By `decision/147`'s own rule this points at the vehicle model (the 0.0994 nominal), not at DR width. Opened as PLAN §10 item 10 `[DECISION-REQUIRED: rotational-inertia]`; recommendation there is to measure the dry inertia (bifilar pendulum / CAD) before choosing.

## Not done
No plant value changed. The dry rotational inertia of the real robot is still unmeasured (this post gives the sim side only).
## Comments
