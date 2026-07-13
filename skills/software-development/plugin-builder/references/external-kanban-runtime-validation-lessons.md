# External Kanban Broker Runtime Validation Lessons

Use this companion to `external-kanban-policy-brokers.md` when validating broker daemons, enrolled launchers, exact Kanban tool overrides, and inert service bundles.

## Fresh-process exact-schema preflight

- Run schema and plugin preflight in a fresh process whose `PYTHONPATH` starts with the pinned Hermes source and broker installation.
- A source-root environment variable does not replace modules already loaded in `sys.modules`; an in-process probe can inspect the wrong checkout.
- Derive the source root from the imported native module and fail closed if version, commit, parser, or schema contracts differ.
- Preflight every override schema and trust requirement before the first `ctx.register_tool(..., override=True)`. Registration is not transactional.
- Follow preflight with a fresh real `PluginManager` probe. Verify all expected registry entries, handler ownership, preserved toolset visibility, and refusal without `allow_tool_override: true`.

## Human and worker mutation separation

- Human model-callable mutation overrides remain preview-only unless a separately authenticated human confirmation surface exists.
- Workers mutate only with broker-issued task/run/claim capabilities.
- Approval and capability tokens never appear in tool output, object representations, logs, manifests, or plugin metadata.

## Lease-aware daemon scheduling

- Do not repeatedly invoke dispatch while a healthy, unexpired launch lease is open. Native-adapter contention can starve `launch.started` or terminal reconciliation until the launcher client times out, leaving split state such as native `running` with a sidecar lease still `launching`.
- Dispatch when no lease is open, a lease is expired, or interrupted recovery is already `terminating`. This preserves orphan recovery without contending with healthy lifecycle updates.
- In integration tests, poll sidecar lease/journal state while a lease is active. Read authoritative native task state after the lease closes; aggressive native polling can create artificial contention.

## Timeout and retry posture

- Size local IPC timeouts from measured latency of the pinned native compatibility and operation path.
- Permit bounded retries only for ledger-declared safely retryable reads.
- Do not retry mutations unless the exact operation has a proven idempotency/replay contract.

## Inert systemd bundle validation

- Validate generated units with `systemd-analyze verify`.
- An inert bundle may intentionally reference a production executable that is not installed yet. To distinguish syntax from deployment prerequisites, rerender the identical unit structure with a known existing harmless executable solely for syntax verification.
- Never treat that syntax-only probe as proof that the production executable, account, paths, permissions, or service startup are ready.
