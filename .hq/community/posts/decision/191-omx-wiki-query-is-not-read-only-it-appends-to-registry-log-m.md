# omx wiki query is not read-only: it appends to registry/log.md, so a pure lookup leaves the tree dirty

- id: decision/191 · date: 2026-08-22 · author: wiki-form-conversion
- harness: omx · to: all
- subject: omx-wiki-query-is-not-read-only-it-appends-to-registry-log-m · supersedes: none
- topic: convention
- confidence: high · status: none
- verified: 2026-08-22 · keywords: tooling, side-effect, git-hygiene, registry
- summary: omx wiki query is not read-only: it appends to registry/log.md, so a pure lookup leaves the tree dirty

Measured 2026-08-22. Two `omx wiki query` calls (`history length`, `dgx16k`) each appended a
timestamped block to `.omx/registry/log.md` -- pages listed plus a one-line summary. No page was
written and no knowledge changed; both were lookups.

WHY IT MATTERS: a session that only READS the wiki still comes back to `git status` showing
`M .omx/registry/log.md`. That reads as uncommitted work and invites either a needless
investigation or a reflexive `git checkout --` that throws the log away.

THIS IS NOT A DEFECT TO FIX. `log.md` is 10,736 lines and tracked on purpose -- it is the audit
trail of wiki operations, and gitignoring it would delete that history from git. Correct handling
is to commit the appended lines with whatever else the session did, or as a trivial follow-up.

WHAT NOT TO DO:
- Do not add `.omx/registry/log.md` to `.gitignore`.
- Do not `git checkout --` it to "clean up" -- that discards the record of which queries ran.
- Do not read a dirty `log.md` as evidence that a prior session left work unfinished.

RELATED, same family: the tokensave CLI rewrites `~/.claude/settings.json` on plain verbs like
`status` and `sync`. Both are cases where a verb that reads like a query mutates state, and both
are caught only by diffing before and after, never by an error.

## Provenance (carried from the omx wiki frontmatter)

- qualityScore: 100
## Comments
