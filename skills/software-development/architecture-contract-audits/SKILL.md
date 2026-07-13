---
name: architecture-contract-audits
description: Audit committed implementations against plans and pinned native contracts, with emphasis on public protocols, transaction boundaries, recovery, and cross-store acceptance.
version: 1.3.7
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [architecture, audit, contracts, atomicity, recovery, exact-head]
    related_skills: [requesting-code-review, systematic-debugging, codebase-inspection]
---

# Architecture Contract Audits

## When to Use

Use this skill for read-only, exact-HEAD audits of an implementation against a saved plan, compatibility ledger, pinned dependency, public protocol, or transactional acceptance contract. Use ordinary code review instead when the question is limited to local diff quality and does not depend on architecture, recovery, atomicity, or pinned-contract evidence.

This complements ordinary diff review: the target is the committed architecture and its observable guarantees, not only changed lines.

## Core principles

- Freeze revisions and pre-existing worktree state before drawing conclusions.
- Audit the complete public path, not isolated native callables.
- Prefer the smallest deterministic public protocol and derive trusted identity/idempotency server-side.
- Never claim operation atomicity without tracing every commit boundary and post-commit side effect.
- Distinguish all-or-nothing authority writes from recoverable cross-store acceptance.
- Use native functions when they exist; do not replace them with authored SQL against native tables.
- Treat a green coverage test as suspect if it covers callables but omits CLI verbs, protocol operations, or sidecar finalization.

## Workflow

### 1. Freeze the evidence boundary

Record the target HEAD, every pinned dependency HEAD, tracked changes, untracked files, and—when auditing staged work—the staged patch hash plus an immutable snapshot of the index objects. Immediately copy each resolved revision to an immutable literal SHA and use that literal in **every** subsequent `git show`, `git ls-tree`, `git diff`, manifest equation, authorship scan, and parallel tool call. For a staged candidate, a patch hash alone is only a drift detector: later working-tree reads can mix a newer index into the audit. Prefer staged blobs (`git show :path`) or export the index to a temporary read-only tree, then re-hash at the end. A practical no-index-mutation export is `mkdir -p "$snapshot" && git checkout-index --all --prefix="$snapshot/"`; retain the staged blob map, hash the exported changed-file manifest, read relevant full files from that export rather than the live worktree, and remove the export after the final seal. The export contains the candidate tree but not deleted paths, so the complete staged diff remains mandatory evidence. **Reproduce the digest with the exact producer command before declaring drift**: `git diff --cached | sha256sum`, `git diff --cached --binary | sha256sum`, and `git diff --cached --full-index | sha256sum` can intentionally hash different patch renderings even when the index tree is identical. Record the accepted rendering command, a sorted index-manifest hash, and—when repository-object writes are allowed—the index tree from `git write-tree`; recheck every applicable seal at the end. Do not keep using symbolic `HEAD`, a branch name, or the live worktree after the freeze: another writer can advance refs or restage files between parallel commands and silently mix evidence from different candidates.

### Exact unstaged worktree candidates

When the user asks for the “exact current diff before commit” and the candidate is not staged, freeze more than `git diff HEAD`: ordinary diff renderings omit untracked files. Record all of:

- literal `HEAD` and requested base SHA;
- `git diff --binary HEAD | sha256sum` for tracked worktree changes;
- `git status --porcelain=v1 -z | sha256sum` for the exact status rendering;
- staged, unstaged-tracked, and untracked path counts;
- a deterministic candidate path/content manifest over the sorted union of `git diff --name-only -z HEAD` and `git ls-files --others --exclude-standard -z`, hashing current bytes and using an explicit deletion marker for absent paths.

If the user supplies only an opaque digest with no producer command or manifest grammar, treat it as supplied provenance—not as independently verified identity. Do not burn time guessing many patch-rendering variants or declare drift from a nonmatching guess. Freeze and report explicit local seals (literal base, tracked patch producer, status hash, counts, and a fully specified path/content manifest), recheck those at the end, and mark the requested exact pin unverified until its producer is supplied.

Use the candidate-manifest digest as the complete snapshot identity; the tracked patch digest alone is insufficient. Recompute every digest at the end. A stable `git status --porcelain` hash proves only that path/state classes are unchanged—not that file bytes are stable. If the patch or candidate-manifest digest changes while the status digest stays constant, treat it as concurrent content drift: freeze the replacement candidate's per-path byte hashes, re-read every drifted file, and rerun all tests or validators affected by those files. Earlier green results are not sealing evidence for the replacement candidate, even when only tests, inventories, or policy defaults changed. Report clearly that acceptance applies only if all reviewed untracked files are staged unchanged. For deletion cleanups, additionally prove a path equation: every base file under each required deleted package root is absent, every deletion belongs to an approved root, and every modification/untracked file belongs to the allowed update surface.

When acceptance requires a “real public-boundary test,” classify proof by the boundary actually crossed: a subprocess CLI test proves the CLI; a real socket test around an in-process server proves transport behavior but not executable startup or signal handling; a pure loader test proves only an inert manifest contract. Do not let a green full-suite log erase a missing boundary-specific proof, and label supplied logs as supplied rather than independently executed.

