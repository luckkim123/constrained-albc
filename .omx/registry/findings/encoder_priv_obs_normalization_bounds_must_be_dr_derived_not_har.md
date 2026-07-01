---
title: "encoder priv-obs normalization bounds must be DR-derived, not hardcoded (silent drift bug)"
tags: []
created: 2026-06-30T08:26:23.774268
updated: 2026-06-30T08:26:23.774268
sources: []
links: []
category: reference
confidence: high
schemaVersion: 1
---

# encoder priv-obs normalization bounds must be DR-derived, not hardcoded (silent drift bug)

Encoder normalizes the 27D privileged obs with static min-max [(2*p_t-(U+L))/(U-L)] -> [-1,1] (HORA-style, deterministic, avoids z-drift/KL-spike). The bounds U/L were HARDCODED literals (_PRIV_OBS_LOWER/UPPER in agents/rsl_rl_ppo_cfg.py) and silently DRIFTED from the DR config they should mirror.

TWO REAL BUGS this caused (not just margin):
- idx12 payload_mass: hardcoded [-0.1, 2.2] vs DR payload_mass_range [0, 3]. A 3 kg payload normalized to (3-(-0.1))/(2.2-(-0.1))=1.35 > 1 -> OVERFLOW, encoder sees an input range it never trained on. Lower -0.1 is also a physically-impossible negative mass.
- idx13/14 payload CoG xy: hardcoded +-0.17 was stale from the old 0.15 m disk radius; DR radius was cut to 0.08 (2026-04-19) -> encoder used only half the normalized range.

FIX (exp/dr-derived-norm-bounds 87b80b0): derive_priv_obs_bounds_from_dr(dr_cfg, ocean_max_velocity, thruster_cfg, hydro_cfg) in envs/main/utils/priv_obs_bounds.py computes all 27 bounds from the DR config + asset base values, bound = DR range EXACTLY (margin 0). Injected by ConstraintEncoderRunner.__init__ (same pattern as num_constraints auto-sync), guarded on encoder-key presence + thrusters!=None. Base physical values are read from the LIVE env cfg (hydro_cfg=env_cfg.hydrodynamics), NOT a fresh default, else base becomes a second drift source. A terminal _assert_bounds_match_dr() fails loud if a future DR change desyncs the bounds (re-drift guard).

5 derivation forms: scale (base*range, e.g. body_mass 9.18*[0.75,1.25]), offset (base+range, idx3 CoG_z base=-0.05 NOT 0), direct (range as-is: payload_mass, joint Kp/Kd, water_density absolute -- do NOT multiply by 998), derived-other (cog xy radius->+-r; ocean strength_hi*max_velocity->+-max, SYMMETRIC not one-sided), measured (idx24-26 lin_vel fixed [-1,1], no DR field).

WHY NOT DORAEMON dynamic stats: rejected. DORAEMON Beta(a,b) get_stats() gives closed-form mean/std but (a) updating norm bounds every 250-step curriculum step reintroduces z-drift/KL-spike (the exact thing static avoids; curriculum WIDENS so drift is structural), (b) DORAEMON covers only 16/27 dims (joint gains + measured vel need static anyway).

IMPACT: changes encoder input normalization for the buggy dims -> NOT byte-identical even with DR unchanged -> needs from-scratch retrain (batched under sim-to-real audit B1). Old constants kept as fallback (student/teacher.py still import them; migration is a follow-up). Spec: docs/plans/2026-06-30-dr-derived-priv-obs-normalization-bounds.md

