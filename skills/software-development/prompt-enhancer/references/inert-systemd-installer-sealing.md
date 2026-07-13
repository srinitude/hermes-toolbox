# Inert systemd installer and exact-candidate sealing

Use this checklist when a security-sensitive Python project renders systemd deployment artifacts without applying them to the host.

## Candidate provenance

1. Stage the complete candidate before sealing. Use the staged binary diff as the canonical candidate:
   ```bash
   git add -A
   git diff --cached --binary --full-index --no-ext-diff > candidate.patch
   sha256sum candidate.patch
   ```
2. Put the exact digest command—not only the expected digest—in every delegated audit prompt. An audit using another stable algorithm is provenance-blocked and cannot pass or fail the requested candidate.
3. Require start/end digest equality. Any edit, including test-only lint/type narrowing, invalidates focused tests, full-suite evidence, wheel hashes, install proofs, and audits tied to the prior digest.
4. Preserve candidate patch, test log, wheel hashes, clean-install log, static-analysis JSON, and audit summaries. Disposable environments are acceptable only when commands and outputs remain durable.

## Installed-tree closure

An inert bundle is incomplete unless it authenticates both bytes and installation semantics.

- Include every runtime dependency imported by installed commands, especially the project wheel used by a profile-local plugin.
- Pin the dedicated worker environment: target venv, entrypoint, upstream source root, upstream tag/version/peeled commit, and exact project wheel.
- Authenticate for every payload: filename, byte count, SHA-256, mode, operation, destination, owner, and group.
- Model non-copy actions explicitly, e.g. `extract-zip` and `venv-install`.
- Verification must receive the closed expected installation specification and recompute the mapping. A valid MAC over an attacker-selected destination map is not authorization.
- Test rejection of a correctly signed bundle under a different expected mapping.
- In a fresh environment install the exact bundled wheel plus pinned upstream, load the rendered profile, discover the plugin, and exercise every registered override.

## systemd topology checks

- Socket-directory GID, socket-creation GID, client supplementary group, and rendered tmpfiles/sysusers contract must agree.
- Every `ReadWritePaths=` entry must be provisioned by tmpfiles, `RuntimeDirectory=`, `StateDirectory=`, or an authenticated mapping. Remove unused writable paths rather than provisioning speculative state.
- Distinct service identities require exhaustive pairwise UID/GID collision tests, including client groups and duplicated top-level/nested fields.
- Run real occupied-path, process-crash, and concurrent `RENAME_NOREPLACE` boundaries. Do not replace production functions to simulate them.

## Independent schema and migration oracles

- Pin accepted migration history with a literal digest and literal version sequence. Do not derive latest, latest+1, rollback expectations, and fixtures solely from production migrations.
- Test schemas against runtime behavior. Strict JSON rejects non-finite numbers, and response encoders enforce all published bounds before emission.

## Differential static analysis

- Compare baseline/candidate machine-readable diagnostics under the same executable, interpreter, dependencies, and config.
- Normalize path, rule/code, location, and message. Isolated runners that cannot resolve dependencies produce invalid comparisons.
- Edits can shift inherited locations; conservatively fix shifted diagnostics reported as introduced.
- After the final static/type edit, rerun Ruff and Pyright differentials, structure, compile, whitespace, focused tests, then reseal before the full suite.