If concurrent work appears during the audit, exclude it and inspect committed objects. Re-run any command that used a symbolic ref against the frozen literal SHA before relying on its result. Record the later HEAD/status only as excluded drift; do not attribute it to the audited commit.

When a staged digest drifts mid-audit, do not automatically discard an otherwise valid exact-candidate review. Compare the final index blob map against the frozen map, identify every changed path, and re-read each frozen blob by object ID (`git show <blob>`). If earlier live reads are proven to match frozen blobs and every drifted path is re-audited from its frozen object, the original candidate can still receive a verdict. Report two decisions separately: the frozen candidate's acceptance result and a hard warning that the current index is not that audited candidate. Inspect the excluded replacement blob for obvious gate regressions—especially tests whose expected migration or compatibility values are newly derived from the production collection—but label those as excluded current-index drift, not defects in the frozen candidate.

If the initial and final path inventories prove that exactly one path was staged later, use Git pathspec exclusion as a deterministic reconstruction probe with the user's exact producer, for example `git diff --cached --binary -- . ':(exclude)path/to/later-file' | sha256sum`. An exact match to the frozen digest proves that the remaining current index still reproduces the original patch; inspect and report the later path separately. This shortcut is valid only when the excluded-path equation reproduces the exact original digest—never infer it from similar stats, line counts, or a plausible-looking diff.

A concurrently staged repair can expose a defect in the frozen candidate without becoming part of its evidence. If frozen production code added an operation or behavior while an already-existing frozen exhaustive assertion omitted the required classification, cite those two frozen objects as the blocker. Treat the later repair as corroborating drift only, and state separately that the current index may close that one defect but is not the audited candidate.

A digest check immediately before a snapshot command does **not** prove the snapshot contains that candidate: another writer can restage files between the two commands. Never attribute test output to a frozen index merely because the preceding live-index digest matched. After materializing an index snapshot, reconstruct its patch against the literal base inside the isolated tree and require the exact producer digest to equal the frozen digest **before running tests**. If it differs, discard those results as replacement-candidate evidence and rebuild from frozen blob IDs. For an independently initialized temporary repository, commit the literal base first, overlay the captured index blob map (including deletions and modes), then verify `git diff --cached | sha256sum`; a content-only checkout with no correct base cannot reproduce the candidate patch identity.

If the initial blob map was accidentally not retained, do not infer changed paths from `numstat` alone: same-count edits are common. A defensible recovery is sometimes possible by locating prior staged blobs among unreachable objects, matching each suspected path by complete content, reconstructing the exact patch in memory, and requiring its SHA-256 to equal the originally captured producer digest. When prior evidence shows the frozen index plus a small unstaged replacement set, those exact unstaged paths and their frozen object IDs can reconstruct the original candidate—but only if the rebuilt patch reproduces the original digest. This is an emergency recovery path, not a replacement for freezing the map. See `references/recovering-frozen-staged-candidates.md`.

### 2. Extract acceptance criteria

Read the exact plan/task objective, implementation constraints, test requirements, completion gates, and explicitly acknowledged risks. Convert them into a short checklist before inspecting implementation.

### 3. Trace the end-to-end operation

For each public operation, inspect:

1. protocol operation registry;
2. strict top-level and nested argument validation;
3. compatibility contract and operation ledger;
4. authorization and approval class;
5. board/project/task scope resolution;
6. policy decision;
7. native adapter and dispatch mapping;
8. result normalization;
9. sidecar state changes;
10. journal replay and recovery.

A native CLI verb is unmapped if any required stage is absent, even when callable coverage passes.

For broker-only operations, also inspect special-route ordering, client retry classification, runtime assembly, success/denial audit parity, and every exhaustive equation relating protocol operations to native-ledger IDs. Do not fabricate a native-ledger entry for an operation with no native callable; update the explicit non-native classification instead. Route-match before consuming clocks or other shared state so unrelated expiry boundaries do not shift.

### 4. Derive the smallest public protocol

Prefer one deterministic mutation whose arguments are the proposal and reuse an existing generic preview/approval flow. Omit caller-controlled fields that the server can derive, including actor identity, idempotency keys, rendering flags, and internal workspace controls. Reject unknown nested fields and bound graph/list sizes.

### 5. Audit transaction ownership

Follow every invoked native function. Record where transactions begin and commit, what partial state an idempotency check can observe, and whether hooks, notifications, filesystem cleanup, or subprocess actions run after an inner commit. A helper composed from independently committing native functions is not atomic.

Do not accept a temporary process-global transaction monkeypatch merely because database rows can be rolled back together. Check unrelated-board concurrency, patch restoration races, inner rollback semantics, and code that assumes its local commit is already durable.

### 6. Handle sidecars honestly

If authority and policy state use separate databases, strict distributed atomicity is unavailable unless the platform provides it. Use this acceptance protocol:

1. validate and reserve intent;
2. atomically commit authoritative native state;
3. verify exact native post-state through public reads;
4. finalize every sidecar binding/edge, journal result, and approval consumption in one sidecar transaction;
5. return success only after finalization;
6. on failure, leave the operation reserved, prevent dispatch of unaccepted native rows, and recover sidecar finalization from exact authoritative post-state without blindly replaying authority writes.

Graph sidecars must represent every edge. A single-parent binding cannot faithfully represent a multi-parent verifier or join node.

