# One-time private file consumption

Use this pattern when a plugin consumes approval catalogs, restore mappings, identity seeds, or other private one-shot files while updating durable state.

## Threat model

A path chain such as `is_file()` → `stat()` → `read_text()` → state write → `unlink()` is unsafe: every operation resolves the path again, symlinks may be followed, and a replacement can be deleted or overwritten. A random claim pathname does not solve this class: `rename()` can overwrite a pre-existing destination, and `same_inode(path)` followed by `unlink()` or `rename()` remains a source-rebinding race. Writing a temporary before mode `0600` can expose private data transiently.

## Preferred descriptor-only transaction

1. Acquire the same exclusive lock used by seed consumers, event reconciliation, and snapshot reconciliation **before** opening the catalog or capturing live state. Hold it through validation, durable-state commit, and consumption.
2. Resolve only a fixed filename beneath an approved absolute config root.
3. Open once with `O_RDWR | O_CLOEXEC | O_NOFOLLOW`. `O_RDONLY` is insufficient for descriptor-bound `ftruncate` consumption.
4. Validate with `fstat()`:
   - regular file;
   - exact `stat.S_IMODE(mode) == 0o600`, including rejection of special bits;
   - non-empty bounded size.
5. Read only through that descriptor with an explicit byte ceiling, and keep it open through the transaction.
6. Do **not** rename, link, unlink, replace, or otherwise mutate any catalog pathname after open. The shared lock serializes cooperating plugin paths; the retained descriptor binds the transaction to the validated inode even if another same-user process atomically replaces the canonical entry.
7. Validate live identity and conflicts while the lock and descriptor remain held.
8. Write durable state through random `mkstemp`/`O_CREAT|O_EXCL` storage that is mode `0600` before private bytes are written. Flush and `fsync()` the file, atomically replace the ledger, then `fsync()` its directory. Clean temporaries and close descriptors on failures.
9. Retain the exact original byte payload in memory through the destructive boundary. After the durable commit, consume only the open validated inode with `ftruncate(fd, 0)` plus `fsync(fd)`. If `ftruncate` succeeds but `fsync` fails, restore the exact bytes through the same descriptor (seek, partial-write loop, original-length truncate, durable sync), then re-raise the original consume error. If restoration itself fails, raise one fixed fail-closed restoration error. This keeps a reported consume failure from silently destroying the retry input; the already-committed ledger update must therefore be idempotent on retry.
10. If consumption succeeds and the canonical path is unchanged, it becomes an exact-`0600`, zero-byte consumed marker and is rejected on retry. If the canonical path was atomically replaced, the replacement remains untouched as a new request.
11. On validation or state-write failure, close the descriptor without pathname mutation. In the ordinary case the original catalog remains intact. If an external same-user actor replaced or removed the path concurrently, preserve that actor's result rather than attempting a racy pathname “restoration.”

This descriptor-only design is simpler and stronger than random claim names plus `renameat2`/`linkat`: there is no destination to overwrite, no source pathname to rebind, and no check-then-mutate cleanup race. On platforms lacking required no-follow/open-descriptor semantics, fail closed rather than falling back to repeated pathname resolution.

## Deterministic TDD matrix

Witness RED for each missing behavior before implementation:

- Hold the real shared `flock`, start reconciliation in a worker, and assert its snapshot barrier is not reached until lock release.
- Reject `0700`, `0400`, group/other-readable modes, special bits, zero-byte inputs, oversized inputs, and symlinks; accept exact `0600`.
- After opening, atomically replace the canonical file with a new inode; consume and prove the replacement survives unchanged.
- Consume an unchanged catalog and prove the canonical entry is zero bytes, remains exact `0600`, and is rejected on retry.
- Inject a post-`ftruncate` `fsync` failure and prove the original byte-for-byte payload and mode are restored through the same descriptor, the original error propagates, and the descriptor closes. Also inject restoration failure and require one fixed fail-closed error rather than a misleading success.
- Raise inside the descriptor scope before commit and prove the original catalog remains unchanged.
- Prove no random claim/link/quarantine entries are created.
- Plant a predictable stale ledger-temp symlink to an unrelated victim and prove the victim is unchanged.
- Verify seed, event, and snapshot paths share lock-before-live-state ordering.
- Reject invalid official identity source/agent/kind, stale terminal/session, duplicate pane/terminal, and cross-profile ambiguity.
- Prove success and every failure output omit configured session IDs and secrets.

Use real filesystem objects and the real local service where practical. For otherwise unobservable lock interleavings, use a narrow deterministic barrier rather than probabilistic timing.

## Verification gates

1. Focused RED→GREEN for every race and filesystem boundary.
2. Full real suite, structure/construct limits, compilation, and diff checks from a quiescent tree.
3. Independent read-only security review of the exact final diff before commit/install.
4. If no canonical command is detectable, create an OS-safe verifier using `tempfile.NamedTemporaryFile(prefix="hermes-verify-", suffix=".py", dir="/tmp", delete=False)`, execute focused real checks, remove it, and report **ad-hoc verification**, never suite green.
