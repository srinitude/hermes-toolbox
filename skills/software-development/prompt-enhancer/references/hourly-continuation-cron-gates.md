# Hourly Continuation Cron Gates

Use this pattern when a long task should resume hourly only if its interactive Hermes agent is no longer working.

## Core design

1. Create an LLM cron with a self-contained continuation prompt, exact project `workdir`, required skill attachments, explicit model/provider, and local delivery when the origin is a TUI.
2. Attach a pre-run script that prints one final JSON object:
   - `{"wakeAgent": false, ...}` when the target agent is actively working;
   - `{"wakeAgent": true, ...}` when recovery should start.
3. Re-run the same gate at the start of the cron prompt. If it now returns false, make no writes/tests and return `[SILENT]`. This closes the check-to-agent-start race.
4. Keep the prompt fully self-contained: cron sessions have no current-chat history or active task list.

## Detect work, not merely an open TUI

A process-exists-only check can suppress recovery forever when an idle TUI remains open. A recent-message-only check can misclassify a long test/build as idle. Combine both:

- identify the exact TUI command, such as `hermes --tui -c <continuation>`;
- derive its live session key from the descendant `tui_gateway.slash_worker --session-key ...` process;
- classify non-infrastructure descendants as active work (pytest, build, shell/tool processes);
- otherwise obtain a redacted session export with `hermes sessions export - --format jsonl --redact --session-id "$session_key"`; require at least one parseable record matching that session before using its newest message timestamp, and never treat exit status alone as proof of an export;
- apply a bounded recent-activity window;
- fail open to `wakeAgent:true` when process/session evidence cannot be verified, so recovery cannot stall indefinitely.

Infrastructure descendants commonly include the TUI Node process, `tui_gateway.entry`, `tui_gateway.slash_worker`, language servers, and the CUA driver. Match exact command structure, not loose substrings. A shell running `grep pytest` or an `rg '*pytest'` filename search is not an active pytest runner.

Do not query `~/.hermes/state.db` from the gate. Its schema is private and release-sensitive. Do not print prompts, exports, credentials, environment dumps, or message content; gate context should contain only reason codes, bounded ages, and non-secret process/session identifiers.

## Scheduler activation and proof

- `hermes gateway start` starts the existing user service; poll `hermes cron status` with a bounded timeout until it reports a fresh startup heartbeat. The current scheduler records that heartbeat before its first sleep. If no fresh heartbeat appears, fail the activation check; do not attribute freshness to a later scheduler tick or restart blindly.
- Trigger one manual run while the interactive agent is active and require the audit artifact to state that `wakeAgent=false` skipped the agent.
- Also inspect the first real scheduled-run artifact; manual success alone does not prove automatic firing.
- In a TUI, default/origin delivery is not live chat delivery. Use `deliver=local` unless a gateway messaging destination was explicitly requested, and state where audit files are saved.

## Verification

Before installation, witness RED against the absent gate. After creation:

- run the gate directly and parse its single JSON line;
- use a disposable real pytest under `/tmp/hermes-verify-*` for the live active-agent suppression contract;
- parser-check file/construct/nesting limits and compile the script;
- require restrictive mode such as `0700`;
- clean the temporary verifier and bytecode;
- verify the cron definition, gateway heartbeat, manual skip artifact, and first scheduled skip artifact.

The gate proves duplicate-work suppression, not task completion. The continuation prompt must retain every substantive security, approval, digest, publication, and commit gate from the underlying plan.
