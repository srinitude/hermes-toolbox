# Hermes Profile Config Value Matrix

This reference supports the `profile-builder` skill. Use it when a user asks to set every config value or wants full-matrix mode. Do not show the entire matrix by default; summarize categories first and drill down only when needed.

Validated against local Hermes `DEFAULT_CONFIG` on 2026-07-06: schema version `33`, `75` static top-level sections, `518` static leaf paths by the current flattening method. Hermes also supports dynamic/plugin-defined maps, so dynamic keys must be verified before setting.

## Setter Legend

- `hermes_config`: `hermes -p <profile> config set <key> <value>`
- `hermes_model`: `hermes -p <profile> model` or model-specific setup
- `hermes_auth`: `hermes -p <profile> auth` / official OAuth or API-key flow
- `hermes_tools`: `hermes -p <profile> tools enable|disable <toolset>`
- `hermes_mcp`: `hermes -p <profile> mcp add|configure|list|test`
- `hermes_gateway`: `hermes -p <profile> gateway setup|status|restart`
- `hermes_cron`: `hermes -p <profile> cron ...` or the `cronjob` tool
- `skill_write`: profile-local skill write via `skill_manage`
- `manual_user_action`: user must act outside the agent, usually for secrets, OAuth, billing, platform admin consoles, or permission dialogs

## Universal Manifest Fields

Every proposed setting should record:

| Field | Meaning |
|---|---|
| `key` | Dot-path, e.g. `terminal.backend` |
| `value` | Proposed value, or a `secret_ref` placeholder |
| `value_type` | `string`, `boolean`, `integer`, `float`, `list`, `map`, `null`, `duration`, `secret_ref` |
| `source` | `user`, `default`, `preset`, `cloned_profile`, `inferred`, `docs`, `current_config` |
| `setter` | One setter from the legend |
| `requires_secret` | Whether the setting depends on secret material |
| `secret_handling` | `none`, `env_or_auth_flow`, or `user_action_required` |
| `restart_required` | Whether a new session, `/reset`, gateway restart, or dashboard refresh is needed |
| `validation` | Command or observation that proves the setting is active |
| `notes` | Safety caveats, source notes, or reason for choosing the value |

## Static Core Sections to Cover

The profile-builder must be able to discuss and set values under these static sections from `DEFAULT_CONFIG`:

- `_config_version`
- `agent`
- `approvals`
- `auxiliary`
- `bedrock`
- `browser`
- `checkpoints`
- `code_execution`
- `command_allowlist`
- `compression`
- `computer_use`
- `context`
- `context_file_max_chars`
- `credential_pool_strategies`
- `cron`
- `curator`
- `dashboard`
- `delegation`
- `desktop`
- `discord`
- `display`
- `fallback_providers`
- `file_read_max_chars`
- `gateway`
- `goals`
- `honcho`
- `hooks`
- `hooks_auto_accept`
- `human_delay`
- `kanban`
- `logging`
- `lsp`
- `matrix`
- `mattermost`
- `max_concurrent_sessions`
- `max_live_sessions`
- `mcp_discovery_timeout`
- `memory`
- `moa`
- `model`
- `model_catalog`
- `network`
- `onboarding`
- `openrouter`
- `paste_collapse_char_threshold`
- `paste_collapse_threshold`
- `paste_collapse_threshold_fallback`
- `personalities`
- `platform_hints`
- `prefill_messages_file`
- `privacy`
- `prompt_caching`
- `providers`
- `quick_commands`
- `secrets`
- `security`
- `sessions`
- `skills`
- `slack`
- `streaming`
- `stt`
- `telegram`
- `terminal`
- `timezone`
- `tool_loop_guardrails`
- `tool_output`
- `tools`
- `toolsets`
- `tts`
- `updates`
- `vertex`
- `voice`
- `web`
- `whatsapp`
- `x_search`

## Dynamic Sections to Cover

These are open-ended maps or compatibility/provider/plugin families. Validate each key against official docs, plugin docs, live CLI output, current profile config, or local first-party code before setting:

- `providers.<name>` / legacy `custom_providers[]`
- `mcp_servers.<name>`
- `plugins.enabled[]` / `plugins.disabled[]`
- `platform_toolsets.<platform>[]`
- `known_plugin_toolsets.<platform>[]`
- `image_gen.*`
- `video_gen.*`
- `tts.providers.<name>`
- `provider_routing.*` for OpenRouter routing hints when supported by the installed runtime
- `honcho.*`
- `hooks.*`
- `quick_commands.*`
- `personalities.*`
- `platform_hints.*`
- provider-specific model config keys such as `base_url`, `api_mode`, `auth_mode`, `extra_body`, `extra_headers`, `ssl_verify`, `ssl_ca_cert`

## Category Cards

### Model and Routing

Representative keys: `model.*`, `providers.*`, legacy `custom_providers[]`, `fallback_providers`, `provider_routing.*`, `openrouter.*`, `vertex.*`, `bedrock.*`.

Ask the user: preferred provider/model, auth method, fallback tolerance, privacy/data-retention preference, speed/cost/quality preference, local/custom endpoint needs.

Use setters: `hermes_model`, `hermes_auth`, `hermes_config`.

