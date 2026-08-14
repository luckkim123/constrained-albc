---
title: "omx wiki page grammar for this workspace: title, category, body sections, and what a merge can never change"
tags: ["omx", "wiki", "convention", "grammar", "style", "curation", "meta", "links", "slug", "truncation", "cross-store"]
created: 2026-08-14T06:43:07.024045
updated: 2026-08-14T06:47:57.120496
sources: ["wiki-curation-2026-08-14"]
links: ["page_0000b26e.md"]
category: convention
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# omx wiki page grammar for this workspace: title, category, body sections, and what a merge can never change

One page = one durable claim, written so the next session can act on it without reopening the source.
This page is the format contract; it was written during the 2026-08-14 curation pass from what the
best existing pages already did, plus what omx_core actually enforces.

WHAT A MERGE CAN NEVER CHANGE (verified in omx_core/wiki/ingest.py, 2026-08-14). Re-adding under an
existing title APPENDS a dated Update block; it does not rewrite the page. On that path:
- title and slug           FROZEN (`slug=storage.title_to_slug(title)`, `title=existing.title`)
- category                 FROZEN (`category=existing.category`) -- a re-add with a new category is a no-op
- created                  FROZEN
- confidence               MAX-RANK wins (a higher-confidence re-add promotes; a lower one cannot demote)
- status / blocked_on      EXPLICIT WINS, None KEEPS (so a capture stub never clobbers a flag)
- tags / sources / links   UNION
- content                  APPENDED VERBATIM, with no equality check
Consequence: the title and the category are one-shot decisions. Get them right at creation, because the
only way to change either is a gc DELETE followed by a fresh add. Everything else is repairable in place.

TITLE -- the retrieval key, and permanent.
- State the CLAIM, not the topic. "roll regresses under hard DR" is a topic; "roll ss_error doubles
  soft to hard while CV stays flat, so the tail is DC bias not outliers" is a claim.
- One sentence, sentence case, no trailing period, aim for 60-120 characters. Measured 2026-08-14 the
  curated median was 123 and the maximum 373 -- titles that long are abstracts and they truncate in
  every listing.
- Write it run-INDEPENDENT. A title naming one run id ages the moment the next run lands.
- `engine-gap: ` (lowercase, colon, space) is the ONE reserved prefix, established by 14 pages. There
  is no other prefix vocabulary -- do not invent `DECISION:` / `INCIDENT:` / `OPEN:`; the category
  field and the body carry that.

CATEGORY -- exactly eight exist and omx_core rejects anything else:
architecture, decision, pattern, debugging, environment, session-log, reference, convention.
In this workspace they mean:
- pattern     a recurring metric BEHAVIOUR (the shape a run takes)
- debugging   a diagnostic PROCEDURE that worked
- decision    why something was adopted or discarded, with the data that decided it; also engine-gap specs
- reference   a stable threshold, formula, or measured fact
- convention  how this workspace operates (protocol, naming, launch discipline)
- session-log RESERVED for auto-capture stubs. Never author one by hand.
`environment` is reserved for the auto-synced `profile` page. `architecture` is unused here.

BODY -- conclusion first, then labelled sections.
Line 1 is the conclusion in one sentence. After that use ALL-CAPS labels on their own line, from this
vocabulary, in this order, including only the ones that apply:
MECHANISM / EVIDENCE / CONSEQUENCE (or CONSEQUENCES) / RULE / SCOPE / WHAT THIS DOES NOT CHANGE /
RELATED / SOURCE.
- EVIDENCE carries numbers WITH the code-exec source that produced them -- `file.py:line`, a
  `summary.json` field path, or the `analysis_id` and report section. A number with no traceable source
  is the classic re-read cost this wiki exists to remove.
- SCOPE and WHAT THIS DOES NOT CHANGE are what stop a page being over-applied later. Use them whenever
  the claim holds only for one run type, one plant, or one protocol.
- engine-gap pages keep the harness block instead of the free-form sections:
  `[ENGINE-GAP] [WHERE] [SPEC] [EVIDENCE] [STATUS]`, status one of proposed / implemented.

DO NOT carry report grammar into the wiki. `[EVIDENCE: ...]` and `[CONFIDENCE: ...]` are report.md's
single-line triplet format; in the wiki the frontmatter `confidence:` field owns confidence and the
EVIDENCE section owns evidence. The only pages here that use the bracket form are auto-capture stubs.

STATUS is a decision on every page, not an optional field. Four mechanisms read it and nothing else
writes it: `queue-launch` refuses on an open needs-apply-before-retrain, the route hook injects the open
roster, and exp-design / exp-loop enumerate it. Omit it for settled knowledge (most pages);
`needs-experiment` for an untested lead; `needs-apply-before-retrain` ONLY for a fact that invalidates
dependent runs; `resolved` to close a lead, re-added under the SAME title.

NEVER hand-write or hand-edit a page file. Always `omx wiki add`; removal and merging are
`omx wiki gc` then `omx wiki gc-apply`. The CLI validates category, holds the wiki lock, regenerates the
index, and appends the log; a hand-written file does none of that. Three pages in this wiki carried
`category: sim2real` -- a value omx_core rejects -- precisely because they were written by hand, and
they had to be deleted and re-added to be fixed.

RELATED: omx wiki has no delete subcommand by design; constrained-albc experiment conventions.

---

## Update (2026-08-14T06:47:57.120496)

LINK RULES, added 2026-08-14 after auditing the five broken refs this wiki carries. Every one of them
is one of three failure modes, and all three are avoidable at write time.

1. NEVER hand-type a wiki link -- COPY THE SLUG. Slugs are TRUNCATED at 64 characters (244 of this
   wiki's 264 slugs are exactly 64), so a slug frequently ends mid-word or on a bare underscore. The
   page `an_off_doraemon_channel_that_costs_return_stalls_the_curriculum_` ends in a trailing
   underscore that a human retyping the title naturally drops, and the link then resolves to nothing.
   Get the string from `omx wiki list` or `omx wiki query` output, never from the title.

2. NEVER link to an auto-memory file. Three broken refs here point at
   `albc_cudnn_fix_is_a_library_path_not_a_package`, `feedback_read_metric_units_from_code` and
   `feedback_derive_a_metrics_healthy_target`. Those are real files -- but they live in
   `~/.claude/projects/-workspace/memory/`, are named with HYPHENS, and are a different store
   entirely. A `[[...]]` in an omx wiki page can only ever resolve to an omx wiki page. If the
   knowledge matters here, write it here; cite the other store in prose, not as a link.

3. A LINK IS NOT REPAIRABLE IN PLACE. `links` is extracted from content and UNIONED on merge, so a
   broken target can never be removed -- only a correct sibling link can be added next to it. That
   makes link accuracy a write-time obligation, not something to clean up later.

SLUG-TITLE ALIGNMENT. The slug is always `title_to_slug(title)` when the CLI creates the page, so slug
and title agree by construction. They can only disagree on a hand-written file, and when they do a
re-add under the true title FORKS a new page instead of merging into the existing one. Two of the
three hand-written pages found in this pass had exactly that drift: their filenames did not match
their own `title:` field, so both were re-created at their correct title-derived slugs during the
2026-08-14 curation. If you ever find a page whose filename is not the slugified form of its title,
that page did not come from the CLI and its merge behaviour is broken.

