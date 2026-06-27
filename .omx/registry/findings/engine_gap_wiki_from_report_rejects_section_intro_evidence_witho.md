---
title: "engine-gap: wiki --from-report rejects section-intro [EVIDENCE] without [FINDING]"
tags: ["engine-gap", "wiki", "exp-analyze"]
created: 2026-06-27T09:04:34.517481
updated: 2026-06-27T09:04:34.517481
sources: ["diagnose-20260627-175826"]
links: []
category: decision
confidence: medium
schemaVersion: 1
---

# engine-gap: wiki --from-report rejects section-intro [EVIDENCE] without [FINDING]

[ENGINE-GAP] omx wiki add --from-report aborts with 'orphan or malformed evidence/confidence tag with no open [FINDING]' when a section opens with a context [EVIDENCE: ...] line before any [FINDING] (a common report convention here: a section-intro EVIDENCE that introduces a table, then [FINDING] blocks follow). [WHERE] the candidate-extraction parser in the omx wiki add --from-report path (omx_core wiki extractor, the [FINDING]/[EVIDENCE]/[CONFIDENCE] state machine) -- it treats any [EVIDENCE] with no currently-open [FINDING] as malformed instead of as section context. [SPEC] allow a leading/standalone [EVIDENCE] line that is not attached to a [FINDING] (treat as section context, skip it for candidate extraction) rather than aborting the whole extraction. [EVIDENCE] this analysis (diagnose-20260627-175826) -- report.md passed report-coverage ok:true but --from-report could not parse it, so wiki capture was done manually. [STATUS] proposed.
