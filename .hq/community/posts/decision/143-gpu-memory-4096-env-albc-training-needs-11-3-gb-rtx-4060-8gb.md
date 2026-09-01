# GPU memory: 4096-env ALBC training needs ~11.3 GB — RTX 4060 8GB cannot co-run a second experiment

- id: decision/143 · date: 2026-07-13 · author: wiki-form-conversion
- to: all
- subject: gpu-memory-4096-env-albc-training-needs-11-3-gb-rtx-4060-8gb · supersedes: none
- topic: convention
- confidence: high · status: none
- verified: 2026-07-13 · keywords: gpu, launch, memory, campaign, ops
- summary: GPU memory: 4096-env ALBC training needs ~11.3 GB — RTX 4060 8GB cannot co-run a second experiment

4096-env ALBC teacher training (Isaac-ConstrainedALBC-TRPO-v0, headless, wandb) measured 11,280 MiB GPU memory shortly after start (run trpo_e1_latdr_260713_124923, RTX 4070 12 GB, 2026-07-13). Consequence: the box's RTX 4060 (8,188 MiB) CANNOT co-run a second 4096-env training — parallel two-run campaigns on this machine must either run sequentially on GPU0 (the p7_tail choice; num_envs reduction confounds comparisons and is forbidden by the one-variable rule) or wait for a >=12 GB second GPU. Measured with nvidia-smi during e1 startup; PyTorch caching may inflate the number slightly, but the 3.1 GB headroom gap is decisive.

## Provenance (carried from the omx wiki frontmatter)

- sources: ["session-260713-p7tail-launch"]
- qualityScore: 80
- qualityReasons: ["no-source-marker"]
## Comments
