# Hermes profile specs for online fine-tuning and validation

Use this reference when a user provides or revises a Hermes profile spec that includes writing, detector validation, managed training, Hugging Face resources, or paid API loops.

## Source-of-truth posture

- Treat a pasted "current spec" as the authoritative artifact to reconcile unless the user explicitly asks to start over.
- Return one integrated canonical spec when requested. Do not frame it as a changelog.
- Preserve explicit approval gates. A phrase like "Take it into account" is not approval to create profiles, call paid APIs, launch Jobs, create buckets, or write plugin files.
- If the spec includes an exact approval phrase, repeat that phrase as the gate and do not weaken it.

## Workspace placement

- Keep the Hermes profile workspace as the profile's `terminal.cwd`.
- Put training, experiment, data repair, eval, and provider job work in a custom subdirectory inside that workspace, e.g. `<workspace>/human-writing-ft/`.
- Do not place checkpoints, generated adapters, large logs, or batch outputs in the profile home.

## Online-only training lane

When the user removes local hardware or asks for online products/services only, remove old local inference language everywhere: architecture, commands, validation, costs, and open questions.

Recommended managed-HF shape:

- HF Jobs for training and batch inference.
- HF Storage Buckets for mutable checkpoints, logs, intermediate outputs, and agent scratch data.
- Private HF model/dataset repos for versioned final artifacts.
- Trackio for lightweight experiment tracking.
- HF Inference Endpoints only after a candidate model passes evals.

Validate current details against first-party HF docs before finalizing:

- `https://huggingface.co/docs/huggingface_hub/main/guides/jobs`
- `https://huggingface.co/docs/trl/main/en/jobs_training`
- `https://huggingface.co/docs/trl/sft_trainer`
- `https://huggingface.co/docs/trl/dpo_trainer`
- `https://huggingface.co/docs/hub/en/storage-buckets`
- `https://huggingface.co/docs/hub/en/storage-buckets-access`
- `https://huggingface.co/docs/inference-endpoints/index`
- `https://huggingface.co/docs/trackio/index`

## Paid API and cost handling

For Pangram-like detector loops:

- Separate word-only estimates from per-item minimum billing estimates.
- Bulk APIs may be cheaper per 1,000 words but short-record datasets can still be dominated by minimum billable units.
- State approval caps before any paid action.
- For full-corpus scans, propose a stratified sample first unless the user explicitly approved the full cost.

For HF Jobs:

- Jobs have default timeouts. Training needs explicit longer timeouts.
- Include job URL or ID, terminal status, logs/metrics path, and artifact path as validation evidence.
- Require private bucket/repo targets for private profile work.

## Model-collapse and detector-evasion guardrails

- Do not train on raw model outputs as chosen human targets.
- Use model outputs as rejected examples or review candidates unless a human rewrites and approves them.
- Keep fixed human-only eval anchors that never enter training.
- Treat detector scores as a signal, not the goal. Meaning preservation and plagiarism safety remain higher priority.

## Final spec validation checklist

A reconciled spec is complete only when it includes:

1. Profile home and workspace paths.
2. Exact allowed and prohibited write surfaces.
3. Current first-party docs used for Hermes, provider APIs, HF, and detector endpoints.
4. Local corpus counts or explicitly labeled assumptions.
5. Paid-action caps and approval phrase.
6. Validation commands and expected proof.
7. Clear separation between profile creation, future plugin creation, paid API calls, and training jobs.
