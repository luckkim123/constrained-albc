# HANDOFF — retrain-simtoreal-2026-09 (revision 3.4, 2026-09-03 tank session)

**State:** PLAN.md is REVISION 3.4 — 3.3 plus the 2026-09-03 tank session. Two corrections landed in `finding/309`. **(a) The "≈ 0.31× / 3× vertical-moment gap" is RETRACTED as a unit error**: the 2026-08-12 m0 probe ran through `b1_channel_probe.py`, which publishes RAW commands with the mixer bypassed, so it sat at **effective u = 0.1176** (undeadband `D = 0.15`), and the corrected ratio is **0.67×** — at the coefficient-DR floor, not 3× below it. **(b) R-1 executed, and the §7 settled-tilt protocol proved structurally unexecutable**: with m3 dead, m0 is the only vertical channel, so `reallocate()` turns every vertical command into net heave and the depth boundary arrives before the tilt settles (both `+` steps clamped at 0.205 m, both `−` at ~0.890 m; doubling the thrust changed neither). The replaced readout — terminal descent rate, 9/9 steps, R² 0.988–0.996, free rise 0.0230 m/s pinning `B = c·v_rise²` so drag cancels — says the law is **neither** pre-registered option: not curvature but a **shifted origin** `T ∝ (u − δ)`, δ ≈ 0.11–0.14, linear above it. The absolute coefficient is **0.39× (B = 0.53 N) or 0.78–0.86× (B = 1.07 N, vault `finding/136`)**, i.e. outside vs inside the DR band on one unmeasured number, so **decision 9 cannot be read and the deciding probe is now a FIRST DIRECT measurement of net buoyancy B (it has never been weighed as an assembly)**, not more thruster levels. R-1's own record is vault `finding/144`. Not approved, not launched, nothing queued. Frozen 09-02 text: `PLAN.md.bak-round2-frozen`; the pre-3.4 PLAN text is in git.

