# Browser/media profile specification validation pattern

Use this reference when a private Hermes profile specification adds browser-automation teaching, screen recordings, Browser Use, LTX Studio/LTX API, FLORA, or similar creative SaaS/API surfaces.

## Read-only validation targets

Prefer first-party docs and live, non-secret probes before producing the canonical profile spec:

- Hermes browser docs for available browser tools, `browser.record_sessions`, local/cloud routing, and CDP support.
- Hermes plugin/hooks docs for supported hook names and plugin APIs.
- Browser Use Cloud docs:
  - `llms.txt` and OpenAPI v3 for Sessions, Browsers, Profiles, Workspaces, Billing, and Boxes.
  - Live preview/recording docs for `liveUrl`, `recordingUrls`/`recordingUrl`, presigned recording expiry, and CDP URLs.
  - Human-in-the-loop, structured output, deterministic rerun/cache-script, secrets, webhooks, and profile-sync pages.
- LTX docs:
  - `docs.ltx.video/llms.txt` plus async jobs, auth, models, upload, and endpoint reference pages.
  - LTX Help Center pages for app/platform vs API/playground behavior, credits, and desktop-browser requirement.
  - A browser visit to `https://app.ltx.studio/` only far enough to identify login/verification surfaces; do not solve or bypass them.
- FLORA docs:
  - `https://developer.flora.ai/llms.txt`; extract every listed page when the user asks for “all pages” or full workflow knowledge.
  - REST API, TypeScript SDK, MCP, auth, idempotency, webhooks, errors, Techniques, assets, projects/canvas/actions, models, generations, and recipes.

## Secret handling

If the user pastes API keys or webhook secrets while asking for a prompt/profile/spec:

- Do not repeat raw secrets in the artifact.
- Refer to them through named environment-secret references and declare the corresponding env/config keys.
- Describe validation as “presence without printing” rather than showing values.
- Treat spend approval as separate from permission to handle secrets.
- For FLORA specifically, use `FLORA_API_KEY` and `FLORA_WEBHOOK_SIGNING_SECRET` as secret refs; note webhook verification must use raw request body bytes.

## Browser demonstration specs

When the profile should teach Browser Use agents how to do something in a browser, add a dedicated screen-recording/demonstration plugin surface. Include:

- tools to start, step, checkpoint, hand off to a human, stop, compile, search, and replay demonstrations;
- `enableRecording` / `browser.record_sessions` where appropriate;
- `liveUrl`/CDP/recording URL redaction;
- Browser Use natural-language task templates and deterministic `@{{...}}` rerun templates;
- explicit human-only steps for login, credentials, 2FA, payment, CAPTCHA/Cloudflare, account creation, OAuth approval, and irreversible actions;
- proof requirements: objective, domain allowlist, prerequisites, redacted screenshots/snapshots, recording disposition, cleanup state, and replay validation.

## Browser Use control specs

For a Browser Use plugin/tools spec, cover the whole current v3 surface at a class level:

- Sessions: create/list/get/delete/stop/messages, `keepAlive`, `maxCostUsd`, `outputSchema`, `enableRecording`, `cacheScript`, `autoHeal`, `workspaceId`, `profileId`.
- Browsers: create/list/get/update/downloads, `liveUrl`, `cdpUrl`, `recordingUrl`, proxy, screen size, timeout, recording.
- Profiles: list/create/get/update/delete, with explicit approval for persistent state and profile sync.
- Workspaces: list/create/get/update/delete, files, upload, size, and deterministic rerun script inspection.
- Billing: account check for cost caps.
- Boxes/shell/windows: treat as expanded execution surface requiring explicit approval.
- Webhooks: verify signatures and replay windows before acting.

## LTX specs

Separate LTX Platform from LTX API:

- LTX Platform (`app.ltx.studio`) is a browser-based creative suite for Gen Space, Storyboards, Video Editor, and API Playground. Operate with Browser Use/browser demonstrations and stop at login/Cloudflare/payment/security prompts.
- LTX API (`api.ltx.video`) is programmatic. Use async V2 submit → poll → download for production. Include upload signed URL, 24h job/output retention notes, model compatibility, duration/resolution/fps constraints, and per-second/credit cost gates.
- Prefer API for deterministic supported endpoints; prefer browser automation for visual app-only workflows or teaching Browser Use how to use the app.

## FLORA specs

For deterministic FLORA workflows, require:

1. Resolve workspace/project.
2. Choose Technique vs generation vs asset vs project/canvas/action.
3. Retrieve schema before any run.
4. Map inputs exactly by id/type; HTTPS media URLs only.
5. Estimate cost from `run_cost × count` or available model/generation data.
6. Require approval for billable or mutating operations.
7. Generate deterministic idempotency keys from work identifiers and normalized request body.
8. Create async run with optional approved public HTTPS `callback_url`.
9. Poll or verify signed webhook; webhook payload contains identity/status, not outputs, so fetch the full result after terminal event.
10. Archive outputs if retention is insufficient.
11. Review outputs and write Kanban/evidence records.

Capture FLORA MCP as an optional interactive surface through Hermes `mcp_servers` using `mcp-remote` for OAuth 2.1 + PKCE, while REST API plugins remain better for deterministic backend automation.

## Output discipline

When the user asks for the entire reconciled specification with no “updates/changes/versions/edits” language, return the complete canonical artifact only. Do not include a changelog, diff, or explanation of what changed.
