---
title: "Real robot has 2 faulted thrusters; user judges buoyancy restoring dominates so baseline proceeds without FTC; thruster is in the actor output partly for gradient-vanishing avoidance (FTC under separate investigation)"
tags: ["thruster-fault", "hardware", "real-robot", "fault-tolerant-control", "ftc", "user-decision", "deployment", "actuator-authority", "buoyancy", "gradient-vanishing", "handoff"]
created: 2026-07-24T08:43:11.395276
updated: 2026-07-24T08:43:11.395276
sources: ["user-report-2026-07-24"]
links: ["thruster_util_is_the_binding_constrainttrpo_constraint_in_7_of_7.md"]
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Real robot has 2 faulted thrusters; user judges buoyancy restoring dominates so baseline proceeds without FTC; thruster is in the actor output partly for gradient-vanishing avoidance (FTC under separate investigation)

Hardware reality + user standing decision recorded from a 2026-07-24 conversation. Factual capture only; the fault-tolerant-control (FTC) question itself is delegated to a separate session (handoff brief path below) and is NOT analyzed here.

[FINDING] The real ALBC vehicle currently has 2 of its 6 thrusters FAULTED (non-functional). This is the deployed state for near-term experiments; no repair is planned before them.
[EVIDENCE: user report 2026-07-24]
[CONFIDENCE: HIGH]

[FINDING] User standing decision (2026-07-24): proceed with the baseline AS-IS, WITHOUT a fault-tolerant-control mechanism, on the assessment that the vehicle is neutrally buoyant and its buoyancy RESTORING force dominates attitude stabilization, making the 2 thruster faults low-impact for the attitude-only task.
[EVIDENCE: user statement 2026-07-24]
[CONFIDENCE: HIGH -- user domain decision, NOT independently verified in sim]

[FINDING] Why the 6D thruster command is in the actor OUTPUT at all: an output dimension that is too small causes gradient vanishing, so the thruster action was included partly to keep the actor output dimension large enough -- a learning-dynamics purpose, not solely control authority. Removing/ignoring the thruster output is therefore not on the table.
[EVIDENCE: user statement 2026-07-24 (design intent)]
[CONFIDENCE: HIGH -- stated design intent]

[OPEN TENSION -- not resolved here] The teacher campaign found thruster_util is the SINGLE binding ConstraintTRPO constraint in 7/7 runs (the plant is actuator-authority-limited, policy runs thrusters near saturation). This is in DIRECT tension with "buoyancy dominates so thruster faults are low-impact": losing 2 of 6 thrusters attacks the already-binding bottleneck. Whether the buoyancy-dominance assessment survives the actuator-authority finding is UNSETTLED and is the crux of the FTC investigation. See [[thruster_util_is_the_binding_constrainttrpo_constraint_in_7_of_7]].
[CONFIDENCE: the tension is real; resolution pending]

[NEXT] Fault-tolerant control (FTC) as a possible addition is under investigation in a SEPARATE session. Handoff brief: /workspace/.sp/plans/2026-07-24-fault-tolerant-control-handoff.md (literature + web research, then wiki record + exp-design if warranted). Eval-design caveat (user-stated): no healthy-robot real-world control group exists (robot permanently in the 2-fault state), so any FTC benefit must be demonstrated via SIM fault-injection + real-robot demonstration, not a hardware A/B.

