# HANDOFF — teacher-final-replicate

Written 2026-08-10 14:15 KST for context compaction. **Read this before doing anything.**
The PLAN (`PLAN.md`, `omx program-lint ok:true`) is the authority on config; this file is the
authority on live state and on what has already been settled.

Deadline: field test **Thursday 2026-08-13**. Today is Monday 2026-08-10.

---

## 1. Live state — two teacher runs are training RIGHT NOW

Launched 14:04 KST with explicit user approval. **Do not relaunch, do not modify, do not kill.**

| arm | run id | machine | seed | iters | rate | ETA |
|---|---|---|---|---|---|---|
| R30 | `trpo_replicate_s30_260810_140415` | workstation container `marinelab-isaaclab`, cuda:0 (RTX 4070) | 30 | 10000 | **3.44 s/iter** measured | today **23:38** |
| R31 | `trpo_replicate_s31_260810_140414` | DGX (`ksm-nas`), native | 31 | 10000 | **5.560 s/iter** measured | tomorrow **05:31** |

Progress at 14:14: R30 `model_150.pt`, R31 `model_100.pt`, 3 processes each. Both verified by
**artifact** (`model_50.pt` present), not by exit code.

Run group `teacher_final_replicate` under `logs/rsl_rl/albc_trpo_teacher/`. Checkpoints in
`<run>/` on DGX and via the `experiments/rsl_rl/.../train` symlink on the workstation.

Check liveness:

```bash
# workstation
ssh -o ConnectTimeout=15 ksm@141.223.223.195 'docker exec marinelab-isaaclab bash -c \
  "cd /workspace/constrained-albc/logs/rsl_rl/albc_trpo_teacher/teacher_final_replicate/latest \
   && ls model_*.pt | sort -V | tail -1; pgrep -cf [t]rain.py"'
# DGX
ssh -o ConnectTimeout=15 ksm-nas 'cd ~/workspace/constrained-albc/logs/rsl_rl/albc_trpo_teacher/teacher_final_replicate/latest \
   && ls model_*.pt | sort -V | tail -1; pgrep -cf "[t]rain.py"'
```

⚠️ `pgrep` **needs `-f`** — the process name is `python3`, not `train.py`. A check without `-f`
returns 0 and reads as a dead run. This already produced one false "both FAILED" report today.

Launch scripts kept for provenance: container `/workspace/launch_R30.sh`, DGX `~/launch_R31.sh`.
Logs: container `/workspace/constrained-albc/R30_launch.log`, DGX `~/R31_launch.log`.

Both sets of paths above are the **fire-time** ones. On 2026-08-14 R30's three artifacts were
filed per `scripts/finalize_run_log.sh` into the run's own dir
`logs/rsl_rl/albc_trpo_teacher/teacher_final_replicate/trpo_replicate_s30_260810_140415/`
as `launch.sh` / `launch.log` / `launch.status`, with a pointer at
`.omx/runs/replicate_s30/stdout-pointer.json`. R31's DGX-side copies were not touched.

## 2. What these runs are — and are NOT

They replicate the **incumbent** `teacher_iter_budget/trpo_iterbudget_s30_260805_012813`
(`model_9998`), which won the last finalist. They do **not** replicate Arm W.

Only 3 keys differ from the incumbent: `resume` true→false (dropping an unreconstructible
`RESUME_SRC` chain), `max_iterations` → 10000 absolute, and seed (30 / 31). Everything else —
`kl_ub` 0.12, `performance_lb` 250.0, `alpha` 0.5, `step_interval` 250, `buffer_size` 2000,
`min_episodes` 200, `entropy_coef_per_dim` ×1, `num_mini_batches` 4, `num_envs` 4096, obs 72 —
is held. The only CLI override is `env.fault.enable=True`. The held-keys table in `PLAN.md` is
the config-provenance gate that the two prior accidents lacked.

