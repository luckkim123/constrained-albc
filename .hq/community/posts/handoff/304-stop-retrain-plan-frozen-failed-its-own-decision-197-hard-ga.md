# STOP: retrain PLAN frozen — failed its own decision/197 HARD-GATE; vertical TAM may be on the WRONG AXIS

- id: handoff/304 · date: 2026-09-03 · author: session-mac
- harness: omo · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: none
- topic: decision
- confidence: high · status: none
- verified: none
- summary: PLAN frozen, not launchable: 2 of 4 decision/197 HARD-GATE items were silently missing (IMU 45deg frame entirely; vertical TAM redesign mis-framed). finding/255 correction says m0=3oclock m3=9oclock (two motors, left-right) so the sim My=+-0.145 pitch coupling may be on the wrong axis. Verify that FIRST.

Session end 2026-09-02 late. The merged PLAN is FROZEN and must not be queued. The user caught what the
plan missed by asking "what about the coordinate frame?" -- they were right.

WHAT WENT WRONG
decision/197 is the OPEN-ACTIONABLE LEDGER: "read before any sim-plant code change or baseline launch",
rule = reconcile the DESIGN delta against its HARD-GATE table and either apply each open item or record
"this baseline is pre-<item>". The plan did neither. That ledger exists because decision/155 already
happened once: teacher_baseline_opt + e1-e4 trained on a plant the record knew was wrong.

HARD-GATE reconciliation still owed:
1. TAM horizontal 3-row rewrite + ESC permutation -- APPLIED (3bb042b). Plan carries it. OK.
2. TAM vertical row (Fz/My) redesign -- measured, NOT applied. Plan mis-framed it as "My value is
   over-estimated" instead of the recorded redesign (single-heave-DOF, left-right placement).
3. IMU 45 deg mounting offset + pitch negation -- sim-UNCOMPENSATED. MISSING FROM THE PLAN ENTIRELY.
   finding/154: sim consumes root_ang_vel_b ground truth and applies no rotation/negation. The user's own
   2026-07-20 decision on that page: "the frame correction WILL be applied to sim ... keep the
   needs-apply-before-retrain flag so a reference retrain cannot silently skip it."
4. TAM moment-arm + max_thrust DR band -- max_thrust applied (0.85,1.15); moment-arm NOT applied.

WHY THE MACHINE GATE MISSED IT (mechanism, so it does not repeat)
Items 2-4 were supposed to be enumerable via status:needs-apply-before-retrain, with omx queue-launch
refusing until applied or --ack-gate'd. The 2026-08-05 backlog-closeout flipped their statuses to
resolved while their BODIES still say deferred-not-done. So `hq query --status needs-apply-before-retrain`
returns finding/264 only, and a status-based enumeration under-reports by 3 items. Status field and body
disagree. Read decision/197's table directly; do not trust the status query alone.

TOP PRIORITY TOMORROW -- verify before touching anything else
finding/255 carries a 2026-08-13 CORRECTION refuting its own headline:
- m0 and m3 are NOT one motor. Two separate thrusters, m0 = 3 o'clock, m3 = 9 o'clock (gripper = 12),
  measured with b1_channel_probe.py, recorded in deployed_tam.json.measured_channel_map. m3 is DEAD.
- Therefore config.py's TAM header comment "real robot is one motor, dual-ESC" is STALE/refuted. Do not
  cite it (an earlier draft of the plan did).
- Therefore G0-G (m0/m3 motor identity, robot check) is ALREADY ANSWERED -- drop it as redundant.
- LEAD, NOT YET CONFIRMED: a 3-o'clock/9-o'clock pair is LEFT-RIGHT. Differential drive of a left-right
  vertical pair produces ROLL (Mx), not PITCH (My). The sim TAM gives that pair My = +-0.145, a FORE/AFT
  pitch coupling. If the geometry is left-right, the sim's vertical differential moment is on the WRONG
  AXIS -- i.e. the incumbent learned "pitch" from an actuator that physically rolls the vehicle. This was
  inferred from the clock positions; deployed_tam.json.measured_channel_map has NOT been read directly.
  Confirm first. It changes D-1, the entire pitch narrative, decision 11, and possibly whether the
  retrain's stated justification survives at all.

STATE: PLAN.md carries a STOP banner with all of the above, program-lint clean, nothing launched, nothing
queued, nothing approved. Decisions already taken by the user this session and still valid: generalized
fault DR (not special-cased on the deployed pattern), final teacher trains on the WORKSTATION (recorded
departure from the objective's "ksm-nas"), incumbent 10 IPO constraints held unchanged with thruster_util
binding measured at G0-C. Prior handoff: handoff/303 (cross-vendor BLOCK review).
## Comments
