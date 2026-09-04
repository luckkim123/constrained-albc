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