### 7. Design focused real tests

Prefer real temporary databases and public behavior. Required classes typically include:

- exact native helper signature, origin, and source trust;
- CLI-verb-to-protocol/ledger coverage;
- strict nested proposal bounds;
- parity with the pinned native helper;
- late real failure after partial progress would begin, proving complete rollback;
- idempotent replay with no duplicate graph nodes;
- sidecar-finalization failure followed by exact recovery;
- partial/tampered topology rejection;
- unrelated-board writer concurrency;
- static prohibition of authored native-table SQL in adapter modules.

Give exact test names and focused commands. Record actual outputs; do not substitute a full-suite claim when only focused tests ran.

### 8. Perform semantic gap and next-slice audits

When the request is about what remains after an in-progress slice, separate three evidence layers:

1. committed HEAD behavior;
2. concurrent/in-flight worktree behavior, inspected but not attributed to HEAD;
3. current external consumers at the pinned dependency revision.

Re-run full untracked status at the end. Worktree files can appear while a read-only audit is running; report that drift and exclude it from committed conclusions. Verify operation registries against compatibility-ledger exclusion sets when an in-flight slice adds a broker-only operation.

Trace real consumers before proposing infrastructure. Search for production constructors and entrypoints, direct native/SQL writers, subprocess launch contracts, notification cursor ownership, and client call sites. A tested server function with no production runtime constructor or executable is not an operable service; a transport client with no request factory or consumer adapter is not consumer integration.

Prioritize the next slices in dependency order:

1. close the current slice's registry, validation, and compatibility coverage;
2. make the service runnable without deployment side effects;
3. close lifecycle wedges such as expiry, reconciliation, duplicate checkout, and terminal cleanup;
4. integrate the consumer that immediately exercises that lifecycle;
5. adapt other existing writers/readers;
6. leave dashboards, installers, publication, and speculative protocol expansion until concrete consumers and cutover prerequisites require them.

Call out dormant duplicate state explicitly. A sidecar table with unit tests but no production producer/consumer must not be mistaken for an implemented integration or selected as the basis for a new slice without reconciling it with authoritative native state.

### Phase acceptance inventory discipline

When a request names several acceptance surfaces, classify each by **public operability**, not by similarly named components:

- `implemented`: a production entrypoint or consumer reaches the behavior and public real-behavior tests cover the complete path;
- `partial`: core library/protocol behavior exists and is tested, but production assembly, a real consumer, recovery, or cutover enforcement is absent;
- `missing`: no behavior artifact exists; metadata, intended-path documentation, a pinned parser contract, or an internal helper does not count.

For accumulated phase audits, add `blocked` for work whose prerequisite approval has not been granted. Keep five columns conceptually separate: committed repository artifacts, current installed consumer state, tests present versus tests executed, locally implementable artifacts, and actions requiring external/profile/privileged/live approval. Never inherit approval from a historical rollout, older plugin generation, plan prose, an adjacent phase, or a request to continue autonomously. A named unapproved prerequisite blocks dependent rollout; a separately reviewed live-enforcement phase is always a hard stop.

For every row, name exact production files, exact public test functions, and the missing link. Inspect pinned external consumers too: direct database writers in a CLI, gateway notifier/dispatcher, dashboard, or service unit can disprove sole-writer and cutover acceptance even when broker operation coverage is exhaustive.

Require separate exhaustive equations for native callables, registered model tools, public protocol operations, and CLI parser verbs/paths. Pinning parser shape without mapping every verb/path to a broker operation, broker-only route, or explicit exclusion is drift detection, not operation coverage.

When exact tool override is claimed, verify all of: exact native tool names, `override=True`, the host override trust gate, the consumer's narrowly inspected non-secret `allow_tool_override` value, request construction, and the broker-client path. Similarly named control-plane tools and pre-tool hooks are not native overrides. Prefer static source/hash/config-key inspection over status CLIs that may append logs.

For remaining-phase traceability, preserve phase labels even when the plan is only available through supplied context, but never invent semantics for opaque task IDs with no repository artifact. Separate the frozen commit, parent-owned dirty worktree, pinned external consumer, installed state, and approval provenance in every row. Use `references/remaining-phase-traceability-matrices.md` for kernel-bound CLI false friends, exact dashboard route inventories, real shadow-mode acceptance, dependency-ordered next slices, and honest no-write reporting.

Keep these look-alikes explicit:

- compatibility snapshots are not deployment backup/restore;
- packaging metadata and a callable `serve()` are not an installer or operable service;
- a transport client used only by tests is not consumer integration;
- parser/ledger compatibility coverage is not a CLI compatibility shim;
- naming an untrusted dashboard in a threat model is not an enforced dashboard posture;
- start/failure acknowledgement is not process spawn, supervision, or running-worker orphan recovery;
- request-driven heartbeat/terminal reconciliation does not reconcile worker death or out-of-band native terminal writes.

Before recommending an actual launcher or other consumer, verify that a foreground production runtime constructor and service entrypoint exist. If the server exists only as a fixture-exercised function, the smallest dependency-correct next slice is usually a non-privileged foreground service command with explicit config, real socket health, clean shutdown, and socket cleanup. Leave installers, system service units, and privileged cutover for later approval gates.

