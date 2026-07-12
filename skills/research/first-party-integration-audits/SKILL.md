---
name: first-party-integration-audits
description: "Use when auditing whether two tools, agents, plugins, or protocols integrate, especially when the user restricts evidence to first-party documentation and official repositories. Produces a release-pinned, read-only compatibility and trust assessment that separates public contract, stable implementation, source-only internals, preview behavior, and unsupported speculation."
version: 0.2.12
author: Kiren Srinivasan
license: Apache-2.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [research, integrations, first-party, compatibility, security, source-audit]
    related_skills: [codebase-inspection, hermes-config-audits]
---

# First-Party Integration Audits

## Overview

Use this skill to answer questions such as:

- Does product A already integrate with product B?
- Which lifecycle, manifest, plugin, protocol, and environment surfaces are stable?
- What does installation modify?
- Which behavior is documented, merely present in source, preview-only, or absent?
- What trust boundary does the integration create?

The core discipline is **contract before implementation**. Start with first-party public documentation, pin implementation claims to an immutable release, then inspect the smallest set of official source files needed to verify exact behavior. Do not convert an implementation detail into a public promise without labeling it.

## When to Use

Use when the request includes any of:

- first-party-only or official-sources-only research
- compatibility or integration readiness audits
- agent lifecycle, plugin, hook, manifest, socket, or environment discovery
- security/trust analysis of an integration
- documented-versus-speculative classification
- read-only repository inspection with no install or execution

Do not use this as a substitute for actually testing an integration when the user asks for installation, execution, or behavioral verification. This skill is for evidence audits; runtime tests are a separate phase.

## Evidence Classes

Assign every material claim one of these classes:

| Class | Meaning | Evidence |
|---|---|---|
| **Documented stable** | Publicly supported contract | Live official docs plus a stable release when implementation detail matters |
| **Stable source-confirmed** | Present in an immutable release but not clearly public API | Release-tagged source, schema, or tests |
| **Preview / experimental** | Explicitly labeled beta, preview, early, or v1-limited | Official docs or release notes |
| **Unreleased** | Present only on a moving branch or unreleased commit | Official default branch or comparison after the latest release |
| **Unsupported / not evidenced** | Official material explicitly excludes it, or the inspected first-party corpus provides no support | Cite the exclusion; phrase absence narrowly |
| **Speculative** | Plausible design with no first-party evidence | Keep out of findings or label as a proposal, never as current behavior |

Prefer “not evidenced in the inspected first-party sources” over absolute claims such as “does not exist” unless the docs or source explicitly reject the capability.

## Workflow

### 1. Freeze scope and source policy

Record:

- Allowed domains and repository owners.
- Whether official raw GitHub, GitHub API, releases, issues, and discussions are allowed.
- Read-only constraints: no clone, install, config mutation, or file creation.
- Requested surfaces: lifecycle, manifests, plugins, protocol, environment, trust, existing integration.

**Completion criterion:** every source used can be traced to an allowed first-party origin, and the action plan contains no prohibited mutation.

### 2. Establish the stability baseline

Find the latest stable release and its immutable tag. Use live docs for the current public contract and the release tag for implementation claims. For GitHub repositories, verify `releases/latest`, record `prerelease`/`draft`, then dereference lightweight or annotated tag objects to the immutable commit SHA. Record signature verification separately from release stability; a stable release may still have an unsigned tag.

Preferred source order:

1. Official documentation pages.
2. Official release page and tagged source.
3. Official generated schema or protocol reference.
4. Official default branch for explicitly unreleased observations.
5. Official issues/discussions only for known limitations or maintainer intent, not as proof of shipped behavior.

Avoid using a moving branch as the primary baseline. If branch content differs from the release, report the release as stable and the branch as unreleased.

When the user explicitly asks for current default-branch code rather than the latest release, resolve the branch SHA twice: once before inspection and once immediately before synthesis. If it moved, pin the final SHA, re-scan every file used for consequential claims, and label it a branch snapshot rather than a stable release. Fast-moving repositories can advance enough during one audit to invalidate line anchors and generated-name claims.

**Completion criterion:** the report names an immutable release/tag, or clearly labels an immutable branch snapshot and explains why no release baseline was used.

### 3. Map the first-party corpus before deep reading

