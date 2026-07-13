# Browser, screen-recording, and creative API plugin pattern

Use this when a plugin-building request involves Browser Use, browser screen recordings/demonstrations, LTX Studio/LTX API, FLORA, or similar creative SaaS/API workflows.

## Surface-fit rule

Prefer the lightest surface that satisfies the goal:

1. Existing Hermes browser tools for one-off browser navigation.
2. Browser Use API/plugin tools when the workflow needs Browser Use sessions, recordings, live preview, deterministic reruns, profiles, workspaces, webhooks, or full API coverage.
3. Screen-recording/browser-demonstration plugin when the outcome is to teach Browser Use agents or worker profiles how to perform a browser workflow.
4. MCP for interactive exploration when the vendor provides a supported MCP server and OAuth is preferred.
5. REST/API plugin for deterministic pipelines, batching, cost gates, webhooks, idempotency, or scheduled/backend work.
6. Browser automation of a web app only when the function is not available through a safer API or when UI demonstration is the goal.

## Mandatory gates

- Do not build or enable plugin files before final agreement.
- Do not print raw API keys, webhook secrets, cookies, recording URLs, live URLs, CDP URLs, signed upload URLs, or private output URLs.
- Use `requires_env` for secrets; handlers validate presence without revealing values.
- All paid or mutating operations require approval and cost cap.
- All browser profile/cookie sync, persistent profile use, login, CAPTCHA/Cloudflare, payment, 2FA, OAuth grant, account creation, and irreversible actions are human-only or approval-gated.
- Network clients, SDK imports, and OpenAPI fetches must be lazy, not import/register time.
- Tool handlers return compact JSON strings and accept `**kwargs`.

## Browser Use plugin coverage

A Browser Use control plugin should cover the v3 API at resource-family level:

- Sessions: create/list/get/delete/stop/messages; fields such as task, model, keepAlive, maxCostUsd, profileId, workspaceId, outputSchema, enableRecording, skills, agentmail, codeMode, cacheScript, autoHeal.
- Browsers: create/list/get/update/downloads; liveUrl, cdpUrl, recordingUrl, proxy, timeout, screen size, recording.
- Profiles: list/create/get/update/delete; persistent state and sync require explicit approval.
- Workspaces: list/create/get/update/delete, file list/upload/delete/size; deterministic rerun scripts require inspection and cleanup rules.
- Billing: account read for cap enforcement.
- Boxes/shell/windows: expanded execution surface; require explicit approval.
- Webhooks: signature/replay verification before acting.

## Screen-recording demonstration plugins

Use a separate demonstration plugin when the requested outcome is “show Browser Use agents how to do this.” Include tools to:

- start a demo with allowed domains, objective, audience profile, and recording mode;
- add step records with evidence refs, selectors, screenshots, and accessibility snapshots;
- add checkpoints and expected state;
- pause for human handoff at sensitive points;
- stop/finalize and collect recording metadata;
- compile an agent-readable how-to packet;
- convert the demo into a Browser Use task template and, when repeatable, a deterministic `@{{...}}` template;
- search/reuse the demo library.

Demonstration outputs must separate agent steps from human-only steps and include explicit stop conditions.

## LTX plugin split

Separate LTX Studio browser plugins from LTX API plugins:

- LTX Studio browser plugin: maps `app.ltx.studio`, creates Browser Use task packets for Gen Space/Storyboards/Video Editor/API Playground, handles login/Cloudflare/payment as human-only, and records demonstrations.
- LTX API plugin: uses `LTXV_API_KEY`, async V2 submit → poll → download, signed upload, model compatibility, retention windows, and cost gates. Submit/download actions require approval.

## FLORA plugin pattern

For FLORA workflows:

- Use REST/API tools for deterministic automation and FLORA MCP for optional interactive exploration.
- Declare `FLORA_API_KEY` and `FLORA_WEBHOOK_SIGNING_SECRET` via `requires_env`; never print raw values.
- Resolve workspace/project, retrieve Technique/model/action schema, map exact input IDs/types, estimate cost, request approval, generate deterministic idempotency key, create async run, poll or verify webhook, fetch full result, archive outputs if needed, review, and write evidence.
- Webhook verification uses the exact raw body and `Flora-Signature` (`t=...,v1=...`) with HMAC-SHA256 and replay-window checks. The event carries identity/status, not outputs, so fetch the run/generation result after verification.
- Use idempotency keys on billable/mutating calls; same key + same body returns the original response, same key + different body is a conflict.

## Validation

Before reporting ready:

- focused fake-ctx registration test proves all tools/hooks are registered;
- bad input and missing env return JSON errors;
- paid/mutating calls block without approval;
- secret-like values are redacted from outputs;
- Browser Use demo dry-run compiles a task template without visiting sensitive pages;
- LTX/FLORA run creation is tested in dry-run/blocking mode unless the user explicitly approved spend;
- source/runtime hygiene check shows writes only occurred in approved plugin paths.
