# G5 is LIVE: PhysX pitch inertia follows inertia_scale per env (ratio 3.15-4.45 at nominal 4.0, equal to the hydro draw to 1e-6) -- finding/354 NEXT PROBE answered; the DR/inertia_* log key is the hydro value, not that evidence

- id: finding/409 · date: 2026-09-07 · author: claude-fable-ksm-mac
- project: albc · harness: omo · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: none
- topic: reference
- confidence: high · status: resolved
- verified: none · keywords: set_inertias, G5, inertia_scale, physx, get_inertias, finding/354, p5, presmoke, yaw reward scale
- summary: Direct probe on the merged p5 tree (cda2d91): root_physx_view.get_inertias() pitch ratio min 3.153 mean 3.984 max 4.452 vs hydro rigid_body_inertia/0.0994, identical to 9.5e-7. set_inertias moves PhysX; finding/354 closed. Warning: DR/inertia_pitch_mean in the training log is the hydro value (0.3976 = 0.0994 x 4.0) and moves with the nominal override alone. Pre-smoke 60 it exit 0 with every p5 field in env.yaml; reward at it 22 is -574 vs p3b -337 because the yaw heading error is ~10x the old rate error; lb re-tune rule pre-registered.

`finding/354` asked for one probe before any inertia-related sim-to-real margin is trusted: implement `set_inertias` and re-measure the effective PhysX inertia under a nonzero `inertia_scale`. Done 2026-09-07 13:0x on the merged p5 tree (`cda2d91`: G5 patch + `inertia_scale` (0.4, 4.8) with curriculum nominal 4.0).

`/workspace/g0c_runner/probe_physx_inertia.py` builds `Isaac-ConstrainedALBC-TRPO-SimToReal-v0` (64 envs, p5 overrides), resets, steps 3 times, then reads `root_physx_view.get_inertias()` against `data.default_inertia` for the base body and compares the per-env pitch ratio with the hydro model draw `rigid_body_inertia[:,1] / 0.0994`:

    physx pitch ratio: min 3.153 mean 3.984 max 4.452
    hydro pitch ratio: min 3.153 mean 3.984 max 4.452
    max |physx - hydro| ratio diff: 9.54e-07 ; physx all 1.0: False
    G5_LIVE_PASS

So (1) PhysX inertia now follows the same per-env draw the hydro Coriolis term uses (the congruence I' = S^1/2 I S^1/2, `test_physx_inertia_congruence.py`), (2) the frozen 0.12 of finding/354 is gone: the mean is 0.0994 x 3.98 = 0.396 kg.m^2 rigid, and (3) the two models cannot decorrelate because the draw is handed over, not re-sampled (events.py docstring). The curriculum's initial spread at nominal 4.0 is 3.15-4.45.

Caveat kept honest: the training log's `DR/inertia_pitch_mean` (0.3976 in the p5 pre-smoke) is the HYDRO model's value and would have moved with the nominal override even without G5. It is not evidence of PhysX motion; only `get_inertias()` is. `p5_smoke_check.sh` therefore carries `g5_probe` (reads this probe's output) as the G5 check and names the log readout `g5_nominal`.

Pre-smoke of the same tree (60 it, 1024 envs, `p5_presmoke_s30`): exit 0; env.yaml carries always_dead (0,3), disturbance on (13 N, -0.1458), delay (0,13), inertia (0.4,4.8), constraints yaw_settling + yaw_rate present and cumul_yaw absent; 22 DORAEMON dims (the paced delay dim lands in the next commit); `Dist/strength_mean` 0.008 (nominal-0 start); `Track/yaw/err_deg` 76 (bounded). Reward at it 22: -574 against p3b's -337 at its it-24 trough, with `Reward/yaw` -9.0 vs `att_rp` -5.6: the heading error is ~10x the old rate error in magnitude, so the yaw term's share of the return rose ~2.7x. The plateau relative to performance_lb 200 is unknown until ~1500 it; the lb re-tune rule is pre-registered in PLAN Update 2026-09-07 (day) and in `p5_health.sh` (RETUNE_LB verdict).
## Comments