Use the official docs index, sitemap, `llms.txt`, navigation, repository tree, or GitHub contents API to locate relevant pages and files. Search by concept and exact identifiers:

- lifecycle verbs: start, stop, attach, wait, resume, restore
- detection: manifest, alias, process, screen, authority, precedence
- plugins: manifest, action, event, pane, link handler, runtime
- protocol: schema, request, method, socket, pipe, subscription
- environment: product prefix, config path, socket path, pane/session IDs
- trust: sandbox, permissions, confirmation, signature, review, marketplace
- integration-specific names, paths, hook names, and source labels

Do not treat search snippets as evidence. Open the source page or file.

**Completion criterion:** each requested audit surface has at least one primary source or is marked “not evidenced.”

### 4. Inspect by layer

#### Public lifecycle layer

Capture exact commands, argument forms, state values, and convenience-versus-raw distinctions. Explicitly identify missing lifecycle verbs rather than assuming start implies stop or restart.

Check whether `wait`, `attach`, `resume`, or `status` are raw protocol methods or higher-level CLI helpers.

#### Detection and manifest layer

Record:

- How the process/agent is recognized.
- Aliases and explicit hints.
- Screen or output regions used.
- State authority precedence.
- Manifest fields, states, matchers, and parser limits.
- Local, remote, and bundled precedence.
- Whether remote data can add identities or only update rules.
- Reload/update behavior and restart requirements.

#### Built-in integration layer

Trace:

- Installation and uninstall commands.
- Files/directories created or removed.
- Configuration keys edited.
- Hook-to-state mapping.
- Transport and timeouts.
- Failure behavior.
- Session identity and restore command.
- OS support and profile/home-directory assumptions.
- Integration version versus package/plugin manifest version.

Keep distinct plugin systems separate. A host application's plugin manifest may not be the same thing as the audited product's plugin package format.

#### Extension/plugin layer

Capture exact manifest fields and all declared surfaces:

- package metadata and version constraints
- builds
- actions and contexts
- event hooks
- pane/UI entrypoints
- URL/link handlers
- platform filters
- runtime context and environment
- install/link/update/uninstall behavior
- persistence and logging

List supported event names from an authoritative schema or constant when docs are incomplete. Separate subscribable events from plugin-hook events; they are often not identical.

#### Protocol layer

Capture:

- transport and framing
- endpoint/path resolution
- authentication or absence of a documented handshake
- permissions/ACL behavior
- schema discovery
- raw methods by area
- subscriptions and one-shot waits
- methods that are source-visible but omitted from public docs
- protocol versioning and compatibility guidance

Do not assume one product has only one protocol. Inventory each layer separately: public automation API, full client/server rendering protocol, direct-terminal bridge format, remote tunnel/stdio bridge, and CLI convenience wrappers. For every layer, state whether it is documented public contract or stable source-only implementation, and preserve distinct framing, envelopes, version negotiation, socket paths, and ownership semantics.

#### Environment layer

Group variables by role:

1. Public runtime/config variables.
2. Managed child-process identity variables.
3. Plugin action/event/pane variables.
4. Integration-target home/config overrides.
5. Source-only or internal testing overrides.

Also identify a meaningful missing override, such as a hard-coded home directory, when stable source confirms the limitation.

#### Trust layer

Check:

- sandboxing versus ordinary user code
- source review and install confirmation
- revision pinning
- marketplace vetting
- build command execution
- socket reachability and per-method authorization
- file permissions
- remote manifest signing/checksum behavior
- secret-bearing terminal history or logs
- rollback/uninstall scope

Distinguish classification data from executable code. A remote detection manifest can still affect status and automation, but it is a different risk from an unsandboxed plugin command.

### 5. Cross-check claims

For every consequential claim, ask:

- Is it in public docs?
- Is it present in the pinned release?
- Does the schema agree with the prose?
- Is this a convenience wrapper rather than a raw method?
- Is it platform-specific?
- Is the version named a minimum compatible version or the currently bundled version?
- Does “plugin” refer to the host product or the integrated product?

Prefer immutable raw/tag URLs. GitHub branch and query-parameter views can drift or be cached; verify that retrieved content matches the requested tag before using it as stable evidence.

When official prose and tagged implementation disagree, record **two independent axes** instead of silently choosing a winner:

1. **Support contract** — what the release-tagged public docs promise.
2. **Observed release behavior** — what tagged source/schema/tests implement.

Name the discrepancy, cite both, and design the integration to feature-detect, authenticate, or use a more stable primitive. Source can establish actual behavior in that release, but it does not retroactively make an undocumented method a supported external API. Conversely, public prose does not justify claiming runtime behavior that the same release's implementation contradicts.

**Completion criterion:** no material conclusion rests only on a search result, moving branch, inferred naming convention, or an unresolved docs/source contradiction.

#### Implementation-plan contract checks

When the input is a saved plan or proposed plugin, audit both the architecture and its concrete sample code:

- Compare the installed live version with the latest stable tag; keep carried commits, dirty trees, stable releases, and `main` distinct.
- For high-churn source files, locate consequential functions/classes/schema assignments structurally, hash their exact UTF-8 source segments, and compare those fingerprints across the stable tag, local checkout, and final default-branch snapshot. This avoids both false holds from unrelated file growth and false confidence from line anchors that merely shifted. Record the hashing algorithm in the compatibility ledger.
- Prefer state-safe live probes such as nested `--help` and signature introspection when runtime databases/configuration are out of scope.
- For a read-only control plugin, inventory **identity, status, and content reads separately**. Determine whether identity is a real method, a context/environment hint, a `current` helper, or a field returned by `get`/`snapshot`; determine whether CLI status is a raw method or a composite wrapper (for example, local build data plus `ping`). When necessary, probe a plausible nonexistent identity/status method read-only so the report does not invent one.
- Cross-check live nested help, tagged parser code, generated schema, and public prose. Help can omit a parser-supported enum or option; preserve CLI spelling separately from raw JSON spelling (for example, hyphenated CLI values versus underscored wire enums).
- Inspect exact registration signatures and manifest parsing. Unknown manifest fields may be inert, while permissive fake contexts can hide wrong argument types or paths.
- For tool overrides, inspect both the public plugin-context gate and the final registry sink, including the exact duplicate-name condition, toolset identity, loader error handling, rollback behavior, and alternate dispatch transports. Validate with a fresh-process real `PluginManager` plus negative permission and partial-load tests; a fake context cannot prove override authorization or handler ownership.
- Trace every global guarantee to an authority that can enforce it. A plugin loaded in selected profiles cannot normally govern native CLI, dashboard, cron, scripts, or other processes; post-commit observers are not veto gates.
- Distinguish display names from IDs/slugs and require explicit resolution, ambiguity behavior, and cross-scope tests when the native CLI does not accept names.
- For a promised explicit-ID/no-link CLI workflow, audit selectors **per nested command**. A `--project` flag on deploy, logs, or service status does not prove that top-level status, environment inspection, buckets, domains, or metrics can avoid linked context. Compare live nested `--help` with the installed tag's context-resolution source, then route uncovered reads to an authenticated API/MCP surface rather than silently linking.
- Audit deployment success by execution mode and terminal state, not by command name or exit code alone. Detached/no-wait success can mean only queued; captured non-TTY paths may return after upload; log streams can end before deployment. Require an explicit terminal success status or a mode whose pinned implementation demonstrably awaits it, and report source/docs discrepancies.
- Do not infer workflow routing from reserved columns or filter flags; verify dispatcher reads, transition APIs, and tests.
- Check semantic correspondence: link operations must call link primitives, phase routes must update authoritative phase state, and “all boards” must not mean only the active board or an arbitrary cap.
- Separate **semantic parity** from **unchanged native mutation UX**. An exclusive broker plus replacement adapters can reproduce outcomes while ACL-denied native commands no longer preserve native success/denial behavior; post-commit observation is neither.
- For shared-database systems, inventory adjacent filesystem and config writes too: board metadata/current pointers, attachments, workspaces, logs, locks, per-profile Project stores, and orchestration settings can all sit outside the nominal lifecycle tables.
- For native-adapter or operation-map requests, enumerate the parser's complete verb/alias tree first, then trace each handler to exact native function signatures, return types, direct SQL, filesystem/process side effects, and source ranges. Treat a missing single aggregate function as a finding rather than inventing one.
- Reject self-referential completeness proofs. A checked-in ledger can appear exhaustive when its test compares only against a hand-curated contract that omitted live verbs, callables, auxiliary writers, or alternate transports. Derive an independent inventory from the pinned parser, registered schemas, public/private call graph, and direct SQL/filesystem/process effects; then require every discovered surface to map to a ledger row or a justified exclusion.
- Rebuild implementation-plan ordering from actual dependencies, not task numbers. Detect omitted transport/server work, client-before-consumer requirements, snapshot/proposal/launcher cycles, and live-cutover steps placed before installation or rollback gates. Split cyclic tasks into foundations and integrations rather than pretending the written order is executable.
- Audit “read-only” and “dry-run” behavior in executable order. Connection setup may create directories, enable WAL, or migrate schemas; a list command may recompute state; and a dispatch dry-run may still reclaim, timeout, terminate, or promote before suppressing spawn.
- When validating an environment-root override, unset every higher-precedence direct path pin and use a real temporary root. Also isolate adjacent stores separately: a Kanban-root override does not imply that per-profile Project/config/profile stores are temporary. Prefer a deterministic native smoke probe with cleanup when execution is allowed.
- Trace external-worker routing in executable order. A pluggable spawn callback is not usable for non-native assignees if profile/identity validation skips them before callback invocation; compare any promised skip event with the actual event append path.
- Treat certainty thresholds and lifecycle rules as local policy unless an approval authority actually enforces them.