**Predicted outcome is a null** and that is acceptable. Value delivered regardless: a final
artifact with single-file provenance, plus the first seed-variance estimate for this plant
generation. R30 additionally tests whether the incumbent's resume chain left it in a worse basin.

## 3. Settled by audit — do NOT re-litigate these

A 15-agent investigation (2026-08-10) overturned four premises of the original brief. Full
writeup and evidence: vault `0_Project/in_progress/albc/notes/2026-08-10-final-training-prompt-audit.md`
(committed `6cfe1d1c`).

1. **`entropy_coef_per_dim` ×2 is NOT a validated improvement.** The "PASS" compared the probe
   against a 4096 *workstation* run. Against the correct single-variable control
   (`teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713`, same DGX, same 16384 envs, differing
   only in `entropy_coef_per_dim`), measured at matched windows and independently reproduced:

   | window | metric | probe ×2 | control ×1 |
   |---|---|---|---|
   | 400–600 | `DORAEMON/success_rate` | 0.06878 | 0.32798 |
   | 400–600 | `Train/mean_reward` | 214.67 | 236.99 |
   | 900–1100 | `DORAEMON/success_rate` | 0.42469 | 0.73864 |
   | 900–1100 | `Train/mean_reward` | 244.29 | 260.80 |
   | 900–1100 | `DORAEMON/mode` | **−2 (contracting)** | 0 (expanding) |

   Sigma recovery is real (0.13067 → 0.17405) and used the correct control; the performance claim
   did not. Do not put ×2 into any final run without a fresh, correctly-controlled probe.

2. **The deployment fixes the brief lists as "unapplied" are all applied.** Joint accumulator
   reset was fixed 2026-06-15 (`code/agent-jetson/robot/albc_rl/numpy_port/np_policy.py:218-220`,
   commit `b28648c`). Gyro passthrough, joint delta, rotateImu, IMU stale, numpy keepdims: all
   applied. The cited path `np_policy.py:75,87` points at a **stale Jun-12 duplicate** under
   `deploy/student_albc_260607/numpy_port/` — copying that file to the board would reintroduce
   the accumulator defect.

3. **The two machines are on different branches, and it is inert.** Workstation
   `exp/koopman-marine-obs@8a41029` (8 commits unpushed, all the NULLed Koopman line, source
   additions default-off), DGX `main@1062dc2`. `main` is a strict ancestor; no reward/DR/
   DORAEMON/algorithm file differs. **Mitigation already baked into the plan**: `eval.py` differs
   by +234 lines and is the selection instrument, so **all selection runs on the workstation**
   with one `eval.py` and one anchor. DGX checkpoints get copied, never scored in place.

4. **The curriculum formula is right in form, wrong as a budget.** `(max_iterations/step_interval)
   × kl_ub` reproduces the *sum of per-step KL* (4.74 predicted vs 4.5599 measured for Arm W) but
   that is 6.6× smaller than the "distance to full DR" (31.2855) the same documents budget
   against, and it over-predicts ~2× after saturation. `kl_ub` 0.06 × 20000 iters did **not**
   preserve curriculum distance in practice — Arm W ended 0/21 saturated.

Also settled: `performance_lb` re-derivation is **deferred to the next round** (inputs recorded
in the audit note: use DR-saturated runs only, and the gate's boundary statistic is the **median**,
not p25, because `alpha = 0.5`). Changing it now would make this round incomparable.

## 4. Measured constants — use these, do not re-measure

| quantity | value | source |
|---|---|---|
| s/iter, workstation 4096 | 3.44 | Arm W full 19999-iter run; R30 reconfirmed |
| s/iter, DGX 4096 solo | 5.56 | `bench_spark`, `seed_floor_dgx` seed 30; R31 reconfirmed |
| s/iter, DGX 4096 ×2 concurrent | 12.0 each | `seed_floor_dgx` seeds 31/32 — **no parallel gain** |
| s/iter, DGX 16384 | 18.37 | `dgx16k` 0–13400 |
| s/iter, DGX 32768 | 34.9 | flagship + pilot |
| `bias_ema_alpha` | 0.99 | incumbent `env.yaml:389` |
| DORAEMON saturation | iter **7250** (not 7251) | `dgx16k` `curriculum_trajectory.json` |

