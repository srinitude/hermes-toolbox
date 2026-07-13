# Exact-object test execution under concurrent drift

Use this when a read-only audit outlives the repository HEAD or when the installed dependency no longer matches the pinned contract.

## Evidence layers

Keep results separate:

1. audited repository object against its pinned dependency object;
2. audited repository object against the currently installed dependency;
3. concurrent committed or uncommitted work, inspected but not attributed to the audited object.

An installed-dependency compatibility hold is rollout evidence. A failure reproduced against the pinned dependency is an implementation defect. Never merge their counts without labels.

## Stable repository export

Record commit and status, then export the exact object to a temporary directory with `git archive <commit>`. Run tests from the export with bytecode and test-cache writes disabled. Use explicit object reads (`git show <commit>:<path>`) during inspection rather than mutable worktree files. Remove the export and re-record HEAD/status when finished.

## Exact staged-patch audits without creating a snapshot

A staged patch is not identified by `HEAD`: the index can change while `HEAD` remains fixed. At the opening boundary, record all three:

1. literal `HEAD` SHA;
2. SHA-256 of `git diff --cached --binary --no-ext-diff`;
3. `git status --porcelain=v2 --untracked-files=all`, whose index object IDs preserve the exact staged blob for every path.

If the staged-diff hash later changes, stop reading mutable worktree or `:<path>` content. Reconstruct evidence directly from the opening blob IDs with `git show <blob-id>` and retain their original line numbers. Compare each opening/current blob pair to classify concurrent drift, but never attribute the newer index to the audited patch. This works even under a strict no-write boundary because it needs no temporary index, checkout, archive, or cache.

When only some staged blobs drift, continue using the opening object IDs for those paths and verify that unchanged production blobs still match their opening IDs. Report the opening patch hash as the audited candidate and the closing patch hash as excluded concurrent drift. A stable `HEAD` alone is not evidence that the staged candidate remained stable.

## Exact-index focused tests while the worktree drifts

If the index is still the audited candidate but unstaged edits appear, never run sealing tests from the live worktree: editable installs, pytest path insertion, and child imports can silently consume replacement bytes. Materialize the index into a disposable directory with `git checkout-index --all --prefix="$candidate/"`, then immediately recheck the accepted staged-patch digest. Run with `PYTHONDONTWRITEBYTECODE=1`, disable the pytest cache provider, and set `PYTHONPATH` to the exported `src` tree. For a pinned dependency, use a disposable shared clone or exact checkout at the literal dependency SHA; delete both exports afterward. Label any earlier live-worktree test results as mixed-generation evidence, even if only tests or configuration files drifted.

For a supplied wheel, compare every package/data member byte-for-byte against `git show :<path>` rather than against the mutable worktree. Require no missing, extra, or mismatched package members, then execute package-data and CLI smoke checks from an extracted temporary wheel tree. This proves wheel completeness and staged-byte identity without installing it. Keep the wheel SHA, staged-patch SHA, and index-manifest SHA as separate identities.

A useful exact-candidate pattern is:

```bash
candidate=$(mktemp -d)
trap 'rm -rf "$candidate"' EXIT
mkdir "$candidate/tree"
git checkout-index --all --prefix="$candidate/tree/"
# Recheck the accepted producer digest here before running tests.
cd "$candidate/tree"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$candidate/tree/src" \
  /absolute/path/to/python -m pytest -p no:cacheprovider <focused tests>
```

## Pinned dependency not reachable from refs

A normal local clone can omit a commit that exists in the object store but is no longer reachable from advertised refs. For a temporary read-only checkout:

1. initialize a temporary Git repository;
2. resolve the dependency checkout's common Git directory;
3. point the temporary repository's `.git/objects/info/alternates` at that common directory's `objects` path;
4. check out the exact dependency commit;
5. direct test `HOME` or source-root configuration to the temporary checkout.

This avoids modifying the dependency checkout and preserves the exact commit identity required by contract tests.

## Child-process import provenance trap

An exact-object test process can still spawn children from the mutable worktree or an installed/editable package. `PYTHONPATH` on the parent is not proof when production launchers sanitize the child environment, and `sys.executable` may resolve to a virtualenv whose editable `.pth` points elsewhere. Before attributing a subprocess/E2E result to the exported object:

1. inspect child environment construction for removed `PYTHONPATH`, `HOME`, and site controls;
2. record the imported package origin in the actual child, not only in the test process;
3. install a wheel built from the exact object into an isolated temporary interpreter, or use an exact-object environment that cannot resolve the live worktree;
4. classify failures from mixed parent/child generations as harness contamination until reproduced with exact child provenance.

A library-only test may remain valid from `git archive`; a daemon test whose launcher recursively invokes `python -m package.cli` usually requires an exact installed wheel.

## Registry-equation trap

When a slice adds a broker-only protocol operation, update its explicit non-native classification before claiming compatibility closure. Do not fabricate a native-ledger record. Run the exhaustive protocol-versus-ledger equation first; a red equation outranks dashboard, installer, backup rollout, and deployment work.

## Reporting

State:

- exact repository and dependency commits;
- tests present versus tests executed;
- exact pass/fail counts for each evidence layer;
- final repository status and concurrent drift;
- whether temporary exports/caches caused any non-repository writes.
