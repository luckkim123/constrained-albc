---
title: "engine-gap: omx CLI/skill gaps found during dr-harder reporting (2026-06-06)"
tags: ["engine-gap", "omx-harness", "cli-bug", "exp-analyze", "wiki", "session-id"]
created: 2026-06-06T08:50:03.836890
updated: 2026-06-06T08:50:03.836890
sources: ["diagnose-20260606-173330"]
links: []
category: decision
confidence: high
schemaVersion: 1
---

# engine-gap: omx CLI/skill gaps found during dr-harder reporting (2026-06-06)

Four omx HARNESS gaps surfaced writing the dr-harder per-run reports (these are omx-core/skill bugs = fix in ~/oh-my-experiments, NOT workspace-specific). 

[ENGINE-GAP 1] omx session-id (argless) crashes with TypeError: 'str' object is not callable. [WHERE] omx-core session-id verb autogen branch. [SPEC] argless call must hit the autogen fallback the exp-analyze SKILL.md advertises ('flag>env>autogen') and print a fresh id; --session-id X works so the bug is autogen-only. [STATUS] proposed.

[ENGINE-GAP 2] No 'omx wiki read --slug' verb; only add/query/lint/list. query returns truncated snippets, so reading a known page full-text forces a hardcoded read of .omx/registry/findings/<slug>.md (bypasses omx_paths getter). [WHERE] omx-core wiki subcommand. [SPEC] add 'omx wiki read --slug <slug> [--root]' returning full page via getter, loud-fail on missing slug. [STATUS] proposed.

[ENGINE-GAP 3] omx wiki add --from-report rejects multi-line [FINDING] blocks: it requires the line immediately after [FINDING] to be [EVIDENCE:], so a [FINDING] whose claim wraps across 2 lines (normal readable prose) makes it exit 2 with 'not followed by [EVIDENCE'. [WHERE] omx-core report.parse_findings / wiki from-report extractor. [SPEC] lookahead to the next non-empty [EVIDENCE:] line within the block instead of requiring the very next line; a readable report should not break auto-capture. [EVIDENCE] diagnose-20260606-173330 teacher report.md has 6 multi-line [FINDING] blocks; --from-report printed 0 candidates + exit 2. [STATUS] proposed.

[ENGINE-GAP 4 — SKILL, highest value] exp-analyze does NOT enforce metrics.yaml vocabulary completeness: a report can cover only a slice of the profile vocabulary (eval-side) and skip training-dynamics (constraint margins/viol, TRPO line_search/kl/surrogate, critic value/cost_value, reward 8-term decomposition, gradient liveness) and still pass. The profile comments are diagnostic INSTRUCTIONS ('total plateau is diagnosed by decomposition not Reward/total alone', 'cost_value: if it does not converge constraint advantages are noise'), not a passive list. [WHERE] exp-analyze SKILL.md (a vocabulary-coverage step) + optionally omx report-parse (a coverage lint). [SPEC] after drafting report.md, check which metrics.yaml diagnostic tokens are referenced; if training-dynamics groups are absent, require justification or addition. Caught live: first-pass dr-harder reports referenced ~4 training scalars of 44 TB vocabulary tokens; user flagged 'metrics보다 확연히 적다'. [STATUS] proposed.
