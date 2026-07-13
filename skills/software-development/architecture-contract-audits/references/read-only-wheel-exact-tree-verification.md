# Read-only wheel verification for an exact staged tree

Use when an audit supplies both a staged binary-diff digest and a prebuilt wheel, while repository writes/rebuilds are forbidden.

## Evidence sequence

1. Reproduce the staged digest with the exact producer command (usually `git diff --cached --binary | sha256sum`).
2. Search approved artifact locations for a wheel associated with that digest; do not assume an absent `dist/` means the artifact is unavailable.
3. Verify the wheel's SHA-256 independently against the supplied value.
4. Open the wheel as a ZIP without extracting it.
5. Derive the expected package manifest from staged index paths, not the live worktree:
   - map `src/<package>/...` to `<package>/...`;
   - add every `force-include` destination from the staged build configuration;
   - treat dist-info and license records separately.
6. Compare every expected wheel member byte-for-byte with `git show :<source-path>`.
7. Report missing members, unexpected package members, byte mismatches, console entry points, metadata version/dependencies, and required non-Python resources such as plugin manifests and contract JSON.
8. Run the staged digest and index-manifest hash again after inspection.

## Interpretation

- Matching wheel hash alone proves artifact identity, not that it contains the staged candidate.
- Matching member names alone does not detect a stale wheel built from an older blob with the same package version.
- A byte-exact package manifest proves packaging freshness for included repository files, but does not prove runtime operability, external policy/config provisioning, or compatibility with the currently installed consumer.
- Keep package version and artifact digest separate. Multiple different wheels with the same filename/version are an ambiguity worth reporting even when the exact requested hash is found.
- Treat supplied full-suite output as supplied evidence. If the external consumer has advanced since that run, execute a current read-only compatibility probe and report the new hold separately rather than letting the old suite seal current compatibility.

## Read-only implementation note

Use Python's `zipfile` module and `git show :path`; do not rebuild, extract, install, or import the wheel merely to inspect it. Disable bytecode/cache creation for any optional import probe.