For daemon/installability audits, also inspect accepted-connection deadlines and head-of-line blocking, stale-socket crash recovery, runtime-directory ownership, production callsites for launcher enrollment, and whether backup "offline" fencing proves process quiescence rather than merely socket-path absence. Keep explicit migration separate from fail-closed startup: a unit-level `ExecStartPre=migrate` can silently turn every restart into a schema mutation even when the daemon command itself correctly rejects stale state. Compare the client deadline against the **sum** of all sequential database opens/transactions on the public path, not one configured busy timeout; repeated per-open migration checks or lock waits can exceed a nominally larger client budget and leave server-side work running after client ambiguity. Keep parser snapshots distinct from a CLI shim, read operations distinct from a dashboard, cursor tables distinct from notification delivery, and manager classes distinct from public operator workflows. For inert bundles that provision named Hermes profiles and directory plugins, separately prove the profile-path equation, authenticated plugin/config inventory, dedicated supplementary groups, broker-database parent provisioning, notify-service ordering, and worker-interpreter wheel closure; source `copytree` or `PYTHONPATH` injection is not installed-wheel proof. Use `references/deployable-daemon-installer-audits.md` for the full checklist, `references/installer-profile-wheel-completeness.md` for named-profile and installed-wheel closure plus side-effect-free syntax probes, and `references/unix-socket-broker-hardening.md` for absolute frame deadlines, bounded admission/drain, exact-inode socket cleanup, and focused adversarial tests. For a combined kernel-peer/UID-GID/Landlock/protected-path/dirfd-installer review, use `references/adversarial-local-service-security.md`; it includes the future-worker-executable persistence trace, renameable-ancestor verification trap, and post-create EMFILE rollback requirements. For adversarial audits that combine volatile dedup with durable recovery, approval death races, polling-state growth, process-group orphaning, restart reconciliation, post-exec readiness, and output quotas, use `references/adversarial-concurrency-liveness-bounds.md`. For daemons owning separate public and private control sockets, use `references/dual-socket-daemon-remediation-designs.md` for two-thread supervision, launcher-failure cleanup ordering, group-separated inert bundles, immutable-index review under concurrent parent work, and real distinct-GID tests. When the repair replaces same-UID broker-spawned launchers and launcher-spawned workers with three systemd-managed identities, use `references/systemd-mediated-distinct-identity-remediation.md`; it covers kernel enrollment without parent assumptions, systemd credentials, durable activation replay, aggregate notify readiness, migration, and real service-manager REDs.

For dashboard rollout posture, inventory the pinned backend routes by HTTP method, prove the bundled mutation API is unmounted or request-gated rather than merely hidden in the UI, and trace replacement GETs through a production request factory and real authenticated broker process. Avoid same-process false greens when authorization is PID-bound. Use `references/dashboard-consumer-posture-audits.md` for replacement-plugin naming, socket/identity checks, and the smallest real-process proof. When the same audit also claims human operator parity, use `references/operator-dashboard-parity-audits.md` to keep operation-ID coverage separate from parser/argument semantics, trace project identity through native persistence, and distinguish an exact manifest from runtime dashboard enforcement.

When a pre-deployment phase asks only for rollout/rollback/drift artifacts, prefer one strict inert deployment-posture envelope over three independently drifting plans. Cross-validate installer, backup, daemon, plugin, dashboard, and pinned-source claims; encode missing quiescence, route disablement, consumer identity, exact-target restore, and sole-writer fencing as blockers. Do not add an execution CLI or let repository-local approval authorize live or privileged actions. Use `references/inert-rollout-rollback-drift-contracts.md` for the schema, validator invariants, focused tests, and later approval packet.

For read-only audits, do not run tests that would violate the requested state boundary. Distinguish source/test evidence from tests actually executed, and state that no test result was observed when none was run. Re-check both audited and pinned-consumer worktrees at the end; report repository cleanliness separately from incidental tool-managed files outside the repositories.

For exact-hash Tailscale policy candidates, keep static grant semantics, test-source completeness, observed policy-editor compilation, and live network/runtime behavior as four separate verdicts. A parseable HuJSON/JSON body and a narrow grant set do not prove editor RED/GREEN or runtime listener posture. Derive per-source/per-protocol assertion matrices, check all-member negative coverage, and require explicit IPv6 destinations when the plan names ICMPv6; an IPv4-only alias with `proto: "icmp"` proves only IPv4. Use `references/tailscale-policy-candidate-audits.md` for the full read-only workflow and reporting taxonomy.

For plugin-candidate publication audits, use `references/read-only-plugin-candidate-classification.md`: pin a canonical source-tree hash, separate deterministic rejection from blocked behavior evidence, perform handler-free real `PluginManager` registration only after proving import/register paths inert, and fall back to in-memory `HEAD` blob checks if concurrent drift removes worktree packages. Treat last-known-good retention as relative to the current hardened gates, not the historical publication event.

### Source-stability sealing for public-package withdrawals

When sealing an exact staged withdrawal against a protected live source, keep three byte surfaces separate:

1. the protected source package at its pinned tree digest;
2. the deterministic public projection produced from that source under a clean/fresh policy context;
3. the existing public package at the literal base commit.

