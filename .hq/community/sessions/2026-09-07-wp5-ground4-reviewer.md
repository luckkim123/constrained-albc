# 2026-09-07 — WP5 ground-4 reviewer ran NATIVE, not through the vendor lane

- session: ksm-ubuntu container, code-cleanup `cleanup/2026-09`
- harness: omo · ground: 4 (adversarial verification)
- worker: native `Agent` (`oh-my-claudecode:critic`, opus), fresh context, did not author the diff
- artifact under review: staged WP5 diff, 80 files / 104 insertions / 4612 deletions

## Why it is not in the codeagent-wrapper ledger

The plan assigns WP5's review to codex (ground 4). The dispatch was built and fired:

    codeagent-wrapper --agent oracle --backend codex --ground 4 - <repo> < wp5_review_prompt.txt

It failed in 3 s with `turn.failed`:

    You've hit your usage limit. Upgrade to Pro (https://chatg...
    codex exited with status 1

`codeagent-wrapper v0.23.0` and `codex` are both on PATH, so this is an ACCOUNT limit,
not a missing backend. `claude` is on PATH but the omo `oracle` role is bound to
`claude-opus-5`, which is this session's own model — routing there would have been a
session consulting itself, and ground 4 would not have been satisfied.

## What that costs, stated plainly

**Cross-vendor model diversity was not available on this machine at this time.** The
review that ran is a fresh-context reviewer of the SAME model family as the author. It
satisfies "did not author this" (no anchoring on the author's reasoning) but not "a
different model's prior". Anyone re-reading WP5 later should treat the vendor axis as
unverified, and re-run the codex pass once the account limit resets.

## Prompt

`scratchpad/wp5_review_prompt.txt` (the codex packet) was reused verbatim as the native
brief, plus the degraded-mode channel rule: write the report to a file and return only the
path, because a subagent's inline result truncates near 4 KB.
