# Descriptor-Bound Private File Consumption

Use this pattern when a privileged or identity-bearing configuration file must be consumed exactly once while resisting symlink, replacement, and check-then-mutate races.

## Threat model

Assume another process with access to the parent directory can replace any pathname between a check and a mutation. Random filenames reduce collision probability but do not make `stat(path); unlink(path)` or `stat(path); rename(path, ...)` exact. `rename()` may overwrite an existing destination, and `RENAME_NOREPLACE` protects only the destination—not a rebound source pathname.

## Safe descriptor-only pattern

1. Acquire the same serialization lock used by every reader/reconciler **before** reading the catalog or taking a live snapshot.
2. Open the fixed canonical path with `O_RDWR | O_CLOEXEC | O_NOFOLLOW`.
3. Validate with `fstat()` on the open descriptor:
   - regular file;
   - exact mode `0600` (reject `0700`, `0400`, and special bits);
   - nonzero bounded size;
   - valid owner when the contract requires it.
4. Read bounded bytes through the descriptor. Decode only after retaining the exact raw payload for recovery.
5. Validate all requested identities against a live snapshot while still holding the shared lock.
6. Commit the idempotent authority/ledger update with a private unpredictable temporary created as `0600` before any content is written; flush, `fsync`, atomically replace, and sync the parent directory.
7. Consume only the validated inode through its descriptor. `ftruncate(fd, 0)` leaves an unchanged canonical path as an exact-`0600` zero-byte consumed marker. A concurrently replaced canonical path remains untouched and becomes the next request.
8. Reject zero-byte markers on retry.

After opening, do not rename, replace, link, or unlink the catalog pathname. Path mutations reintroduce source-rebinding or destination-overwrite races.

## Failure retention

`ftruncate()` followed by `fsync()` has a destructive intermediate state. Keep the exact original bytes and recover through the same descriptor if either step fails:

1. seek to offset zero;
2. loop over `write()` until every byte is restored (short writes are valid);
3. truncate to the original exact length;
4. `fdatasync()` the restoration;
5. re-raise the original consumption failure;
6. if restoration itself fails, raise a fixed fail-closed restoration error.

This supports an idempotent retry when the ledger committed before catalog consumption: the retained catalog can be validated again, the ledger merge remains single-entry/idempotent, and a later successful consume completes the operation.

## Required tests

Witness RED before implementation for:

- exact-mode rejection and symlink rejection;
- lock-before-catalog and lock-before-live-snapshot ordering with a deterministic barrier;
- canonical replacement after open remains untouched;
- unchanged catalog becomes a zero-byte `0600` marker;
- zero-byte retry is rejected;
- validation/ledger failure retains the original bytes;
- `fsync` failure restores byte-identical payloads, including BOM, CRLF, multibyte UTF-8, and embedded NUL;
- deterministic short writes restore the complete payload;
- restoration failure returns the fixed fail-closed error;
- secure ledger temporary cannot be redirected through a predictable stale symlink.

## Test-observation pitfall

For asynchronous restore launchers, recorder output may appear before the control process returns and consumes its one-time target file. Do not weaken the eventual-consumption contract with an immediate assertion. Poll for bounded eventual removal and fail if the deadline expires; repeat the focused test to prove the race is closed rather than masked.