A stable source digest does not prove that either public byte surface is valid. Reproduce sanitizer defects in memory when possible, using the real sanitizer and inclusion rules without creating an export tree. Ensure the simulated repository context matches the claim: a live checkout's untracked denylist can change replacement output, so use an intentionally absent/fresh repository context when verifying a clean-isolated projection. Report exact defect counts and paths rather than only saying the projection fails.

For withdrawal disposition, independently inspect the existing base package. A newer source projection failing does not justify deleting a valid last-known-good package; withdrawal is correct only when the existing public bytes also fail the current hardened semantic/standalone contract. The source projection and base package may exhibit different malformed placeholders while proving the same semantic defect—record both rather than requiring byte-identical corruption.

At final seal, recheck in one bounded packet: exact staged digest (with the producer command named), staged path count, zero unstaged/untracked paths, index-manifest digest, literal HEAD/base/live remote equality, protected source hashes, source quiet-window duration, publisher paused state, and absence of active exporter/publisher processes. Make this packet exception-safe: parse optional runtime-state JSON defensively or in a separate non-gating probe so a schema assumption cannot abort after source hashes are printed but before the seal completes. Rehash protected sources again after any aborted packet; output preceding an exception is partial evidence, not a final seal. For process checks, avoid substring `grep` against the audit command itself—inspect NUL-delimited `/proc/<pid>/cmdline` argv and match exact script basenames/arguments, otherwise the scanner commonly reports itself as a publisher/exporter. Distinguish independently rerun tests from supplied prior sealing evidence; a strict read-only final audit should not rerun tests that can create caches or runtime records.

For candidate universes spanning skills, plugins, profiles, and personalities, compute one deterministic **source-map aggregate** over sorted `kind + NUL + name + NUL + canonical_digest + NUL` records. Keep each class's canonical policy explicit: package-tree hashes for skills/plugins, distribution-owned surface hashes for profiles, and package-tree hashes for personalities. Compare the complete expected and current maps, report exact mismatch rows and the matching count, and retain both aggregate digests. This catches stale rejected candidates outside the few sources informally called “protected”; a stable staged index does not repair a source-map mismatch.

Capture protected-source hashes before long evidence reads. If a source first matches and later changes, preserve the observed sequence (`start hash/path count → intermediate → final`) rather than reporting only the final mismatch; increasing path counts can prove in-review drift without attributing the writer. If the requested hash differs on the first computation, state that the requested snapshot was never observed. Either condition fails the quiet-window/reclassification gate even when the replacement likely keeps the same disposition.

When TDD chronology is recorded only by a sealing report, separate three claims: supplied RED attestation, independently reconstructable RED semantics from the literal base, and independently rerun GREEN tests. A read-only reconstruction can compare base behavior/data with the staged test assertion—for example, a nonempty fallback versus an explicit-empty expectation—without materializing a replacement tree. Do not describe supplied chronology as independently witnessed, and do not run a prohibited full suite merely to compensate for absent raw RED logs.

When the withdrawal is already committed, seal the literal commit rather than adapting staged-tree equations informally: reproduce `git diff "$BASE_SHA" "$WITHDRAWAL_SHA"` with its named producer, prove manifest/package-root and fingerprint/blob equations from `git show`/`git ls-tree`, query the live remote base, and re-run the production sanitizer/inclusion policy in memory against an intentionally absent repository context. Match the exact malformed-output class, not merely repeated tokens. See `references/committed-withdrawal-source-seals.md`.

For a read-only security/quality seal, prefer equations that cannot mutate the candidate: verify every manifest digest and fingerprint with `sha256sum`/`jq`, prove manifest package roots equal tracked package roots, resolve package-local support references, inspect final staged blobs for encoding/newline/special-file defects, and scan only added lines for high-confidence secret and unsafe-code signatures. In a strict no-write audit, do **not** run `git write-tree`: it can materialize a repository object and refresh index cache metadata even when staged entries remain identical. Use the user's exact staged-diff digest producer plus a sorted `git ls-files --stage`/blob manifest; use `git write-tree` only when repository-object writes were explicitly allowed. Set `PYTHONDONTWRITEBYTECODE=1` for Python validators and rerun only test classes whose code paths are known not to create temporary homes, caches, installs, or runtime records. **Freeze ignored repository artifacts at the start as well as tracked status**: record a sorted `git ls-files --others --ignored --exclude-standard -z` path/content manifest (and mtimes when write attribution matters), then compare it at the end. `git status` with zero untracked files does not reveal ignored `__pycache__`, coverage, or tool-cache writes; without an initial ignored manifest, a final ignored artifact can only be reported as ownership-indeterminate, never safely deleted or claimed as audit-created. Report broader supplied suites as supplied evidence rather than implying they were independently rerun. State “no repository or protected-source changes” instead of an unqualified “no files changed” when Hermes may update logs or skill-usage metadata outside the audited boundary.

