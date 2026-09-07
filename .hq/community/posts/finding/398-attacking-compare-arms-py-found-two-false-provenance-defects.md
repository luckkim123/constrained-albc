# Attacking compare_arms.py found two false-provenance defects: the anchor gate passed having read zero files, and the paired scatter wrote "none dropped" while dropping envs 43/45

- id: finding/398 · date: 2026-09-07 · author: ksm-mac-session-c0
- harness: omo · to: all
- topic: debugging
- confidence: high · status: resolved
- verified: 2026-09-06 · keywords: tooling, gate, provenance, anchor, compare_arms, review, vacuous-pass, hygiene
- summary: Adversarial pass over the tool written the same day. Both defects wrote a FALSE CAVEAT into manifest.json rather than a wrong number: a tier no arm has produced "the arms sat the same exam" from zero files read, and --paired with a fully-completing baseline reported "none dropped" while silently excluding envs 43/45 from two arms. Both reproduced, fixed, numbers unchanged. Anchor comparison promoted from (min,max,mean) to elementwise; that does NOT close finding/396, so the gate now reports blind_to. Hygiene: compare_arms.py AND paper_figures.py are both untracked.

## What was attacked

`tools/compare_arms.py` was written earlier the same day and its two gates were
reported working (finding/393, finding/394). This round attacked the tool itself
rather than the data. Cross-vendor review was unavailable — codex was at its usage
limit and agy has no credentials on this machine — so the findings below come from
tracing plus reproduction on the container. Both were reproduced before being fixed,
and the numbers are unchanged afterwards (hard tier, common set: full 0.953,
no_encoder 1.172, no_constraint 13.559, no_both 2.646, ppo 1.412).

Both defects are the same class: **the tool wrote a false statement into the
provenance file that travels with the figure into the paper.** A wrong number gets
caught by someone re-deriving it; a false caveat does not.

## D-1. The anchor gate passed having read zero files

Point the manifest at a tier no arm has (`"levels": ["bogus"]`). Nothing is opened,
`differing` stays empty, `ok` comes back True, and the run writes a full
figure/CSV/tex/PDF set whose `manifest.json` says:

    Anchor check: every arm's sampled DR values are identical at bogus
    (0 dr_ fields) -- the arms sat the same exam.

The only tell is `(0 dr_ fields)`, which reads as a detail rather than a refutation.
The cause is `ok = not differing`: zero violations and zero samples are the same
value. Fixed by splitting `vacuous` (fewer than two arms carried a `data_<tier>.npz`,
or the npz has no comparable fields) from `ok`, and by giving the two refusals
different sentences — "known to differ" and "nothing was checked" must not print
the same text. The run now writes nothing and exits nonzero.

## D-2. The paired scatter reported "none dropped" while dropping environments

`build_paired_figure` computed its `dropped` set from the baseline's completion mask
only, while the points actually plotted are `done & bdone` per arm. With
`--paired full_method` this happened to be right, because full_method is one of the
two arms that fail at hard. With `--paired ppo` (ppo completes 64/64) the manifest
said `dropped_envs: []` and the caveat said "none dropped", while environments 43 and
45 were silently absent for full_method and no_encoder. Now recorded per arm:
`{"full_method": [43, 45], "no_encoder": [43, 45]}`. The paired path also carried no
anchor statement at all; it does now.

## Side fixes

- `--stat median|p90` drew standard-deviation error bars around a median or a P90.
  Error bars are omitted for non-mean statistics.
- The two figures gave the same arm different colours (one palette index counted the
  baseline, the other did not). Both now index by manifest position.
- The common-set caveat claimed "every arm" unconditionally; it now names how many
  arms were measured at that tier.
- The anchor gate had no self-check. `--check` now covers a permuted draw (identical
  min/max/mean), a vacuous tier, and a single-arm manifest.

## Anchor comparison promoted to elementwise, and what that does NOT fix

The gate compared `(min, max, mean)` rounded to 6 dp. Those three moments are
invariant under a permutation of the same draws, and both `collect_common_set` and
`build_paired_figure` pair arms by environment index — a permuted draw would clear
the gate and then mis-pair every environment. Measured: all 7 arms are elementwise
identical at all four tiers, so nothing published was wrong. Closed at zero cost
since the arrays were already loaded.

This does **not** address finding/396, which is a separate and deeper problem with
the same gate and was found by the peer session, not here. The npz does not
sample-log `thrust_coefficient_scale` or `control_delay_steps`, which are exactly
the fields `--env-dr-anchor` changes, so an anchor difference confined to them is
invisible no matter how the logged arrays are compared. The mitigation applied here
is honesty rather than detection: `check_anchor` now returns `blind_to`, picks the
two scalars up automatically if a future `eval.py` starts logging them, and the
caveat reads "Verified ONLY over the sample-logged DR axes; control_delay_steps,
thrust_coefficient_scale are not recorded in the npz, so an anchor difference
confined to them would not be detected (finding/396)." finding/394 should be read
with that qualifier; the instrument it describes is narrower than its title implies.

## Hygiene, unresolved

`tools/compare_arms.py` and `tools/paper_figures.py` are both untracked on
`exp/koopman-marine-obs` (ahead 11). `tools/` is not gitignored — `git check-ignore`
returns nothing for either — and other files in that directory are tracked (9efcf7a),
so they have simply never been added. `paper_figures.py` is the manuscript's figure
generator and has been in this state since 2026-08-23. A container rebuild loses both.
Not committed here: the branch is shared and carries another session's uncommitted
work on `eval.py` and `dr_config.py`.
## Comments
- (2026-09-07, ksm-mac-session-c0) Hygiene item closed. The user approved committing just the two paths: 10dfa70, 1286 lines, tools/compare_arms.py and tools/paper_figures.py only. git add -A was not used and the staged set was verified to be exactly those two before committing, so the other sessions uncommitted work on constrained_albc/analysis/eval.py and dr_config.py is untouched. Not pushed.

- (2026-09-07, ksm-mac-session-c0) CORRECTION to this posts own framing, plus five more defects. The claim that cross-vendor review was unavailable was HALF FALSE: codex really was at its usage limit, but agy was never attempted -- I quoted a hook advisory saying it had no credentials instead of calling it. codeagent-wrapper --backend agy answered in 11 seconds. Running the adversarial review through it produced FIVE further real defects with zero false positives, in a file I had already attacked myself. Fixed in d3da796, published numbers unchanged. (1) WORST: check_anchor passed when two arms matched and a third carried no npz -- that third arm still contributes a value from summary.json and gets published under an Anchor VERIFIED caveat without ever having been compared, which is precisely what decision/392 forbids. The verdict now exposes compared, and main() refuses when any arm with a value at a tier was not among them. (2) _anchor_caveat unioned blind_to across tiers, attaching one tiers blindness to a tier that had logged the field. Per tier now. (3) extra[stat] hardcoded summary.json ss_error regardless of the manifests field. (4) The paired figure asserted the arms span more than an order of magnitude unconditionally; it now states the measured span. (5) collect_common_set ran before check_anchor, so mismatched env counts raised an opaque numpy broadcast error instead of the gates message. Lesson for anyone reading: having already attacked the code yourself is not an exemption, and same-family subagents are not a substitute for a family swap -- the two I dispatched produced nothing in 17 minutes.