Safety notes:

- Do not store raw API keys in YAML when an auth/env flow exists.
- Custom provider endpoints and TLS settings should be verified before saving.
- Routing preferences such as provider allow/deny lists should be explained because they affect cost, latency, and data handling.

### Tools and Capabilities

Representative keys: `toolsets`, `tools.tool_search.*`, `platform_toolsets.*`, `mcp_servers.*`, `plugins.*`, `web.*`, `browser.*`, `image_gen.*`, `video_gen.*`, `x_search.*`.

Ask the user: minimal/balanced/power-user/custom, network tools allowed, browser allowed, media generation allowed, MCP/plugins needed.

Use setters: `hermes_tools`, `hermes_mcp`, `hermes_config`.

Safety notes:

- Toolset changes usually require `/reset` or a new session.
- Browser/private URL and MCP tools can access external or local resources; ask when the safety boundary changes.
- Plugin-defined toolsets must be checked against the installed plugin.

### Terminal and Sandbox

Representative keys: `terminal.*`, `code_execution.*`, `computer_use.*`, `checkpoints.*`.

Ask the user: local vs sandbox, cwd, persistence, Docker/Modal/SSH needs, rollback/checkpoints, env passthrough.

Use setters: `hermes_config`.

Safety notes:

- Profiles isolate Hermes state, not the full filesystem. Use Docker/Modal/Daytona/Singularity/SSH when real execution isolation is required.
- Do not point `terminal.cwd` at sensitive directories unless the user explicitly asks.

### Safety, Privacy, and Secrets

Representative keys: `approvals.*`, `security.*`, `privacy.*`, `secrets.*`, `command_allowlist`, `credential_pool_strategies.*`.

Ask the user: trusted local vs production bot, approvals mode, PII redaction, private URL access, secret backend, data-retention expectations.

Use setters: `hermes_config`, `hermes_auth`, `manual_user_action`.

Safety notes:

- Secret values belong in official auth/setup/env flows, not in the manifest or transcript.
- `approvals.mode: off` / YOLO should be treated as high-risk and explicitly confirmed.

### Memory and Identity

Representative keys: `memory.*`, `honcho.*`, `personalities.*`, `display.personality`, profile `SOUL.md`, profile-local skills.

Ask the user: memory on/off, external provider, write approval, profile identity and tone, whether memory should be shared or isolated.

Use setters: `hermes_config`, `skill_write`.

Safety notes:

- Store durable identity/preferences only; avoid task diaries or stale facts.
- Use profile-local skills for reusable procedures.

### UI and Surfaces

Representative keys: `display.*`, `desktop.*`, `streaming.*`, `voice.*`, `stt.*`, `tts.*`.

Ask the user: CLI/TUI/desktop/gateway, streaming, markdown style, voice input/output, language, theme/skin, accessibility preferences.

Use setters: `hermes_config`.

Safety notes:

- STT/TTS providers may require credentials or send audio/text to third-party APIs.
- Display changes may need a fresh CLI/TUI session.

### Automation and Gateway

Representative keys: `gateway.*`, `cron.*`, `discord.*`, `slack.*`, `telegram.*`, `matrix.*`, `mattermost.*`, `whatsapp.*`, `kanban.*`, `goals.*`, `hooks.*`.

Ask the user: platform, allowlists, delivery target, cron schedules, webhooks, worker/orchestrator needs, authorization policy.

Use setters: `hermes_gateway`, `hermes_cron`, `hermes_config`.

Safety notes:

- Gateway tokens and bot credentials are secrets.
- Cron prompts must be self-contained because future runs have no current-chat context.
- In TUI/local-only contexts, cron output is saved but not live-delivered unless a gateway delivery target is configured.

### Performance and Lifecycle

Representative keys: `agent.*`, `compression.*`, `auxiliary.*`, `prompt_caching.*`, `tool_output.*`, `tool_loop_guardrails.*`, `logging.*`, `sessions.*`, `updates.*`, `curator.*`, `model_catalog.*`, `network.*`, `lsp.*`, `moa.*`.

Ask the user: speed vs quality, prompt size, retries/timeouts, logging retention, session pruning, skill curation, MoA, language server needs.

Use setters: `hermes_config`.

Safety notes:

- Auxiliary models can change cost and privacy posture.
- Logging/session retention controls can affect both auditability and privacy.

## Validation Pattern

For every approved profile, run or plan the applicable checks:

```bash
hermes -p <profile> config check
hermes -p <profile> config show
hermes -p <profile> tools list
hermes -p <profile> status --all
hermes -p <profile> chat -q "Reply with OK and the active profile name."
```

Add feature-specific checks for gateway, cron, MCP, dashboard, voice, browser, image generation, video generation, or external memory when enabled.

## Manifest Outcome Statuses

Every manifest entry should end as exactly one status:

- `applied`: value set and verified.
- `left_default`: intentionally left at default/current inherited value.
- `skipped`: intentionally not configured because it was irrelevant.
- `blocked_user_action`: requires user action such as OAuth, API key setup, platform admin step, payment/billing, permission dialog.
- `failed_validation`: attempted but validation failed; include exact command/output summary and next step.