When a sanitizer patch adds placeholder grammar, executable-path rejection, token-boundary rules, or person-versus-product author classification, use `references/semantic-sanitizer-adversarial-audits.md`. For exact-digest Tasks-style reviews spanning profile-field scope, real shell outcomes, strict JSON-versus-YAML semantics, path-scoped authorship, URL/command-substitution boundaries, mixed `printf` formats, YAML spans/aliases/merges, privacy, LKG, and C++ compatibility limits, also use `references/semantic-sanitizer-exact-digest-review.md`; it includes repeated inline-comment profile identifiers, author-bearing YAML sequence merges, staging-versus-final-validator separation, per-word shell comparison, and exception-safe no-write fixture sealing. For package exporters that combine staging validation, direct package swaps, inventories, auxiliary change lists, and batch cleanup/rollback, also use `references/public-export-transaction-adversarial-review.md`; it covers credential-threshold and placeholder-marker bypasses, direct-versus-canonical context drift, discarded real-manager call evidence, compiler-backed compatibility controls, recovery-interruption retry wedges, auxiliary-path collisions, and partial-snapshot cleanup loss. Require a false-positive/bypass matrix and disposable real-exporter repros: valid Markdown HTML can expose overbroad angle-bracket regexes, asymmetric delimiters can bypass apparently comprehensive placeholder tests, and organization-word heuristics can both reject products and exempt people. Treat unsafe acceptance and deterministic false rejection as independent blockers.

For skill-candidate publication audits across default and profile-local trees, use `references/read-only-skill-candidate-classification.md`. It distinguishes bundled/hub content, canonical local skills, profile-only primitives, and stale/specialized overlays; checks package-local references plus cross-skill dependency closure; simulates sanitization in memory; and treats privacy-safe but semantically broken exported commands or product-name rewrites as publication blockers.

For standalone profile-distribution and personality publication audits, use `references/read-only-profile-personality-candidate-classification.md`. It freezes only distribution-owned source surfaces, separates native installability from exporter acceptance, catches per-skill-author sanitizer corruption, audits dispatcher/plugin/MCP dependency closure, verifies nonactivating personality installs, and reports incidental Hermes log writes honestly.

For public package freshness audits, use `references/public-package-freshness-matrices.md`. Compute public, raw-source, and deterministic export-projection tree hashes; compare public bytes to the export projection rather than unsanitized source; preserve version and digest as separate freshness axes; and report stale-by-version/digest separately from invalid-under-current-contract so `outdated` never becomes implicit deletion evidence. When a read-only staged-tree audit supplies a prebuilt wheel, use `references/read-only-wheel-exact-tree-verification.md`: locate digest-associated artifacts outside `dist/`, verify the wheel hash, and compare every package member byte-for-byte with staged blobs without rebuilding, extracting, or installing it. If the artifact pins live Python runtime objects or parser shapes, also use `references/python-runtime-sensitive-compatibility-contracts.md`: record the supplied-suite and target interpreter patch versions separately, install under the exact target runtime, structurally diff any hold, and cross the real consumer boundary rather than accepting import or `--help` as operability.

### Exact-plan semantic traceability

When the user names an authoritative plan and asks for task-by-task traceability:

1. verify the exact file hash before analysis and again at the end;
2. preserve each task's acceptance sentence rather than replacing it with weaker shorthand;
3. map every task to committed path/HEAD, live path/hash, public proof actually observed, missing proof, gate state, and the smallest next action;
4. use explicit states such as `pass`, `partial`, `fail`, `blocked`, and `not started`—a similarly named file, pane, workspace, profile, or lifecycle plugin is not semantic acceptance;
5. pin every repository whose contents or status influenced the conclusion, including backup and publication repositories;
6. order remaining work by dependency, with rollback and approval provenance before implementation and rollout.

Keep three look-alike distinctions explicit: source repository versus installed consumer; official lifecycle integration versus custom control plugin; named workspace/tab topology versus an operable plugin or workflow. A mirrored plan or backup inventory is preservation evidence, not implementation evidence.

### Read-only probes that append runtime artifacts

Some nominally read-only CLIs (`status`, `doctor`, MCP connectivity tests, update checks) can append logs or refresh caches. Prefer static config/log inspection when it answers the question. If a live probe is materially required:

- avoid cloud inventory calls when the user forbids paid/API operations;
- record pre/post status or mtimes for the relevant runtime log/cache surface when practical;
- report incidental runtime log/cache writes separately from source/config/state mutations;
- never claim “nothing modified” when the probe appended a log;
- do not treat a successful MCP handshake/tool listing as proof of cloud authentication, least privilege, read-only inventory access, or lifecycle acceptance.

For launcher acknowledgement and worker-capability slices, derive the operation set from pinned worker-visible tools and behavior tests rather than plan shorthand. Separate task-scoped lifecycle tools from policy-constrained related-work tools, preserve native start/failure semantics, and keep the slice bounded. For PID binding, native spawn-failure accounting, replay checks, cross-store ordering, and the exclusive-writer assumption, use `references/launcher-lifecycle-native-wrappers.md`. For public process operability, sanitized argv/environment/streams, direct-child supervision, signal/orphan handling, consumer cutover, and duplicate failure acknowledgements, use `references/public-launcher-process-contracts.md`. When checkout authorization requires a pre-seeded PID/start-time principal, audit how a real subprocess is enrolled and how the service is assembled; fixture-side principal insertion plus an in-process CLI call is not public proof. Use `references/launcher-principal-enrollment-services.md` for broker-supervised gating, restart-safe binding, distinct-identity database isolation, and real-process tests. When the immediate task is the smallest config/schema/enrollment step toward three fixed service identities and one worker slot, use `references/distinct-identity-config-migration-slices.md`; it prevents config-only false security, destructive legacy-lease migration, launcher-controlled systemd, and tautological runtime tests. For standalone human CLIs, also verify that request authorization preserves the `SO_PEERCRED` start time, approval challenges bind the exact process and binding generation, enrollment uses a private trusted registrar rather than a public bearer-secret operation, and local implementation is not confused with privileged OS-isolation acceptance; see `references/ephemeral-operator-enrollment.md`.

