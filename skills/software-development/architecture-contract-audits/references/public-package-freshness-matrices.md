# Public package freshness/version/hash matrices

Use this procedure when auditing tracked public packages against live local source trees while preserving fail-closed publication semantics.

## 1. Freeze and separate evidence surfaces

Pin the public repository commit to a literal SHA and read public package bytes from Git objects. Record the live source root separately and rehash it at the end. Treat old candidate reports as historical evidence only; compare their recorded hashes to live hashes before relying on their status.

Do not run the publisher in place during a read-only audit. Reproduce deterministic projection and validation in memory when possible, and never expose private sanitization terms in output.

## 2. Compute three hashes, not one

For every package, record:

1. **public tree hash** — tracked package bytes at the frozen commit;
2. **raw source tree hash** — every live source file using the package's canonical tree algorithm;
3. **current export tree hash** — only files the publisher includes, after deterministic sanitization with the recorded publisher parameters.

Use the repository's exact canonical equation, commonly SHA-256 over sorted `relative_path + NUL + bytes + NUL` entries.

Freshness compares the **public tree** to the **current export tree**. Comparing public bytes directly to raw source bytes creates false drift when sanitization intentionally rewrites author identities, absolute paths, API-key setup examples, private profile prefixes, or plugin-source profile names.

Do not silently omit the raw hash: publishing investigations still need it to distinguish source mutation from a changed sanitization projection.

## 3. Preserve version and digest as independent axes

Extract the public and source versions independently. Classify a package as stale when either:

- the versions differ; or
- versions match but the deterministic export tree differs from the public tree.

An unchanged version does not imply byte currency. Conversely, a raw-source digest difference does not imply stale public output when the current export projection remains byte-identical.

Unversioned public primitives, such as manifest-backed personality overlays, must be labeled `unversioned`; do not invent a version.

## 4. Keep freshness distinct from validity

Build two explicit sets:

- **A — stale by version/export digest**;
- **B — invalid under the current public contract**.

Run the pinned public safety, identity, completeness, and package-specific validators against the frozen public tree. A package may be in A but not B: older public bytes can remain valid and safe. Do not use `outdated` as shorthand for both states, and never recommend deletion from freshness evidence alone.

Useful primary classifications are:

- `byte-current` — public tree equals current export tree;
- `source-newer-but-public-valid-LKG` — export digest/version differs while public bytes pass current gates;
- `source-newer-and-public-invalid` — stale and current public bytes fail gates;
- `no-live-source-match` — tracked public package has no source in the stipulated source inventory.

Clarify that `LKG` in a requested reporting taxonomy may mean only “older retained public bytes that remain valid.” It does not prove the latest source candidate fails. Report latest-source gate results separately if evaluated.

## 5. Reproduce sanitization exactly

A current export projection must use the same inclusion rules and deterministic sanitization parameters as the publisher. Reuse recorded local publisher parameters internally without printing private values. If those parameters are unavailable, label the projection incomplete rather than guessing.

Watch for a second class of failure: a projection can pass regex-based privacy checks but be semantically corrupted by replacement ordering, such as malformed profile names or commands. Treat semantic usability as a separate publication gate; script-green does not prove meaning-preserving sanitization.

## 6. Minimum matrix

For each tracked public primitive report:

- package name and exact public path;
- public version;
- public tree SHA-256;
- live source path or `none`;
- source version;
- raw source tree SHA-256;
- current export tree SHA-256;
- public contract validity;
- primary classification;
- concise reason for version-only, digest-only, or combined drift.

Finish with exact members of sets A and B, validator commands and observed outcomes, final source rehash stability, frozen HEAD, final tracked status, and files modified by the audit.