For the Hermes-specific control-plane checklist—including exhaustive parser/callable/dispatcher/auxiliary-writer ledger audits and mid-audit source-drift handling—load `references/hermes-kanban-control-plane.md`.

### 6. Design and adversarially review bidirectional bridges

When the request asks for an architecture rather than only a capability inventory, split the design into independent planes before recommending components.

When the UI/process host and browser/desktop host differ, first separate these traffic classes: terminal thin-client traffic, local-browser access to remote loopback services, remote access to local services, selected-process egress, system-wide egress, remote desktop control, and public ingress. For each, prove the initiator, listener, bind address, DNS side, authentication, persistence owner, and rollback. Explicitly trace which host interprets `localhost` and which host invokes the browser; rendering a URL locally is not network forwarding. Load `references/cross-host-terminal-web-desktop-bridges.md` for the full audit and acceptance matrix.

For general bidirectional bridges, use these independent planes:

1. **Telemetry plane** — product A reports lifecycle/session state to B. Confirm authority, failure behavior, and whether errors are surfaced or silently swallowed.
2. **Control plane** — B invokes A through structured tools, CLI wrappers, a socket, or an API. Prefer structured requests or argv execution over generated shell text.
3. **Event plane** — event subscriptions, hooks, webhooks, or run APIs. Determine delivery semantics, replay/cursor support, deduplication, rate limits, and reconnect reconciliation.
4. **Identity plane** — map process, runtime container, pane/window, product session, agent profile, conversation session, request/run, and correlation-chain identities separately. Never assume one ID implies the others.
5. **Trust plane** — locate secrets, execution privilege, human approvals, network binds, same-host assumptions, and unsandboxed extension code.

For each proposed arrow, record the source interface, destination interface, authentication, serialization, timeout/cancellation behavior, identity carried, and retry semantics. Do not call the result bidirectional merely because each product has a plugin system.

#### Complete primitive-coverage requests

When the user asks for “every primitive,” “complete integration,” or a full native mapping:

1. Inventory **primitive families and their exact public methods/shapes**, not every marketplace package, provider instance, or installed skill. State this boundary explicitly.
2. Build an ownership matrix before proposing one-to-one mappings. Similar names are not equivalence: a profile is not a workspace, a conversation session is not a terminal-server session, and an in-process subagent is not automatically a pane.
3. Cover human/UI, runtime topology, lifecycle, persistence, protocol, extension, automation, identity, and trust planes. For terminal hosts, explicitly include client/server modes, local/remote attach, mouse/clipboard behavior, direct attach, restart versus detach, and OS branches.
4. If the local machine is inaccessible, validate its path documentarily and return OS-conditional branches rather than inventing its version or state.
5. Separate native built-in behavior from a user-local compatibility layer. A user-local plugin may reproduce an outcome without making the upstream built-in contract itself support it.
6. For profile-aware restore, prove the complete invariant chain: install target, reported identity, persisted fields, restored environment, and final argv. If one link is missing, either degrade safely or replace the restore path with an explicitly owned compatibility layer.
7. Treat documentary acceptance criteria as unexecuted until runtime tests actually run; a read-only audit can specify the matrix but cannot declare deployment complete.

