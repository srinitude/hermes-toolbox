# Marker-Rollout Scope-Preservation Audits

Use this checklist for read-only audits of marker-delimited changes rolled across customized skill/configuration trees.

## Preservation proof

1. Freeze the authoritative plan, baseline inventory, rollback archive, and rollback-member manifest by SHA-256.
2. Extract the canonical block directly from the frozen plan, including marker lines; hash those bytes.
3. For every pre-existing target, compare baseline and current line sequences with a deterministic sequence diff:
   - require exactly one non-equal opcode;
   - require that opcode to be an insertion;
   - verify the inserted marker block and its semantic anchor;
   - separately verify old lines remain an ordered subsequence.
4. Compare support-file manifests as exact `(relative path, SHA-256, size)` sets, excluding only the intentionally patched primary file.
5. Re-snapshot all target trees twice at the end and require identical aggregate digests.

A subsequence check alone is insufficient: it permits unrelated extra insertions. Pair it with the one-insertion diff equation.

## Missing-tree seeding

For a previously absent tree:

- derive the source manifest from regular files only;
- allow only the primary file plus approved support directories;
- reject symlinks, special files, hidden path components, and runtime/credential/database/key filenames;
- compare the complete seeded manifest byte-for-byte with the canonical source;
- scan conservatively for high-confidence secret signatures (private-key headers and provider token formats), reporting the signature set used;
- record file and directory mode distributions, but distinguish unusual permissions from explicit acceptance failures.

## Rollback archive

Stream archive members without extracting them. Require:

- file hashes equal the rollback manifest exactly;
- no manifest-only or archive-only members;
- every member is beneath an approved target root;
- no links, special members, hidden components, runtime/secret filenames, or high-confidence secret signatures.

## Unexpected-path evidence

A target-only baseline proves preservation only within the enumerated target trees. It cannot prove that unrelated skill/configuration paths were unchanged.

For broader scope evidence:

1. Prefer a full pre-rollout hash manifest of every path whose immutability is claimed.
2. If only target baselines exist, scan out-of-target mtimes/ctimes from the recorded rollout start as a drift detector.
3. Report each drifted path with timestamp and current hash, but do not attribute the writer without provenance.
4. Treat mtime-only evidence as a blocker to an absolute “no unexpected modifications” claim, not as proof that the audited rollout caused the write.
5. Separate hidden tool-managed indexes such as skill-usage metadata from skill content. A mandated read may update such metadata; record it as incidental runtime drift and do not silently claim a perfectly read-only audit.

## Reporting

Lead with the narrowest honest verdict, for example: `target preservation passes; global scope cleanliness blocked`. Report current evidence and blockers only when requested. List exact blocker paths; summarize fully passing target cohorts by counts and manifest equations rather than repeating every path.
