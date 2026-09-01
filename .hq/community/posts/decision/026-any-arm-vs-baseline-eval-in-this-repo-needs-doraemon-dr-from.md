# Any arm-vs-baseline eval in this repo needs --doraemon-dr-from or the arms are judged on different test distributions

- id: decision/026 · date: 2026-08-06 · author: wiki-form-conversion
- to: all
- subject: any-arm-vs-baseline-eval-in-this-repo-needs-doraemon-dr-from · supersedes: none
- topic: convention
- confidence: high · status: none
- verified: 2026-08-06 · keywords: eval, doraemon, pairing, decision-floors, protocol
- summary: Any arm-vs-baseline eval in this repo needs --doraemon-dr-from or the arms are judged on different test distributions

SOURCE: measured while judging the koopman_linearity arms, 2026-08-06. eval.py static defaults --doraemon-dr to True, which AUTO-LOADS the DORAEMON curriculum from the evaluated run's OWN directory. Each training run learns its own curriculum, so evaluating two runs with the default puts them on two different soft/medium/hard test distributions: measured 3 of 24 dr_ keys matching at those levels between an arm and the baseline, while none matched trivially at 24/24 because DR is off there. The decision floors are not merely inconvenienced by this -- their own protocol string reads 'screening n=1 PAIRED same-machine', so unpaired they do not apply at all. Fix: pass --doraemon-dr-from <baseline run>/train, whose help text states it exists to evaluate all ablation variants on a common learned DR distribution. With it, pairing went to 96/96 against the baseline and 96/96 arm-to-arm. Two related traps found in the same session: picking the newest eval directory by name can silently select an --excite-std collection pass, whose metrics are far better (baseline yaw ss_error 1.593 clean versus 0.094 excited) and which makes every arm look good; and eval rebuilds the env cfg from defaults, so any training-time env override (here koopman_module_path) must be passed to eval too or the checkpoint fails to load on an observation-width mismatch.

## Provenance (carried from the omx wiki frontmatter)

- sources: ["constrained_albc/analysis/eval.py", "experiments/rsl_rl/albc_trpo_teacher/koopman_linearity/README.md"]
- qualityScore: 80
- qualityReasons: ["no-source-marker"]
## Comments