Adversarial checks:

- Can an event emitted by one direction trigger the reverse direction and recurse?
- Does a nested or background process inherit context variables that let it impersonate an interactive process or claim the wrong session?
- Are plugin/hook callbacks durable messages, or fire-and-forget observers?
- Can duplicate, reordered, or state-flicker events spawn duplicate work?
- Does an event envelope contain a stable delivery ID and origin/authority source, or must the bridge enrich it with a fresh state query?
- Do named profiles survive native resume, or does the host reconstruct a generic executable command that loses profile identity?
- Does a generated command interpolate labels, branches, pane output, URLs, or event JSON into a shell?
- Does a background API expose the full agent toolset, and is it bound to loopback with mandatory authentication?
- Do containers, SSH backends, remote thin clients, Unix sockets, and Windows named pipes actually share a host and namespace?
- Does a proposed MCP layer exist first-party on both sides, or is it a custom adapter being mislabeled as native support?

Required loop controls for any automatic reverse path: `origin`, `chain_id`, bounded `hop_count`, per-identity concurrency lock, dedupe key, state-transition debounce, bounded retries, and bridge-owned resource exclusion. When the source offers no replay cursor, require a fresh snapshot and reconciliation after reconnect; do not claim exactly-once or at-least-once delivery.

Security defaults:

- Keep read-only tools separate from mutators.
- Make every mutator use a documented human-approval path or remain disabled in unattended sessions.
- Use argv arrays / `shell=False` / structured socket or HTTP requests; never interpolate untrusted fields into `sh -c`.
- Keep provider credentials on the agent side and give the bridge only a dedicated bridge secret.
- Treat authenticated payload fields as untrusted content.
- Treat profiles as state isolation unless the docs explicitly establish process, filesystem, credential, or network isolation.

### 7. Define objective validation before recommending deployment

Translate claims into pass/fail probes covering:

- version/protocol negotiation and unknown-field tolerance
- lifecycle transitions and single-authority behavior
- cross-direction read and mutation flows
- human deny/timeout producing zero mutation
- process/profile/session correlation across moves, restarts, and resumes
- duplicate-event suppression and maximum active runs per correlation key
- bridge outage, reconnect, fresh snapshot, and reconciliation
- injection payloads containing quotes, semicolons, newlines, command substitutions, and Unicode controls
- wrong/missing bearer or HMAC yielding zero accepted work
- loopback/CORS exposure and absence of secrets from argv, logs, pane output, and event payloads
- burst behavior against documented hook/process/output limits

Distinguish documentary acceptance criteria from tests actually executed. If the user prohibited installs or writes, provide the test plan but do not imply it ran.

### 8. Write the report outcome-first

Recommended structure:

1. Verdict and existing integration summary.
2. Stability baseline and evidence legend.
3. Lifecycle commands and states.
4. Detection/manifests.
5. Existing integration behavior.
6. Plugin/action/event/pane/link surfaces.
7. Socket/protocol API.
8. Environment variables.
9. Security and trust boundaries.
10. Stable/source-only/preview/speculative matrix.
11. Exact source index.
12. Read-only audit record: actions, files changed, blockers.

Use exact command names, paths, event names, environment variables, and URLs. Keep implementation archaeology out of the main narrative unless it changes the compatibility conclusion.

## Read-Only Discipline

When the user prohibits writes or installs:

