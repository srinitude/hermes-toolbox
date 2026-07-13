# Humanized writing / detector-loop profile pattern

Use this reference when building a dedicated Hermes profile for writing that must pass external human/AI/plagiarism checks before release.

## Intake and blockers

- If the user provides `starting-rules` but the message is truncated, redacted, or summarized by the UI, treat the missing full text as a blocker for exact merging. Offer two paths: proceed with reconstructed rules, or wait for the full original rules.
- Analyze any supplied labeled writing corpus read-only before drafting the final spec. Record objective counts and simple discriminators, not vibes.
- Distinguish dataset-backed patterns from universal claims. Report sample size, label counts, parse/repair count, and deduping policy.

## Profile primitives

Map the writing goal beyond SOUL:

- `identity`: profile-specific SOUL for voice, release posture, and anti-slop stance.
- `capabilities`: humanizer/writing skills plus a profile-local rules/learnings skill.
- `configuration`: validator personality overlay; `terminal.cwd` to the writing workspace.
- `memory`: generalized durable learnings only. Do not store draft history, detector scores, or per-iteration diaries as memory.
- `automation`: usually on-demand, not cron, unless the user explicitly wants scheduled writing checks.
- `security`: no publishing/sending without explicit user approval; no raw API keys in chat or skill files.
- `performance`: external detector calls usually happen at release-readiness checkpoints, not every draft turn.
- `model`: if the user names a specific model and reasoning level for the writing profile, carry that into the config manifest explicitly, for example `model.default: gpt-5.5`, `model.provider: openai-codex`, and `agent.reasoning_effort: xhigh`. Validate reasoning levels against live Hermes CLI/source/docs before presenting them as supported.

## External detector feedback loops

For APIs such as Pangram AI detection / plagiarism detection:

- Verify endpoints against first-party docs before finalizing the spec.
- Represent API keys as `secret_ref` / manual setup actions, never raw values.
- If the user supplies a raw API key in chat, do not repeat it in the profile spec; refer to a named secret reference and the profile-local `.env` or secret-manager storage path.
- Mark live API validation as blocked until the key exists and the user approves billable/external calls.
- If the user asks for the detector loop to run throughout the process, design the loop across intake/source draft, local audit, draft, candidate final, final validation, and plagiarism check. Skip only text that is too short/invalid or non-writing meta-chat, and make quota/cost approval explicit.
- Prefer a future plugin-builder workflow for tools/hooks that call the detector; do not silently create or enable plugin code during profile creation.
- The pass/fail contract should be explicit: terminal AI-detection success with human classification or agreed thresholds, plagiarism below the agreed threshold, and no failed/in-progress task status.
- Detector feedback should drive rewrites and generalized rule updates; preserve only reusable patterns in profile-local references/skills.

## Output shape

- If the user asks to reconcile or integrate multiple changes into the entire profile spec and explicitly says not to use “updates/changes/versions/edits/etc.” language, return the complete integrated spec as the canonical artifact. Do not include a changelog, diff summary, or headings that describe what changed.

## Objective corpus analysis notes

Good enough corpus analysis for the profile spec can include:

- recoverable record count, bad/multiline repair count, label counts;
- explicit text-field discovery before word counts. Social/export corpora often use fields such as `body` or `tweet_body`, not just `text`, `human_text`, or `ai_text`; if all records appear empty, inspect sample keys and patch the parser before trusting the metrics;
- deduping key and duplicate counts;
- medians/means for simple features: first-person rate, contraction rate, AI/tool-term rate, ALL-CAPS rate, list/line count, arrows, marketing phrases, uncertainty markers;
- top terms/openings by label with caveats about author/topic confounds.

Do not overfit SOUL to one dataset. Convert findings into compact rules that a future plugin or skill can revise as detector-loop evidence accumulates.
