# Ad-hoc verification when no canonical test exists

Use this when a prompt executes file/script/config changes but the workspace has no obvious canonical test, lint, or build command for the changed behavior.

## Pattern

1. Create a temporary verifier with an OS-safe tempfile path under `/tmp` and filename prefix `hermes-verify-`.
2. Make the verifier exercise the changed behavior directly, not merely repeat a command that already succeeded.
3. Keep fixtures isolated in temp dirs. For shell/cron scripts, simulate stripped cron-like environments with `env -i HOME=... PATH=...`.
4. For backup/publisher/automation code, verify both the positive path and the no-op/idempotent path.
5. Clean up the verifier after it passes when practical.
6. In the final response, label the result explicitly as **ad-hoc verification**, not full suite green.

## Useful checks for automation scripts

- `bash -n` for changed shell scripts.
- `python -m py_compile` for changed Python scripts.
- Repository cleanliness before/after no-op commands.
- Silent no-op behavior: `rc=0`, `stdout=0`, `stderr=0`.
- Temp fixture proving first-run side effects and second-run idempotence.
- Manifest/schema assertions for generated metadata.
- Restore/read-back checks for backup workflows.
- If the verification reminder names previous `/tmp/hermes-verify-*` paths as changed, make the fresh verifier assert those old paths are absent, then clean up the new verifier too. This avoids a loop where the verification artifact itself remains the only unverified changed path.
- For already-pushed automation changes, verify the live repository is clean and local `HEAD` matches the intended remote branch after the ad-hoc checks, so the result proves the committed artifact rather than only a working-tree draft.

## Pitfalls

- Do not leave `/tmp/hermes-verify-*` scripts behind if they can be safely removed.
- Do not call this canonical suite green unless a project-standard test/lint/build command actually ran.
- Avoid persisting environment-specific failures as durable rules; capture the verification pattern, not the transient failure.