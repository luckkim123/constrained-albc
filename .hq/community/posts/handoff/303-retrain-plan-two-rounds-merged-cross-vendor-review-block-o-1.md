# retrain PLAN: two rounds merged + cross-vendor review BLOCK → O-1..O-4 open

- id: handoff/303 · date: 2026-09-02 · author: session-mac
- harness: omo · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: none
- topic: decision
- confidence: high · status: none
- verified: none
- summary: Round1+Round2 merged into one PLAN; codex adversarial review returned BLOCK (11 defects, code-confirmed); corrections applied, 4 tensions O-1..O-4 left for the user; nothing launched.

Two planning rounds were merged into the single PLAN.md (retrain-simtoreal-2026-09), then adversarially
reviewed cross-vendor (codex, ground 4 — the Mac session is Opus so oracle=opus-5 would be self-approval).

VERDICT: BLOCK. 11 ranked defects, the code-level ones independently confirmed against source
(faults.py:sample_thruster_health, constraints.py:thruster_utilization_cost, albc_env.py:_reset_physics).

Corrections FOLDED IN (verifiable in the PLAN):
- Phase 0 relabeled honestly: G0-C/G0-D are training/DGX launches (go through omx queue-launch), not "desk/zero-GPU".
- G0-E made observational only; the earlier "raise the J1 penalty weight" lever REMOVED (no such knob; it is new shaping, violates constraint 1).
- Fault sampler reframed as a DESIGN task (O-3), not a ~10-line edit: needs a zero-health atom, must keep severity=0->all-healthy, and must mass the deployed (m3,m4) pattern (m4 is a STRUCTURAL exclusion, not a random pair). Recommendation shifted A->C.
- Vertical-TAM: DR band is NEW code (no moment-arm DR in _reset_physics) and no measured value exists -> nominal-if-measured / defer, not "DR band now".
- Control-rate: Phase 0-R settles only incumbent-DECIMATION on the robot, not the retrain rate (D-6); retrain stays 50 Hz unless a screening arm S3 shows a gain.
- Exam vector 1,1,1,0,0,1 decoupled from G0-G (valid regardless of motor topology); G0-G gates only the TAM My-row correction.

OPEN before approval (the user decides -- surfaced, not silently resolved):
- O-1: do the incumbent's 10 IPO barrier constraints themselves count as rule-based shaping? (keep as-is for attributability vs redesign)
- O-2: thruster_util (0.82-0.93 of budget) will likely BIND under heavier fault mass -> penalizes the survivors' extra work -> teaches thrust under-use (anti-FTC). If it binds, no resolution compatible with constraint 1 without a decision.
- O-3: fault-sampler shape (recommend C: explicit (m3,m4) mass) -- needs a small design pass + tests before G0-C.
- O-4: DGX vs workstation for the FINAL deployed teacher (training-machine risk unresolved; recommend workstation-final).

program-lint clean. Nothing launched, queued, or approved. Local review artifact: Mac scratchpad review-codex-out.txt.
## Comments
