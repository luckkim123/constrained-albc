# Program retrain-simtoreal-2026-09 opened: teacher retrain on the real actuator set (m3 dead, m4 excluded) + control_delay (0,1) — pending user approval, 10 decisions listed

- id: decision/301 · date: 2026-09-02 · author: ksm-mac
- harness: omo · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: none
- topic: decision
- confidence: high · status: needs-experiment
- verified: none
- summary: 2026-09-02: after vault finding/137 showed the incumbent learned pitch from the vertical thrusters (14.5 Nm) and never saw the real m3+m4-dead plant (2-dead exposure 1/30,000 per episode), a retrain program was opened at .hq/community/programs/retrain-simtoreal-2026-09/PLAN.md. Config delta vs incumbent is exactly two knobs (fault.thruster_fixed_health=[1,1,1,0,0,1]; control_delay_steps=(0,1)), 10000 iter, >=2 seeds, 4096 envs, everything else byte-identical; no new constraint or shaping. Phase 0 desk gates (G0-A fixed-health eval of the incumbent, G0-C paired 500-iter feasibility probe) precede any launch. Ten [DECISION-REQUIRED] items await the user, incl. whether a DGX-trained teacher may be deployed (the +109% machine-isolation caveat rests on one same-seed pair inside the 56% seed floor).

See `programs/retrain-simtoreal-2026-09/PLAN.md` (lint clean). This post records that the program exists and is unapproved; the plan itself is the SSOT for its content. Grounds are cited there per row: vault `finding/137` (pitch = deploy-configuration gap; reallocate() drops My), `posts/finding/264` (control_delay (0,1) decision + paired gate), `iter_budget/README.md` (saturation 7748; 5000 leaves 0/21 dims), `posts/decision/236` (seed floor 56 %), `posts/decision/048`/`finding/183` (machine-isolation caveat and its n=1 basis), `posts/decision/209` (plant-v2 stays gated), codex code inventory (`thruster_fixed_health` honored on the training reset path: `_reset_idx → _reset_physics → sample_thruster_health → set_thruster_health`).

Not decided here: everything under `## Decisions for the user` in the plan.
## Comments