### Marker-delimited rollout and scope-preservation audits

For rollouts that insert canonical blocks across customized trees, prove more than marker counts:

- extract and hash the canonical inclusive marker block from the frozen plan;
- require each pre-existing file’s baseline-to-current diff to contain exactly one insertion, then separately prove baseline lines remain an ordered subsequence;
- compare support-file `(relative path, SHA-256, size)` manifests exactly;
- for a seeded missing tree, require complete manifest equality with the canonical source and reject links, special files, hidden components, runtime/credential filenames, and high-confidence secret signatures;
- stream-validate rollback archives against their member manifest without extraction;
- take two final target snapshots and require a stable aggregate digest.

Keep target preservation distinct from global scope cleanliness. A baseline containing only target trees cannot prove unrelated skill paths were unchanged. Use rollout-time mtime/ctime scans only as drift detectors, list exact out-of-target paths and current hashes, and do not attribute the writer without provenance. If a required skill read updates a hidden usage index or similar tool-managed metadata, report that incidental runtime drift rather than claiming the audit made no changes. See `references/marker-rollout-scope-preservation.md` for the deterministic equations and reporting pattern.

## Responding to blocker audits during sealing

When an exact-candidate audit returns a substantive blocker, immediately invalidate that candidate as sealing evidence. Stop any still-running full-suite process for that candidate; continued green output cannot repair an architectural acceptance failure and should not be reported as current progress. Preserve the frozen tree identifier and audit reports as historical evidence, but do not reuse its wheel hash, partial/full-suite log, or prior PASS results after remediation changes begin.

Under one-writer discipline, every delegated reviewer remains read-only; do not hand fixes to a third agent merely because a generic review workflow recommends auto-fix delegation. The original writer validates each claim, writes the deterministic public RED, applies the smallest coherent correction, and owns resealing.

Validate each audit claim against the frozen implementation before editing, then group confirmed findings into dependency-ordered class-level slices. Use public RED→GREEN tests where deterministic; when a scheduler-exact race would require a prohibited hook, test the real kernel/transaction invariant at the narrow public state boundary and pair it with a top-level behavior test. After remediation, create a new exact tree and rerun every sealing stage from scratch, including independent audits. Never claim completion, commit readiness, or exact-tree acceptance while any blocker tranche remains open.

## Reporting format

Lead with `pass`, `fail`, or `blocked`. Then provide:

1. smallest correct public contract;
2. atomicity verdict and evidence;
3. sidecar/recovery acceptance semantics;
4. blockers in dependency order;
5. exact required tests;
6. commands actually run and their output;
7. tracked-file status and excluded concurrent work.

Keep the summary decision-oriented. Put reusable technology-specific details in `references/` rather than expanding the main skill indefinitely.

## References

