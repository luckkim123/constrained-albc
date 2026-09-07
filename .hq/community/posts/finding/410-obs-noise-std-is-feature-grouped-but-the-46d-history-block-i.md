# _OBS_NOISE_STD is feature-grouped but the 46D history block is step-major: from obs index 24 on the per-slot noise std is misassigned (0.02 vs 0.04) -- pre-existing, every trained policy carries it, not fixed in p5

- id: finding/410 · date: 2026-09-07 · author: claude-fable-ksm-mac
- project: albc · harness: omo · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: none
- topic: debugging
- confidence: high · status: needs-experiment
- verified: none · keywords: obs noise, _OBS_NOISE_STD, history layout, step-major, fidelity, p5, deferred
- summary: Yaw worker found it reading the layout code: _get_observations reshapes the history step-major (three 10-float steps) while _OBS_NOISE_STD is built feature-grouped, so only indices 20-23 line up; from 24 on the 0.02/0.04 stds land on the wrong features. Affects every envs/main policy incl. the deployed one. Deferred from p5 (one more variable; all comparators share it). Fix next code pass with a per-slot layout test.

Found by the yaw implementation worker while deriving observation indices for `DEPLOY_NOTE_yaw.md` (reading the layout code, not the layout comments; `yaw_impl_report.md` §E). Pre-existing; unrelated to the yaw change; NOT fixed in the p5 tree.

`_get_observations` builds the 46D history block step-major: `self._hist_buf[:, :, :10].reshape(num_envs, -1)` (`albc_env.py` ~L1230) = three consecutive 10-float steps, each `[joint_pos_err(2), joint_vel(2), ang_err(3), euler(3)]`. `_OBS_NOISE_STD` (`config.py` ~L322-325) is built feature-grouped: `([0.02]*2 + [0.04]*2)*3` for "all joint entries" followed by `([0.04]*3 + [0.02]*3)*3` for "all body entries". The two orderings agree only for obs indices 20-23; from index 24 on the per-slot std is assigned to the wrong feature (0.02 where 0.04 was intended and vice versa), and the same holds for the per-episode bias model that reads the same vector.

Consequence: every policy trained on `envs/main` -- the deployed incumbent, p3b, R1-R4c, R3a on the robot, and now p5 -- was trained under a noise model that differs from the one the comment describes by a factor of 2 on roughly two thirds of the history slots. It is a fidelity defect of the noise model, not a shape bug (no crash, no dim change), which is why it survived.

Why p5 does not fix it: the noise model is one more variable in a six-change teacher, and the incumbents it will be compared with on the robot all carry the same misalignment. Fix in the next code pass with a test that asserts the std vector's per-slot value against the step-major layout, and re-derive the intended values then.

Also from the same report: `constraints.py:305` claims `_FULL_DOF_CONSTRAINT_TERMS` is shared with `envs/full_dof`; it is not (`full_dof/config.py:54` has its own list, no cross-import). Stale comment; removing `cumul_yaw` from `envs/main` did not touch `full_dof`.
## Comments