The brief's three contradictory timing numbers: `18.07s` was right; `7.1 s/iter` and
`ETA 4:57:38` were startup-window artifacts. **No pilot run is needed** — completed runs carry
steady-state timing.

## 5. Critical path — the deploy chain (NOT the training)

**The ship blocker is here.** Board `np_policy.py:57` hardcodes `POLICY_OBS_DIM = 69`; every pack
from the current plant generation is 72D. `:153-155` raises `ValueError` on mismatch, so the
policy will not load at all. User authorised board modification 2026-08-10.

Board repo (readable from this Mac, its own git repo, origin `HERO-Lab-POSTECH/agent-jetson`):
`/Users/kimseungmin/ksm_Obsidian/0_Project/in_progress/albc/code/agent-jetson/`, currently at
`edd735c`, clean.

### Port spec — fully determined, verified against sim

The 3 extra channels are `_bias_ema`, landing at obs `[69:72]`, immediately after the integral.

| sim | board |
|---|---|
| `policy_obs = cat(..., _error_integral(3), _bias_ema(3))` (`albc_env.py:1228-1235`) | obs ends with `self._integral` (`np_policy.py:291`) — append in the same place |
| `err3 = [att_rp_err(2), yaw_rate_err]` (`:1390-1397`) | **already computed** as `err` at `np_policy.py:278` — nothing new to derive |
| `_yaw_rate_err = ang_cmd[2] - root_ang_vel_b[2]` (`:1351`) | `cmd_3[2] - ang_vel_b[2]` (`:262`) — same sign |
| `_att_rp_err = atan2(sin(raw), cos(raw))` (`:1350`) | `_wrap_angle(cmd_3[:2] - euler[:2])` (`:261`) — same wrap |
| `_bias_ema = a*_bias_ema + (1-a)*err3`, `a=0.99` (`:1398`) | one line to add |
| `_bias_ema[env_ids] = 0.0` on reset (`:1835`) | add to `reset()` (`:181`) |

Net change: `POLICY_OBS_DIM` 69→72, one EMA line, one concat term, one reset line.

**One open question, to be settled by parity and NOT by reading the call graph**: sim updates
`_bias_ema` inside `_get_rewards` (`:1398`) while obs is assembled in `_get_observations`
(`:1234`), so whether step *t*'s obs carries the *t* or *t−1* value depends on Isaac Lab's step
order. If the board update is placed one step off, 1e-5 parity fails immediately and the fix is
to move the update. Do not guess it from source.

### STATUS 2026-08-10 15:20 KST — steps 1-3 DONE, step 4 blocked on hardware

| step | state |
|:--|:--|
| 1. export 72D pack | **DONE** `deploy/student_final_round/pack_inc9998_gru_260810_150713`, self-close CLOSED |
| 2. GRU + TCN both | **DONE 16:22.** TCN student `..._tcn_select_inc9998_s30_260810_160551` (1000/1000, rc=0, loss_total 0.002264 vs GRU 0.002990) -> `pack_inc9998_tcn_260810_162157`, self-close CLOSED, TCN latent 8.94e-08. Same teacher; `weights_teacher.npz` and `npforward.py` are byte-identical across the two packs. Board test_tcn went SKIP -> PASS; `test_np_policy_api` now parametrized over both encoders (13 passed). Board commit `c1c33f8`. |
| 3. port board np_policy + parity | **DONE** board branch `deploy/72d-inc9998-gru` (`1916f25`), 8 passed / 1 xfailed on Mac numpy 2.0.2 |
| 4. parity ON the board | **BLOCKED** — agent-jetson unreachable (192.168.2.100 connection refused, board off/disconnected) |
| 5. board clone git state | **BLOCKED** — same |
| 6. stale duplicate np_policy | not touched |

