# Ephemeral CLI/operator enrollment

Use this reference when a local Unix-socket broker must authorize standalone human CLI reads and mutations using exact process identity, without same-UID trust or reusable worker-readable bootstrap secrets.

## Detect the false-operability pattern

A CLI is not publicly operable when:

- the daemon requires a pre-seeded human/operator principal bound to PID/start time;
- tests seed the test runner and call the client from that same process or a thread;
- authorization compares UID/PID but ignores the `SO_PEERCRED` process start time;
- runtime startup checks start time once, but request authorization later drops it;
- approval records bind only UID/profile, allowing a challenge to outlive a process rebinding;
- the package CLI has no broker-backed operator verbs or can fall back to native database access.

Require a separately executed CLI subprocess as public proof.

## Smallest fail-closed contract

Keep enrollment off the public request protocol. Prefer a broker-private control socket available only to a dedicated registrar OS identity:

1. the registrar authenticates the human and spawns the installed CLI as a direct child behind a one-byte gate;
2. the registrar sends only the child PID over the private channel—principal, profile, UID, and start time come from fixed broker configuration or kernel inspection;
3. the broker validates registrar `SO_PEERCRED`, opens and holds a pidfd, derives child UID/parent/start time, requires the direct-child relationship and a live target, then atomically binds the configured operator principal;
4. the registrar releases the gate only after durable broker acknowledgement;
5. the CLI exec retains the bound PID/start tuple and every public request is authorized from its own `SO_PEERCRED` tuple.

Do not add a generic public `operator.enroll` operation. Do not use an enrollment bearer token in argv, environment, a file, or worker-readable storage.

### Ambient-registrar bypass

A private socket plus `SO_PEERCRED`, direct parenthood, child UID, pidfd liveness, and PID/start binding still does **not** prove that the child is the confirmation CLI. Any code running as the accepted registrar UID can spawn its own direct child, enroll it, and have that child speak `approval.preview` and execution frames directly, bypassing the intended confirmation layer. A generic gated launcher that accepts caller-selected absolute executables makes this bypass explicit; pathname `is_file`/`access` checks followed by later `exec` also introduce an executable-swap TOCTOU.

Treat confirmation as a security control only when enrollment authority is not ambient to ordinary processes. Prefer a dedicated registrar identity that alone authenticates the human and spawns one fixed, administrator-owned executable from an already-open verified FD, or have a privileged socket-activated component supply the fixed child/connection. Do not attempt to repair this solely by inspecting `/proc/<pid>/cmdline` or an executable pathname after spawn.

Audit control-socket ownership together with the UID model. A daemon-owned `0600` control socket is unusable by a distinct registrar UID; setting registrar UID equal to daemon UID restores liveness by collapsing the boundary and granting every daemon-UID process enrollment authority. A daemon-created `0660` socket is not sufficient either: unless the socket is explicitly chowned, ACLed, or socket-activated, its group is the daemon's effective GID rather than a separately configured registrar GID. Require an explicit socket-activation/ownership/ACL design and tests under genuinely distinct UIDs.

At daemon startup, require the configured operator principal's exact kind/profile/UID to match enrollment configuration; checking only that the persisted UID is an integer allows a stale differently owned binding to remain authorized despite the new configuration. Resolve the daemon service UID/GID too and enforce that broker, registrar, operator, launcher, and worker boundaries do not collapse. Trace every descendant `Popen`: a service unit with one `User=` plus worker subprocesses that omit `user=`, `group=`, and supplementary-group clearing gives workers the broker's database/key authority even when operator enrollment itself drops credentials correctly.

For the smallest slice, use one stable configured operator principal and one active process binding. Persist PID, start time, binding generation, and expiry. Deny replacement while the exact prior process is live; permit replacement only after exact stale-process verification; fail closed on ambiguous pidfd or `/proc` state. Implement liveness as a three-way result (`live`, `definitively dead`, `unknown`), not a boolean that maps every `pidfd_open`/`proc` error to dead. `EMFILE`, `ENFILE`, permission changes, parse failures, unsupported pidfds, and transient inspection errors must preserve the incumbent binding. Treat `ESRCH`, a pidfd's definitive exit-readiness, or an inspected PID with a different start time as death; unexpected poll flags remain unknown. Session expiry denies authorization but is not death evidence: an expired operator process that is still live must continue blocking replacement. Keep generic human-session expiry renewal separate from operator replacement semantics.

Enrollment-time GID/group validation is not sufficient when the gated process later calls `exec`. PID and start time survive exec while effective GID, supplementary groups, set-ID state, and file capabilities can change. Bind the expected effective GID and canonical supplementary-group set and verify them from each request's `SO_PEERCRED` plus current process identity, or execute only an already-open administrator-owned non-set-ID/non-capability image under a contract that makes credential changes impossible. A principal table and authorization path that persist/check only UID/PID/start silently discard the very GID/group invariant enrollment claimed to establish.

