---
title: "A one-variable retrain must be verified against the BASELINE RUN's recorded config/env.yaml, not against the committed git diff -- a baseline launched dirty hides plant flags from every source-level check"
tags: []
created: 2026-08-03T19:54:01.344116
updated: 2026-08-03T19:54:01.344116
sources: []
links: []
category: convention
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: resolved
---

# A one-variable retrain must be verified against the BASELINE RUN's recorded config/env.yaml, not against the committed git diff -- a baseline launched dirty hides plant flags from every source-level check

## The failure

obs4 Phase D attempt 1 (`trpo_obs76_s30_260803_233239`) was launched as a declared one-variable
experiment against the E-int teacher. Its launch note recorded the verification as: "E-int's
commit (7e6dab9) is an ancestor of this branch and the committed env-config diff since it is
insertions only, with max_thrust_scale (0.85, 1.15) on both sides (gate D-a)."

That check was performed correctly and still missed a plant difference. E-int's manifest records
`git.dirty: true`. Its `fault.enable: true` therefore came from an uncommitted working-tree edit
or a CLI override, and NO source-level diff -- however carefully scoped -- can see it. The run
trained without the thruster fault-DR the campaign had ADOPTED on 2026-07-27, so its H1 verdict
is uninterpretable.

## The check that actually works

Diff the two runs' RECORDED configs, which are written at startup and capture overrides, dirty
edits and defaults alike:

    diff <(grep -vE '^\s{6,}[A-Za-z0-9+/=]{20,}$|^log_dir:' <baseline>/config/env.yaml) \
         <(grep -vE '^\s{6,}[A-Za-z0-9+/=]{20,}$|^log_dir:' <new>/config/env.yaml)

The two `grep -v` filters are load-bearing: `env.yaml` embeds the observation noise model as
base64 pickle blobs that change with obs width, and `log_dir` always differs. Without stripping
them the real differences are buried in blob noise -- which is how a truncated `head -60` view of
this same diff showed the obs-width entries and stopped one screen short of `fault.enable`.

Read the ENTIRE diff. Never `head` it.

## Rule

Before launching any experiment whose claim is "one variable versus run X":
1. Diff `X/config/env.yaml` against the config the new run WILL write -- or, if that is not
   available pre-launch, launch, then immediately diff the recorded configs and kill the run if
   an unintended key appears. A 2-minute check beats a 5-hour void result.
2. Enumerate every remaining difference explicitly in the launch note, as a table, and mark each
   one intended or not.
3. Treat `git.dirty: true` on the BASELINE as a hard signal that source-level verification is
   insufficient for that pairing.

Attempt 2 (`trpo_obs76fault_s30_260804_043926`) added `env.fault.enable=True` and was gated on a
bite check: its recorded config carries `fault: enable: true` and the full stripped diff against
E-int reduces to the obs-width entries plus the 6 gen-2 keys. Nested Hydra-style overrides DO
reach nested config dataclasses; that was verified from the recorded config rather than assumed.

Related: the 2026-07-14 incident where teacher_baseline_opt + e1-e4 trained on a known-wrong TAM
is the same class -- a plant belief that was never checked against what the run actually loaded.

