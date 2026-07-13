# Post-Commit Verification That External Trackers Can Recognize

Use this when a long-running code task has passed tests but an external workspace guard still reports `unverified`.

## Durable pattern

1. Reach a clean, committed checkpoint first. Record `HEAD` and confirm the worktree is clean.
2. Run the authoritative full suite against that exact tree. A tracked background process is valid execution evidence, but its completion log may not satisfy an external verifier that only observes foreground test commands.
3. After the commit, run a **fresh foreground focused suite** covering every changed behavior family and compatibility boundary. Use the project interpreter explicitly when needed, for example:
   ```bash
   .venv/bin/python -m pytest <changed-test-files> -q
   ```
4. Run structural limits, compilation/lint, `git diff --check`, worktree status, and `git rev-parse HEAD` in a separate verification packet. Do not append them with `&&` to the tracker-facing `pytest` command when the tracker is command-shape-sensitive.
5. Report full-suite, standalone focused-suite, and structural/status evidence separately. Never claim the earlier pre-commit or background result is the tracker-visible post-commit proof.

## Durable background-suite artifacts

A process-manager handle is useful but not sufficient evidence for a long suite. Before launch, create unique named paths under `/tmp/hermes-verify-*` for the complete log and numeric exit code. Remove stale files first, preserve pytest's exact exit code, and make the wrapper exit with that same code:

```bash
set +e
LOG=/tmp/hermes-verify-<slice>-full.log
EXIT=/tmp/hermes-verify-<slice>-full.exit
rm -f "$LOG" "$EXIT"
python -m pytest -q --durations=30 >"$LOG" 2>&1
code=$?
printf '%s\n' "$code" >"$EXIT"
cat "$LOG"
exit "$code"
```

Record the process handle, candidate HEAD/digest, log path, and exit path together. A valid result requires the exact candidate plus both a complete final summary and exit `0`. If the runner disappears and no exit artifact exists, the run is invalid even when the OS child is still active or the log contains progress. Stop the orphan when its final status cannot be recovered; do not spend the remaining runtime on evidence that cannot pass the gate. Never write secrets or raw environment dumps into the durable log.

## Authoritative process ledger and shared-resource isolation

Long suites often outlive several candidate revisions. Keep one explicit authoritative process ID and mark every superseded process ID with its invalidation reason (candidate changed, missing required environment, overlapping shared resources, or intentional SIGTERM). Delayed completion notifications from those IDs are stale evidence; never merge their dots, failures, or exit codes into the current candidate's verdict.

Before launching tracker-facing tests while a full suite runs, classify the selected tests:

- **Process-local and isolated:** pure unit tests or temporary-file tests with no shared HOME/profile/runtime/service state may run independently.
- **Shared-resource:** daemon, launcher, profile, worker, socket, persistent database, or fixed-HOME tests must never overlap the authoritative suite.

If a guard requires immediate shared-resource evidence, stop and invalidate the background suite first, run the exact named tests alone, then restart exactly one full suite. If an overlapping failure disappears in isolated reproduction, record it as invalid test concurrency rather than changing production code.

## Repeated `unverified` guard

If the guard repeats after a successful foreground run:

- Do not edit production code merely to appease the guard.
- Confirm the command exited zero and the tree/HEAD are unchanged.
- Prefer one direct, relevant foreground `pytest` invocation over repeatedly rerunning a long full suite. If the successful command chained `pytest` with other checks, repeat only the focused `pytest` portion as a plain standalone command with no `&&`, wrapper, linter, status probe, or background-log retrieval.
- If a generated console launcher is unusable because of transient environment state, use the functioning project interpreter with `-m pytest`; do not rewrite venv/runtime files as part of source verification.
- State the exact command shape, pass count, HEAD, and clean-tree result.

### Intentionally uncommitted blocked candidates

A security-sensitive candidate may need tracker-facing verification before commit because a separate external gate blocks the authoritative suite or commit, such as a vulnerable exact upstream release pin. In that case:

