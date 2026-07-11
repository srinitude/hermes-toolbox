# External detector feedback-loop plugin pattern

Use this reference when building a plugin that sends draft content to an external detector/evaluator, uses returned feedback to drive rewrites, and optionally updates reusable learnings.

## Surface fit

Prefer a general Python plugin when the profile needs model-callable tools, slash commands, or plugin hooks around release-readiness checks. Prefer a skill-only workflow when no external API call is needed. Prefer MCP only if a maintained MCP server already provides the detector API.

## Capability shape

Typical minimal tools:

- `submit_detection_task` / `check_detection_result` for async detector APIs.
- `check_plagiarism` for plagiarism APIs.
- `run_release_check` for an orchestrated one-shot pass over a unit of writing.

Optional slash command:

- `/human-ready <text-or-path>` when the user wants an interactive command, not just model-callable tools.

Optional hooks:

- Use hooks only when the workflow needs automatic enforcement at a well-defined lifecycle point. Do not silently run billable/external checks on every draft turn.

## Config and secrets

- Declare API keys in `requires_env`, e.g. `PANGRAM_API_KEY`.
- Never put raw keys in plugin files, skills, SOUL, or chat transcripts.
- Treat API calls as external side effects and potential billable operations. Get explicit approval before live validation if cost/credits are uncertain.

## Handler and API rules

- Keep imports cheap at module import/register time; construct clients lazily in handlers.
- Set request timeouts and poll limits.
- Return compact JSON strings with both raw status fields and normalized verdict fields.
- Preserve external task IDs and dashboard links only in immediate tool output unless the user approves storing them.
- For async APIs, distinguish in-progress, success, failed, timeout, auth error, quota error, and validation error.
- A detector-loop pass should not be declared complete while any task is in-progress or failed unless the final status explicitly reports the blocker.

## Learning updates

- Save only generalized writing patterns/rules, not draft text, detector scores, task IDs, or source matches, unless the user explicitly requests an audit log.
- For profile-specific writing systems, prefer updating a profile-local skill/reference file such as `references/writing-learnings.md` after user approval.
- Do not let the plugin mutate skills automatically from a hook without an explicit tool/command invocation or approval step.

## Validation

Before enabling the plugin:

1. `HERMES_PLUGINS_DEBUG=1 hermes -p <target-profile> plugins list` shows the plugin without load errors.
2. Missing-env behavior is graceful and does not import/network at load time.
3. Bad input returns JSON error, not an uncaught exception.
4. If credentials are configured and live calls are approved, run one minimal API call and verify terminal status handling.
5. If live calls are not approved/configured, report `blocked_user_action` rather than faking detector output.
