# encoder adapter test fixture

`mini_encoder_24d.pt` — 192 KB extract of `experiments/legacy/final_models/r13_A/model_4999.pt`
(input_dim=24, latent_dim=9, softsign, static-minmax bounds, pre-softsign LayerNorm).

Holds only the keys `_load_encoder_for_sweep` reads: `encoder.*`,
`_enc_obs_lower`, `_enc_obs_upper`, `_encoder_output_norm.{weight,bias}` (12 keys).
Wrapped as `{"model_state_dict": <those keys>}` so the engine loaders see the
expected top-level structure.

Re-extract: see Step 1 of Task 2 in
`/workspace/docs/plans/2026-06-05-omx-encoder-adapter.md`.
