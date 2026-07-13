# Dashboard Consumer Posture Audits

Use this when a rollout claims that a native dashboard can remain readable while its direct authority mutations are disabled.

## Evidence layers

Keep these separate:

1. **Native dashboard route inventory** — enumerate every GET, WebSocket, POST, PUT, PATCH, and DELETE route at the pinned consumer revision. A threat-model statement or hidden UI control does not disable backend mutations.
2. **Disable mechanism** — prove how the bundled dashboard backend is excluded at discovery, mount, and request time. A replacement tab that merely covers the same UI path does not disable the old API.
3. **Replacement read path** — trace each replacement GET through a production request factory, transport client, authenticated broker principal, broker read dispatch, and native result normalization.
4. **Process identity and socket access** — verify the real dashboard process, not an in-process fixture, can authenticate and connect. PID-bound human identity can make same-process tests pass while a production dashboard subprocess is denied.
5. **Rollout action** — distinguish repository-local plugin/bundle/test artifacts from live plugin installation, enable/disable config, service identities/groups, socket ownership, restarts, database fencing, and rollback.

## Smallest credible local proof

Prefer an inert, repository-local read-only replacement plugin under a distinct name with a dashboard route override. Pair it with one real-process integration test that:

- starts a real broker Unix socket and temporary authoritative board;
- starts the dashboard bridge as a distinct enrolled read-only principal;
- enables the replacement and disables the bundled native dashboard in a temporary consumer home;
- proves a replacement GET returns broker-sourced seeded data;
- proves native mutation paths are unavailable and replacement non-GET methods are rejected;
- verifies authoritative state is unchanged;
- statically forbids direct native database imports, authored SQL, and native fallback in the replacement.

Use a distinct replacement plugin name when the host's disabled-plugin set is keyed by plugin name; disabling `kanban` while shadowing it with another user plugin also named `kanban` may disable both.

Audit disable gates by transport, not only by URL prefix. HTTP middleware does not automatically gate already-mounted WebSocket routes. If runtime disablement only intercepts HTTP, require the bundled plugin to be disabled before process startup and verify a restart leaves no stale WebSocket route; otherwise add and test an explicit WebSocket gate. Distinguish “all mutation HTTP routes return 404/405” from “the native plugin is fully unmounted.”

Before designing the replacement, compare every native GET response shape with existing broker reads. A task list/read operation does not imply comments, events, graph links, attachment reads, current-board metadata, assignee rosters, run-by-ID inspection, configuration, or event streaming. Mark missing reads as explicit fidelity gaps rather than filling them through direct native access.

Inspect broker principal selection as part of dashboard operability. A daemon that authorizes every human request against one fixed principal cannot concurrently bind a short-lived operator CLI and a long-lived dashboard process. The smallest credible dashboard path needs a separately scoped read-only principal selected from kernel peer identity, or another dedicated service-principal mechanism; seeding the operator PID into an in-process dashboard test is not acceptance.

## Common false positives

- **In-process dashboard test:** shares the operator PID and passes PID-bound authorization that production cannot satisfy.
- **Transport-only proof:** a client library and read ledger exist, but no dashboard request constructor or production callsite uses them.
- **UI-only read-only mode:** buttons are hidden while POST/PATCH/DELETE backend routes remain mounted.
- **Plugin shadowing only:** a replacement tab wins visually, but the bundled API remains reachable.
- **Socket mode only:** `0660` is asserted without proving the dashboard identity has the socket's effective group/access.
- **Installer-name inflation:** a renderer that emits a service unit/config/manifest is an inert staging bundle, not an installer, deployed consumer, or cutover.
- **Logical-read overclaim:** native connection helpers may initialize or migrate a database before a read callback; describe this honestly and keep the broker as the only process allowed to invoke that path after cutover.

## Read-only audit technique

For large pinned dashboard modules, use a read-only AST inventory to count and list route decorators by method and path. Compare that inventory with the broker read-operation ledger and production client callsites. Do not run tests when the requested evidence boundary forbids them; label source tests as present but unexecuted.