When adding posture to an existing schema, keep generic human sessions nullable and operator posture mandatory. A coherent migration adds principal binding GID/groups plus matching approval-challenge fields, invalidates legacy operator bindings by clearing them and incrementing binding generation, and leaves generic-human rows untouched. Bind operator and generic-human sessions through distinct APIs or SQL branches so the generic expiry shortcut cannot overwrite a live operator. Include GID/groups in the trusted context proof and delegated approval identity. In SQLite reservation predicates use `IS` rather than `=` for nullable posture fields, otherwise preserved generic-human challenges fail because `NULL = NULL` is not true. Canonicalize supplementary groups as set semantics before persistence and comparison.

At production runtime, the configured operator slot must resolve to exactly `kind == operator`, the configured UID, and the configured profile; accepting any integer UID or generic `human` kind permits stale principal ownership. An unbound exact operator may still allow daemon startup, but a partially bound or legacy posture-less operator must fail closed until re-enrolled.

## Human context and approval binding

Exact operator authorization must compare all of:

- principal kind/profile and configured UID;
- peer UID, PID, and non-null start time;
- persisted PID/start tuple;
- current binding generation and expiry.

Include start time and binding generation in any keyed context proof. Caller actor JSON is descriptive only.

Bind approval challenges to principal ID, UID, profile, PID, start time, and binding generation in addition to request fingerprint and policy version. The short-lived plaintext approval may remain in the CLI process between preview and execution, but must be one-time, exact-request-bound, absent from argv/environment/disk/logs, and unusable from a different peer tuple.

Preview, terminal confirmation, and execution should remain in the same CLI process. Parse and normalize the mutation once, mint its final request ID once, send that exact proposal through `approval.preview`, render the returned request without exposing the token, and—after confirmation—execute the exact returned request object without rebuilding or reparsing it. A fresh Unix-socket connection is acceptable only while the same process retains the enrolled PID/start/generation tuple. Keep the token in memory only.

Require a foreground controlling TTY for mutations when the contract calls for interactive posture, not merely readable stdin: reject piped input and unattended `--yes` modes before preview. However, do not describe `isatty` + foreground process-group checks as proof of human presence. A program can create a session, claim a controlling PTY, make the child foreground, and write the confirmation token through the PTY master. Treat the check as anti-accidental-automation/UX friction unless a separate authenticated-human mechanism exists. Reads may remain non-interactive. Decline, EOF, broker denial, malformed response, disconnect, expiry, or timeout must produce no native fallback and no authority mutation.

### Native-parser mapping discipline

A pinned parser snapshot is syntax evidence, not an operator compatibility shim. Build an independent path-and-flag ledger in which every nested route and alias is either mapped to one or more broker operations or explicitly excluded. Record semantic subsets per flag: a route can be broker-backed yet fail native parity when the native handler also recomputes state, writes workspace/config metadata, appends comments, loops over multiple targets, spawns processes, or removes files. Reject unsupported flags before contacting the broker.

Do not implement multi-target native loops as repeated approved calls unless partial commit is an explicit accepted contract; prefer exclusion until a bounded batch operation exists. Static no-fallback checks should forbid imports of native database modules, SQLite, direct SQL, and native adapters in the operator package. Real-process tests should prove that a missing socket, post-preview disconnect, denial, and malformed response leave authoritative state unchanged and do not create a native runtime home/database.

Before adding another long-lived human consumer such as a dashboard, inspect principal selection in request authorization. A runtime with one fixed human-principal ID cannot safely serve a short-lived operator CLI and a separately bound dashboard process concurrently; same-process fixtures hide this conflict. Require peer-derived selection among separately scoped principals or a dedicated read-only service-principal path before claiming both consumers are operable.

## Generic operation/arguments CLIs

Treat a generic `--operation NAME --arguments JSON` surface as a low-level broker RPC, not automatically as a native CLI compatibility shim.

Audit four separate equations:

1. every human-eligible immutable-ledger operation is exposed or explicitly excluded;
2. every broker-only human control read is exposed or explicitly excluded outside the native ledger;
3. every pinned native parser path, alias, and flag has an argument transform, result projection, or explicit semantic exclusion;
4. every exposed operation has enforced public JSON argument, result, error, and ambiguous-result/retry contracts.

A parser snapshot plus a native-callable ledger does not establish equation 3. Require a separate immutable operator compatibility artifact containing the pinned parser digest, paths, aliases, flags, operation mapping, semantic subset, output projection, retry behavior, and exclusion rationale. Multi-target loops, workspace/config pointer writes, comment-appending commands, process launchers, stream/watch commands, and filesystem cleanup frequently require explicit exclusions or dedicated bounded operations.

Do not treat ledger metadata as enforced merely because fields such as `result_shape`, `user_error_class`, or `retry_class` are populated. Trace their production consumers. A generic JSON conversion that accepts any serializable value—or silently converts native tuples to lists—needs a separate public result validator and matching ledger vocabulary. Test actual broker JSON, not only native Python values.