- Prefer official web docs, browser inspection, raw tagged files, and GitHub API/tree endpoints.
- Under a literal “do not create files” constraint, avoid extractors that automatically persist large-page caches; prefer browser DOM inspection or network reads streamed to stdout.
- **Budget stdout before every streamed read.** Hermes may automatically persist oversized terminal results under `/tmp/hermes-results/`, so `curl ...` to stdout is not by itself a zero-write guarantee. Query line/byte counts first, then emit only headings, tables, selected ranges, identifiers, or compact schema summaries. Never concatenate several long documents in one call.
- For large official JSON schemas, parse in the pipe and emit compact inventories: protocol/schema versions, method-to-definition maps, required/optional/default fields, enums/unions, event kinds, and selected response types. Split output by subsystem instead of printing the full schema.
- If a managed tool creates an automatic cache despite the constraint, disclose its exact path separately from project/config mutations. Do not delete it without permission.
- Under a literal zero-write constraint, do not capture stdout/stderr with shell redirection to `/tmp`, `mktemp`, process substitution that materializes files, or helper utilities that spill output. Keep capture in pipes or process memory, and accept that an exit-code probe may need a separate invocation. If an accidental transient file is created and removed, disclose it; do not claim absolute zero filesystem writes.
- Do not clone the repository merely for convenience.
- Do not run installers, package managers, binaries, or integration commands.
- Do not edit configuration to “verify” install behavior.
- Tool-managed temporary caches are not deliverables; do not open or mutate user/repository files unless explicitly permitted.
- State that verification was documentary/source-based rather than runtime-tested.

## Common Pitfalls

1. **Conflating docs with source.** A tagged implementation can prove behavior exists, but not that it is a supported public contract. Label it source-confirmed.

2. **Using the default branch as stable.** Pin to a release first. Branch-only behavior is unreleased even when official.

3. **Treating all events as the same surface.** Subscription events, one-shot wait matches, and plugin hooks may have different allowlists.

4. **Conflating plugin ecosystems.** An integration may install a plugin into product B while product A also has its own unrelated plugin manifest.

5. **Missing helper-versus-protocol distinctions.** CLI `attach`, `wait`, or `update` commands may compose lower-level methods and have no raw counterpart.

6. **Overstating absence.** Say “no first-party evidence found” unless the official material explicitly says unsupported.

7. **Ignoring home/profile assumptions.** Inspect path resolution and supported override variables, especially for multi-profile agents.

8. **Calling context markers authentication.** Variables like `*_ENV=1` are usually guards, not credentials.

9. **Listing security advice without mechanism.** Tie each trust statement to code execution, permissions, confirmation, revision pinning, signature verification, or protocol reachability.

10. **Dumping every file read.** Cite the minimal source set that supports conclusions; keep the report focused on integration outcomes.

11. **Ignoring documentation drift inside one official corpus.** Compare prose, generated schemas/capability endpoints, and pinned source for names and lifecycle semantics. When they disagree, report the mismatch and recommend runtime discovery or feature negotiation instead of choosing one silently.

12. **Treating “non-blocking” as timed or isolated.** In hook/plugin documentation it may only mean exceptions are caught. Verify whether callbacks execute synchronously, have timeouts, and share the host process before making reliability or security claims.

13. **Proving session resume but not profile resume.** For profile-isolated agents, trace installer target, reported identity, snapshot fields, restored environment, and final resume argv as one invariant chain. A valid conversation ID is insufficient if the host can restart it under the wrong profile home.

14. **Mapping a multi-session service to one terminal identity.** Gateways and other long-lived services may host many conversations while a pane stores one lifecycle/session authority. Keep such services outside interactive pane ownership unless the protocol has an explicit multiplexed identity model.

15. **Exposing terminal input as a normal control tool.** Sending generated commands into another PTY can bypass the agent framework’s terminal approval and redaction path. Prefer narrow structured argv tools, separate read-only from mutation surfaces, and require fail-closed approval for every mutator.

16. **Treating launch-injected UI IDs as durable process identity.** A host may reassign public pane/window IDs when a live process moves between workspaces while the child’s environment remains immutable. Trace move semantics, underlying terminal/process IDs, and reporter rebinding before allowing topology changes; otherwise prohibit the move in the supported baseline.

17. **Assuming profile distributions ship plugins by default.** Distribution defaults may cover prompts, skills, cron, and MCP while omitting plugin directories. Verify the `distribution_owned` contract, hard exclusions, plugin enablement, and update behavior. A copied plugin can still remain disabled when local config is preserved on update.

18. **Conflating two remote frontends.** A terminal thin client attached to a remote process server and a product-native desktop client attached to an HTTP/WebSocket backend may share underlying session storage without sharing process ownership, input authority, layout, or reconnect semantics. Document them as separate control/data planes and avoid unsupported dual-writer claims.

## Supporting References

