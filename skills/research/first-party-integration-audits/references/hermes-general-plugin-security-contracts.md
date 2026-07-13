# Hermes general-plugin security/compatibility audit notes

Version-specific findings from a read-only contract audit against Hermes Agent `0.18.2`, commit `5e849942c3b9d36fdd48c80e9d13cb66212d9731`. Re-pin and re-check source before reuse.

## Public surfaces that fit a narrow control plugin

- `PluginContext.register_tool(name, toolset, schema, handler, check_fn=None, requires_env=None, is_async=False, description="", emoji="", override=False)` supports read-only and preview-only model tools.
- Tool handlers must return strings, normally compact JSON strings. The registry turns unsupported return types into a tool-result contract error.
- `register_command(name, handler, description="", args_hint="")` registers a slash command whose handler receives only `raw_args: str`; it may return `str | None` and may be async.
- `profile_name` derives profile identity from `HERMES_HOME`; it can return `default`, a named profile, or `custom`.
- `register_skill(name, path, description="")` requires a `pathlib.Path` to the actual `SKILL.md`. Plugin skills are namespaced, explicit-load, and read-only through the plugin registry.

## Security-significant implementation details

### `dispatch_tool` is not the whole model tool pipeline

At this release, `PluginContext.dispatch_tool()` calls `registry.dispatch()` directly. The normal model-facing path separately runs `pre_tool_call`, approval escalation, post hooks, output persistence/budgeting, and message framing. Do not rely on `dispatch_tool()` alone for native human approval, secret redaction, output budgeting, or untrusted-content framing. This differs from plugin-guide prose that says dispatched tools traverse the normal approval/redaction/budget pipelines.

For a human slash-confirmation command, enforce validation, approval semantics, timeout, output projection, redaction, and readback in the command implementation itself. If a second native Hermes approval prompt is mandatory, verify a public command-context approval API exists in the pinned release; otherwise report the contract blocked rather than importing private internals.

### Slash command handlers lack caller/session context

The registered handler receives only raw argument text. It does not receive gateway user, channel, conversation session, or task identity. A confirmation token is therefore a bearer capability unless another supported surface supplies caller binding.

Safe baseline for preview/confirm designs:

1. Model tools are read-only or preview-only; never accept `confirm: true` or perform mutation.
2. Store high-entropy preview tokens in process memory so restart invalidates them.
3. Bind each record to canonical operation hash, source/target profile, external session/socket identity, exact opaque IDs, expected pre-state, monotonic expiry, and process nonce.
4. Atomically reserve/remove the token before mutation. Burn it on wrong profile, expiry, replay, ambiguity, stale state, malformed native output, or failed validation.
5. Treat a transport timeout after dispatch as indeterminate, not safely replayable; perform authoritative readback and never auto-retry.
6. Prefer same-process slash confirmation. A separate CLI confirmation process cannot consume an in-memory ledger; persisting the token for CLI use can let an agent with terminal access self-confirm unless a separate trusted broker enforces human presence.

### Registration is not transactional

The loader catches an exception from `register(ctx)` and records the plugin as disabled, but does not roll back capabilities registered before the exception. Source also supports force rediscovery even when docs describe `register()` as called exactly once.

Preflight every static invariant before the first `ctx.register_*` call: schemas, unique names, exact skill paths, dependencies, and handler availability. Then make registration cheap, deterministic, idempotent, and free of network/socket calls, subprocesses, client construction, state writes, or directory creation.

### Collision behavior

- Built-in slash command collisions are rejected.
- Plugin-to-plugin slash command names overwrite in the manager dictionary; use one strongly prefixed namespace.
- Tool shadowing across different toolsets is rejected unless `override=True`, with an additional operator grant for non-bundled plugins.
- A duplicate tool name in the same toolset can still replace the prior handler. Use unique prefixed tool names and verify a fresh-process consumer registry.
- Register CLI command names carefully: duplicate plugin names overwrite each other in storage, while argparse collisions with native commands can disrupt discovery/startup.

### Profile-safe launches

- Reject `ctx.profile_name == "custom"` for mutators.
- Treat the `profile_name` fallback to `default` cautiously: resolver exceptions also return `default`. Bind and re-check the expected source profile at preview and confirmation.
- Launch target Hermes profiles with explicit structured argv equivalent to `hermes -p <validated-existing-profile> --resume <opaque-session-id>`; never rely on sticky profile state.
- Bind both source and target profile identity into the canonical operation.

### Output safety is plugin-owned

Generic plugin tool output is not automatically classified as untrusted Herdr/external data, and slash-command results are stringified directly by CLI/gateway/TUI paths. The fallback tool-result budget can also be much larger than a narrow control plugin should return.

Before returning native output:

- parse complete native JSON before any presentation truncation;
- reject oversized frames before unbounded allocation where possible;
- project an allowlist of fields and bound list counts, string lengths, pane text, and final JSON size numerically in the contract;
- strip ANSI and unsafe Unicode controls;
- redact secrets without relying on slash-command transport;
- label pane/output text as untrusted data;
- catch all expected errors and return compact deterministic strings;
- never return raw stdout/stderr, credentials, signed URLs, transcript text, or arbitrary environment.

## Discovery and visibility checklist

A profile-local plugin is discovered only under that profile's active `HERMES_HOME` and must be explicitly enabled. Plugin enablement and model visibility are separate:

1. verify `kind: standalone`, exact flat plugin key, and `plugins.enabled`;
2. enable without a tool-override grant when no override is intended;
3. inspect `hermes -p <profile> tools list` because plugin toolsets obey normal enabled/disabled toolset filters;
4. verify the intended tool schemas in a fresh agent process for every consumer profile;
5. verify the exact namespaced bundled skill with `skill_view("plugin:skill")`;
6. do not use `plugins list` alone as proof that the model can call the tools.

## Audit reporting discipline

When a literal read-only audit uses tools that automatically persist oversized web/session output, disclose each cache/result path and distinguish it from project/profile/config/service mutation. Do not delete the artifacts without permission. Record pre-existing Git dirt before inspection and confirm the same tracked status at the end. Do not claim “no writes” if managed tooling created caches; say exactly which operational surfaces remained untouched.
