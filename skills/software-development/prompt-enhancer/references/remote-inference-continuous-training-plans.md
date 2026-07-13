# Remote Inference + Continuous Training Plan Pattern

Use this reference when enhancing or executing prompts for plans where Hermes runs on one machine (often a VPS) while inference runs on a separate local workstation/server, and the user wants inference outputs or feedback to feed a recurring training loop.

## Core distinction

Always separate these roles explicitly:

- **Control/orchestration host**: where Hermes runs, schedules jobs, stores plans, calls APIs, manages artifacts, and owns logs/config.
- **Inference server**: where the model actually runs; may be a Mac Studio, GPU server, local workstation, or private LAN machine.
- **Training platform**: where fine-tuning happens; may be Hugging Face Jobs, local GPUs, a cloud VM, or a cluster.
- **Observability/dataset store**: where traces, feedback, eval sets, and preference candidates are stored.

Do not imply Hermes is running on the inference machine unless the user said so. If the user says Hermes is on a VPS and a Mac Studio is the inference server, the plan must route VPS→Mac through a private endpoint rather than using localhost on the VPS as if it were the Mac.

## Validation checklist

Before producing the artifact, validate current docs for:

1. Hermes custom/OpenAI-compatible endpoint configuration.
2. The inference runtime's OpenAI-compatible API behavior and security notes.
3. Private networking choice: Tailscale, WireGuard, SSH tunnel, LAN, or reverse proxy.
4. Observability/trace platform: whether it supports OpenAI SDK tracing, custom base URLs, datasets, feedback, and experiments.
5. Training stack: SFT and preference training formats, job execution, artifact persistence.
6. Synthetic/model-generated data risk and safeguards against recursive model collapse.

Prefer first-party docs. Use web tooling for current product claims and pricing.

## Architecture pattern

A safe default shape:

```text
Hermes/control host
  -> local authenticated gateway
  -> private network link
  -> inference-host authenticated gateway
  -> inference runtime bound to localhost
  -> trace/eval/dataset store
  -> curated training dataset
  -> training jobs
  -> candidate artifact
  -> inference-host candidate endpoint
  -> eval and approval
  -> production pointer
```

The raw inference runtime should bind to `127.0.0.1` on the inference host when its docs warn that it only has basic security. Expose only an authenticated proxy/gateway over the private network.

## Continuous training loop safeguards

When generated outputs or production traces feed training:

- Treat raw model outputs as **generated data**, not human-authored corpus.
- Use generated outputs primarily as rejected candidates, eval cases, or comparison samples.
- Use human rewrites or human-selected candidates as `chosen` responses for preference training.
- Require explicit training consent, privacy/PII review, and source-leakage/plagiarism checks.
- Keep a frozen human-only eval set and a human-only anchor corpus.
- Cap generated-derived tokens in each cycle.
- Require candidate artifacts to beat the current production model on fixed evals before promotion.
- Preserve rollback artifacts.

## Output guidance

If the user requests a reconciled full artifact with no changelog language, return the canonical complete plan only. Do not include headings such as updates, changes, revisions, deltas, or what changed.
