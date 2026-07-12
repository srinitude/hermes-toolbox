# Deterministic Workflow Primitives

This repository packages reusable primitives that make Hermes workflows
repeatable and auditable.

## Session primitives

- Validator personality primitive: install the preset with
  `./scripts/install-toolbox.sh --apply --personalities` (activation is the
  separate, explicit `--activate-validator` step), then start sessions with
  `/personality validator`.
- Configuration-audit primitive: use `/hermes-config-audits` for public-safe
  Hermes configuration checks.
- Memory-provider primitive: use `/honcho-memory-provider` for current Honcho
  integration and isolation guidance.
- Integration-audit primitive: use `/first-party-integration-audits` to verify
  cross-product claims against current first-party evidence.

## Publishing primitives

- Explicit allowlist primitive: export candidates are selected only through
  repeatable exporter flags or local, untracked allowlists under
  `.git/info/`; there is no default plugin or profile sweep.
- Transactional export primitive: each candidate is staged, sanitized, and
  fully validated before it atomically replaces its destination, so a failing
  candidate leaves the current public package byte-for-byte unchanged
  (latest-passing wins; last-known-good is retained otherwise).
- Public-safety validator primitive (`scripts/validate-public-safety.py`).
- Identity-neutrality validator primitive
  (`scripts/validate-identity-neutrality.py`).
- Package completeness primitive (`scripts/validate-package-completeness.py`):
  plugin packages, native profile distributions, personality primitives, and
  skill packages with resolvable references.
- Structural gate primitive (`scripts/verify-python-structure.py`): 200-line
  files, 30-line named constructs, nesting depth of three.
- Tutorial-suite primitive (`scripts/validate-tutorial-suite.py`): passes only
  when the suite is entirely absent from the manifest or entirely present and
  real-runtime valid; partial publication fails closed.
- Manifest/fingerprint primitive (`inventory/public-manifest.json`,
  `inventory/source-fingerprints.json`) for meaningful update detection.
- Public publisher primitive: fails closed on a dirty checkout, stages only
  accepted paths, and exits silently with no output when there is nothing to
  publish.
