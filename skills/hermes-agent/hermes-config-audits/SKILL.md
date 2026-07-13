---
name: hermes-config-audits
description: Audit and explain Hermes Agent profile config.yaml schemas safely, using first-party docs, live CLI, and local source without exposing secrets.
version: 0.1.1
author: Kiren Srinivasan
license: Apache-2.0
metadata:
  hermes:
    tags: [hermes-agent, configuration, profiles, config-yaml, audit, safety]
    related_skills: [hermes-agent, prompt-enhancer]
---

# Hermes Config Audits

## When to use

Use this skill when the user asks for a detailed rundown, audit, schema inventory, migration review, or troubleshooting explanation of a Hermes Agent profile's `config.yaml` or configuration behavior. It also governs read-only profile-environment audits where configuration determines Projects, Kanban worker/orchestrator surfaces, plugin enablement, or consumer-profile eligibility.

This is a class-level companion to the protected `hermes-agent` skill. Load `hermes-agent` first for general Hermes CLI/doc guidance, then use this skill for config-schema and live profile-environment audit workflows and pitfalls.

## Safety boundaries

- Treat config investigations as read-only unless the user explicitly asks to change settings.
- Do **not** read or reproduce raw secrets from `.env`, auth stores, MCP token files, dashboard passwords, provider API keys, OAuth stores, SSH key material, or project `.env*` files.
- If local `config.yaml` must be inspected, redact credential-like values (`api_key`, `token`, `password`, `secret`, `headers.Authorization`, connection strings) as `[REDACTED]`.
- Prefer first-party schema/docs/CLI over raw user config when the task is conceptual.
- Do not edit Hermes source checkout files for ordinary user configuration work.

## Source-of-truth order

1. Official docs: `https://hermes-agent.nousresearch.com/docs/`
2. Live Hermes CLI output for the installed version:
   - `hermes --version`
   - `hermes config --help`
   - `hermes config check`
   - `hermes config show` only if safe/redacted; beware it can display masked secrets.
   - `hermes config path` and `hermes config env-path` for paths, not contents.
3. Local first-party installed source for exact schema/runtime behavior, read-only:
   - `hermes_cli/config.py` (`DEFAULT_CONFIG`, `set_config_value`, provider normalizers)
   - `cli.py` (`load_cli_config` compatibility defaults)
   - `hermes_cli/runtime_provider.py` (model/provider/api_mode behavior)
   - `hermes_cli/fallback_config.py` (fallback chain shape)
   - `hermes_cli/mcp_config.py` and MCP docs (MCP server schema)
   - `tools/tool_backend_helpers.py` and provider registries for `use_gateway`/plugin behavior
4. If docs and local installed source differ, say so and identify which applies to the user's installed version.

## Audit workflow

1. Load `hermes-agent` first when available.
2. Establish the action mode: usually **answer-only/read-only**.
3. Convert the user's ask into a validation threshold, e.g.:
   - all static built-in keys from the installed default config are enumerated;
   - dynamic schemas are separately described;
   - secrets are not exposed;
   - unverifiable/plugin-defined keys are explicitly called dynamic or unknown.
4. Extract static schema from `DEFAULT_CONFIG` rather than manually scanning prose.
   - Use a small Python/AST/import script to flatten the default config into `top.section.key`, type, and default value.
   - Preserve runtime/source order and map every flattened path back to its AST source line.
   - Harvest adjacent source comments as the first-party explanation for each leaf. Add concise path-specific explanations only where source comments are absent; never leave generic placeholder prose such as “configures X.”
   - Assign every leaf an accepted-value/domain statement: exact enums where finite, `true|false` for booleans, bounded ranges when enforced, and explicitly open-ended domains for provider/model/plugin IDs.
   - Compare with `cli.py::load_cli_config` for legacy/compatibility defaults.
5. Inspect targeted runtime files only for shapes not present in `DEFAULT_CONFIG`:
   - `model` object form and `api_mode` enum from `runtime_provider.py`.
   - fallback provider chain from `fallback_config.py`.
   - custom provider schemas from `config.py` normalizers.
   - MCP shape from docs and `mcp_config.py`.
   - plugin, image/video/TTS/web `use_gateway` shapes from plugin docs/source.
