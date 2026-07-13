# Exact Single-Skill Public Classification

Use this when asked to freshly classify one local skill at an expected source-tree hash without changing the live source or publication repository.

## Classification sequence

1. **Freeze the source.** Compute the repository `tree_sha` convention over relative path, NUL, bytes, NUL. Require the observed start hash to equal the user-supplied expected hash and read the version from exact frontmatter. A mismatch is a hold; do not classify a different generation.
2. **Project from the exact repository generation.** Materialize the repository index into a disposable `/tmp/hermes-classify-*` root with `git checkout-index --all --prefix=...`, copy only required untracked sanitizer policy inputs such as identity/private-profile deny lists and approved authorship, and invoke the real transactional exporter for exactly one `--public-skill`. Do not use live repository output paths.
3. **Hash the projected package.** Use the same deterministic package-tree hash as the exporter. Record exporter exit, change list, projection hash, and exact projected path set.
4. **Separate static acceptance from byte semantics.** Run production public-safety, identity-neutrality, package-completeness, tutorial, package-local-reference, and included structural checks. Then independently diff source versus projection and inspect every changed line. Production validators passing does not prove semantic validity.
5. **Run focused byte gates.** Enumerate every file missing a final LF. Search changed projected lines for malformed nested placeholders, sanitizer-corrupted product/CLI/profile names, invalid executable paths, broken author/email forms, and doubled placeholders. Report exact projected file, line, token, and occurrence count.
6. **Resolve dependencies.** Distinguish advisory `metadata.hermes.related_skills` from body-mandated loads. Require each hard peer to be bundled by the pinned runtime or accepted in the projected public manifest. Verify package-local support references separately.
7. **Probe a clean home.** Copy only the exact projected package into a disposable Hermes home and run real `hermes skills list --source local --enabled-only`. Treat discovery as orthogonal evidence: successful discovery cannot override semantic, newline, or dependency failures.
8. **Seal and clean.** Recompute source and projection hashes at the end. Source drift changes the outcome to hold. Record repository HEAD, branch, staged digest/path count, unstaged/untracked counts, then remove the complete disposable root and verify absence.

## Disposition rules

- `accepted-current`: expected/start/end source hashes match and exact projected bytes pass static, semantic, newline, dependency, structure, and clean-home gates.
- `hold`: expected hash mismatch, source drift, unresolved dependency/provenance, or incomplete proof.
- `rejected`: stable current source has a decisive hard failure and no valid existing public package.
- Judge an existing public package independently for last-known-good retention; source rejection alone does not withdraw it.

## Reporting minimum

Report version; expected, observed-start, end, and projection hashes; every decisive blocker with exact projected locations; all gate outcomes; clean-home result; repository integrity; temporary and persistent side effects. Explicitly state when production validators pass but the independent exact-byte gate fails.