The bias_ema timing question in the port spec is **settled by structure, not by guess**: sim
updates `_error_integral` (:1366-1384) and `_bias_ema` (:1389-1398) inside the SAME `_get_rewards`,
and `_get_observations` (:1229-1235) consumes both, so the board mirrors the already-parity-closed
integral exactly — update, then append, in one `_assemble_obs`.

Both packs copied to the field SSD: `ksm-ubuntu:/media/ksm/ksm-ssd/10_Code/16_albc_deploy/`
(`pack_inc9998_gru_260810_150713`, `pack_inc9998_tcn_260810_162157`), each 5/5 sha256 verified
against its MANIFEST; new Johnny-Decimal id registered in the SSD README.

**Launching a TCN distill without the cuDNN preamble costs 20.8x.** Measured today: 18.88 s/iter
(1000 iters = 4.8 h) without, 0.91 s/iter (15.5 min) with. `/workspace/launch_student_tcn.sh`
carries the `LD_LIBRARY_PATH` prebundle line and fail-fasts; wiki page
`a_resolved_wiki_page_does_not_protect_a_launch_the_cudnn_preambl`.

Board repo change is committed but **NOT pushed** to `HERO-Lab-POSTECH/agent-jetson` (shared lab
remote, and the board is offline so the pull cannot be verified). Push + board pull is the next
human action.

### Order of work

1. Export a 72D pack **with golden traces** from the already-completed incumbent student
   `student_final_round/trpo_sdfinal_c3_gruselect_inc9998_s30_260810_124813/models/student_999.pt`
   (finished 12:59 today; no pack exists yet). Entry point:
   `scripts/export_deploy_pack.py --student-ckpt … --teacher-ckpt … --run-group … --tag pack_… --device cpu --golden --report`
   (`--list-specs` first; docs at `docs/how-to/deploy-pack-export.md`). CPU-only, so it will not
   disturb the two training runs.
2. **GRU primary + TCN fallback** (user decision) — export both.
3. Port the board `np_policy.py`; close 1e-5 parity in-container.
4. Close parity **on the board** (TX2, numpy 1.11.0, py2.7). This is the real gate: the GRU
   runtime path has never been closed on the physical board (`albc_rl/CHANGELOG.md` v1.0.0 —
   TCN-only deployment, `test_npforward.py::test_gru [SKIP]`). Current packs' `gru_closed: true`
   is `closed_in_container` only.
5. `ssh agent-jetson 'cd ~/catkin_ws/src/robot/albc_rl && git log -1 --oneline && git status -s'`
   — confirm the board clone carries `b28648c` (accumulator seed) and `e9a8f01` (gyro), and that
   the ATmega is flashed with the gyro-publishing build. Neither is verified yet.
6. Mark or remove the stale duplicate `deploy/student_albc_260607/numpy_port/np_policy.py`.

**Target: a shippable incumbent-based artifact by Tuesday**, so Wednesday is buffer. A winning
replicate swaps in on Wednesday — it does not gate the ship.

⚠️ Open wiki lead with a live consequence: `the_c3_recipe_does_not_transfer_across_teachers_on_a_same_width_`.
If a replicate wins, its student must pass the same gates rather than inheriting the incumbent's
c3 recipe by assumption.

## 6. Selection (pre-registered, before any result is read)

Three-way on the workstation, one `eval.py`, one anchor: incumbent `model_9998`, R30 best,
R31 best. Decide at `hard` and `ood`, never `none`. Per-env **paired** differences, not group
means; before reading any metric confirm the 24 `dr_*`/`fault*` arrays are elementwise identical
(24/24). Quote `rms`/mean only — never `peak` across runs. Best-checkpoint tracking per run, not
last-checkpoint. Filter eval dirs by a batch-start-time cutoff (the tree holds prior-session
leftovers at other anchors/seeds). Prior round measured ~9–12 min per eval.

