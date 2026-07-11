# One-time private file consumption

Use this pattern when a plugin consumes approval catalogs, restore mappings, identity seeds, or other private one-shot files while updating durable state.

## Threat model

A path chain such as `is_file()` → `stat()` → `read_text()` → state write → `unlink()` is unsafe: every operation resolves the path again, symlinks may be followed, and a replacement can be deleted or overwritten. Even `same_inode(path)` followed by `unlink(path)` and `not exists(path)` followed by `replace(path)` remain TOCTOU races. Writing a temporary before mode `0600` can expose private data transiently.

## Required transaction order

1. Acquire the same exclusive lock used by seed consumers, event reconciliation, and snapshot reconciliation **before** reading the catalog or capturing live state. Hold it through validation, state commit, and consumption.
2. Resolve only a fixed filename beneath an approved absolute config root.
3. Open once with `O_RDWR | O_CLOEXEC | O_NOFOLLOW` when exact-descriptor consumption will use `ftruncate` (`O_RDONLY` is insufficient).
4. Validate with `fstat()`:
   - regular file;
   - exact `stat.S_IMODE(mode) == 0o600`, including rejection of special bits;
   - non-empty bounded size.
5. Read only through that descriptor with an explicit byte ceiling, and keep it open through the transaction.
6. Atomically move the directory entry to an unpredictable claim name while locked; verify its `(st_dev, st_ino)` matches the open descriptor. Restore unexpected moved entries only with an atomic no-replace primitive such as Linux `renameat2(RENAME_NOREPLACE)`.
7. Validate live identity and conflicts while the lock and descriptor remain held.
8. Write durable state through random `mkstemp`/`O_CREAT|O_EXCL` storage that is mode `0600` before private bytes are written. Flush and `fsync()` the file, atomically replace, then `fsync()` the directory. Clean temporaries and close descriptors on setup/write failures.
9. Consume the **open validated inode**, not a pathname. On Linux, `ftruncate(fd, 0)` plus `fsync(fd)` cannot delete or modify a replacement claim/canonical entry. An intentional zero-byte, random, exact-`0600` claim may remain; test and document that it contains no session or secret data.
10. On validation or state-write failure, restore the exact open inode atomically without replacement. On Linux, `linkat` through `/proc/self/fd/<fd>` with `AT_SYMLINK_FOLLOW` creates the canonical hard link while refusing an existing newer request. Preserve both entries rather than overwriting either.

These Linux primitives require a portability gate on other platforms; fail closed rather than falling back to check-then-mutate pathname logic.

## Deterministic TDD matrix

Witness RED for each missing behavior before implementation:

- Hold the real shared `flock`, start reconciliation in a worker, and assert its snapshot barrier is not reached until lock release.
- Reject `0700`, `0400`, group/other-readable modes, special bits, and symlinks; accept exact `0600`.
- Replace the random claim immediately before consumption and prove the replacement survives unchanged.
- Create a newer canonical request immediately before restoration and prove it is not overwritten. A deterministic monkeypatch may force the old existence check false to reproduce the race; the fixed atomic primitive must remain correct.
- Raise inside the claim scope and prove the exact original catalog is restored.
- Plant a predictable stale-temp symlink to an unrelated victim and prove the victim is unchanged.
- Verify concurrent seed/event/snapshot paths share the same lock ordering.
- Reject invalid official identity source/agent/kind, stale terminal/session, duplicate pane/terminal, and cross-profile ambiguity.
- Prove success and every failure output omit configured session IDs and secrets.
- Prove successful consumption leaves only the documented zero-byte exact-`0600` claim and no sensitive content.

Use real filesystem objects and the real local service where practical. For otherwise unobservable interleavings, use narrow barriers/monkeypatches to force the race rather than relying on probabilistic timing.

## Verification gates

1. Focused RED→GREEN for every race.
2. Full real suite, structure/construct limits, compilation, and diff checks from a quiescent tree.
3. Independent read-only security review of the exact final diff before commit/install.
4. If no canonical command is detectable, create an OS-safe verifier using `tempfile.NamedTemporaryFile(prefix="hermes-verify-", suffix=".py", dir="/tmp", delete=False)`, execute focused real checks, remove it, and report **ad-hoc verification**, never suite green.
