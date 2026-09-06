# G6 premise is false: pair34_d2 exists on 13 arms and finding/363 already read it -- finding/360 was superseded the same day and the PLAN inherited the superseded one

- id: finding/404 · date: 2026-09-07 · author: ksm-mac-session
- project: albc · harness: omx · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: finding/360
- topic: reference
- confidence: high · status: needs-experiment
- verified: 2026-09-07 · keywords: G6, pair34_d2, additivity, negative-claim, finding360, finding363, exam
- summary: The PLAN G6 row said fault and delay have never been scored together, citing finding/360. One ls refutes it: ls -d .hq/work/p4/*/pair34_d2 returns 13 arms (inc13w, p3b_7500, p3b_final, sd_inc9998, sd_p3b7500, sd_r1, sd_r2, sd_r3a, sd_r3a_envdr, sd_r3b, sd_r4a, sd_r4a999, sd_r4c). And finding/363 (2026-09-05, confidence high) already scored pair34_d2 on three arms and found the stressors NON-additive -- the incumbent overshoots its own additive prediction by 7.232 deg and sits at 9.360 deg in the exact deployment condition while both retrained checkpoints match theirs. What survives in G6 is only its second half, the two resonance regimes (policy-generated vs externally excited, finding/158). General shape: a plan row asserting X has never been done is a negative claim needing the same evidence as a positive one.

The PLAN's G6 row read: "Add a `pair34_d*` exam config. **Fault and delay have never been scored
together** although the robot has both", citing `finding/360`. Both halves of that are wrong, and
the record that corrects them is from the same day as the one it cites.

**The config exists and has been run on 13 arms.** `ls -d .hq/work/p4/*/pair34_d2` returns
`inc13w`, `p3b_7500`, `p3b_final`, `sd_inc9998`, `sd_p3b7500`, `sd_r1`, `sd_r2`, `sd_r3a`,
`sd_r3a_envdr`, `sd_r3b`, `sd_r4a`, `sd_r4a999`, `sd_r4c`.

**And it has already been read.** `finding/363` (2026-09-05, `confidence: high`,
`status: needs-experiment`) scored `pair34_d2` — m3 dead, m4 excluded, plus two control steps of
observation delay, i.e. the condition the robot actually flies in — on three arms and found the two
stressors **non-additive**: the incumbent overshoots its own additive prediction by 7.232 deg and
sits at 9.360 deg in that exact deployment condition, while both retrained checkpoints match theirs.
Measured apart the incumbent merely looks worse; measured together it is somewhere else entirely.

So `finding/360`, which says the two had never been scored together, is **superseded by
`finding/363` of the same day**, and the PLAN inherited the superseded one.

What survives in G6 is only its second half, which is genuinely open: score the two resonance
regimes separately — policy-generated (thrust off) and externally excited (thrust on) —
because `finding/158` measures them as different (thrust A: 0.5837 Hz, roll-band share 0.115 at
10 Hz, where the policy-only 10 Hz run sat at 0.030), and `decision/159` 결정 1 explicitly defers
the phase-margin trade to that split.

General shape of the defect, worth carrying: a plan row that says "X has never been done" is a
negative claim and needs the same evidence as a positive one. Here one `ls` refuted it. The row had
been read and re-read across several revisions without anyone running that `ls`, because the citation
looked like evidence.
## Comments
