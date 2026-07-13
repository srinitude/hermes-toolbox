# Humanized-writing profile specification pattern

Use this reference when a user asks to reconcile or produce a full Hermes profile plan for humanized writing, detector validation, plagiarism checks, managed fine-tuning, or a private plugin that manages custom model activity.

## Trigger

Apply this when the task includes any of:

- a user-specific/private writing profile
- Starting Rules / local human-vs-AI corpus / humanizer calibration
- Pangram AI detection or plagiarism validation
- Hugging Face Jobs, Storage Buckets, Trackio, private adapters, or candidate endpoints
- a Hermes plugin that manages custom model workflows for a profile
- a request to restore prior plan context and return a single canonical artifact with no changelog/update language

## Required reconciliation shape

When the user asks for the entire proposed plan/spec, return the full canonical artifact only. Do not add sections named updates, changes, deltas, revisions, what changed, or summary of edits. Treat any pasted/current plan as the source artifact to reconcile, not loose background.

Preserve all active context lanes:

1. Profile identity and privacy class.
2. Hermes profile home and workspace path.
3. Local rulebook and corpus evidence.
4. Main model/provider/reasoning configuration.
5. Pangram AI detection and plagiarism loop.
6. Managed online training lane.
7. Private plugin lane for custom model activity.
8. Cost caps and exact approval gates.
9. Write-safety boundaries.
10. Objective validation commands.

## Web validation checklist

Use current web/provider tools before finalizing claims. Prefer first-party sources.

- Hermes profiles/config/plugins/provider docs and live CLI output.
- OpenRouter model catalog/endpoint data for the selected main model.
- Pangram API docs for detection, bulk, file upload, plagiarism, auth header, terminal states, retention, and billing units.
- Pangram model card/research for detector limitations, score bands, long-form guidance, false-positive caution, and humanizer/distribution-shift caveats.
- Hugging Face Jobs, TRL SFT/DPO, Storage Buckets, Trackio, Inference Endpoints, and pricing pages.
- Model cards for open training candidates such as Qwen3 smoke and serious adapter models.
- Licensing/source pages for extra human corpora: Project Gutenberg, Wikimedia dumps, PMC OA, SEC EDGAR, govinfo, arXiv, Common Crawl, and any HF datasets named.

Do not rely on model memory for prices, endpoint paths, supported hooks, or current model capabilities.

## Plugin lane inside a profile spec

If the profile will contain or depend on a private plugin that manages custom model activities, include both roles explicitly:

- **Operational profile**: the approved profile that will use the plugin at runtime.
- **Workshop/source profile**: the deployment-configured private plugin workshop when the plugin is user-specific/private.

The plan should say that plugin files are not written until a separate final plugin agreement is approved. A profile-creation approval is not a plugin-build approval.

Typical private human-writing lab plugin responsibilities:

- dataset inspection and repair planning
- train/validation/eval split creation
- SFT and preference dataset preparation
- Pangram sample/release checks and plagiarism checks
- HF auth checks, job preparation, launch, status, logs
- batch inference against candidate adapters
- style/meaning/eval reports
- promotion reports and rollback metadata

Typical deferred capabilities:

- automatic hooks around every writing turn
- silent Pangram calls
- autonomous recurring training jobs
- model-provider registration for promoted endpoints
- public dashboard publishing
- automatic skill mutation from detector results

## Data and training safeguards

For humanized-writing fine-tuning, state these explicitly:

- Raw model outputs are generated data, not human-authored targets.
- Chosen examples for SFT/preference training require human authorship or explicit human approval.
- Generated outputs may be rejected candidates, eval cases, or comparison samples.
- Keep a frozen human-only eval set that is never trained on.
- Keep provenance for every record.
- Filter for rights, consent, duplicates, near-duplicates, boilerplate, URL-only text, and metadata junk.
- Use pre-2022 human corpora where possible to reduce AI-contamination risk.
- Treat detector passing as a validation signal, not as permission to train on or publish text.
- Do not launder plagiarism; fix source/provenance problems.

## Cost and approval gates

Separate fixed/storage/compute/API costs and show formulas. For Pangram, compute both word-only and per-record minimum estimates because short-record corpora can be dominated by the one-billable-unit-per-item minimum. For HF Jobs, include timeout requirements and the fact that billing is per minute while jobs are Starting/Running.

Use exact approval phrases for side-effecting phases:

- profile creation
- plugin creation
- Pangram live calls
- HF job launch
- endpoint creation/promotion
- recurring cron jobs

## Output standard

The final artifact should read as one coherent plan. Avoid meta-commentary about what was restored or revised. Include validation evidence and source URLs inside the plan where useful, but do not preface with a changelog.