- `references/dirty-schema-wheel-seals.md` — exact dirty-candidate manifests under untracked drift, append-only migration fixtures, exhaustive config/wire-schema parity, latest-upstream oracles, reproducible wheels, and installed-artifact proof.
- `references/staged-semantic-gap-static-probes.md` — staged-blob set equations, polling-to-journal outage traces, deployable readiness, schema/runtime parity, test-double classification, and supplied-versus-observed evidence.
- `references/exact-candidate-sealing-remediation.md` — exact-generation identity, one-writer blocker remediation, package/full-suite resealing, and adversarial replay/deadline/authenticity/startup checks.
- `references/accumulated-phase-rollout-audits.md` — phase matrices, approval provenance, native/CLI/override equations, shadow/cutover operability, and backup/restore acceptance.
- `references/remaining-phase-traceability-matrices.md` — exact remaining-phase matrices across committed, dirty, pinned-consumer, installed, and approval evidence; operator/dashboard/shadow false friends and dependency-ordered slices.
- `references/deployable-daemon-installer-audits.md` — distinguish libraries from operable daemons/installers; audit socket availability, launcher assembly, OS isolation, consumer cutover, backup quiescence, and concurrent RED drift.
- `references/installer-profile-wheel-completeness.md` — audit named Hermes profile shape, authenticated plugin/config inventories, supplementary-group and tmpfiles closure, cold-start ordering, installed-wheel availability, and no-write syntax probes.
- `references/unix-socket-broker-hardening.md` — audit absolute frame deadlines, bounded independent connections, safe stale-socket recovery, exact-inode cleanup, and bounded transport drain.
- `references/adversarial-local-service-security.md` — combined kernel peer/liveness, UID/GID/group, Unix namespace, Landlock/protected-path, operator enrollment, and descriptor-bound installer audit checklist.
- `references/systemd-distinct-identity-worker-services.md` — audit fixed systemd worker units, per-lease credentials, pidfd-to-unit/invocation binding, narrow polkit or root-supervisor control, shared-worker-UID theft, readiness, and restart/recovery races.
- `references/systemd-255-fixed-worker-activation.md` — exact systemd 255 `StartUnit`/`StopUnit`/`GetUnitByPIDFD` signatures, job correlation, fixed-slot credentials, post-exec notify readiness, invocation/cgroup checks, compensation, concurrent-drift handling, and real-VM test boundaries.
- `references/systemd-mediated-distinct-identity-remediation.md` — replace same-UID direct spawning with broker/launcher/worker service identities while preserving enrollment, credential handoff, replay, recovery, and aggregate readiness.
- `references/dual-socket-daemon-remediation-designs.md` — design and audit supervised public/private listeners, fail-safe launcher cleanup, group-separated inert runtime provisioning, and real distinct-GID proofs.
- `references/dashboard-consumer-posture-audits.md` — audit native dashboard route disablement, broker-backed replacement reads, PID/socket identity traps, plugin naming, and real-process rollout proof.
- `references/operator-dashboard-parity-audits.md` — audit broker-backed human CLI and dashboard parity: operation equations, parser/tool argument semantics, project persistence, exact confirmation, and runtime route enforcement.
- `references/operator-cli-config-migration-remediation.md` — read-only remediation for sealed internal argv, optional-board canonicalization, bounded CLI failures, strict config versioning, real-socket tampering proof, non-tautological migrations, and concurrent parent-owned RED drift.
- `references/inert-rollout-rollback-drift-contracts.md` — design the smallest repository-local deployment posture envelope, cross-surface validators, rollback inverses, drift pins, and live-phase approval packet.
- `references/pre-cutover-validation-shadow-audits.md` — audit isolated comprehensive-validation packets, installed-wheel proof, real versus quarantine shadow behavior, inert cutover/rollback manifests, and privileged probes deferred to later gates.
- `references/sqlite-native-sidecar-atomicity.md` — SQLite nested transactions, native composite operations, multi-parent sidecars, and recovery tests.
- `references/descriptor-bound-private-file-consumption.md` — race-safe exact-`0600` one-time catalogs: lock-before-snapshot, descriptor-only consumption, byte-exact fsync-failure restoration, idempotent retry, and bounded eventual-removal tests.
- `references/broker-protocol-expansion.md` — broker-only operation routing, native-ledger exclusions, retry/audit checks, expiry traps, and focused verification.
- `references/launcher-lifecycle-slice-audits.md` — exact-HEAD launcher/worker lifecycle audits: PID/start binding, replay-safe secret bootstrap, native/sidecar acceptance, reconciliation, and real-process tests.
- `references/launcher-lifecycle-native-wrappers.md` — fixed private-helper invocation, pidfd-derived identity, exact PID/failure pre/post states, replay-safe cross-store ordering, expiry/heartbeat/terminal reconciliation, and exclusive-writer cutover assumptions.
- `references/public-launcher-process-contracts.md` — public launcher operability, argv/environment/stream and signal contracts, real consumer cutover, duplicate failure acknowledgements, running-lease death reconciliation, and exact-object evidence under concurrent drift.
- `references/launcher-principal-enrollment-services.md` — detect pre-seeded-principal gaps; design broker-supervised, PID/start-bound launcher enrollment, restart-safe rebinding, OS database isolation, service assembly, and real subprocess proof.
- `references/ephemeral-operator-enrollment.md` — secure standalone CLI enrollment through a private registrar, exact `SO_PEERCRED` PID/start/generation binding, process-bound approvals, local-versus-privileged acceptance, and adversarial tests.
- `references/staged-security-contract-audits.md` — staged-diff verification for exact argv grammar, incremental kill/reap, full ANSI/credential redaction matrices, caller ordering, closed schemas, binding/single-use semantics, and fail-closed test resources.
- `references/fail-closed-restore-launchers.md` — restore-target provenance, TOCTOU/rebinding, one-time consumption, partial multi-target launch, argv parsing, and realistic adversarial tests.
- `references/per-target-journal-and-generated-manifest-seals.md` — strict raw JSON seal-map validation before key coercion, absent-target completeness, pre-restore rejection probes, staged generated-inventory freshness equations, and compact no-write verdicts.
- `references/export-pipeline-plan-audits.md` — exact-object audits of public artifact refresh pipelines: dirty-source isolation, last-known-good/gate contradictions, linked-worktree policy paths, recoverable directory replacement, exact staging, and PR-only publication.
- `references/public-export-transaction-adversarial-review.md` — read-only exact-generation review of sanitizer blind spots, compatibility false positives, direct pre-swap publication, auxiliary-output collisions, and partial-cleanup rollback integrity.
- `references/read-only-plugin-candidate-classification.md` — classify plugin inventories without handlers or writes; canonical source hashes, structural/test-double/skill gates, handler-free real-manager parity, exact-HEAD fallback, and last-known-good retention.
- `references/broker-aware-plugin-overrides.md` — exact native-tool override audits: schema/visibility/behavior equations, preflight against partial registration, broker request identity, model-versus-human approval separation, semantic parity traps, real-manager TDD, and retry review.
- `references/exact-object-testing-concurrent-drift.md` — run exact-object tests while HEAD moves, reconstruct temporary checkouts for pinned commits no longer reachable from refs, and separate intrinsic failures from installed-dependency compatibility holds.
