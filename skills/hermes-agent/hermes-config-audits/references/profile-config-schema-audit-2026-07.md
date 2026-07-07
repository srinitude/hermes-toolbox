# Profile `config.yaml` schema audit notes — 2026-07

This reference captures a durable technique from a session where the user asked for “a thorough rundown of a profile's config.yaml with every single parameter and value type/options.”

## Validation threshold used

A correct answer had to:

1. Be read-only: no edits to Hermes config, source, skills, plugins, cron, or projects.
2. Avoid secrets: no raw `.env`, auth store, API key, token, password, SSH, OAuth, or MCP token reads.
3. Use first-party sources: official docs, live Hermes CLI, and local installed Hermes source.
4. Separate installed static schema from dynamic/plugin-defined config maps.
5. Explicitly state limitations: no universal finite schema exists for arbitrary plugins/providers.

## Useful first-party probes

Read-only CLI probes:

```bash
hermes --version
hermes config --help
hermes config check
hermes config path
hermes config env-path
```

Avoid quoting sensitive parts of:

```bash
hermes config show
```

It masks secrets but can still reveal enough account/provider context that redaction is safer.

## Local source files that proved useful

- `hermes_cli/config.py`
  - `DEFAULT_CONFIG`: main static default schema.
  - `set_config_value`: type coercion and routing of secret-shaped keys to `.env`.
  - custom provider normalizers: accepted `providers` / `custom_providers` entry keys.
- `cli.py`
  - `load_cli_config`: legacy/compatibility defaults not all present in `DEFAULT_CONFIG`.
- `hermes_cli/runtime_provider.py`
  - accepted `model` object behavior.
  - `api_mode` enum: `chat_completions`, `codex_responses`, `anthropic_messages`, `bedrock_converse`, `codex_app_server`.
  - Azure Foundry `auth_mode: entra_id` and `model.entra.scope`.
- `hermes_cli/fallback_config.py`
  - `fallback_providers` and legacy `fallback_model` shapes.
- `hermes_cli/mcp_config.py` plus official MCP config reference
  - `mcp_servers` dynamic map shape.
- `tools/tool_backend_helpers.py`
  - `<section>.use_gateway: true` behavior for managed Tool Gateway preference.
- `hermes_cli/tools_config.py`
  - `platform_toolsets`, `known_plugin_toolsets`, image/video generation provider/model selection, xAI storage config.
- `toolsets.py` and docs/reference/toolsets-reference
  - built-in toolset names, wildcard `all` / `*`, and platform toolset behavior.

## Static-vs-dynamic answer framing

Use this framing in future answers:

- “Complete for built-in/static keys in the installed Hermes version” means flattened `DEFAULT_CONFIG` plus compatibility defaults from `cli.py` were enumerated.
- “Dynamic schemas” means maps where user plugins, provider plugins, MCP servers, or gateway/platform integrations can add keys:
  - `providers`
  - `custom_providers`
  - `mcp_servers`
  - `plugins`
  - `hooks`
  - `quick_commands`
  - `platform_hints`
  - `credential_pool_strategies`
  - platform/provider sections such as `image_gen`, `video_gen`, `tts.providers`, `web`, `browser`
- Avoid saying “every possible key” without the dynamic caveat.

## Verified notable shapes

### `model`

Accepted as string or map.

Map keys verified during the session:

- `provider`: string provider id.
- `default`: string model id.
- `model`: alias for `default` when `default` missing.
- `base_url`: string endpoint URL.
- `api_base`: alias normalized to `base_url`.
- `api_key` / `api`: string secret-like values; discourage raw YAML storage.
- `api_mode`: enum listed above.
- `openai_runtime`: `codex_app_server` is a verified opt-in for OpenAI/Codex routes.
- `auth_mode`: Azure Foundry supports `api_key` and `entra_id`.
- `entra.scope`: optional Azure Entra scope.
- `aliases`: map string→string.
- `persist_switch_by_default`: bool.

### `providers` / `custom_providers`

Provider entry keys accepted by normalizers:

- URL aliases: `api`, `url`, `base_url`.
- Auth/key fields: `api_key`, `key_env`, `api_key_env`.
- Transport aliases: `api_mode`, `transport`.
- Model fields: `model`, `default_model`, `models`.
- Limits/options: `context_length`, `rate_limit_delay`, `request_timeout_seconds`, `stale_timeout_seconds`, `discover_models`.
- Request customization: `extra_body`, `extra_headers`.
- TLS: `ssl_ca_cert`, `ssl_verify`.

### `fallback_providers`

List of maps with required `provider` and `model`; optional `base_url`. Legacy `fallback_model` can be a map or list and is appended after `fallback_providers`.

### `provider_routing`

OpenRouter routing map:

- `only`: list[str]
- `ignore`: list[str]
- `order`: list[str]
- `sort`: `throughput`, `latency`, `price`
- `require_parameters`: bool
- `data_collection`: string; commonly `deny`

### `mcp_servers`

Official MCP docs verify dynamic map entries with stdio keys (`command`, `args`, `env`) or HTTP keys (`url`, `headers`, TLS keys), plus `enabled`, `timeout`, `connect_timeout`, `supports_parallel_tool_calls`, `auth: oauth`, `tools.include`, `tools.exclude`, `tools.resources`, `tools.prompts`, and `sampling`.

## Response style lesson

For long config inventories, lead with the validation evidence and limitations before the huge list. The user asked for thoroughness, but the answer should still be structured so the “complete static vs dynamic” distinction is visible near the top.