- For cross-host terminal thin clients, native-browser previews, SSH/Tailscale routing, localhost semantics, and remote real-desktop control through MCP, load `references/cross-host-terminal-web-desktop-bridges.md`.
- For cross-host signed-in browser CLI/MCP/REPL integrations, capability-specific forced SSH identities, maintenance-only raw tools, schema allowlisting, shared desktop leases, and no-fallback safety, load `references/browser-cli-mcp-repl-bridges.md`.
- For the release-pinned Hermes/Herdr ownership matrix, recommended no-core-change surfaces, primitive distinctions, and documented source/prose discrepancies at `v2026.7.7.2`, load `references/hermes-release-v2026.7.7.2-integration-map.md`.
- For the Herdr-side integration package, detection model, and socket/plugin distinctions, load `references/herdr-hermes.md`.
- For the exact multi-profile restore invariant chain, safe degradation modes, upstream contract shape, and adversarial test matrix, load `references/herdr-hermes-profile-restore.md`.
- For a no-upstream-change Herdr/Hermes/Daytona tailnet control plane—including local thin clients, named-profile ownership, official Daytona MCP, Tier-3 Tailscale gates, VNC/computer use, rollout, and adversarial acceptance—load `references/herdr-hermes-daytona-tailnet.md`.
- For converting a read-only Daytona/Tailscale/VNC audit into an exact approval-gated execution manifest—including CLI/schema unit reconciliation, conservative spend guards, persistent browser-profile/cookie storage choices, snapshot-from-sandbox stability checks, bootstrap exceptions, secret-bearing artifact controls, concrete-host grants/tests, private-preview distinctions, objective probes, and verified teardown—load `references/daytona-tailnet-vnc-execution-manifests.md`.
- For read-only Tailscale segmentation audits—including compiled-netmap evidence limits, additive grants, direct-member preservation, protocol-complete tests, concrete controller selectors, Serve/Funnel interpretation, Certificate Transparency, and `tailscaled --state=mem:` ephemeral joins—load `references/tailscale-segmented-grants-audits.md`.
- For Hermes Agent’s plugin SDK, hooks, profiles, MCP, terminal/process, Kanban/delegation, session protocols, and security boundaries, load `references/hermes-extension-surfaces.md`.
- For release-pinned audits of narrow Hermes general plugins—especially preview/confirm tokens, slash-command caller limits, `dispatch_tool` pipeline gaps, non-transactional registration, profile-safe launches, collision behavior, output security, and plugin-enabled-versus-tool-visible checks—load `references/hermes-general-plugin-security-contracts.md`.
- For validating staged public Hermes plugin and profile-distribution packages with the real manager/installer—without fake contexts or model calls—and for exact local-package, registration-parity, provenance, dry-run, and disposable-home caveats, load `references/hermes-public-package-runtime-validation.md`.
- For the smallest fresh-process validation of a staged plugin overriding native Kanban tools—including disposable-home layout, exact handler ownership, trust-gate negative controls, partial-load checks, and the native `0 / 9 / 7` visibility matrix—load `references/hermes-kanban-pluginmanager-validation.md`.
- For no-core-change external Kanban brokers—dedicated writer UIDs, compatibility snapshots, tool overrides, cross-UID worker supervision, WAL/ACL/backup hazards, split-brain goal behavior, and production go/no-go gates—load `references/hermes-external-kanban-broker.md`.
- For the dated Railway CLI/Cap self-host selector, deployment-success, pricing, privacy, playback, and embed audit map, load `references/railway-cap-contract-audit.md` and revalidate every live contract before use.

## Verification Checklist

- [ ] Only allowed first-party sources were used
- [ ] Stable release/tag identified and cited
- [ ] Live docs and pinned source are clearly distinguished
- [ ] Every requested integration surface is covered or marked not evidenced
- [ ] Exact commands, paths, method names, events, and environment variables are preserved
- [ ] CLI helpers are distinguished from raw methods
- [ ] Plugin systems are not conflated
- [ ] OS/profile limitations are explicit
- [ ] Security findings identify concrete trust mechanisms
- [ ] Branch-only or future behavior is labeled unreleased/speculative
- [ ] Exact source URLs are included
- [ ] No prohibited install, execution, or user/repository file mutation occurred