## 7. Traps that have actually fired in this project

- **`CUDA_VISIBLE_DEVICES` — the "12:48 student produced zero checkpoints" claim is RETRACTED
  (2026-08-10 15:30).** That run, `student_final_round/trpo_sdfinal_c3_gruselect_inc9998_s30_260810_124813`,
  ran with `CUDA_VISIBLE_DEVICES=1` and **completed 1000/1000**: 10 checkpoints
  `student_99.pt`..`student_999.pt` (mtimes 12:49-12:59), TB `student/loss_total` 1000 points
  0.067226 -> 0.002990, `rc=0 at 12:59:45`. Its log's first line reads `gpu=1` and
  `[INFO][AppLauncher]: Using device: cuda:0` — i.e. CVD=1 correctly selected the 4060.
  The likely instrument error is the same one `handoff_final.md` already documents: students write
  to `models/`, and this run has no `train/` subdir, so a `train/`-based check reads as zero.
  There is no `student_armw.log` at all, so the failed launch it may have meant was never fired.
  The Omniverse CVD warning is still real on the **eval** path (a CVD-set eval logged
  `Skipping NVIDIA GPU due CUDA being in bad state: RTX 4060`), so prefer `--device cuda:N`
  where the entry point supports it — but do NOT treat CVD as a known-broken student launch:
  it is the form that has actually worked twice today.
- **`TERM=xterm` + `--headless` required** in detached shells, else `'ansi+tabs': unknown terminal
  type` and a clean-looking rc=1.
- **Container has no `~/workspace`** (`HOME=/root`). Use absolute `/workspace/constrained-albc`
  and `/workspace/isaaclab/isaaclab.sh`. The `~/…` form in `dgx-final-teacher/PLAN.md` is correct
  only for DGX.
- **`pkill -f <pattern>` over ssh kills the ssh shell first.** Kill by PID. Container processes
  are root-owned — kill inside `docker exec`.
- **Decoy container `marinegym-isaaclab`** has identical paths. Always `marinelab-isaaclab`.
- **`ssh ksm-ubuntu` hits Tailscale reauth.** Use `ksm@141.223.223.195`.
- **`manifest.json` `status` is stale `running`** on 63/65 runs. Use checkpoint files as the
  completion signal.
- **`resume: true` makes `max_iterations` incremental**, not absolute (`e3_extend10k`: 10000 →
  `model_14998`).
- **Checkpoint root is `experiments/rsl_rl/`**; `train/` is a symlink that exists only there.
- **`.omx/programs/` is root-owned** — write via `docker exec -i … 'cat > …'`, not `scp`.
- **No `timeout` command on macOS.** Use `ssh -o ConnectTimeout`.
- **`omx queue-launch` needs `--proposal-id`**, and warns about unresolved `needs-experiment`
  leads. All 5 are dispositioned by slug in `PLAN.md`.

## 8. Where things live

| what | where |
|---|---|
| Config authority | `.omx/programs/teacher-final-replicate/PLAN.md` (container) |
| Queued launch records | `.omx/runs/replicate_s{30,31}/pending-launch.json` |
| Audit findings + evidence | vault `0_Project/in_progress/albc/notes/2026-08-10-final-training-prompt-audit.md` (commit `6cfe1d1c`) |
| Original brief (superseded in parts) | vault `notes/2026-08-10-final-training-prompt.md` |
| Prior round's operational record | `.omx/programs/dgx-final-teacher/HANDOFF.md` (878 lines) |
| **Never opened by anyone** | `.omx/programs/teacher-final-closeout/PLAN.md` (720 lines) — carries `control_decimation` still 1 and a 2026-07-20 user direction on latency, both flagged `[DECISION-REQUIRED]` in this program's PLAN |
| Board repo | vault `0_Project/in_progress/albc/code/agent-jetson/` |
| Deploy packs | container `deploy/<group>/pack_*/MANIFEST.json` |

## 9. Open decisions for the user

