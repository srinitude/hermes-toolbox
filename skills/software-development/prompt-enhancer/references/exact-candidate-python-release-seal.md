# Exact-Candidate Python Release Seal

Use this for large staged Python candidates where tests, packaging, and independent audits must all bind to identical bytes.

## One authoritative test process

- Do not run focused tests concurrently with an authoritative full suite when they may share HOME, sockets, processes, databases, workers, or pinned source trees.
- Create the background suite log and numeric exit artifact **at launch**, tied to the candidate digest and exact command. A SIGTERM, vanished process, missing exit artifact, or suite from an older tree is invalid evidence.
- When a socket client masks an exception as an availability error, reproduce through the direct handler/API seam to preserve the traceback.
- Measure successful request duration before changing behavior. Test-client deadlines should match production-class deadlines; a deadline barely above normal recovery time creates load-only flakes.

## Seal the tested tree

After intended edits:

```bash
git add -A
git diff --check
test -z "$(git diff --name-only)"
test -z "$(git ls-files --others --exclude-standard)"
git diff --cached --binary | sha256sum
```

Record the binary staged-diff digest and staged path count. Any later edit invalidates the digest, wheel, full-suite evidence, and exact-tree audits; reseal and rerun affected gates.

## Baseline-differential static analysis

A whole-repository linter failure does not itself prove candidate regression.

1. Export clean `HEAD` into a temporary directory.
2. Run identical machine-readable Ruff/Pyright commands on baseline and candidate.
3. Normalize paths relative to `src/`.
4. Compare Ruff by path, code, location, and message.
5. Compare Pyright semantically by path, severity, and message as well as by location; harmless edits can shift an inherited diagnostic.
6. Block on introduced findings and report inherited/resolved counts separately.

Do not auto-fix inherited repository debt during a scoped seal.

## Prove the wheel

Build in a fresh temporary directory, then:

- hash the wheel;
- rebuild from the unchanged candidate and require identical SHA-256;
- install only that wheel into a fresh supported-Python environment;
- run import-provenance, packaged-data, and CLI-startup checks outside the source tree;
- run package metadata and dependency-vulnerability checks;
- compare every packaged Python/data member byte-for-byte with candidate source;
- reject traversal/absolute members, bytecode, caches, or build residue.

Recompute the staged digest after build/install checks and require zero unstaged/untracked drift.

## Pin independent reviews

Provide each read-only reviewer with the repository path, exact staged digest/path count, wheel path/hash, current evidence, and explicit no-write/no-commit/no-full-suite constraints. Require hash verification at start and end plus a fail-closed `PASS` or `BLOCK` with file/line evidence.

For high-risk brokers or installers, separate security/authority, specification/semantic, and packaging/deployment reviews. Do not commit until every blocker is fixed or explicitly accepted at the correct human gate.
