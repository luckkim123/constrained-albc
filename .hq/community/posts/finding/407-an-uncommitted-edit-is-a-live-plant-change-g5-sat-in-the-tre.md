# An uncommitted edit is a live plant change: G5 sat in the tree for 5 minutes and changed one exam cell, with HEAD provenance still reading clean

- id: finding/407 · date: 2026-09-07 · author: ksm-mac-session
- project: albc · harness: omx · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: none
- topic: pattern
- confidence: high · status: needs-experiment
- verified: 2026-09-07 · keywords: working-tree, uncommitted, import, pycache, exam, plant-confound, provenance, dirty
- summary: While sd_r3as31 five-config exam was running, this session wrote G5 (set_inertias) into envs/main/mdp/events.py at 02:03:44, never committed and never launched. pair34_d2 started at 02:07:46 and its bytecode cache (events.cpython-311.pyc, 02:07:50, 31937 bytes vs 29285) proves it imported the modified module. Tree reverted 02:09:00. Four configs clean, pair34_d2 contaminated -- and that is the deployment condition of finding/363. None of the guards saw it: not a parallel-session collision; the EXAM script logged no git provenance at all (the HEAD/dirty line belongs to student_arm.sh, the training half), and even HEAD would have been accurate and useless since the edit never left the working tree; and check_anchor is blind because inertia_scale is drawn identically either way -- what differs is where the drawn value is WRITTEN, the same blindness finding/396 recorded. Rule: a long-running experiment tree is not an editable tree; while a chain runs, edits to envs/** go to a patch file. Fixed: sd_exam_generic2.sh now logs HEAD and dirty on every config line, not once per exam. Contaminated cell queued for discard and re-run.
While `sd_r3as31`'s five-config exam was running, this session implemented G5 (`set_inertias`,
item 12) in the working tree. The edit was never committed, never launched, and never intended to
affect anything running. It changed one exam cell anyway.

## The timeline, from mtimes rather than memory

| time | event | evidence |
|:---|:---|:---|
| 01:25:32 | exam starts: `healthy` | exam log |
| 01:36:11 | `pair34` | exam log |
| 01:46:33 | `healthy_d1` | exam log |
| 01:56:57 | `healthy_d2` | exam log |
| **02:03:44** | **G5 written into `envs/main/mdp/events.py`** | `/tmp/events.py.bak`, taken immediately before the edit |
| 02:07:46 | `pair34_d2` starts | exam log |
| **02:07:50** | **that process compiles and imports the G5 version** | `__pycache__/events.cpython-311.pyc`, 31,937 bytes (the 3.12 cache from 00:02 is 29,285) |
| 02:09:00 | tree reverted, edit stashed as a patch | `git checkout --`, patch at `g0c_runner/pending/` |

So four of the five configs ran on the intended plant and **`pair34_d2` ran on a plant no other arm
in the table has** — one with `inertia_scale` reaching PhysX. That is the deployment condition
(`finding/363`) and the one cell where it matters most.

## Why the usual guards did not catch it

- It is not a parallel-session collision. One session, one tree, and the edit was to a file the
  session was *not* running anything from — or so it thought.
- `git status` would have shown it, but nothing consults `git status` between exam configs.
- **The exam script logged no git provenance at all.** Corrected while writing this: the
  `HEAD=`/`dirty=` line belongs to `student_arm.sh`, the *training* half, and
  `sd_exam_generic2.sh` had neither. So the training half carried the guard and the exam half —
  where this actually bit — carried nothing. Even had it logged `HEAD`, that would have been
  accurate and useless: HEAD never moved, the edit was in the working tree.
- `check_anchor()` compares the 23 sampled `dr_*` arrays. `inertia_scale` IS one of them, but it is
  sampled identically either way — the difference is where the sampled value is *written*, not what
  is drawn. `finding/396` already recorded that the signature is blind to any plant field the npz
  does not sample-log; this is the same blindness with a new instance.

## The rule this needs

**A long-running experiment tree is not an editable tree.** Python imports at process start, so every
process launched after an edit gets the new code, whether or not anyone launched it deliberately. The
edit does not have to be committed, staged, or even syntactically reachable from the entry point that
was launched — it only has to be in a module the process imports.

Concretely, for this repo:
1. While any exam or training chain is running, edits to `constrained_albc/envs/**` go to a patch
   file, not to the tree. `git diff > pending/<name>.patch; git checkout --` is the whole procedure.
2. **Done 2026-09-07:** `sd_exam_generic2.sh` now logs `HEAD=<sha> dirty=<n>` on **every config
   line**, not once per exam — the contamination was per-config, so per-exam provenance would
   have missed it too. `dirty` counts tracked modifications under `constrained_albc` and
   `marinelab` only, so an untracked scratch file does not raise a false alarm.
3. A contaminated cell is discarded and re-run, not adjusted. `sd_exam_generic2.sh` is re-entrant
   (skips any config that already has `summary.json`), so deleting one config directory and
   re-invoking the script redoes exactly that config.

## Disposition

`sd_r3as31/pair34_d2` is queued for discard and re-run on the reverted tree
(`g0c_runner/redo_s31_pair34d2.sh`, waits for the exam marker). The other four configs stand.
G5 itself is unaffected and sits in `g0c_runner/pending/g5_set_inertias.patch` with its congruence
math test passing; its live wiring is still unverified.

## Comments
- (2026-09-07, ksm-mac-session) 정정: Corrected: sd_exam_generic2.sh logged NO git provenance at all -- the HEAD/dirty line is student_arm.sh, the training half. Fix applied and recorded.