**Resume order (do not skip):**
1. `review/306` (31-claim ledger, 9 corrections) → `finding/305` (axis lead refuted, HARD-GATE re-scored) → `finding/309` **§0 first** (the two 2026-09-03 corrections: the unit-error retraction, and what R-1 actually returned) → vault `finding/144` (R-1's own record) and vault `finding/143` (G0-H closed).
2. `PLAN.md` §10 — nine user decisions. Changed in 3.4: decision 4 `r1-before-final` stays **yes** but on a corrected ground (not "a 3× gap outside the DR band" — retracted — but "the absolute coefficient is unresolved between 0.39× and 0.86×"); **decision 9 `vertical-moment` is now DEFERRED pending a FIRST DIRECT measurement of net buoyancy B (it has never been weighed as an assembly)** — R-1's ratio selector cannot fire (no single power law fits), and R-1's residual deadband δ ≈ 0.12 argues *against* option (d), whose `thrust_deadband 0` assumed the mixer fully inverts the ESC deadband (`finding/281`). G0-C (training launch) runs only after `fault-config` and `seeds` are decided.
3. Vault side: `vault:finding/143` (**G0-H closed** — bag `10-19-06` was a thrust-live run with `fault_reallocate` ON, proved by replaying the deployed mixer; realized `My` is pinned at `−0.145 × Fz` in all 7 segments, which is also *why* R-1's settled-tilt protocol was unexecutable) and `vault:finding/144` (R-1 rev1 invalidation + rev2 results + the added-mass/damping identification). `vault:finding/142`'s R-1 ratio readout is superseded. Vault PLAN `#### 4-6` G0-H and R-1 rows updated; the tank note is `0_Project/in_progress/albc/notes/2026-09-03-tank-handoff.md`. The board WAS reachable on 2026-09-03.

**Cross-vendor status:** codex (gpt-5.6-terra) carried the ground-2 sweeps, the ground-4 axis check and the ground-4 review of revision 3 (`review/307`). agy (`gemini-3.1-pro-high`, effort `high`) reviewed the 3.1 text on 2026-09-03 with the three files INLINED in the prompt (`review/310`): 7 findings — the 40 N coefficient and the linear-only R-1 readout were found independently of `finding/309` and were already fixed in 3.2; two accepted into 3.3 (delay row tied to G0-B; G0-B's [1.3×, 2×) gap closed); two rejected with the config lines that answer them (axis naming → convention sentence in D-1; fixed-health index order → `config.py:130-137`); one partly (deadband inert by code, asserted in G0-J). **Two-family gate: met**, caveat: codex reviewed 3.0, agy 3.1. Operating note: agy cannot see files in the workdir — inline them; a 64 KB inline prompt returned in 3 m 57 s, two file-pointing attempts failed (297 s timeout; "files missing").

**Correction 2026-09-03 21:40 (operator-surfaced):** every sentence above that called the
next vertical probe a "remeasurement" of B was wrong -- **B has never been measured directly.**
`finding/309` §0d carries the arithmetic: only the hull was weighed submerged (15.55 N); the
buoy's 16.62 N is a cylinder approximation; B = 1.07 N is their difference, so a 3.2 % error in
the buoy term alone gives 0.53 N and R-1's fitted 0.53 is inside the error bar rather than in
conflict. The probe is the **first direct** measurement, and it need not be a hanging weigh
(the vehicle is slightly positive, so that route needs lead) -- a bottom-tethered scale reads B
directly, or one known weight plus two free-rise rates separates B from drag with no scale.

**What the next session must NOT redo:** the axis question (closed, `finding/305`); the IMU/frame item (closed robot-side, `finding/309` §5); m0/m3 motor identity (two motors); the search for a J2 software guard (none exists); the literature check (`finding/308`, 13 sources against primary text — only Whitcomb & Yoerger 1999 remains unread); the thrust-coefficient question (40 N/unit linear, `config.py:140-141`, `thrust_coefficient_scale (0.7, 1.3)` — read, not remembered); **G0-H** (closed 2026-09-03, vault `finding/143`); and above all **R-1's settled-tilt protocol** — it is not a dwell-tuning problem, it is structurally impossible while m3 is dead, and re-running it costs a tank session for nothing. The open vertical question is B, and B has never been measured directly -- vault `finding/136` weighed only the hull submerged (15.55 N) and got the buoy's 16.62 N from a CYLINDER APPROXIMATION, so B = 1.07 N is a difference of two ~16 N numbers and a 3.2 % error in the buoy term alone yields 0.53 N.

## 3.5 (2026-09-03 late, Mac session) — resume order

1. vault `finding/146` (R-1 closed: T/B = 7.25, B = 0.44 N by lead-tare weighing, 0.16× outside the band, `finding/144` absolutes retracted, 4.2× tilt contradiction open).
2. PLAN §13 (frozen launch order) → §7 R-3 / R-4 (pre-registered readouts) → §10 items 9 and 5.
3. Vault handoff note `notes/2026-09-03-tank-handoff.md` §5 for the two robot procedures; results arrive as vault `finding/`.
4. Then G0-J. **Nothing queued; user said "plan only, do not train yet."** G0-I and G0-A/B/E were dispatched to agents on this container (posts by `session-mac-g0i` / `session-mac-g0abe`).

## 3.6 (2026-09-04 00:5x) — read vault `decision/147` (operator: B 0.44 N, item 9 = re-center, R-3 + added inertia ordered) and `finding/312` (desk: coefficient DR per-env scalar; sim inertia 0.0994/0.0372 = URDF; J_total 0.49 vs ceiling 0.39) before §10 items 9/10. G0-I DONE (`4cef724`, `finding/311`). Still nothing queued.

## 3.7 (2026-09-04 01:2x) — item 9 CLOSED by the user (rough mode): thrust nominal 13 N/unit, band (0.5, 2.0); R-4 dropped, R-3 optional, item 10 held. §5 delta is now five values (see §13 row 6). Next desk step: G0-J manifest once G0-A/B/E report. Nothing queued.

## 3.8 (2026-09-04 01:4x) — R-3 done from bags (vault `finding/148`, 152 ms); item 5 re-set to (0,3) under rough mode. §5 delta = {thruster_fail_prob 0.15, thruster_dead_frac 0.5, control_delay_steps (0,3), thrust_coefficient 13, thrust_coefficient_scale (0.5,2.0)}. No robot work remains before launch. Nothing queued.


## Resume block — 3.9 (2026-09-04 03:3x)

- User directive 02:5x: pull, review, finalize, **start training**, no questions (user asleep).
- Decided in-session: p₀ **0.30** (d 0.5) on the user's own upward lean; item 10 → (c) now + (b) `set_inertias` follow-up (vault `finding/149`).
- G0-J: HEAD `e618e86`, incumbent config `logs/rsl_rl/albc_trpo_teacher/teacher_iter_budget/trpo_iterbudget_s30_260805_012813/params/env.yaml` sha256[:16] `830be5ddcc0005aa`, code delta dormant (3 commits), dirty = untracked only.
- G0-C queued (`omx queue-launch`). **Fire refused to the session by the auto-mode permission classifier** — user fires from PLAN §13's fire block. Nothing is running.
- G0-A/B/E: previous agent lost at compaction, no output; re-dispatched — not a blocker.
- Next after fire: diff `params/env.yaml` vs incumbent (five keys + `thruster_dead_frac`), read G0-C at 500, queue Phase 3.

## Resume block — 3.9a (2026-09-04 03:5x) — FIRED

- 03:42 the user granted the permission; runner `/workspace/g0c_runner/run.sh` in tmux `g0c` on GPU0, serial: WITH → WITHOUT → Phase 3 `p3_ftc_s30` (chained, no human stop). Status log `/workspace/g0c_runner/status.log`, markers `G0C_DONE`, `DONE`.
- G0-J confirmed on the live run (PLAN §13 row 6). ≈ 4.5 s/iter, 11.5 GB VRAM → Phase 3 ≈ 12.5 h, end ≈ 17:00.
- Next: at `G0C_DONE` read `Train/mean_reward` and `DORAEMON/mode` at iteration 500 for both arms (TB event files under each run dir), write the G0-C verdict into §13 row 7; at `DONE` run Phase 4 (`eval static` paired vs incumbent, health 1,1,1,1,1,1 and 1,1,1,0,0,1, DR none/hard) and the exp-analyze report.
- G0-A/B/E: second agent running on GPU1 (2.3 GB), writes `.hq/work/g0abe/report.md`.

## Resume block — 3.9b (2026-09-04 05:1x) — G0-C read, Phase 3 running

- G0-C: WITH/WITHOUT reward at 500 = 0.82× (last), 0.77× (last-50), 0.70× (400–499) → FAIL on the 5 % threshold; mode −3 both (curriculum not started, reward < lb 250); fault_severity 0.01 both → faults inactive → gap = delay/thrust, not p₀. `finding/313`.
- Phase 3 `trpo_p3_ftc_s30_260904_0506xx` running, ETA ≈ 17:15. Not killed (night directive). Morning decision for the user: keep or kill.
- G0-A/B/E: agent finished its evals 04:38 (`.hq/work/g0abe/{g0a_fault_m3m4,g0a_healthy,g0b_delay1,g0b_delay2}/data_*.npz`), report.md pending from the agent.
- After Phase 3 `DONE`: Phase 4 paired eval vs incumbent (health 111111 / 111001, DR none/hard), then exp-analyze report.

## Resume block — 3.9c (2026-09-04 05:3x) — G0-A/B/E closed

- `finding/314`: no arm-pitch fallback (retention 0.26/0.25), delay 1 step = 4–5× attitude error, 2 steps = 12–16×; constraint margins all positive. §13 row 4 DONE. Row 7's FAIL re-read as the delay-regime price.
- Still running: Phase 3 `p3_ftc_s30` (ETA ≈ 17:15). Nothing else in flight.

## Resume block — 3.9d (2026-09-04 13:5x) — Phase 3 killed, Phase 3b fired

- `finding/315`: Phase 3 curriculum never opened (mode −2, fault_severity 0.0045, all DR dims initial). Cause: performance_lb 250 > delta plateau ≈ 237. User decided lb 200; Phase 3 killed at 8010 (checkpoint kept, `model_8000.pt`), Phase 3b `trpo_p3b_lb200_s30_260904_1345xx` fired 13:45 in tmux `p3b`, log `/workspace/g0c_runner/p3b.log`, marker `P3B_DONE`.
- Early readout (pre-registered): mode 0/1 and fault_severity > 0.05 by it 1 000 (≈ 15:00). Monitor armed in the Mac session.
- After `P3B_DONE` (≈ 02:15 09-05): Phase 4 paired eval (incumbent vs p3b vs the p3 no-DR reference), health 111111 / 111001, delay 0/1/2, DR none/hard; exp-analyze report.

## Resume block — 3.9e (2026-09-04 14:3x) — Phase 3b at 596 it, Phase 4 runner started

- p3b health at it 596: reward 190.5 (r50 182.7), success 0.40, `fault_severity` 0.010, modes −3/−3/−2 at 0/250/500 — pre-gate, expected (lb 200 not yet crossed). Verdict at it 1000 (≈ 15:00): mode 0/1 and severity > 0.05, else kill (`tmux kill-session -t p3b`) and re-open §10 item 11.
- Health monitor: `/workspace/g0c_runner/p3b_health.py` (run from the repo root), read every 500 it; stall signature = it ≥ 1500 and last 3 modes ≤ −2 and severity < 0.05.
- Phase 4 exam runner started 14:34 on GPU1 (§13 row 12): `.hq/work/p4/runner.log`, `pgrep -af p4_runner`. Kill/restart is safe (re-entrant).
- Next: 1000-it verdict → PLAN row 11; after `P3B_DONE` (≈ 02:15 09-05) the runner scores p3b final; then exp-analyze report (per-env pairing at `hard`, floors 0.10° / 15 envs / 1.6 pp), finding post, vault brief §0, memory.

## Resume block — 3.9f (2026-09-04 15:0x) — Phase 3b 1000-it verdict PROCEED

- it 1056: reward 217.5 > lb 200, success 0.786, mode 0 at 750 and 1000 (opened), severity 0.0132 rising. No kill. Stall signature armed from it 1500 (mode ≤ −2 ×3 and severity < 0.05).
- Phase 4 runner: inc13/healthy done 14:43 (rc 0); override verified — none-level roll ss_error 0.230° (own plant) vs 0.336° (13 N), hard 0.329° vs 1.345°.

## Resume block — 3.9g (2026-09-04 16:1x) — Phase 3b 2000 it, exposure track pre-registered

- it 2003: reward 234.2 (r50 232.5), success 0.880, `fault_severity` 0.0230, mode 0 at 1250/1500/1750/2000. Healthy, no stall signature.
- Exposure track (PLAN row 11): severity grows x1.312 per 500 it since the curriculum opened; reaches 0.45 at it ~7 600 on that rate. Check at it 5 000, expect ~0.12; below ~0.07 is a Phase 4 caveat, not a kill.
- Phase 4 scorer installed: `/workspace/g0c_runner/p4_score.py`, run from the repo root with `/isaac-sim/python.sh`. Prints per-env paired deltas against `inc13` with the section 9 floors, and switches to candidate-vs-incumbent automatically once a p3b arm is scored. The incumbent-only run reproduced finding/316 and surfaced two survival deltas: pair34 hard +4.7 pp (the 13 N plant survives more) and healthy hard -3.1 pp.
- Runner progress: inc13 core 4/4 done; incumbent single/pair losses 3/20 (m0, m1, m2) as of 15:42.

## Resume block — 3.9h (2026-09-04 16:5x) — container restart, p3b resumed and verified

- **Incident**: host docker daemon restarted 15:56:09 KST, killing p3b (~2 100 it) and the Phase 4 runner. Container `sshd` died too; the bootstrap is now at `.hq/config/project/env/sshd-up.sh` (the old `.omp/env/` path in the operator memory is stale). Recovery: `ssh ksm-ubuntu 'docker exec -d marinelab-isaaclab bash /workspace/.hq/config/project/env/sshd-up.sh'`.
- **p3b resumed** 16:35 from `model_2050.pt` into `trpo_p3b_lb200_s30_r2050_260904_163518`, iterations 2050 to 10 000, ETA 09-05 02:2x. Verified restore (`finding/317`): curriculum `fault_severity` opens at 0.0230, env config identical but `log_dir`, reward 238.3 at it 2114 against 234.2 pre-crash.
- **Resume recipe** (both traps are silent): `--resume` must be a CLI flag, and `load_run` must name a directory one level under `logs/rsl_rl/albc_trpo_teacher/` — use the `RESUME_p3b_2050` symlink. Script: `/workspace/g0c_runner/p3b_resume.sh`.
- **Watch out**: the wrapper's `touch P3B_DONE` runs on any exit, including a failed launch, and the Phase 4 runner polls that marker — it began scoring `model_2050.pt` as the final checkpoint. Marker and `p3b_final/` were removed and the runner restarted. Make the marker conditional on a zero exit before the next long unattended stretch.
- Phase 4 runner back on GPU1 from `inc/m0m1`; incumbent single/pair losses 7/20 done.

## Resume block — 3.9i (2026-09-04 17:4x) — Phase 4 exam confound found and fixed

- **`finding/318`**: the exam runner scored each arm on its own training plant, so the DR band differed and per-env pairing broke at soft/medium/hard (`pairDR` 0.5/1.0/2.0). Only `none` rows were ever valid. Fixed by adding arm `inc13w` (incumbent on the full section-5 plant); runner restarted 17:4x with it scheduled first among the incumbent arms.
- **Rule for reading the scorer**: `pairDR` first, `delta` second. Every confounded row carried a large favourable delta, which is why it read as a result rather than a defect.
- p3b resumed run healthy through 2539 (reward 244.9, success 0.935, severity 0.0306, mode 0 at 2249 and 2499); severity tracks the pre-registered x1.312/500it line (2500 predicted 0.0302, measured 0.0306).
- Scorer: `/workspace/g0c_runner/p4_score.py`, run from the repo root with `/isaac-sim/python.sh`.

## Resume block — 3.9j (2026-09-04 22:3x, Mac session handoff) — the exam confound is a FLAG, not an arm

- **`finding/318`'s fix was a no-op** (`debugging/319`). Arm `inc13w` is **byte-identical**
  to `inc13`: same md5 on `data_none.npz` for both `healthy` (`d238a30b...`) and `pair34`
  (`fca2b3e9...`), same `dr_*` ranges to four decimals at `hard`, and `p4_score.py` prints
  numerically identical tables for `p3b_2500 vs inc13w` and `vs inc13` — every row.
  `env.randomization.thrust_coefficient_scale` is **inert in `eval.py static`**.
- **Mechanism** (`eval.py:1382-1404`): `--doraemon-dr` defaults **True** and auto-loads the
  *evaluated checkpoint's own* DORAEMON-learned distribution into
  `_dr_config_module._DORAEMON_FULL_DR` — the hard anchor that soft/medium interpolate
  toward. The band is a property of the scored checkpoint, so the Hydra override lands on
  the static cfg that the DORAEMON load then replaces. **No arm can fix this** (the operator
  said so and was right); `--doraemon-dr-from <run_dir>` or `--no-doraemon-dr` can.
- **Operator decision 22:4x — option C**: re-score the CORE matrix with **`--no-doraemon-dr`**
  so both arms sit on the static hard `DomainRandomizationCfg` and the section-5 band
  (0.5, 2.0) finally applies. The exam becomes *the designed plant* rather than either
  policy's own curriculum. Flag verified present (`eval.py static --help`).
  WARNING: a common *band* is not a common *draw*. `--deterministic-dr`'s own help text says
  seed alone does not fix DR draws across different networks (RNG consumption order). If
  `pairDR` is still non-zero under C, the follow-up is C + `--deterministic-dr`, which
  buys per-env pairing at the cost of collapsing each level to its midpoint plant.
- **Operator decision 22:4x — `p3b_final` EXTRA 20**: report as **candidate-only** fault map,
  no delta column. Their only possible reference (`inc`, incumbent on its own 40 N plant,
  no overrides) is a worse confound than the one `finding/318` chased.
- **New runner**: `/workspace/g0c_runner/p4c_runner.sh` (PID 19246, launched 22:32, alive,
  log `.hq/work/p4c/runner.log`). It **blocks on `.hq/work/p4/ALL_DONE`** and uses zero GPU
  until then, so it does not compete with training. Config-major on purpose (cand then ref
  per config) so the first pair is scorable ~20 min in and `pairDR` can be read early.
  Output `.hq/work/p4c/{p3b_finalC,inc13w}/<config>`. Re-entrant; kill/restart safe.
- **Scorer**: `p4_score.py` line 11 now reads `BASE = os.environ.get("P4_BASE", ".hq/work/p4")`
  (backup `p4_score.py.bak_pre_p4base`). Score the C matrix with
  `P4_BASE=.hq/work/p4c /isaac-sim/python.sh /workspace/g0c_runner/p4_score.py` from the
  repo root. The arm names inside `p4c` were chosen so the existing cand/ref filters work
  unchanged.
- **Measured timeline** (rate taken clean over 90 s: it 6696 to 6720 = **3.75 s/iter**;
  the earlier 4.9 s/iter reading was polluted by this session's own health-script runs):

  | when | what |
  |:--|:--|
  | ~23:25 | `model_7500.pt` → runner preempts, `p3b_7500` CORE |
  | **02:01** | training ends (10 000 it) → `P3B_DONE` |
  | 02:01~ | `p3b_final` CORE+EXTRA 24; faster than the 10 min/config measured while sharing GPU |
  | ~05:00-05:40 | `.hq/work/p4/ALL_DONE` → `p4c_runner` wakes |
  | ~06:00-06:40 | `.hq/work/p4c/ALL_DONE` → score, then exp-analyze report |

- **Training health at 22:3x**: it 6720, reward 194.6 (r50 191.9), success 0.595,
  `fault_severity` 0.3045, `obs_noise` 0.3332, `DORAEMON/mode` 0 at 5499/5749/5999/6249/6499.
  Stall signature (it >= 1500 AND last 3 modes <= -2 AND severity < 0.05) fails on both
  clauses. The reward/success dip against 2500 is the difficulty rising in the same window,
  not degradation.
- **Monitors re-armed in this session** (they are session-bound and did not survive the
  handoff): 30-min training+runner health, `p4/runner.log` milestones, `p4c/runner.log`
  progress.
- **Still open, unchanged**: the GitHub PAT (`luckkim123/hero_agent.git`) revocation is the
  operator's own action. Wiki backlog at handoff: 11 `needs-experiment`
  (163, 198, 263, 296, 301, 305, 309, 312, 313, 315, 318) plus the new `debugging/319`, and 1
  `needs-apply-before-retrain` (**`finding/264`** `control_delay_steps` — this run applies
  (0,3), so it is closable once the report lands).

## Resume block — 3.9k (2026-09-05 02:1x) — training done clean, p3b_final running

- **Phase 3b finished cleanly at ~02:04.** The evidence is the marker itself: `p3b_resume.sh`
  writes `P3B_DONE` only under `[ $RC -eq 0 ]`, so its existence *is* the zero-exit check. The
  runner picked it up at 02:04:31.
- **Final checkpoint = `model_9999.pt`** (saves are every 50 it, and this is the
  end-of-training save after `model_9950.pt`). 2050 + 7950 = 10 000 iterations completed.
  `p4c_runner.sh` selects with the same `ls model_*.pt | sort -V | tail -1` expression, so
  **both matrices score the same checkpoint** — the precondition for option C's re-scoring to
  be a DR-distribution comparison rather than a different-policy comparison.
- **Per-config cost did NOT drop when the GPU freed up.** Measured on the first `p3b_final`
  config: 02:04:31 to 02:14:12 = **9 min 41 s**, against ~10 min while sharing GPU1 with
  training. The earlier "~7 min once training ends" estimate in 3.9j was a guess and is wrong
  — a 64-env `eval.py static` is dominated by Isaac Sim startup, not by GPU contention. Do
  not plan around a speedup that does not exist.
- **Revised schedule**: `p3b_final` 24 configs about 3.9 h → `.hq/work/p4/ALL_DONE` **~06:00**;
  `p4c` 8 configs about 1.3 h → `.hq/work/p4c/ALL_DONE` **~07:20**; score + exp-analyze report
  **~07:50**.
- Last training health (it 9902, 01:52): reward 170.4, r50 177.5, success 0.465,
  `fault_severity` 0.4782, `obs_noise_scale` 0.4811, `DORAEMON/mode` 1 at
  8999/9249/9499/9749. The curriculum sat at its [0, 1] bound from it 7249 onward and
  regulated around it; no stall signature at any point after the gate opened.

## Resume block — 3.9l (2026-09-05 02:5x) — CORE verdict is IN; option C is now corroboration

- **Read `finding/321` before anything else.** It carries the full table. Headline: the
  candidate (`model_9999`) halves `pair34` pitch error with a **64/64** per-env sign and
  improves both delay configs by about half, while being **worse on fault-free `healthy`
  att and roll at every level** (per-env 10-15/64 against, all above the 0.10 deg floor).
  That is the intended sim-to-real trade, and the cost is real -- report both halves.
- **`pairDR = 0e+00` on all 16 rows, and the reason is physical.** Both arms load their own
  DORAEMON distribution (no fallback), and at saturation both `mean +- 2 sigma` exceed the
  static box on every dim, so both clip to the **same** bounds: payload_mass [0, 3],
  added_mass_scale [0.5, 1.5], linear/quadratic damping [0.4, 1.7]. `p3b_5000` was still
  inside the box ([0.0844, 2.9021] etc.), which is why the milestones did not pair.
  **All four levels are readable at the final checkpoint without option C.** Do not
  generalize this -- it is a property of where the curricula ended.
- **Option C's rationale changed, and the run was deliberately left going.** `p4c`
  (PID 19246) is no longer the repair of a broken comparison; it is an independent exam on
  the *designed* section-5 plant (thrust scale 0.5-2.0) rather than the learned box the two
  curricula converged to. Score it the same way (`P4_BASE=.hq/work/p4c`) and present it as
  corroboration in the report, not as the fix.
- **`model_9999` is not the best checkpoint on every axis.** `healthy` att went 0.442
  (it 5000) -> 0.426 (7500) -> **0.511 (9999)** while the `pair34` rows kept improving.
  `p4_runner.sh` selects last, not best. If nominal accuracy is weighted in the deployment
  decision, `model_7500` is the checkpoint to re-score -- that is an operator call, not a
  session call.
- **Timeline holds**: CORE 4 finished 02:43, EXTRA under way (`m0` from 02:43, 10 of 24
  configs on disk). `.hq/work/p4/ALL_DONE` ~06:00, `p4c/ALL_DONE` ~07:20, report ~07:50.
- **Report still owes**: `omx exp-analyze` into the experiments tree (results SSOT), parsed
  via `omx report-parse`, plus the wiki-backlog cross-check -- 11 `needs-experiment`
  (163, 198, 263, 296, 301, 305, 309, 312, 313, 315, 318) plus `debugging/319` and now
  `finding/321`, and `finding/264` (`control_delay_steps`, `needs-apply-before-retrain`)
  which this run applies (0,3) and can therefore close with the report.

## Resume block — 3.9m (2026-09-05 06:2x) — report landed, gates green, and the config is override-only

- **The Phase 4 report is written and passing every gate.** Path:
  `experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/diagnose-20260905-060354/`
  with `report.md`, `report.ko.md`, `manifest.json`, `review.json`. 4,162 words, 26 findings,
  128 table rows. `omx report-coverage --min-coverage 0.5` → `ok: true`, all seven groups at
  full coverage (tracking 4/4, reward_decomp 6/6, trpo 7/7, critic 2/2, encoder 5/5,
  constraint 21/21, doraemon 4/4), no missing sections, engine cited. `omx report-review` →
  `approve`. Independent `report-reviewer` agent → **approve**, zero major findings, having
  re-run `p4_score.py`, `extra_read.py` and `tb-final` itself and matched every spot-checked
  figure.
- **THE FINDING THAT MATTERS MOST — every section-5 setting is launch-override-only.** Checked
  while trying to close `finding/264`, and it is why that page must stay open:
  `control_delay_steps` default `(0,0)` at `constrained_albc/envs/main/config.py:263`,
  `performance_lb` `250.0` at `:612`, `thrust_coefficient` `40.0` at `:141`,
  `thrust_coefficient_scale` `(0.7,1.3)` at `:231` — as-run values were `(0,3)`, `200.0`,
  `13.0`, `(0.5,2.0)`. **A retrain launched without the override block silently reverts to the
  exact configuration `finding/315` measured stalling for a whole run.** Filed as
  `finding/352`, status `needs-apply-before-retrain`. The blocking roster is now
  `finding/264` + `finding/352` — it used to be one item and read as empty.
- **Wiki curated (6 pages) + 26 auto-captured stubs** (`finding/323`-`348`):
  `349` saturation → `pairDR = 0` mechanism · `350` fault ranking (m0 dominates) ·
  `351` "a monotone reward decline under a widening curriculum is the difficulty tax, not
  divergence" (the engine's DIAGNOSIS false positive) · `352` override-only (blocking) ·
  `353` engine-gap spec (nine TB tags the engine never scans) · `354` inertia gap
  (measured pitch 0.49 vs effective 0.12).
- **Findings posted this session**: `finding/321` (CORE verdict + the `pairDR = 0`
  explanation), `finding/322` (EXTRA fault map).
- **STILL TO APPLY — one re-analysis pass, through the skill's re-analysis path (old report as
  BASE, `atomic_path` writer, never hand-Edit).** Four reviewer minors plus two additions:
  1. **The deployment framing gap (the reviewer's substantive catch).** The report calls the
     real robot's condition "m3 dead, m4 excluded, ~152 ms delay" but **no scored config
     combines fault AND delay** — `pair34` has no delay, `healthy_d1`/`d2` have no fault.
     The two axes were only ever tested in isolation and the report must say so.
  2. Carry the MED caveat on the `performance_lb`-vs-plant attribution into the TL;DR bullet
     and the verdict, where it currently reads as flat fact.
  3. `fault_severity 0.0132 (it 1056)` has no citation that leads to a TB-scalar-at-step
     source; either cite it properly or soften.
  4. `finding/149` does not resolve in this store (dead link) — cite `PLAN.md` item 10 instead.
  5. Add the override-only finding (`finding/352`) to the report body.
  6. Add the `p4c` option-C corroboration once it lands.
- **`p4c` (PID 19246) is still running**, ~08 min per eval under `--no-doraemon-dr` (faster
  than p4's 9m41s because it skips the DORAEMON load). `healthy` pair done 06:08, `pair34`
  under way; ETA `.hq/work/p4c/ALL_DONE` **~06:56**. Score with
  `P4_BASE=.hq/work/p4c /isaac-sim/python.sh /workspace/g0c_runner/p4_score.py`.
- **Engine invocation gotcha, for the next session**: `analyze_training.py` must run under
  `/isaac-sim/python.sh` (the system python3 fails preflight on a scipy/numpy mismatch and
  says so), but `omx_core` / `omx_paths` is only importable from the **system** `python3`.
  Two different interpreters for the two halves of this workflow.
- **`omx report-review` grammar is strict**, and getting there cost five round trips:
  `[FINDING]` → `[EVIDENCE: …]` → `[CONFIDENCE: HIGH|MED|LOW]` must be **adjacent lines**,
  each tag must **open and close on one line**, the confidence tag must be the **bare grade**
  with no trailing rationale, and every `[EVIDENCE]` needs an opening `[FINDING]`.
- **`omx tree-audit` is `ok: false`** (4 errors, 3 warnings). One is ours: a dangling
  `data_pointer` symlink at
  `experiments/.../retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_162821/train`, left by
  the failed from-zero resume that `finding/317` isolated. Report-only by rule; not fixed.
- **Wiki backlog at this handoff**: 13 `needs-experiment` (163, 198, 263, 296, 301, 305, 309,
  312, 313, 315, 318, 319, 321) and 2 `needs-apply-before-retrain` (264, 352). Neither 264 nor
  315 was closed, and the reason is the override-only finding above — the corrections were
  applied to the run, not to the code.

## Resume block — 3.9n (2026-09-05 07:0x) — PHASE 4 COMPLETE. Everything below is done, not pending.

- **The program's Phase 4 is finished.** Final deliverable:
  `experiments/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518/analysis/`
  **`diagnose-20260905-070135/`** (`report.md`, `report.ko.md`, `manifest.json`, `review.json`).
  It supersedes `diagnose-20260905-060354`, which stays on disk as the baseline the regression
  gate compared against. 5,019 words, 32 findings, 134 table rows.
- **Every gate is green, including the regression gate.** `omx report-coverage
  --min-coverage 0.5 --baseline auto` → `ok: true`, `is_regression: false`
  (words 4163→5019, findings 26→32, tables 128→134), no missing groups or sections, engine
  cited. `omx report-review --baseline auto` → `approve`. The independent `report-reviewer`
  agent approved the 060354 base with zero major findings after re-running the scorers itself;
  all four of its minors were applied in 070135.
- **Option C came back byte-identical and that is the good outcome** (`finding/355`). The
  `p4c` matrix (`--no-doraemon-dr`, finished 06:56) reproduced the default scoring digit for
  digit — three md5 matches on `data_hard.npz`, all 24 rows — while the eval logs show the two
  runs genuinely taking different branches (`Attempting to load DORAEMON-learned DR from: …`
  versus `DORAEMON-DR disabled. Hard DR = static DomainRandomizationCfg.`). **That proves the
  DORAEMON-clipped box IS the static hard box**, which `finding/321` had only inferred from
  printed ranges agreeing to four decimals.
- **What option C also proved, which nobody wanted**: the section-5 thrust band (0.5, 2.0)
  **has never been exercised by any Phase 4 exam, on either branch.** `data_hard.npz` records
  23 `dr_*` dims and not one contains `thrust`; neither eval log prints a thrust line;
  `debugging/319` showed the same from the other side. `--deterministic-dr` will not fix it —
  the band does not reach the eval at all rather than being drawn differently. Testing the
  designed plant needs a different mechanism, not a different flag.
- **Two caveats now carried in the report, both from that check.** `pairDR` covers only the 23
  recorded dims, so `pairDR = 0` means the arms agree on what the eval writes down, not on
  every aspect of the plant; and the shared thrust band rests on `p4_runner.sh` passing the
  identical `DELTA` to both arms — construction, not measurement.
- **The reviewer's substantive catch, now in the report**: **fault and delay were never scored
  together.** `pair34` is the fault at zero delay, `healthy_d1`/`d2` are the delay with six
  healthy thrusters, and no `pair34_d*` exists in either matrix — while the deployed robot has
  both. Every claim about "the real robot's condition" joins two separately measured axes.
- **Posts this session**: `finding/321` (CORE verdict + saturation), `finding/322` (EXTRA fault
  map), `finding/355` (option C). Curated wiki: `349` saturation mechanism · `350` fault
  ranking · `351` reward-decline-is-not-divergence · `352` **override-only (blocking)** ·
  `353` engine-gap spec · `354` inertia gap. Breadcrumbs `323`-`348` plus 32 more from 070135.
- **The operator decisions that remain, and they are the only open items**:
  1. **`model_7500` vs `model_9999`.** Fault-free attitude regressed 0.426 → 0.511 over the
     final 2500 iterations while `pair34` kept improving, and the runner takes the last
     checkpoint. If the deployment weights nominal accuracy, `model_7500` should be re-scored.
  2. **Whether to change the four code defaults** (`finding/352`) or to require the override
     block in every launch ack. The blocking roster is `finding/264` + `finding/352`.
  3. **Whether a `pair34_d2`-style config is worth scoring** before deployment, given that the
     two axes have only been measured apart.
- **Not done, deliberately**: `omx tree-audit` is still `ok: false` (4 errors, 3 warnings),
  including our dangling `data_pointer` at `…/trpo_p3b_lb200_s30_r2050_260904_162821/train`
  from the failed from-zero resume. Report-only by rule.
- **Still the operator's own action**: revoke the GitHub PAT for `luckkim123/hero_agent.git`.

## Resume block — 3.9o (2026-09-05 13:3x) — the three operator decisions executed

The user answered all three items 3.9n left open. What follows is what was measured, not
what was planned.

**1. Checkpoint (`model_7500` re-score) — answered, and it reverses 3.9n's framing.**
`p3b_7500` CORE was already on disk from the runner's milestone loop, so this cost no GPU.
Scored head to head against `model_9999` (`g0c_runner/ckpt_read.py`): `pairDR = 0e+00` on all
16 CORE rows — same run, both curricula past the clamp box, so all four DR levels read with no
saturation caveat. **15 of 16 deltas favour `model_7500`, 12 clear the 0.10 deg floor, 3 tie,
and `model_9999` wins exactly one row** (`pair34` at `none`, by 0.129 deg). Both delay configs
shed **3.1 pp of survival** at `hard`. The last 2500 iterations were a net regression, not the
accuracy-for-robustness trade `finding/321` and the 070135 report described. `finding/362`.
**The deployment checkpoint should be `model_7500`, not the runner's last-checkpoint pick.**

**2. Config group — built as an Isaac Lab task variant, because this repo has no Hydra YAML
tree.** `@hydra_task_config` builds from registered dataclasses, so the repo's own idiom for a
config variant is a cfg subclass behind a new task id (precedent: `config_noconstraint.py` /
`Isaac-ConstrainedALBC-TRPO-NoIPO-v0`). Added `constrained_albc/envs/main/config_simtoreal.py`
(`ALBCSimToRealEnvCfg`) registered as **`Isaac-ConstrainedALBC-TRPO-SimToReal-v0`**. No base
default moved, so no other task or experiment is affected.

`finding/352` **undercounted: the override block is seven settings, not four.** The four it
listed differ from the code defaults, and so do `fault.enable` (False), `fault.thruster_fail_prob`
(0.10) and `fault.thruster_dead_frac` (0.0). All seven are in the variant. Equivalence is
checked, not asserted — `test_simtoreal_cfg.py` resolves both configs and requires the
difference set to be exactly those seven fields with exactly the launched values.
Verified through the real launch path: `eval.py static` on the new task id with **no
overrides at all** produced `data_*.npz` **byte-identical** to the already-scored
`p3b_final/pair34` at all four DR levels (`none` bef6fdbaae43, `soft` b4ac09a90825, `medium`
c5e7ce058b6a, `hard` 80065dc14412). `thrust_coefficient` alone (40 N vs 13 N) would change
every trajectory, so the identity is the proof. **Scope**: that eval sets health with
`--fault_fixed_health`, which overrides all three `fault.*` settings, and `performance_lb` is
training-only — so execution covers **one field of seven, not three**. The eval baseline is
`p4_runner.sh`'s `DELTA`, which is only TWO overrides (`thrust_coefficient`,
`thrust_coefficient_scale`); the seven belong to the TRAINING launch. Only
`thrust_coefficient` is exercised: the band never reaches a Phase 4 exam, and
`control_delay_steps` cuts against the naive reading — the variant sets `(0,3)`, the base task
default is `(0,0)`, `DELTA` never overrode it, so the two runs genuinely DIFFERED there and
still produced identical bytes. That is positive proof the eval cannot see the field. The other
six rest on
`test_simtoreal_cfg.py`, which is written but **could not be run on this container**: a
standalone `AppLauncher` boot exits 0 during Kit startup with no traceback (reproduced with a
seven-line script) while `eval.py`'s own boot works. Run it where standalone Kit starts.

Future retrain launch, replacing the seven-override block:

```bash
/workspace/isaaclab/isaaclab.sh -p scripts/train.py \
  --task Isaac-ConstrainedALBC-TRPO-SimToReal-v0 --num_envs 4096 --headless --seed 30 \
  --max_iterations <N> --run_group <group> agent.run_name=<name>
```

`finding/352` and `finding/264` stay `needs-apply-before-retrain`: the variant removes the way
to forget the block, it does not bind a launch that does not use it. They close when a retrain
ack names this task id.

**3. `pair34_d2` — scored, and it is the strongest deployment evidence in the program.**
Three configs, 8m25s each, GPU1, `g0c_runner/p4d_runner.sh` + `p4d2_runner.sh`.
Three arms, and **the `pairDR` rule removed most of the table before it was read.** Arm vs arm
on `pair34_d2` the `hard` rows are `1e-01` (every CORE row of the same pair is `0e+00`), so they
are excluded. And the additivity test is valid at `none` only: within one arm `pair34` and
`pair34_d2` draw different plants at soft/medium/hard (`pairDR` 2, 4, 6 — the delay flag changes
RNG consumption). Reading the confounded rows would have produced a plausible, wrong interaction
number (+1.9 deg for the candidate at `hard`).

At the one level that tests it, against the additive prediction `pair34 + healthy_d2 - healthy`:

| arm | predicted | actual | excess |
|:--|--:|--:|--:|
| inc13w | 2.128 | 9.360 | **+7.232** |
| p3b_7500 | 1.062 | 1.080 | +0.018 |
| p3b_final | 0.963 | 0.963 | +0.000 |

**The incumbent's combined error is 4.4x what its own single-axis results predict; both
retrained checkpoints match theirs.** On the deployment condition itself the candidate beats the
incumbent by -8.397 / -9.303 / -12.592 deg at none/soft/medium with a 64/64 per-env sign. So the
retrain's real product is removing the fault-delay interaction, and the single-axis numbers do
not bound the deployment case — `finding/321` could not have been read off them. `finding/363`.
Head to head the two checkpoints agree with the CORE verdict here too (`pairDR` 0 on all four:
9999 ahead at `none` by 0.117, behind at soft/medium/hard, -1.6 pp survival at `hard`).

**Two record corrections.**
- `HANDOFF.md:34` and `PLAN.md:208` say `thruster_fail_prob 0.15`. The live value is **0.30**
  — PLAN.md:91 carries the 3.9 decision (p₀ = 0.30), the fire blocks at :223/:234 use 0.30,
  and the as-run confirmation on :208 itself says `0.1 → 0.3`. Both stale strings sit inside
  historical rows whose own DONE columns already contradict them, so they were left rather
  than rewritten. Read the launch script, not the prose.
- The `pairDR` rule earned its keep twice more in this round. On `pair34_d2` the `hard` rows
  are `1e-01` (every CORE row of the same arm pair is `0e+00`), so they are excluded; and the
  additivity test is valid only at `none`, because within one arm `pair34` and `pair34_d2`
  draw different plants at soft/medium/hard (`pairDR` 2, 4, 6 — the delay flag changes RNG
  consumption). Reading the confounded rows would have produced a large, plausible, wrong
  interaction number for the candidate.

**Report**: `analysis/diagnose-20260905-140134` is current. It supersedes `-134031`, which
superseded `-070135`: 5019 → 6923 → **7813** words, 32 → 42 → **44** findings, 134 → 176 →
**191** table rows, both revisions `omx report-coverage` `ok: true` (7/7 groups, no regression)
and `omx report-review` `approve`.

**An independent `report-reviewer` pass on `-134031` returned `revise` with six major findings,
and all six were real.** They are worth carrying forward as a pattern, because five of them are
the same failure: an ADDITION that should have been a SUBSTITUTION. (1) The stale
"fault and delay were never tested together" finding survived alongside the new section that
refutes it, and its own cited `ls` now returns `pair34_d2`. (2) The report recommended
`model_7500` while every incumbent table in it graded `model_9999` — the recommended
checkpoint's actual bill (three ties, one win, two `hard` rows) was absent. (3) "does not trade
anything away on the deployment condition" is false at the report's own floor (`model_9999` is
0.117 deg better at `pair34_d2 none`). (4) The 15-of-16 count hid a clean perturbed-exam versus
nominal-plant split: at `none` every above-floor fault row favours `model_9999`. (5) The
task-variant scope was over-claimed at 3 of 7 (see above). (6) `DORAEMON/mode` was **0 at it
8499**, not 1 throughout from 7249, and the cited `curriculum_trajectory.json` has no mode
field. Minors: EXTRA survival is 18 of 20 not 17; the candidate's `+0.000` additivity match is
mean-level cancellation (per-env std 0.702), not per-env additivity; "4.4x" is
additive-null-dependent (a multiplicative null gives 2.41x); the `pairDR` blind spot covers at
least seven dims, not just thrust — though an independent diff of all 19 clipped DR boxes found
them identical across arms, which STRENGTHENS the same-clamp-box claim; `ocean_current_strength`
also never reaches the exam; the confounded `hard` rows blanked only `delta` while keeping
`better` and `survD`; and one md5 evidence path named the wrong directory. All are applied in
`-140134`, and `finding/352`, `362` and `363` were edited to match.

**Nothing is queued and nothing is running.** Repo changes are uncommitted on branch
`exp/koopman-marine-obs` (no commit was asked for): `config_simtoreal.py`,
`test_simtoreal_cfg.py`, the registration in `envs/main/__init__.py`, plus the new posts and
this file. `omx tree-audit` is still `ok: false` (4 errors, 3 warnings) including the dangling
`data_pointer` symlink from the failed from-zero resume — report-only by rule. The GitHub PAT
for `luckkim123/hero_agent.git` is still the user's to revoke.

## Resume block — 3.9p (2026-09-05 20:3x) — option B decided, student distillation QUEUED, no retrain

**Operator decisions (2026-09-05 evening, Mac session).**
1. The deploy path proceeds on `model_7500`. **No teacher retrain.** Phase 4 selected the checkpoint; distillation and export were never started — the newest student run on disk is the incumbent's (`student_final_round`, 2026-08-10), no student run exists after p3b, and `deploy/` has no p3b pack. The board runs a GRU student (teacher actor input 81 = obs 72 + latent 9), so the teacher checkpoint alone is not deployable.
2. Distillation plant = **option B**: `--task Isaac-ConstrainedALBC-TRPO-SimToReal-v0`. The incumbent recipe's default task (`Isaac-ConstrainedALBC-TRPO-v0`) is the 40 N zero-delay fault-off plant; `finding/352`'s override-only trap applies to the student launch exactly as to a teacher launch, and with `dagger_mix select` β 0.5 half the rollout actions are the student's own, so the rollout plant matters.
3. The report's entropy-collapse and constraint findings are **not retrain grounds** (below).

**Queued, not fired.** `omx queue-launch` run-id `sd_p3b7500_c3_gruselect_s30` → `.hq/work/experiments/runs/sd_p3b7500_c3_gruselect_s30/pending-launch.json` (queued 2026-09-05T11:28:45Z UTC, `queued_commit` 4b257ec, acked gates `finding/264` + `finding/352` — per-launch acks, both pages stay `needs-apply-before-retrain`). Script `/workspace/g0c_runner/student_p3b.sh` (md5 `3c1bc89026954d2ae2732ca606a60883`), `bash -n` clean, both preflights pass (teacher ckpt present, task id registered). Fire from the user's shell, e.g. `tmux new -s sdp3b 'bash /workspace/g0c_runner/student_p3b.sh'`; GPU1; the incumbent's identical recipe took 11 min 38 s. Liveness within 2 min: bytes in `/workspace/g0c_runner/student_p3b.log` and GPU1 memory in `nvidia-smi` — zero bytes is not "still thinking".

**Provenance hole — fix before firing.** `queued_commit` 4b257ec predates `constrained_albc/envs/main/config_simtoreal.py` and the `SimToReal-v0` registration in `envs/main/__init__.py`; both are uncommitted on `exp/koopman-marine-obs`. A launch recorded against a commit that cannot rebuild it is the provenance defect this program was opened to end. Commit them (plus `test_simtoreal_cfg.py`) first.

**What this launch does NOT verify, stated now so nobody reads the marker as proof.**
- `train_student.py` writes no `params/env.yaml` (the 2026-08-10 student run dir holds only events/launch.log/launch.sh/models/wandb, and its launch.log prints no cfg field). So this launch does not close `finding/352`'s six execution-unverified fields. A three-line `dump_yaml` of the env cfg in `train_student.py` would; not added unasked.
- `train_student.py` has no DORAEMON/curriculum handling (grep: 0 hits), so the distillation env starts the curriculum from its initial state. Fault exposure during distillation is therefore ≈ severity 0.01 × p₀ 0.30 — the same limit the incumbent's distillation had. Read the student run's `DORAEMON/mean/fault_severity` at the first readout rather than assuming faults were seen.

**Why entropy collapse and constraints are not retrain grounds.**
- trpo group: p3b final-window `Policy/entropy` −8.41, `mean_noise_std` 0.10 (2× the 0.05 `min_std` floor), `sigma_step` 1/36 of `actor_step`; the collapse signature was already present at it 2092, before the curriculum opened. At the deployed checkpoint (it 7400–7600) entropy −8.46, noise std 0.095. **The incumbent that flew is MORE collapsed**: final window `Policy/entropy` −9.26, `mean_noise_std` 0.083 (`omx reduce tb-final --window 200` on `teacher_iter_budget/trpo_iterbudget_s30_260805_012813`). The deployed numpy policy executes the mean action, so the std never reaches the board. The cost is late-training exploration — consistent with the flat return across the 7500→9999 regression window — which is a note for the next hyperparameter set (`entropy_coef` 0.003 / `min_std` 0.05), not a reason to launch one now.
- constraint group: 10/10 margins positive and 0 violations in the final window; the binding constraint is `thruster_util` (JC/dk 0.821), consistent with the fault curriculum pushing the surviving thrusters toward budget; `barrier_penalty` spikes 3 (max 0.147), MED. Nothing here is a misconfiguration.

**Open leads.** The 17 `needs-experiment` pages the queue verb listed (163, 198, 263, 296, 301, 305, 309, 312, 313, 315, 318, 319, 321, 354, 355, 362, 363) are all teacher-side — exam validity, inertia, thrust band, checkpoint selection. **DEFERRED for this launch**: distilling an already-judged teacher changes none of them. They carry into the next teacher retrain, if one is ever opened; the pre-registered triggers for that are Phase 5 pitch span < 15° or tracking < 50 %, a mission-level rejection of ~6° `hard` attitude error, or measured attitude sluggishness pointing at `set_inertias` (item 10(b)).

**Also on the record.** `test_deploy_constants.py`, named in PLAN Phase 4, does not exist in this repo (`find` returned nothing) — locate or replace before export. The Mac session could not read the user's referenced transcript (`9d19b3a6…` lives on `kim-macbookair`, key not registered); the three restated questions were answered from the report, the wiki, and this tree.

**3.9p addendum (2026-09-05 21:0x) — `joint1_pos` question answered with a new measurement.** The user's 19:56 question in `08_notes/2026-09-05-p3b-phase4-verdict/conversation.ko.md` (that file IS the transcript the user pointed at; the claudian session saved it there at 20:13) asked whether the inert joint1 constraint will hold on the robot. Answer, recorded as wiki `finding/378`: the shipped `joint1_pos` indicator cannot fire because the measured angle wraps at +-2*pi under a 4*pi limit; on the Phase 4 npz the incumbent winds `joint1_target` to 41+ rev in 7/64 envs at `pair34`/`hard` and `pair34_d2`/`hard` (none terminated — cable-wrap signature), while `p3b_7500` and `p3b_final` never exceed 0.49 rev in any of the six configs read. Not a retrain ground; a watchdog on the deploy-side integrator and a fireable (command-side) constraint for the next teacher retrain. The report's constraint group still reads "no issue" — RE-analysis pending, offered to the user.

## Resume block — 3.9q (2026-09-05 23:xx) — student FIRED and FAILED its exam; root cause in the runner; R1/R2 QUEUED

**What happened after 3.9p.** The user approved committing and firing (2026-09-05 "커밋하고 발사까지 해"). Provenance commits a3cc20f (task variant) + 9328805 (ledger); `student_p3b.sh` fired 21:20:16 on GPU1, rc 0 at 21:32:31 (12 min 15 s), run `trpo_sd_p3b7500_c3_gruselect_s30_260905_212022`, TB healthy (teacher_frac 0.4996, loss_latent 0.0030 → 0.0022). Student-mode exam (`sd_p3b_exam.sh`, five configs, cuDNN preamble needed — finding/382) → `.hq/work/p4/sd_p3b7500`. **Verdict: the student is worse than `p3b_7500` on all 20 rows, +0.21 … +3.26°, pairDR 0 (finding/380). Deployment blocked; no pack exported.**

**Root cause (finding/381, HARD gate).** `configure_env_for_student` flips `cfg.doraemon.enable` after `gym.make`, which the env never re-reads: the student rolled out on DORAEMON's frozen initial Beta (payload 1.5 ± 0.27 kg, inertia 1.2, water 1010, fault severity 0.01 → fault-free) and, because the runner also substitutes a fresh `DomainRandomizationCfg()`, on thrust band (0.7, 1.3) and delay (0, 0) instead of the SimToReal (0.5, 2.0) / (0, 3). Option B was defeated silently. Same construction for every student since 2026-04-21, including the deployed inc9998 — re-read finding/274 / decision/186 through this. Second mechanism (finding/380 §4): the exam horizon is 155 s against 30 s training episodes; in-loop latent error grows 3× over the exam and is largest in idle segments.

**Patched in tree, UNCOMMITTED:** `constrained_albc/envs/_core/student/runner.py` (drop `_doraemon`, keep task DR, print the plant line) and `scripts/train_student.py` (`params/env.yaml` dump). `py_compile` clean. **Commit these with the launch** — `queued_commit` was recorded at 9328805, which does not contain them; R1/R2 scripts refuse to start from an unpatched tree.

**Queued (approval required — `omx queue-launch`, proposal `retrain-simtoreal-2026-09`):**
- **R1** `sd_p3b7500_c3_dr5_s30` — `/workspace/g0c_runner/student_p3b_r1.sh`, GPU1: recipe/teacher/task/seed verbatim, only the runner fix. Isolates the plant.
- **R2** `sd_p3b7500_c3_dr5_ep155_s30` — `student_p3b_r2.sh`, GPU0 (waits for `SD_INC_EXAM_DONE`): R1 + `env.episode_length_s=155.0`. R2 − R1 isolates the horizon. Confound: 5× fewer resets (≈6k vs ≈33k DR draws).
Each script chains its own exam (`sd_exam_generic.sh` → `.hq/work/p4/sd_r1`, `sd_r2`; markers `SD_R1_EXAM_DONE`, `SD_R2_EXAM_DONE`). Score with `p4_score.arm_pair("sd_r1","p3b_7500",CORE+["pair34_d2"])`, then `("sd_r2","sd_r1",…)`. Success = student inside the 0.10° / 1.6 pp floors against the teacher on pair34 and pair34_d2 at none and hard; the healthy/none latent bias (finding/380 §3) should collapse toward the training loss if finding/381 is the mechanism.

**Control running now:** the incumbent student `pack_inc9998_gru` on the same exam → `.hq/work/p4/sd_inc9998` (`sd_inc_exam.sh`, GPU0, marker `SD_INC_EXAM_DONE`, started 23:09). Score against `inc13w` (its teacher, teacher-mode) and against `sd_p3b7500` (student vs student — the deployment question). Its `latent_none.npz` time profile tells whether the deployed student drifts the same way.

**Also on the record.** finding/382: the Phase 4 exam's `thrust_coefficient_scale=[0.5,2.0]` override never reached `eval.py static` (all arms ran (0.7, 1.3) at hard; verdicts stand, the "full §5 plant" claim of inc13w does not) — RE-analysis of `diagnose-20260905-140134` owed; cuDNN preamble scope corrected (GRU RNN path too). finding/379 (vacuous cfg test) posted earlier, uncommitted. Monitors: the 3.9p monitors died with that session — re-arm on `SD_INC_EXAM_DONE`, `SD_R1_EXAM_DONE`, `SD_R2_EXAM_DONE`.

**3.9q addendum (2026-09-05 23:5x) -- R1/R2 FIRED, follow-ups QUEUED.** User approved R1+R2 23:3x: fix commit 4438492, ledger f861a04, queue artifacts re-recorded at f861a04. R1 (`sd_p3b7500_c3_dr5_s30`) ran 23:25-23:38 on GPU1, rc 0; `params/env.yaml` shows randomization enable true, thrust (0.5, 2.0), delay (0, 3), fault fail_prob 0.3 / dead_frac 0.5, doraemon enable false -- finding/381's verification owed is half paid (the exam readout remains). Its exam runs on GPU1 (`.hq/work/p4/sd_r1`). R2 starts on GPU0 when `SD_INC_EXAM_DONE` lands. Literature pass finding/383 (RMA, HORA, ROA, Lee 2020, NORBC). **Queued on user request ("후속도 큐에 걸어줘"), marker-chained, approval still required to fire:** R3a `sd_p3b7500_c3_dr5_beta0_s30` (beta 1->0, GPU1 after SD_R1_EXAM_DONE), R3b `sd_p3b7500_tcn_dr5_s30` (TCN + cuDNN, GPU0 after SD_R2_EXAM_DONE), R4a `sd_p3b7500_c3_dr5_it10k_s30` (10k it, GPU1 after SD_R3A_EXAM_DONE). Wrappers `/workspace/g0c_runner/student_p3b_r3a.sh|r3b.sh|r4a.sh` -> `student_arm.sh` -> `sd_exam_generic2.sh` (highest ckpt, encoder arg). NOT queued: R4b trainable actor (needs runner + export changes first). Fire order once approved: `tmux new -d -s sdr3a 'bash /workspace/g0c_runner/student_p3b_r3a.sh'` etc.; each waits for its marker so all three can be started at once.

---

## 3.9r (2026-09-06 00:4x) -- R1 FAILED the pre-registered floor; finding/381 RESOLVED (mechanism confirmed, insufficient for the score); control exam reframes Phase 4; all remaining runs on GPU1

**Resume here.** Session continued after compaction; monitors re-armed. Read finding/384 and finding/385 before anything else.

**R1 `sd_p3b7500_c3_dr5_s30` (plant fix only) -- finding/384.** vs teacher `p3b_7500`: 19/20 rows `cand worse` (+0.25 to +2.27 deg), only healthy/hard -0.15 with 18/64 envs (tail). Pitch pair34/none +0.18, pair34_d2/none +0.17. vs old student `sd_p3b7500`: 8 better (every medium/hard, -0.12 to -1.70), 10 tie, 2 worse (pair34/none +0.13, pair34_d2/medium +0.47). vs deployed `sd_inc9998`: worse on all healthy rows and most delay rows, better on pair34 / pair34_d2 medium-hard by 0.9-6.4 deg. Latent: shared bias^2 collapsed 2.4-17x on all 10 cells (healthy/none 0.033 -> 0.008) = finding/381 mechanism confirmed and **381 set to resolved** (env.yaml + bias collapse both in). Per-env bias^2 unchanged (0.03-0.05 at none), within-episode variance 3x, drift past 30 s steeper at hard. `student/loss_latent` at it 1000: old 0.0022 (converged, nominal-concentrated plant), R1 0.0201 (falling 17%/200 it), R2 0.0168 (falling). The 1000-it budget was tuned on the defective plant.

**Control `sd_inc9998` (deployed student) -- finding/385.** vs its teacher inc13w: nominal rows worse (healthy/none +0.15, healthy/hard +0.62 surv +3.1 pp), pair34 tie to +0.28, but every delay row better by 0.24-2.29 and pair34_d2 by 6.2-10.5 deg (teacher 9.36 at none, student 1.51). Cause: under delay the student latent is a constant wrong vector (mse 0.596, shared bias^2 0.588) -> a damped prior on the frozen actor. Not competence. vs `p3b_7500` at none: candidate teacher better on 17/20, delay margin +0.24 (d1) / +0.40 (d2), fault margin +0.35 to +6.9. Phase 4 report compared teacher modes; deployment verdicts need student-mode exams on both sides. **RE-analysis of `diagnose-20260905-140134` now owed for finding/378 + /382 + /385** (still offered, not decided).

**R2 `sd_p3b7500_c3_dr5_ep155_s30` (R1 + 155 s episodes) -- early read, healthy only.** vs R1: none -0.08 tie, soft -0.07 tie, medium +0.18 worse, hard +0.98 worse; vs teacher +0.18 to +0.82. Latent time growth is GONE (healthy/none 0.052 -> 0.039, hard 0.119 -> 0.096) but the 0-5 s error is 1.5-1.7x R1 (5x fewer episode starts per iteration). Horizon explains the drift signature, not the gap. Full 5/5 pending (`.hq/work/p4/sd_r2`, marker `SD_R2_EXAM_DONE`).

**GPU move (user, 00:28): stonefish owns GPU0.** R2 exam killed on GPU0 mid-pair34 and restarted re-entrantly on GPU1 at 00:29 (healthy kept; `sd_r2_exam.log` carries the note); `student_p3b_r3b.sh` re-pinned `GPU=0 -> GPU=1` and its waiting session relaunched 00:28. R3a started 00:37:48 on GPU1 (`trpo_sd_p3b7500_c3_dr5_beta0_s30_*`). Chain now: R2 exam (GPU1) -> `SD_R2_EXAM_DONE` -> R3b (GPU1, TCN+cuDNN); R3a exam -> `SD_R3A_EXAM_DONE` -> R4a (GPU1, 10k it, expect ~3 h on the shared 8 GB card). Two processes at a time on GPU1; do not add a third.

**Open leads at this point** (`omx wiki list`): blocking = finding/264, finding/352 (unchanged, acked on every queue entry); finding/381 resolved this round. needs-experiment 24 incl. 380, 382, 383, 384, 385. Nothing dropped; the RE-analysis is the only owed non-run item.

**Next reads, in order:** R2 5/5 -> `arm_pair("sd_r2","sd_r1",CORE+["pair34_d2"])`; R3a -> vs `sd_r1`; R3b -> vs `sd_r1` (ckpt = highest `student_*.pt`); R4a -> vs `sd_r1` and its `student_999.pt` vs R1 for reproducibility. Post one finding per arm; then decide R4b (trainable actor, needs code + export path; not queued).

---

## 3.9s (2026-09-06 01:4x) -- R2 FAILED the floor (finding/386: horizon is not the lever); R3a early read is the first student inside the floor; GPU0 hand-off automated

**Resume here.** Read finding/386 (R2) and the R3a partial below; R3a's own finding lands at 5/5.

**R2 `sd_p3b7500_c3_dr5_ep155_s30` (R1 + 155 s episodes) -- finding/386.** vs teacher 20/20 worse (+0.11 pair34/medium .. +2.02 healthy_d2/hard); vs R1 7 better / 5 worse / 8 tie. The horizon removed the in-episode latent drift (late-window error -30..45 %, within-episode var 2-3x lower on all 10 cells read) but bias^2 did not move and the early-window error rose 30-70 %, so faulted rows at none-medium gain 0.3-0.9 and every hard row loses 0.4-1.0. Mechanism for the slower start (5x fewer resets per 49M steps) is MED, not ablated. Open lead R5 = beta anneal + 155 s, low priority, not queued.

**R3a `sd_p3b7500_c3_dr5_beta0_s30` (R1 + DAgger beta 1->0 over 600 it) -- PARTIAL, 2/5 configs at 01:32.** Run `trpo_sd_p3b7500_c3_dr5_beta0_s30_260906_003754`, trained 00:37-00:59 on GPU1 (21 min sharing the card with the R2 exam), plant line verbatim (thrust (0.5,2.0), delay (0,3), payload (0,3), inertia (0.4,2.0), fault 0.3), `env.yaml` 693 lines. vs teacher: healthy none/soft/medium +0.099/+0.071/-0.036 (ties), hard -0.587 (33/64, better); pair34 none/soft +0.115/+0.150 (just over the 0.10 floor), medium -0.129 (better), hard -0.069 (tie). vs R1: all 8 cells better, -0.16..-0.63. vs deployed sd_inc9998 pair34: better on all 4 (hard -7.0, surv +3.1 pp). Latent mse is HALF of R1's on both configs (healthy/none 0.047->0.029, healthy/hard 0.093->0.048, pair34/none 0.038->0.021, pair34/hard 0.064->0.042) with the time growth gone (healthy/hard 0-5 s 0.056 -> 100-155 s 0.053); the gain is per-env bias^2, not variance. Caveat for anyone reading TB: R3a's training `student/loss_latent` at it 800-1000 is 0.037 vs R1's 0.020 -- beta->0 measures the loss on the student's own (harder) state distribution, so the training loss ranks arms backwards; use the exam latent error only. 6 of 8 cells inside the floor so far (R1: 0 of 20). Remaining: healthy_d1 (~01:50), healthy_d2 (~02:05), pair34_d2 (~02:20) -- the delay rows are where R1 lost +1.6..+2.3 at hard; that is the real test.

**Consequence for the queue.** R4a (10k it) keeps beta 0.5 -- it was queued before R3a read. If R3a holds at 5/5, the budget axis should be re-run on top of the anneal (R4c = beta 1->0 + 10k it), which is a NEW launch: `omx queue-launch` + user approval, not a re-pin. R4a stays useful as the pure budget read against R1 and for the student_999 reproducibility check.

**GPU0 hand-off (user 01:0x: "stonefish 가 다 끝나면 gpu0 사용해도 괜찮아").** The stonefish job is `runlist.sh sep.txt` -> `run_replay.sh` -> `ros2 launch stonefish_slam` inside `stonefish_dev` (host PID 3036699, started 00:31). Host-side watcher `~/workspace/1_code/5_marinelab_ws/gpu0_watch.sh` (nohup, pid 3443485, log `gpu0_watch.log` next to it; `g0c_runner/` is root-owned so the marker sits one level up) touches `/workspace/GPU0_FREE` after 5 consecutive minutes without those processes. `student_arm.sh` wait loop gained `ALT_GPU_MARKER`/`ALT_GPU` (wait block self-checked both ways); `student_p3b_r4a.sh` carries `ALT_GPU_MARKER=/workspace/GPU0_FREE ALT_GPU=0`, re-queued 01:09:58 (`sdr4a`), so R4a starts on GPU0 alone the moment the marker appears, else on GPU1 after `SD_R3A_EXAM_DONE` as before. R3b stays GPU1 (same-GPU sharing is the expensive kind: training 21 min vs 12 min alone; cross-GPU sharing cost ~nothing). Caveat: a follow-on stonefish job launched after the marker would share GPU0 with R4a.

**Chain state at 01:4x.** R3b (TCN, cuDNN) training started 01:38:43 on GPU1 (3.1 GB) beside the R3a exam; exam follows into `.hq/work/p4/sd_r3b`. R4a waiting (`sdr4a`). Timeline: R3a 5/5 ~02:20 -> R4a on GPU1 ~02:20-04:45 (or earlier on GPU0) -> R4a exam ~05:40; R3b train ~02:00, exam ~03:00. Whole chain ~06:00 on GPU1-only, ~04:15 if GPU0 frees by 01:30.

**Open leads (`omx wiki list`, 01:4x):** blocking finding/264, finding/352 unchanged (acked on every queue entry). needs-experiment now 25 = the 24 of 3.9r + finding/386. Nothing dropped.

**Next reads, in order:** R3a 5/5 -> `arm_pair("sd_r3a","sd_r1",CORE+["pair34_d2"])`, vs teacher, vs sd_inc9998; pitch/roll; latent on delay configs -> finding, then decide R4c with the user. R3b -> vs `sd_r1` and vs `sd_r3a`. R4a -> vs `sd_r1`, and its `student_999.pt` vs R1 (reproducibility). Post one finding per arm; ledger + commit after each.

---

## 3.9t (2026-09-06 02:3x) -- R3a 5/5: first student inside the floor (finding/387); R3b (TCN) failing; R4a running on GPU0; R4c QUEUED pending approval

**Resume here.** Read finding/387. Two decisions are the user's: (1) approve or drop R4c (`pending-launch.json` below); (2) whether R4b (student actor fine-tune) gets code time. Nothing fires without them.

**R3a `sd_p3b7500_c3_dr5_beta0_s30` -- finding/387.** att vs teacher: 11 tie / 2 better (healthy/hard -0.59, pair34/medium -0.13) / 7 worse; the 7 = pair34 none/soft +0.115/+0.150, healthy_d1 none +0.100, pair34_d2 none/soft/medium +0.15..+0.17, and hard+delay +1.65/+1.83/+1.15. vs R1 18/20 better (-0.15..-1.16), the 2 losses are the hard+delay tail. vs deployed sd_inc9998: every faulted row better (pair34/hard -7.0 surv +3.1 pp, pair34_d2/hard -5.2), nominal tie, hard+delay +0.13..+0.18 behind. Pitch 15 tie / 2 better / 3 worse; roll 11 tie / 2 better / 7 worse (pair34-type none/soft +0.11..+0.17, delay hard +0.8..+1.5). Latent mse halves on all 14 cells (per-env bias^2), drift flat; the estimator now explains ~half the plant variance per embedding dim (R1: almost none). Not fixed: constant offset at the nominal point (true latent variance ~0, error 0.02-0.09; shared bias^2 slightly above R1 on healthy/healthy_d2), and the delay sensitivity (same latent error, +0.59 win without delay -> +1.65 loss with one step). Pre-registered floor on pair34 missed by 0.015/0.050; the exam moved from 0/20 (R1, R2) to 13/20 at-or-better-than floor.

**R3b `sd_p3b7500_tcn_dr5_s30` (TCN window 27 steps, cuDNN) -- PARTIAL 1/5 at 02:18, failing.** Run `trpo_sd_p3b7500_tcn_dr5_s30_260906_013849`, trained 01:38-02:01 on GPU1 (23 min beside the R3a exam; exam launched with `--encoder_type tcn`, verified on the process cmdline). healthy vs R1 +0.66/+0.34/+0.36/+0.57, vs teacher +0.92 (0/64) / +0.67 / +0.63 / +0.42, vs R3a +0.60..+1.00. Latent mse at healthy/none 0.184 = 4x R1, shared bias^2 0.052 and within-episode var 0.060 both large: a 0.54 s window cannot integrate the latent. Exam left running to 5/5 for the record (GPU1, ~03:00); finding at 5/5, expected FAIL.

**R4a `sd_p3b7500_c3_dr5_it10k_s30` (beta 0.5 + 10k it) -- RUNNING on GPU0.** GPU0 hand-off worked end to end: stonefish `runlist.sh` gone 02:12, `gpu0_watch.sh` touched `/workspace/GPU0_FREE` 02:16:46, R4a read it 02:16:58 and started on GPU0 alone (HEAD 9e0dfa5, dirty 0, run `trpo_sd_p3b7500_c3_dr5_it10k_s30_260906_021704`). Rate 93 it/min (177 it in 114 s; R1 on a shared card was 77) -> 10k done ~04:05, exam (`.hq/work/p4/sd_r4a`, GPU0) ~04:35. Reads: vs `sd_r1` (budget alone), vs `sd_r3a`, and `student_999.pt` vs R1 for reproducibility.

**R4c `sd_p3b7500_c3_dr5_beta0_it10k_s30` -- QUEUED 02:30, NOT fired.** `omx queue-launch` -> `.hq/work/experiments/runs/sd_p3b7500_c3_dr5_beta0_it10k_s30/pending-launch.json` (queued_commit 9e0dfa5, gates finding/264 + finding/352 acked per-launch as on every entry of this program; the "proposal not planned in any campaign" warning is the standing one). Recipe = R3a + MAXIT 10000, ANNEAL kept at 600 so R4c-R3a isolates budget and R4c-R4a isolates the anneal at 10k. Wrapper `/workspace/g0c_runner/student_p3b_r4c.sh` (GPU1 after `SD_R3B_EXAM_DONE`, or GPU0 after `SD_R4A_EXAM_DONE` via ALT marker). To fire after approval: `tmux new-session -d -s sdr4c "bash /workspace/g0c_runner/student_p3b_r4c.sh"`, then confirm `student_r4c.log` shows `start=` and a python process on the card. Predicted outcome is in the artifact. If the user prefers to wait for R4a's read (04:35) before approving, that costs nothing: the wrapper waits on markers anyway.

**Chain state at 02:3x.** GPU0: R4a training. GPU1: R3b exam (pair34 ~02:30, then 3 configs alone ~6-7 min each, done ~03:00). tmux `sdr3b`, `sdr4a`. Markers present: SD_INC/R1/R2/R3A_EXAM_DONE, GPU0_FREE. Monitors: `b2a3f0et9` (chain), `btzntkwy0` (GPU0 hand-off + R4a + R2 log). Finish of everything queued so far: R4a exam ~04:35; R4c, if approved at 03:00, ~05:30.

**Open leads (`omx wiki list` at queue time):** blocking finding/264, finding/352 unchanged. needs-experiment 26 = 3.9s list + finding/387. Nothing dropped; R5 (beta anneal + 155 s) stays recorded in finding/386, low priority.

**Next reads, in order:** R3b 5/5 -> finding (expected FAIL, vs `sd_r1` and `sd_r3a`); R4a 5/5 -> finding (budget alone; decides how much R4c is worth); then user decisions on R4c / R4b. Ledger + commit after each.

---

## 3.9u (2026-09-06 03:1x) -- R3b (TCN) FAILED 20/20 (finding/388, resolved); R4a at it ~4k on GPU0; GPU1 idle; R4c still pending approval

**Resume here.** Read finding/387 (R3a, the live recipe) and finding/388 (R3b, closed). Pending user decisions unchanged from 3.9t: approve/drop R4c; whether R4b gets code time.

**R3b `sd_p3b7500_tcn_dr5_s30` -- finding/388, status resolved.** vs teacher 20/20 worse (+0.42..+2.82; 0/64 envs better at `none` on the healthy configs), vs R1 18 worse / 2 tie, vs R3a 20/20 worse, vs deployed 16 worse (the 4 "wins" are pair34-type medium/hard where the deployed student's own constant latent fails, finding/385). Estimator regime is different from the GRU arms: in-episode variance 5-8x R1, shared bias^2 at `none` 4-6x, and the error grows 2.8x across the episode (0.07 -> 0.21 at healthy/none) -- a 0.54 s window re-derives the latent from half a second of history and wanders with the state. Closes the windowed-estimator (HORA-style) arm of finding/383 on this plant at this budget. Leads recorded, not queued: longer TCN window (5-10 s), TCN under beta 1->0.

**R4a `sd_p3b7500_c3_dr5_it10k_s30` -- RUNNING, GPU0.** it 3903 at 03:04 (47 min, 83 it/min; slower than the first 2 min's 93 as the student data buffer grows), `student/loss_latent` 0.0163 at it ~3.9k (R1 at it 1000: 0.020; still falling -- but remember finding/386's caveat, this is beta 0.5 so it IS comparable to R1, not to R3a). 10k at ~04:17, exam `.hq/work/p4/sd_r4a` on GPU0 ~04:17-04:50.

**GPU1 is idle from 03:02** (R3b exam done, marker `SD_R3B_EXAM_DONE`). R4c's wrapper would take it the moment it is fired; until the user approves, nothing runs there. tmux: `sdr4a` only.

**Scoreboard of the student-distillation round so far (att vs teacher, 20 rows each):** R1 0 tie / 1 better / 19 worse (384); R2 0 / 0 / 20 (386); R3a 11 / 2 / 7 (387); R3b 0 / 0 / 20 (388); R4a pending; R4c queued. The only lever that moved the score is the rollout distribution (beta 1->0); horizon and window did not. Residual after R3a: pair34 none/soft +0.115/+0.150, pair34_d2 none-medium +0.15..+0.17, hard+delay +1.2..+1.8.

**Open leads (`omx wiki list`, 03:1x):** blocking finding/264, finding/352 unchanged. needs-experiment: 3.9t list minus nothing (finding/388 posted as resolved, so the count stays 26). Nothing dropped.

**Next reads:** R4a 5/5 (~04:50) -> finding (budget alone vs R1; vs R3a; `student_999.pt` vs R1 for reproducibility) -> ledger + commit. Then the user's R4c / R4b call.

---

## 3.9v (2026-09-06 05:0x) -- R4a FAILED 20/20 (finding/389); a same-seed second realization of R1 measured the exam noise floor; the hard-level mean is tail-made; both GPUs idle; R4c still pending approval

**Resume here.** Read finding/387 (R3a, the candidate recipe) and finding/389 (R4a + reproducibility + tail). Pending user decisions: (1) approve or drop R4c (`pending-launch.json` unchanged); (2) whether R4b gets code time; (3) NEW: whether the next GPU-hours go to a second realization of R3a instead of R4c -- finding/389 measured the single-realization noise at ~0.1 (none/soft) and 0.2-0.7 (medium/hard), a verdict class wide, and R3a's 11 teacher-ties are single-realization. Nothing fires without them.

**R4a `sd_p3b7500_c3_dr5_it10k_s30` -- finding/389, needs-experiment.** att vs teacher 0 tie / 0 better / 20 worse (+0.10..+2.61); vs R3a 4 tie / 0 / 16; vs R1 8 better (all none/soft, -0.10..-0.36) / 3 tie / 9 worse (all medium/hard, +0.18..+1.05); vs deployed 5 / 7 / 8. `loss_latent` floors at it ~2k at R1's value (last-50 mean 0.0186 vs 0.0188) and 8k more iterations move nothing. Budget axis on beta 0.5 closed; finding/384's under-training lead closed. Latent: best of the three at `none` (healthy 0.021), between R1 and R3a at `hard`, within-episode variance 0.001-0.007, no drift -- and still worse att than R1 at hard, see tail.

**Reproducibility `sd_r4a999` = R4a's `student_999.pt` (R1 recipe, same code, same seed s30).** Encoder weights relL2 0.88 vs R1's `student_999.pt` (max |dw| 0.70). Exam vs R1: 11 tie / 2 better / 7 worse -- none/soft within 0.10 on 9 of 10 rows, medium/hard |delta| 0.19-0.72 on 8 of 10. vs teacher 1 tie / 19 worse (R1 was 0/1/19): the verdict class reproduces, the cells do not. Its latent mse is 2-7x R1 at the same score (pair34/none 0.268 vs 0.038, bias on dims whose true variance is ~0), so latent mse is not a sufficient statistic for the score. Consequence: between single realizations a cell delta below ~0.3 (medium) / ~0.7 (hard) is noise; R4c - R3a is readable at the 0.10 floor on none/soft rows only.

**Tail (finding/389 section 4).** Per-env att mean / median / P90: teacher healthy/hard 3.33 / 0.66 / 5.47 -- the mean is the top decile. R3a ties the teacher MEDIAN at hard on all four core configs (0.67 vs 0.66, 1.08 vs 1.07, 0.81 vs 0.82, 1.00 vs 0.85); its hard+delay losses are P90 (9.0 vs 5.0, 10.0 vs 4.5). R4a is worse than R3a in both median and P90 at hard; per-env corr(att, latent mse) is +0.4 for R3a/R4a at hard (bimodal) and ~0 for R1 (uniformly mediocre). Scoring lead recorded: report median and P90 per cell next to the mean. The mean-based pre-registered floor is not re-declared.

**Scoreboard (att vs teacher, tie / better / worse, 20 rows):** R1 0/1/19 (384), R2 0/0/20 (386), R3a 11/2/7 (387), R3b 0/0/20 (388), R4a 0/0/20 (389), R1-second-realization 1/0/19 (389). R4c queued, not fired.

**Chain state 05:0x.** Both GPUs idle from 04:55 (the stonefish job ended 02:12; the user allowed GPU0 after it). tmux empty. Markers present: SD_INC/R1/R2/R3A/R3B/R4A/R4A999_EXAM_DONE, /workspace/GPU0_FREE. If R4c is approved: `tmux new-session -d -s sdr4c "bash /workspace/g0c_runner/student_p3b_r4c.sh"` -- the wrapper checks WAIT_MARKER (`SD_R3B_EXAM_DONE`, present) before the ALT marker, so it starts at once on GPU1; confirm `student_r4c.log` shows `start=` and a python process on GPU1. Monitors of this session end with it; re-arm on `student_r4c.log` / `sd_r4c_exam.log` if it fires. Scratch symlink dir `/workspace/g0c_runner/r4a999_ckpt/` and `.hq/work/p4/r4a_*.py` are re-usable for any later realization exam (point the symlink at another ckpt, change the arm/tag).

**Open leads (`omx wiki list`, 05:0x):** blocking finding/264, finding/352 unchanged. needs-experiment 27 = 3.9u list + finding/389. Nothing dropped.

**Next reads:** none pending on the machine. The three user decisions above come first.