6. Answer with a clear separation:
   - **Static built-in defaults**: directly verified leaf keys.
   - **Accepted compatibility aliases**: e.g. `model.model`, `model.api_base`, legacy `fallback_model`.
   - **Finite value domains**: extract enum-like choices from installed source/registries and current first-party docs rather than inferring them from defaults.
   - **Dynamic/open-ended maps**: `providers`, `mcp_servers`, `plugins`, `hooks`, plugin-specific sections.
   - **Secret handling**: what belongs in `.env`/auth flows instead of YAML.
7. For requests phrased as “every possible/potential config value,” produce concrete artifacts in a safe temporary/export location:
   - an exact source-ordered YAML dump of the installed `DEFAULT_CONFIG`;
   - a flattened `dotted.path`, runtime type, default value, accepted domain, explanation, and source-line inventory;
   - a separate dynamic/compatibility schema reference for aliases and open-ended maps.
   Verify YAML value equality **and recursive key/path order** against imported `DEFAULT_CONFIG`; verify flattened paths are unique, complete, source-ordered, explained, and domain-annotated; report top-level/leaf counts and config schema version; and scan every artifact for credential-shaped literals as well as secret-shaped non-empty defaults.
8. Package long inventories as an exact user-visible archive plus a concise summary. Include an artifact manifest with source and file hashes, then independently recompute those hashes and inspect archive members before delivery. If attaching `cli-config.yaml.example`, label it supplemental: it can document optional/compatibility shapes but may lag runtime defaults, so `DEFAULT_CONFIG` remains authoritative for the installed build.

## Pitfalls

- Do not claim a complete universal schema for third-party plugins. Hermes config has dynamic plugin/provider maps; the honest claim is “complete for built-in/static keys in this installed version, plus verified dynamic schemas.”
- Do not rely only on docs for defaults; local installed source may have newer schema defaults than published docs.
- Do not treat a successful `hermes config set` plus YAML parse as proof that a setting is effective at runtime. For non-standard or task-specific keys, verify the live call path actually reads and forwards the key. Example: in Hermes v0.18.0, `auxiliary.<task>.extra_body` is consumed by centralized `call_llm()`, but `/goal` judge calls may manually use `get_text_auxiliary_client("goal_judge")` + `get_auxiliary_extra_body()`; if that helper does not merge `auxiliary.goal_judge.extra_body`, a config such as `auxiliary.goal_judge.extra_body.reasoning.effort: xhigh` can be present in YAML yet not sent on the wire.
- Do not read `.env` just to list available credential variables. `hermes config check` lists required/optional env names without exposing values.
- `hermes config show` can print masked credentials. If quoting it, only quote non-sensitive sections or redact aggressively.
- `hermes config set` type-coerces simple strings; mention this when explaining value types.
- Do not trust UI/dashboard `CONFIG_SCHEMA` option lists as runtime enums without checking the actual normalizer/consumer. These metadata lists can lag current behavior; installed runtime source and current first-party docs win.
- `config.yaml` belongs to a profile (`HERMES_HOME`); it is not a project file and does not sandbox filesystem access.

## Reference notes

- Session-specific schema-audit method and verified key families: `references/profile-config-schema-audit-2026-07.md`.
- Exhaustive, source-linked config-reference artifact and adversarial-validation pattern: `references/exhaustive-config-reference-artifacts.md`.
- Read-only Projects/Kanban/plugin/worker-lane audit procedure and contract checks: `references/kanban-control-plane-read-only-audit.md`.
- Saved-plan execution drift, rollback, cron/watch/publication, protected-repository, and approval-gate audits: `references/execution-plan-drift-rollback-audit.md`. This reference includes strict no-temp-file discipline, concurrent-state revalidation, evidence plan-hash authority checks, and a JSON reporting contract.
- Read-only public primitive candidate classification for standalone plugins, native profile distributions, and custom personalities: `references/public-primitive-candidate-classification.md`. It defines accepted/rejected/approval-required precedence, logical exporter staging, report-drift handling, dependency closure, sanitization findings, and real runtime/install gates.