Required-field validation must reject a present JSON `null` when the operation requires non-null text, integers, selectors, or enums. Test missing, null, wrong-type, unknown, oversized, and secret-bearing values for every operation, and prove rejection occurs before preview or reservation.

Perform mutation interactivity checks before contacting `approval.preview`. `stdin.isatty()` alone does not prove a controlling terminal: a parent can call `pty.openpty()`, pass the slave as stdin, and programmatically write the confirmation through the master without creating a controlling foreground terminal. Real-process tests must distinguish a genuine controlling foreground TTY from this automatable pseudo-TTY case. Malformed JSON and unsupported operations should likewise fail before enrollment or broker contact where practical.

For ambiguous mutation results, preserve the exact request in the same process and define behavior from the immutable retry class. A fresh random request ID on every invocation makes exact journal recovery inaccessible after a post-commit disconnect. Tests must cover safely retryable, idempotency-keyed, CAS-guarded, and non-retryable classes without rebuilding the approved request.

Minimum compatibility proofs include exhaustive parser mapping/exclusion, human-ledger plus declared control-operation coverage, actual public result-shape checks, controlling-TTY preflight, no-fallback failure matrices, same-request recovery, static native-import prohibitions, and approval secrecy across process and persistence surfaces.

## Cross-artifact operability checks

Do not accept individually plausible registrar, daemon, and installer components without proving their identity transitions compose:

- If the registrar launches the operator child with `Popen(user=..., group=...)` or equivalent, require a production mechanism that actually grants the registrar `setuid`/`setgid` authority. A distinct ordinary registrar UID cannot switch to the operator UID merely because both IDs appear in config.
- Inventory the authenticated bundle exactly. A daemon unit, tmpfiles fragment, and config do not establish an authenticated human-to-registrar invocation path; require the matching PAM/polkit/sudoers/socket-activation artifact or classify production operator operability as missing.
- Resolve the service account to numeric UID/GID and reject collisions with registrar, operator, launcher, and worker identities. String `User=`/`Group=` fields plus registrar-versus-operator checks leave boundary collapse possible.
- A real-process test that assigns registrar and operator to the same test UID/GID proves only local mechanics. Production acceptance requires a privileged distinct-identity test covering the actual credential transition and cross-identity denial.
- Treat a programmatically driven controlling PTY as confirmation-UI coverage, not authenticated-human proof; foreground-TTY checks remain automation friction.

Migration acceptance must test usability, not only row preservation. When new posture columns are nullable for legacy generic-human rows, prove that a migrated active session and pending challenge still authorize and reserve as intended; SQL comparisons involving preserved nullable fields need null-safe semantics. Conversely, malformed partially populated operator bindings must be rejected at startup rather than allowed to create a service that can never authorize a request.

Mutation TTY/foreground checks belong before `approval.preview`. A test that merely verifies no authority mutation after cancellation can miss persistent pending challenges and audit events created by preview; assert zero broker-side state change for noninteractive preflight rejection.

## Local versus privileged acceptance

Classify separately:

- **Locally implementable:** schema/CAS logic, exact authorization, approval binding, unbound startup, private registrar protocol, gated real subprocesses, same-UID sibling denial, no-native-fallback CLI mapping, connection deadlines, and inert installer rendering.
- **Locally emulatable but not security proof:** registrar UID allowlisting and filesystem mode assertions under one development UID.
- **Privileged rollout only:** distinct broker/registrar/launcher/worker identities, control-socket ACLs, database/key denial, ptrace and `/proc` isolation, PAM/polkit/systemd authentication, service ordering, live install, restart, rollback, and cutover.

A `0600` database or digest key does not isolate workers sharing the broker UID. A service unit that launches broker and workers under one `User=` cannot satisfy the privileged security claim.

## Required tests

Use real Unix sockets, pidfds, gates, subprocesses, and temporary databases:

- daemon starts unbound and denies all human operations;
- trusted registrar enrolls a gated, separately executed CLI;
- wrong registrar, non-child, exited child, PID reuse, missing start time, and ambiguous process state fail closed;
- live binding blocks replacement; verified dead binding renews; concurrent enrollment has one CAS winner;
- a same-UID sibling worker cannot use the operator binding;
- approval is bound to principal/PID/start/generation and fails from a sibling, after rebinding, and after expiry;
- approval remains one-time and exact-fingerprint-bound;
- real CLI reads and mutations use the broker with no native fallback;
- CLI decline performs no mutation;
- argv, environment, inherited descriptors, logs, and databases expose no enrollment secret or plaintext approval;
- every pinned native CLI parser path maps to broker behavior or an explicit exclusion;
- partial, slow, reset, and oversized clients cannot block unrelated requests;
- shutdown/restart leaves no authorized stale binding or orphaned CLI.

Privileged acceptance must additionally prove distinct service UIDs, worker denial of the control socket/databases/key/operator process, authenticated operator invocation, full installed end-to-end behavior, and rollback.
