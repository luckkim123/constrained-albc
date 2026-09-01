# static-eval plots regenerate sim-free from npz (reconstruct segment metadata)

- id: finding/242 · date: 2026-06-08 · author: wiki-form-conversion
- to: all
- subject: static-eval-plots-regenerate-sim-free-from-npz-reconstruct-s · supersedes: none
- topic: debugging
- confidence: high · status: none
- verified: none · keywords: eval, plots, sim-free, recompute, npz
- summary: static-eval plots regenerate sim-free from npz (reconstruct segment metadata)

To regenerate static-eval plots (summary_*.png, traj_*.png, summary_failuretime.png) with the CURRENT plotter (yaw deg/s, OOD 5-level, lin_vel error bars) WITHOUT re-running GPU eval: the existing data_*.npz hold only per-step ndarrays, NOT the segment metadata (segment_names, steps_per_segment) that compute_metrics + generate_plots require -> KeyError if you just load npz. But that metadata is DETERMINISTIC: build_step_trajectory(segment_duration, step_dt) in _eval_dr/trajectory.py is pure numpy (no Isaac Sim) and depends only on (segment_duration=5.0 for static, step_dt) + fixed amplitude constants. Recipe: infer step_dt=median(diff(npz['time'])), call build_step_trajectory, inject segment_names/steps_per_segment/num_segments/segment_duration/step_duration into each level's npz dict, then compute_metrics(d) + generate_plots(all_data, all_metrics, dir). Reconstructed traj_len matches npz length exactly (7750 = 31 segs x 250 steps at 50Hz) -- loud-fail if not. Reusable script: .omx/scratch/regen_dr_harder_plots.py. CAVEAT: import the sim-free modules DIRECTLY (from _eval_dr.metrics import compute_metrics; from eval_plots import generate_plots) -- importing eval.py pulls in isaacsim and fails. CAVEAT2: analyze.py recompute (PATH B, recompute_plots.py) does NOT have the P2 yaw deg/s / OOD-5-level fix; only eval_plots.py (PATH A) does -- use generate_plots, not recompute, for the corrected plots. ONLY failure_dr_correlation.png + summary_drdist.png cannot be made this way (need per-env dr_* snapshot / DR config = GPU-time).

## Provenance (carried from the omx wiki frontmatter)

- sources: ["diagnose-20260608-120155 dr_harder replot"]
## Comments
