# HANDOFF — retrain-simtoreal-2026-09

Opened 2026-09-02 22:40 KST from the Mac session (vault `ksm_Obsidian`, session 96be433c).

## State

- PLAN.md written and `omx program-lint` clean; **no gate has run, nothing is launched, nothing is approved.**
- Ten `[DECISION-REQUIRED: …]` items are listed in PLAN.md `## Decisions for the user`; the user was
  sent the plan by e-mail (luckkim123@postech.ac.kr) and in the Mac session on 2026-09-02.
- Phase 0 gates G0-A..G0-F are the first work; all run on this container via Orca `worker-start --on marinelab`.

## Where the inputs are

- Code inventory (codex, 493 lines) and the vault-side digest used to write the plan live in the Mac
  session scratchpad only; every fact they carried that the plan relies on is cited inline in PLAN.md
  to a post, program section, or `path:symbol`, so the plan stands without them.
- Incumbent as-run config: `logs/rsl_rl/albc_trpo_teacher/teacher_iter_budget/trpo_iterbudget_s30_260805_012813/params/{env,agent}.yaml`.

## Resume order

1. Read PLAN.md `## Decisions for the user`; do not run Phase 3 before every marker has an answer.
2. G0-A first (10 min, eval only), then G0-C (2 seeds × 500 iter paired, ~1 h on GPU0).
3. Post each gate readout as a `finding` on this board (`hq post … --subject retrain-simtoreal-2026-09`).

## Correction 2026-09-02 ~23:10 KST — the draft's design axis was rejected by the user; PLAN.md banner is the truth

Two corrections, verbatim in the PLAN.md `REVISION PENDING` banner: (1) FTC strengthening (faults as a distribution
incl. double loss; fixed health = eval instrument only; paper framing = fault-tolerant control validated on a robot with
real failures), (2) the vertical thrusters' pitch authority (`My ±0.145`) is over-estimated per the tank and must not be
re-taught as-is (moment-arm DR band and/or measured nominal; G0-G decides whether the row exists).

**Resume order (replaces the one above):** 1) read the banner, 2) rewrite Phase 1 / Tier 2 / Phase 2 arms / Phase 4
exam matrix / Predicted outcome / decisions 2, 10, 11 to the FTC axis, 3) re-lint, 4) then G0-A (still valid: it asks
whether the incumbent has ANY arm-pitch fallback) and G0-G. The Mac session compacted right after this note; its
scratchpad digests (codex code inventory, 10 corpus slices, 5 literature notes) are not on this machine — every fact the
plan relies on is cited inline.
