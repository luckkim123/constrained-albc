---
title: "TAM vertical pair is one physical motor with dual-ESC wiring (measured 2026-07-05)"
tags: []
created: 2026-07-05T15:24:24
updated: 2026-07-14T09:55:52.971012
sources: []
links: ["tam_columns_must_match_robot_firmware_esc_channel_order_reorder_.md", "next_from_scratch_retrain_manifest_what_rides_on_the_post_tam_ba.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: needs-apply-before-retrain
blocked-on: "m4 remeasurement (HW fault) + full B1 vertical translation"
---

# TAM vertical pair is one physical motor with dual-ESC wiring (measured 2026-07-05)

Scope: envs/main + envs/full_dof TAM vertical channels (m0, m3). B1 watertank measurement session 3, 2026-07-05. Companion to [[tam_columns_must_match_robot_firmware_esc_channel_order_reorder_]] and the retrain manifest [[next_from_scratch_retrain_manifest_what_rides_on_the_post_tam_ba]].

MEASURED: m0 and m3 are physically the SAME single motor, dual-ESC wired (two ESC channels driving one physical thruster). Evidence: standalone-actuation test on each channel produces rotation of the same physical thruster -- m0 spins it at full/expected speed, m3 spins it only intermittently. The intermittent behavior on m3 is a hardware contact/wiring fault on that individual unit (loose connector or corroded contact), NOT a design difference between the two ESC channels -- i.e. this is a per-unit HW defect, not evidence that m0 and m3 are functionally distinct channels.

WHAT THIS REFUTES: the sim TAM models T4 and T5 as two INDEPENDENT heave channels -- each contributing Fz=1.0 (full authority) plus opposite-signed My=+-0.145 (pitch coupling), as if there were two physically separate vertical thrusters offset fore/aft. That assumption is physically wrong for this robot: there is one vertical thruster, wired to two ESC channels for redundancy/control reasons, not two independent thrusters that can be driven differentially.

TAM IMPLICATION (not yet applied -- code untouched pending full B1 completion): the Fz row currently has independent authority on both m0 and m3 columns; physically there is only one heave DOF, so commanding m0 and m3 differently does not produce two independent forces -- it produces contention/redundancy on the same physical actuator. The My (pitch) coupling terms on T4/T5 columns are also likely wrong as modeled, since they were derived assuming fore/aft-offset independent thrusters. Roll (Mx) differential control via this vertical pair is NOT physically achievable (no two independent vertical actuators to differential-drive). This is a TAM row/value rewrite candidate, not a column-permutation fix -- see the "columns only never rows" premise partially refuted in [[tam_columns_must_match_robot_firmware_esc_channel_order_reorder_]]'s 2026-07-05 checkpoint section.

POSITION (wasd frame, launch-agent w=forward convention): the vertical thruster pair is mounted LEFT-RIGHT (left/right side placement), not fore/aft. This means the sim's implicit fore/aft pitch-coupling model (My +-0.145 split across "front" and "rear" heave channels) is also positionally wrong -- there is no fore/aft vertical thruster separation on this hardware.

CAVEAT (do not conflate): m4's intermittent/faulty behavior (see the horizontal measurement in [[tam_columns_must_match_robot_firmware_esc_channel_order_reorder_]]'s checkpoint) is a SEPARATE per-unit hardware fault on a different (horizontal) channel -- unrelated to this vertical dual-ESC finding, and not evidence of a design flaw. Sim should still model a healthy actuator; unit-specific faults belong in FaultInjectionCfg, not the nominal TAM.

STATUS: measured, high confidence for the "one physical motor, dual-ESC" finding and the left-right placement. The exact TAM row rewrite (Fz/My values) is NOT yet implemented -- pending full B1 completion (translation axes, m4 remeasurement) before any config.py edit, per the "no premature TAM rewrite" constraint on this session.

---

## Update (2026-07-14T09:55:52.971012)

Flagged needs-apply-before-retrain 2026-07-14. Verified NOT applied: envs/main/config.py:93 Fz row (0,0,0,0,1,1) still models T4,T5 as two independent heave channels; header comment lines 86-88 confirm "OPEN (unchanged): Fz/My vertical rows ... redesign blocked on m4 remeasurement". Horizontal TAM (3bb042b) was applied piecemeal; this vertical row was NOT. Any from-scratch reference baseline must apply this together or explicitly record pre-vertical-TAM.
