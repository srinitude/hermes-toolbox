# Dual-socket daemon remediation designs

Use this reference when a foreground daemon owns a public Unix socket plus a more privileged private control/registrar socket and the request is for a read-only remediation design.

## Evidence boundary under concurrent parent work

Freeze both committed HEAD and the staged candidate separately. Record a staged patch hash and the index blob IDs for every relevant file, then inspect those immutable blobs rather than the live worktree. When the requester supplies an expected staged digest, reproduce it with the exact canonical command first (commonly `git diff --cached | sha256sum`): options such as `--full-index` change the patch bytes and therefore produce a different, non-comparable digest. Use the expected-command hash as the candidate identity and index blob IDs as the immutable inspection boundary.

Recheck the canonical patch hash, relevant index blob IDs, HEAD, and full status at the end. If the hash changes, compare the old and new blob IDs to identify exactly which paths drifted; do not imply the current index is still the audited candidate merely because cited source blobs stayed stable. If the parent continues editing, inspect new drift only to identify overlap and report it as excluded concurrent work rather than silently mixing it into the frozen verdict.

## Smallest lifecycle contract

Represent each listener with explicit supervision state: thread, readiness, exit, and captured exception. Startup waits for readiness **or failure**, not readiness alone. After readiness, the foreground loop treats an exception or unexpected normal thread return as fatal, stops the peer listener, and propagates the original cause. Set daemon readiness only after both listeners and any launcher are ready.

Shutdown ordering must guarantee server cleanup even when launcher termination fails:

```python
try:
    stop_launcher()
finally:
    stop_servers()
```

If both cleanup stages can fail, preserve both with an exception group rather than masking the first. Join all listener threads against one absolute deadline, not one full timeout per thread.

A practical real-behavior trigger for post-readiness supervision is namespace loss: listeners periodically verify that their pathname still names the inode created at bind time. Removing or replacing one pathname then produces a real listener failure, allowing a public daemon test to prove that the foreground process notices it and cleans the peer socket.

## Shared socket-path primitive

Do not duplicate bind/cleanup code across public and control servers. Use one helper that:

1. requires an absolute path and a pre-provisioned parent; never creates deployment directories;
2. opens the parent with `O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC` and retains the directory FD;
3. validates parent type, service ownership, expected client GID, and a fail-closed mode such as `0710`;
4. rejects and preserves every pre-existing pathname unless stale-socket recovery is explicitly in scope;
5. after bind, captures `(st_dev, st_ino, st_uid, type)`, assigns the requested GID, applies `0660`, and revalidates the same inode;
6. cleans up with no-follow stat plus unlink relative to the retained parent FD only when the identity still matches;
7. preserves missing, replaced, symlink, and non-socket paths.

Capture the inode immediately after bind so setup failures after bind can remove only the inode created by that attempt. Never perform broad pathname unlink in an exception handler.

## Group-separated inert bundle

For a service-owned public socket and private registrar socket:

- public socket GID = operator group;
- control socket GID = registrar group;
- parent directories are distinct, service-owned, group-specific, and non-writable by clients;
- the service unit supplies both target GIDs through `SupplementaryGroups=`;
- keep `CapabilityBoundingSet=` and `AmbientCapabilities=` empty when the service owns the sockets, because an owner may change a file group to one of its supplementary groups;
- do not grant broad `CAP_CHOWN` merely to avoid provisioning groups.

An inert install bundle should include and authenticate a tmpfiles/runtime-directory fragment describing exact parent owners, GIDs, and modes. It must not execute tmpfiles or install the fragment. Adding this artifact changes the exact authenticated file set, so bump the bundle-manifest version. Adding mandatory operator/registrar identity fields likewise warrants a daemon-config schema version bump instead of redefining an existing released schema.

## Real test inventory

Socket-path tests:

- missing parent is rejected without creation;
- symlink, wrong owner/GID, and writable modes are rejected;
- non-socket and symlink occupants are preserved;
- bind failure removes only the inode created by that attempt;
- shutdown preserves a replacement socket;
- parent rebinding cleanup operates on the original opened directory inode.

Daemon tests:

- each listener's startup failure propagates promptly;
- control startup failure stops and cleans the public listener;
- public and control namespace loss each terminate the foreground daemon and clean the peer;
- a real launcher-stop error still permits both real server sockets to be cleaned;
- two-listener shutdown uses one absolute deadline.

Installer/system tests:

- rendered unit has exactly the two supplementary groups and no capabilities;
- authenticated bundle includes the runtime-directory fragment;
- a root-capable isolated job proves exact distinct socket GIDs, parent metadata, and cross-group access denial with real processes. Do not weaken production ownership checks or add caller-controlled UID/GID overrides solely for unprivileged tests.

## Compatibility ledger

Call out these effects explicitly:

- making `socket_gid` mandatory breaks direct `serve()` callers and fixtures;
- pre-provisioned parent validation breaks tests and deployments that relied on automatic `mkdir()`;
- old daemon configs fail after a schema-version bump;
- old bundle verifiers reject the new authenticated file set and vice versa;
- full foreground tests need a service-group-capable fixture or a dedicated root/system job to exercise two genuinely distinct GIDs.