- `[DECISION-REQUIRED: control_decimation]` — 1 → 5, parked since 2026-06-29 with "resolve at
  robot bring-up" as its trigger; bring-up is Thursday. Recommendation: do not apply, carry as a
  known gap and log for it in the field test.
- `[DECISION-REQUIRED: latency_obs]` — user direction of 2026-07-20 that latency be in the final
  training config, still blocked on a missing instrument (Z4). Recommendation: explicit defer,
  recorded so it is not silently dropped a third time.

---

## 10. 정정 (2026-08-11 06:00) — §1·§5가 stale 했다

이 문서 §5의 "보드 `POLICY_OBS_DIM = 69`가 Thursday blocker"는 **2026-08-11 기준 틀렸다.**
그 서술은 2026-08-10 14:00 시점 사실이고, 이후 다음이 완료됐다(내 작업 아님, 실측으로 발견):

- 팩 2벌 export + 컨테이너 파리티 종료
  - `deploy/student_final_round/pack_inc9998_gru_260810_150713` — obs 72, `gru_closed: true`, latent/hidden max_err 1.49e-7
  - `deploy/student_final_round/pack_inc9998_tcn_260810_162157` — obs 72, `tcn_closed: true`, latent max_err 8.94e-8
  - 둘 다 teacher = `teacher_iter_budget/trpo_iterbudget_s30_260805_012813/model_9998.pt`, atol 1e-5
- 보드 코드 69D→72D 포팅 완료 + 커밋 (Mac 클론 `.../albc/code/agent-jetson`, 브랜치 `deploy/72d-inc9998-gru`)
  - `1916f25` 69D→72D 전환(np_policy·npforward·rl_inference_node·launch·weights·golden·tests)
  - `c1c33f8` TCN 폴백 팩 72D 교체
  - `POLICY_OBS_DIM = 72`, `BIAS_EMA_ALPHA = 0.99`, `_bias_ema`는 integral 직후 갱신·obs 말미 3채널
  - bias_ema 갱신 시점(t vs t-1) 미결 문제는 코드 주석이 해소 — env의 `_get_rewards`에서 갱신되어 **다음** `_get_observations`가 소비

### 실제로 남은 blocker 2건 (둘 다 사람 필요)

1. **push 안 됨** — `git ls-remote origin`은 `refs/heads/main` 하나뿐이고 `edd735c`(72D 이전)다.
   `deploy/72d-inc9998-gru`는 upstream 없음 → 두 커밋은 이 Mac에만 존재. 보드는 origin에서 pull하므로 못 받는다.
   공용 org 저장소(HERO-Lab-POSTECH/agent-jetson) push는 사용자 결정.
2. **보드 파리티 미실행** — `ssh agent-jetson` = Connection refused (전원/연결 없음).
   GRU 경로는 보드(numpy 1.11.0, TX2)에서 한 번도 파리티가 안 닫혔다. 이게 진짜 관문이다.

### 골든의 적용 범위 (이 문서가 과대평가했던 지점)

`golden_gru.input_seq`는 `(1, 9, 72)`로 **이미 조립된 obs**부터 시작한다. 골든은 모델 순전파만
검증하고 **obs 조립은 검증하지 않는다**(EXPORT_REPORT의 `golden_status`도 같은 취지). 보드 파리티가
통과해도 obs 조립 정합은 별도 근거가 필요하다.

### 열린 항목

- `test_np_policy_api.py` xfail 2건 (gru·tcn 공통): 전 오차항이 ~0인 tick 1에서 |a|~1.05 포화.
  "root cause still under investigation" 주석. Mac numpy 2.0.2에서 10 passed / 3 passed.

### 학습 결과 (이 라운드 종료)

- R30 `trpo_replicate_s30_260810_140415` — 08-11 00:18 종료, iter 9999, 텐서 43, nonfinite 0, LOAD_OK
- R31 `trpo_replicate_s31_260810_140414` — 08-11 05:29 종료, iter 9999, 텐서 43, nonfinite 0, LOAD_OK
- 3-way 선택(현직 model_9998 vs R30 vs R31)은 미실행. eval.py가 워크스테이션에만 있으므로 거기서.