1. Stage the complete intended tree and require no unstaged or untracked paths.
2. Bind every result to `sha256(git diff --cached --binary --full-index --no-ext-diff)` plus the base HEAD and staged path count.
3. Run directly modified test files and source-boundary tests in standalone foreground invocations, but label them **pre-commit focused evidence**, not post-commit verification or full-suite green.
4. If repeated tracker notices ignore successful `python -m pytest` commands, make exactly one materially different attempt using a disposable environment built from declared test dependencies and invoke its real `bin/pytest` entrypoint directly. Remove the environment afterward and recheck the staged digest.
5. If the tracker repeats after file-by-file GREEN and the real-entrypoint run, stop. Preserve outputs and report stale evidence attribution; do not recreate removed verifiers, rerun equivalent tests, edit production code, or weaken the external blocker.

Do not commit merely to satisfy the tracker. The substantive full-suite, security, review, and approval gates still control commit eligibility.

## Disposable verification for packaged console entry points

A stale generated script in a project venv can have a dead interpreter shebang even when the current source entry point is correct. Keep source verification separate from environment repair:

1. Read the generated launcher only to attribute the failure; do not rewrite the venv as part of a source-code slice.
2. Build the current wheel into `/tmp/hermes-verify-*/dist` with the project's available build frontend. If the project interpreter has no `pip`, prefer an already-installed frontend such as `uv build` rather than modifying the project venv.
3. Create a disposable venv, install the wheel without unrelated dependencies when the smoke path permits it, and invoke the installed console script directly (`--help` plus the narrow behavior smoke when practical).
4. Remove the complete `/tmp/hermes-verify-*` tree and verify no temporary artifact remains.
5. Report the stale generated launcher as environment state, the disposable wheel result as package-entry-point evidence, and the normal focused `python -m pytest` result as source behavior evidence. Do not treat one as a substitute for the others.

Example shape:

```bash
uv build --wheel --out-dir /tmp/hermes-verify-cli/dist .
uv venv /tmp/hermes-verify-cli/venv
uv pip install --python /tmp/hermes-verify-cli/venv/bin/python --no-deps \
  /tmp/hermes-verify-cli/dist/*.whl
/tmp/hermes-verify-cli/venv/bin/<console-command> --help
rm -rf /tmp/hermes-verify-cli
```

## Guard-mandated `/tmp/hermes-verify-*` scripts

When the guard explicitly requests a temporary verifier rather than a normal test command:

1. Create the path with the OS tempfile API and the exact requested prefix. Write the script through a top-level file tool so the artifact is visible to the verification tracker.
2. Run the script in a **top-level foreground terminal call**. Do not hide creation or execution inside `execute_code`, a background process, or another wrapper; nested tool execution may be real but invisible to command-shape tracking.
3. Let the invoked test runner print its normal pass count and `OK`/success line. Add focused real-behavior probes only for changed behavior not already exercised by those tests.
4. Clean up the verifier in the same foreground terminal call after preserving its exit code. Print both the verifier exit and cleanup result.
5. Label this evidence **ad-hoc verification**, not canonical suite green. If the harness itself fails only while formatting its final report, fix the harness and rerun the complete verifier; do not reinterpret earlier partial execution as a pass.

If the guard names changed paths in a superseded or removed worktree after those commits were merged, do not recreate or edit that stale worktree. Verify the canonical merged checkout, prove its tree contains the changed branch tree (or map each named path to the merged copy), and report the stale-path mapping separately.

### Tracker remains stale after a successful ad-hoc verifier

A later notice may still list the removed verifier path or replay output from an older, unrelated verification generation. Treat this as an evidence-attribution problem, not permission to loop:

1. Preserve the successful verifier output, exact candidate digest, invoked test count, structure result, cleanup confirmation, and the removed path.
2. Confirm the substantive repository tree/digest did not change after the verifier ran.
3. Compare the notice's reported command/output and paths with the verifier generation. Explicitly identify stale or unrelated evidence instead of merging it into the current verdict.
4. Do not recreate an equivalent verifier after one exact top-level foreground run already passed and cleaned up. A second identical run adds no correctness evidence and can cause the removed artifact to be reported again.
5. Continue only according to the substantive workflow gate (for example, wait for independent reviews or run a newly required test). Report the ad-hoc verifier as passed while stating that the external tracker did not recognize it; never claim tracker-visible green.

Re-run only when the candidate bytes changed, the first verifier did not complete, cleanup failed, or the guard asks for materially different behavior evidence.

## Why this matters

A test process can be genuinely green while the surrounding workflow still lacks machine-recognizable evidence. Treat execution correctness and verification-state recognition as two separate boundaries, and satisfy both without fabricating results or mutating generated runtime state.
