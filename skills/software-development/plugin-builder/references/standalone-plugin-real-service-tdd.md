# Standalone plugin real-service TDD

Use this when a directory plugin is also the root of its own repository and tests must exercise a live local service through a real Hermes `PluginManager`.

## Fresh-process probe pattern

1. Run each integration scenario in a fresh Python process.
2. Create a temporary Hermes home under `/tmp/hermes-verify-*`.
3. Symlink the source plugin into `<temp-home>/plugins/<name>` and write only the temporary `plugins.enabled` config.
4. Point `HERMES_BUNDLED_PLUGINS` at an empty temporary directory to keep discovery focused.
5. Load the real `PluginManager`, inspect its real registries, and dispatch through the real global tool registry. Do not substitute a fake `PluginContext`.
6. Set `PYTHONDONTWRITEBYTECODE=1` so validation does not dirty the plugin or Hermes source trees.

## Repository-root `__init__.py` pitfall

A standalone plugin must have a root `__init__.py`, but pytest may import that file as a collection/setup module without package context. Top-level relative imports can then fail with `attempted relative import with no known parent package` before tests run.

Keep plugin-local imports inside `register(ctx)` rather than at module import time. This also enforces the performance requirement that import itself is cheap. When needed, use pytest's `--import-mode=importlib`, but do not rely on that alone: collection can still import the repository-root `__init__.py`.

## Profile-awareness plus a live user service

A temporary custom `HERMES_HOME` outside the normal profile tree can resolve as the deployment's `default` profile. To prove `ctx.profile_name` with a named temporary profile while still reaching a real user service:

1. Capture the real home before changing environment variables.
2. Set `HOME` to a temporary OS home.
3. Set `HERMES_HOME` to `<temp-OS-home>/.hermes/profiles/<probe-profile>`.
4. Preserve the service's real configuration discovery explicitly, for example with its documented config-path variable and `XDG_CONFIG_HOME`, when the service depends on the original user config/socket location.
5. Assert the plugin output reports `<probe-profile>` and that the service command reaches the real running service.

This is test-process isolation, not permission to edit the real service config.

## Side-effect state-machine testing

For preview/token/confirm plugins, keep model tools preview-only. Test the human confirmation route in one process so its in-memory token store is real:

- wrong token: compare live state before/after;
- expiry: mint with a bounded one-second TTL and wait on real time;
- replay: confirm once successfully, then reuse the same token;
- stale state: mint two tokens from state A, use one to move to state B through the confirmation route, then prove the other fails stale;
- restoration: mint and confirm a fresh token to restore the original live state.

Use an idempotent or reversible live operation for confirmation tests. Avoid spawning persistent agents merely to prove execution when a focus operation exercises the same approval state machine.

## Security-boundary acceptance tests

When a plugin projects native service data into model-visible output, treat every native string as hostile—even identifiers, status fields, caller metadata, socket paths, session names, topology labels, and native error codes.

- Validate raw authority first (exact socket/profile/session/caller equality), then sanitize the separate public projection. Never sanitize before authority comparison, and never expose the raw authority value afterward.
- Strip complete 7-bit ESC and 8-bit C1 control strings, not only CSI/OSC prefixes. Cover terminated and unterminated DCS, SOS, PM, APC, OSC, and CSI forms; remove the payload with the introducer.
- Redact quoted and unquoted Basic/Bearer credentials, folded Authorization/Cookie headers, and complete multipart `Cookie=`/`Set-Cookie=` values. Tests must assert that synthetic payload markers—not merely control bytes—are absent.
- Bound subprocess output while reading pipes incrementally. A size check after `capture_output` has already buffered the response is not a memory bound. On output overflow, timeout, or read failure, kill and reap the child.
- For stored side-effect argv, validate the complete argv against the sealed canonical operation. A generic verb allowlist is insufficient; test adjacent unapproved verbs and tampered child arguments.

Use synthetic non-secret markers and real local service boundaries. Do not print or probe real credentials.

## Fail-closed live fixture lifecycle

A unique session name and collision check are necessary but not sufficient. Start the cleanup `try/finally` immediately after the pre-existing-resource check and before `Popen`/socket wait/setup operations. Cleanup must:

1. attempt the native stop route;
2. terminate or kill and reap the process if native stop or wait fails;
3. attempt exact unique-session deletion in an outer `finally`;
4. verify the session/socket directory is absent;
5. re-check protected-session topology.

A collision must abort without deleting anything. Setup failures after process launch must follow the same cleanup path as normal teardown.

## Checkpoint discipline

After each coherent vertical slice: focused GREEN, relevant full GREEN, parser-based structure check, prohibited-pattern scan, `git diff --check`, commit, and clean-status proof. Prefer a test invocation that prints an explicit `N passed` summary when an external verification tracker consumes terminal evidence. If a tool-loop ceiling arrives during the next RED slice, report the last clean commit separately from the dirty unfinished test files; never call the repository complete.