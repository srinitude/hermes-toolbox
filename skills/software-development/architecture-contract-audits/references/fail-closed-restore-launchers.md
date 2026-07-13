# Fail-Closed Restore and Multi-Target Launcher Audits

Apply this checklist to human-confirmed restore, resume, and batch-launch paths.

## Target provenance and ambiguity

- Internally consistent writable JSON is not trusted provenance. Bind each target to a preview generation, trusted ledger row, or live agent identity.
- Test whole-target substitution, not only contradictory duplicates: same profile/new session, new profile/new session, and multiple distinct sessions mapped to one live slot.
- A redacted confirmation cannot help an operator detect session-ID substitution.
- Re-read or compare a version/nonce/digest after confirmation. Delete only the exact generation that was approved and launched.

## TOCTOU and current-pane rebinding

- Preserve the first rebound terminal/pane identity and require confirmation-time identity to equal it. Comparing both observations only to an older pre-restart ID accepts a second rebind.
- Verify that the rebound identity actually constrains launch placement; a checked value that is never used is not a binding.
- Prefer atomic server-side validate-and-launch. Otherwise revalidate each target immediately before spawn, especially when earlier launches may take seconds.
- Profile directory/config existence is weaker than profile identity stability through child startup.

## One-time consumption and partial batches

- Serialize controllers or atomically claim a target generation; two confirmation panes must not launch the same target set.
- Define partial-N behavior explicitly: atomic batch, rollback, or an atomic per-target completion journal.
- Never retain already successful targets unchanged for blind retry; this duplicates agents or creates name collisions.
- Cover subprocess timeout/exception, unlink failure, and concurrent preview replacement.

### Descriptor-only catalog consumption

For private one-time catalogs, prefer opening the fixed final component once with `O_NOFOLLOW | O_CLOEXEC`, validating the open object with `fstat` (regular file, exact mode, positive bounded size), performing a bounded descriptor read, and consuming that exact inode with descriptor operations. Do not rename, replace, unlink, or restore the catalog pathname after open: a concurrent canonical replacement is a distinct newer request and must survive unchanged. Keep the shared ledger/event lock held before opening the catalog or taking a live snapshot so catalog validation, snapshot acceptance, ledger replacement, and event reconciliation are serialized. A successful unchanged request may leave an exact-mode zero-byte marker; retries must reject zero length. Ensure every success and exception path closes the descriptor. For ledger writes, use unpredictable same-directory temporaries created by `mkstemp`, set exact mode before writing, fsync the file, atomically replace, then fsync the directory.

Do not infer failure retention merely because validation failures preserve the source. Fault-inject every destructive descriptor step separately. In particular, `ftruncate(fd, 0); fsync(fd)` can raise from `fsync` after the inode is already empty, causing the public operation to report failure despite irreversible consumption and possibly after the ledger commit. This is a concrete blocker whenever the contract says ordinary failures retain the original request. Add a deterministic probe that makes `fsync` fail after a real successful truncate and asserts both the reported outcome and catalog bytes. Either narrow the documented guarantee explicitly or redesign the acceptance protocol so reported failure cannot imply retained input.

## Argv safety

- Require `shell=False`, fixed executable/flags, and an outer `--` separator where supported.
- Validate values for the parser that ultimately consumes them. An argv recorder proves transport, not interpretation by the real CLI.
- Probe option-shaped IDs, spaces, Unicode, controls, and shell metacharacters. Leading-dash values may cause parser confusion even without shell injection.

## Realistic tests

- Mutation before loading does not prove post-confirmation revalidation.
- Closing a pane does not prove changed-but-still-valid rebinding is rejected.
- Appending a contradictory duplicate does not prove whole-target drift is rejected.
- A successful multi-profile matrix does not test partial launch or retry behavior.
- When stateful execution is prohibited, use pure in-memory probes and clearly separate observed execution from source-derived conclusions.

## Evidence-boundary pitfall

A branch may advance while review is in progress. Keep all conclusions anchored to the user-specified commit range, refresh status/log only to detect drift, and exclude later commits rather than silently changing the audit target.