---

## 11. 3-way 선택 결과 (2026-08-11 14:54) — 현직 유지, 교체 없음

스윕 11회 전부 rc=0 (inc_9998 + R30 5 + R31 5, 회당 598~627 s, 64 envs, seed 42, `--fault --ood`).

### 게이트: hard PASS / ood FAIL

프로토콜의 "24개 dr_*/fault* 배열 원소 단위 동일" 검사를 32개 조건 배열로 실행:

- **hard: 11개 런 전부 32/32 일치 → 짝지어 비교 유효**
- **ood: 불일치. R30 5개는 동일한 6키(`dr_cob_x/y/z`, `dr_cog_x` 등)에서, r31_9000·9250은 `dr_added_mass_1`에서 어긋남**

원인은 구조적이다. OOD 경계는 `build_ood_dr_config`가 **그 런 자신의 DORAEMON 학습 분포**에서 역산한다(런당 tfevents 필요). 런마다 학습 분포가 다르므로 ood 레벨은 **설계상 런 간 비교 불가**다. 프로토콜의 "hard와 ood에서 판정"은 ood에 대해 그대로 실행할 수 없다.
ood를 비교 가능하게 하려면 런 독립 고정 프리셋(`--extreme-ood`, `--ood-scale`)으로 다시 떠야 한다.

### hard 판정 (환경별 대응차 64쌍, rms만)

기준 inc_9998: roll_rms 2.9961 deg · pitch_rms 4.6708 deg · yaw_rms 0.06152 rad/s · survival 100.00 %

| run | Δroll(deg) | Δpitch(deg) | Δyaw(rad/s) | Δsurv(%p) |
|:--|--:|--:|--:|--:|
| r30_9000 | +0.4845 | +0.2119 | +0.00212 | 0 |
| r30_9250 | +0.4771 | +0.3413 | +0.00139 | 0 |
| r30_9500 | +0.4086 | +0.1975 | +0.00196 | 0 |
| r30_9750 | +0.5728 | +0.1720 | +0.00208 | 0 |
| r30_9999 | +0.5086 | +0.1692 | +0.00019 | 0 |
| r31_9000 | +1.1422 | +0.8381 | +0.04075 | −1.040 |
| r31_9250 | +0.9200 | +0.5111 | +0.02017 | −1.009 |
| r31_9500 | +0.6673 | +0.3572 | +0.03000 | 0 |
| r31_9750 | +0.3119 | +0.0622 | +0.00239 | 0 |
| **r31_9999** | **+0.1785** | +0.0388 | +0.00133 | 0 |

하한(ss_error 0.1 axis, survival_pct 1.6)은 summary.json의 `decision_floors`.

**판정: 현직 `model_9998` 유지.** 10개 후보 전원이 roll에서 하한 초과로 악화됐고, **개선 방향(음수 Δ)은 어느 지표·어느 후보에서도 나오지 않았다.** 최선인 r31_9999도 Δroll +0.1785로 하한 위(악화). 방향이 2시드·10체크포인트에서 일관되므로 우연으로 보기 어렵다.

부수 관찰: R31은 iteration에 따라 단조 개선(9000→9999에서 Δroll 1.14→0.18)이라 9999 시점에도 아직 수렴 중으로 보이는 반면, R30은 9000~9999 내내 평평(0.41~0.57)하다.

### 후속 영향

- **팩 재추출 불요.** 현재 GRU·TCN 팩 2벌은 현직 `model_9998` 기반이고 그대로 정본이다
- **보드 재파리티 불요.** 지금 보드 상태가 실기동 정본이다
- 이 라운드의 목적(재현 가능한 provenance + 최초 시드 분산)은 달성. 성능 교체는 예측대로 null
