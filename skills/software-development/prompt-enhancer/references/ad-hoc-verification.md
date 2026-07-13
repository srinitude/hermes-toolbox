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
- When a verifier must create a temporary repository fixture for code that calls `git ls-files`, clone the repo into the temp directory instead of using `git archive`; archive fixtures have no `.git` metadata and can exercise a different code path.
- When testing public exporters/validators, include both a positive fixture that should pass and a deliberately bad fixture that must fail with the expected diagnostic, then remove the bad fixture and prove validation passes again.
- Generate complex verifier scripts with a single raw string or a temporary file writer that avoids nested triple-quoted f-strings; syntax-check the verifier itself before trusting its result.
- If source emits executable code inside strings or templates, render the real artifact, extract the executable fragment, and run a language parser against that fragment too. Parsing only the outer file treats embedded code as inert data and can miss construct, nesting, or syntax violations.
- When an automated verification notice names a canonical command such as `npm run test`, run that exact command after the final edit even if an equivalent lower-level command passed earlier; record the fresh canonical result.
- If an exporter has optional publication surfaces such as plugins or profiles, only enable those flags in the verifier when that surface is in scope; otherwise a valid skill-export test can be polluted by unrelated generated packages.

## Pitfalls

- Do not leave `/tmp/hermes-verify-*` scripts behind if they can be safely removed.
- Do not call this canonical suite green unless a project-standard test/lint/build command actually ran.
- Avoid persisting environment-specific failures as durable rules; capture the verification pattern, not the transient failure.
- Do not treat a failed first verifier as evidence about the product code until you have ruled out verifier bugs such as quoting/syntax errors, missing `.git` metadata, or out-of-scope fixture generation.
