# Daytona–Tailscale–VNC execution manifests

Use this reference when converting a read-only integration audit into a bounded, approval-gated Daytona sandbox execution manifest with private Tailscale access, VNC/Computer Use validation, spend accounting, and deterministic teardown.

Revalidate every live contract before reuse. The observations below were checked on 2026-07-11 against Daytona CLI/release `v0.190.0`, live Daytona API `v0.196.0`, current Daytona docs/pricing, and current Tailscale docs/pricing.

## Read-only baseline first

Before any billable or network mutation:

1. Pin the latest stable Daytona release and dereference its tag to a commit.
2. Compare installed CLI and live API versions. Treat an API-ahead warning as compatibility risk, not proof of failure.
3. Run only read operations such as `daytona list --format json`, nested `--help`, and tailnet status inventory.
4. Capture exact current host names/IPs needed for a least-privilege policy; do not use broad user/autogroup selectors when the request requires concrete hosts.
5. Verify tier, wallet, automatic top-up, and current spend in the authenticated dashboard when API-key mode lacks organization/billing visibility. Do not infer them from successful resource-list calls.
6. Verify Tailscale plan and remaining ephemeral-minute allowance separately; Daytona spend approval does not bound Tailscale overage.

Document any managed web-extraction caches created during a nominally read-only audit separately from project/config mutations.

## Resolve CLI-help/schema unit contradictions

Do not trust a flag description when it conflicts with the tagged request schema and SDK types.

Daytona `v0.190.0` is a concrete example:

- `daytona create --help` says `--memory` is MB.
- Tagged CLI source passes the integer directly to `CreateSandbox.Memory` without conversion.
- The tagged generated API model says the create field is GB.
- SDK resource types and sandbox responses say GiB.

Therefore a 1-GiB create uses `--memory 1`, not `--memory 1024`. General rule: trace parser → request assignment → generated API schema → response unit, record the contradiction, choose the wire-contract value, and verify the created object immediately. On any mismatch, teardown before continuing.

## Audit hidden create, MCP, lifecycle, and desktop side effects

A read-only re-audit against installed CLI `v0.190.0`, live API `v0.196.0`, and current first-party docs exposed several reusable gates:

- Preserve the actual root CLI grammar: this release uses `daytona create`, `daytona list`, and `daytona info`, not a speculative `daytona sandbox ...` namespace. Capture live nested help before writing a manifest.
- Inspect the complete post-create path, not only the create request. Tagged `daytona create` unconditionally requests a standard preview for web-terminal port `22222` and prints its URL after the sandbox is created. A strict no-preview manifest must therefore use a current SDK/API or human Dashboard path that does not call a preview method. Also assume the sandbox may already exist if a later preview lookup makes the CLI return an error.
- Audit MCP registration and handler logic separately from CLI/API schemas. The tagged `create_sandbox` MCP handler rejects explicit CPU, GPU, memory, or disk whenever `buildInfo` is absent, despite its error text referring to snapshot use; it also retries creation up to three times. Do not use that handler for a strict one-resource run with explicit resource overrides. The same MCP release has no native Computer Use tools.
- Treat lifecycle intervals according to their triggering state. `auto-stop` is an idle timer, while `auto-delete=N` counts continuous stopped time; neither is a wall-clock deadline from creation. For a bounded ephemeral run, pair an external deadline with `autoDeleteInterval=0` and exact-ID cleanup.
- Do not infer listener binding from a loopback backend argument. Tagged Computer Use defaults to x11vnc port `5901` and noVNC port `6080`; noVNC proxies to `localhost:5901`, but its `--listen 6080` and the x11vnc command do not explicitly bind listeners to loopback. Require `ss -ltnp` after start. Tailnet policy denial of raw ports is useful defense but is not proof of localhost-only binding.
- Keep current-contract and release-source axes separate when the hosted API is ahead of the latest public release. Prefer current official SDK calls and feature detection for execution, while labeling source-only findings with the pinned release.
- API-key authentication can prove sandbox-list access while still withholding organization/tier/wallet commands. A zero sandbox list does not establish VPN eligibility, wallet balance, automatic top-up state, or spend. Require a human Dashboard check without starting a reauthentication flow or exposing a login URL.

## Minimal bounded create contract

Prefer the default Daytona image when VNC/Computer Use is required; it includes Xvfb, XFCE, x11vnc, noVNC, and supporting libraries. Keep the exact create contract explicit:

- fixed name and run ID
- default `daytona-small` snapshot
- 1 vCPU, 1 GiB RAM, 3 GiB disk
- no GPU, VM, volume, or public flag
- 15-minute idle auto-stop
- `auto-delete=0` so stop destroys the sandbox
- labels for owner, purpose, run ID, spend cap, and hard-stop timestamp
- external wall-clock deadline; labels and idle auto-stop are not budget enforcement

After create, query full info and assert resources, `public=false`, lifecycle intervals, snapshot, and labels. Never continue on partial drift.

## Spend accounting that actually bounds risk

Build a conservative rate from live first-party pricing and ignore promotional credits. When wording such as “first N GiB free” is ambiguous by scope, calculate both published and all-resources-charged rates; use the latter as the guard.

For Daytona’s 2026-07-11 Linux rates and a 1/1/3 sandbox:

```text
CPU     1 × $0.0504/h
RAM     1 × $0.0162/h
Disk    3 × $0.000108/h   # conservative: charge all disk
Total       $0.066924/h
```

A two-hour hard deadline costs at most `$0.133848` at those rates. For a `$10` authorization, stop at the earliest of a short wall-clock deadline, failure, or a `$9.50` estimated threshold; reserve headroom for drift and delayed metering. Daytona documents up to 48 hours of billing delay, so dashboard totals are reconciliation, not a real-time kill switch.

For Tailscale, convert run duration into ephemeral minutes. Current plans include monthly pools, but no public automatic overage rate is stated. Require enough remaining included minutes or written zero-incremental-cost confirmation before claiming a combined exact-dollar cap.

## Least-privilege tailnet policy

Use a dedicated non-user tag such as `tag:daytona-ephemeral`. Build policy fragments from exact current host aliases/IPs and allow only required ports:

- TCP 22 for Tailscale SSH
- TCP 6080 for direct noVNC

Prefer modern `grants` with `ip: ["tcp:22", "tcp:6080"]`, a matching `ssh` rule for non-root users, and positive/negative policy tests. A fragment is not a safe full-policy replacement: merge it with the existing policy and ensure no broad allow-all rule defeats the negative test.

Do not automatically include phones, tablets, offline devices, or every host owned by the same user. Name at least one concrete denied-test source when practical.

## Ephemeral browser-authenticated join

When the user explicitly requires no auth key, combine Daytona’s documented interactive setup with Tailscale’s documented in-memory ephemeral daemon:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo sh -c 'nohup tailscaled --state=mem: >/tmp/tailscaled.log 2>&1 &'
sudo tailscale up \
  --hostname=<fixed-run-hostname> \
  --advertise-tags=tag:daytona-ephemeral \
  --ssh \
  --accept-routes=false \
  --accept-dns=true
```

The tailnet policy/tag owner must exist first. Isolate the browser gesture:

- the terminal may display the one-time login URL;
- only the human opens it and performs IdP/passkey/2FA/device-approval/Tailnet Lock steps;
- the agent never types credentials or approves security UI;
- do not persist the one-time URL.

Use a short-lived Daytona SSH token for bootstrap. Verify Tailscale status/IP and inbound reachability from an allowed controller before starting desktop validation.

## Private preview distinctions

Keep these surfaces separate:

1. **Direct tailnet noVNC** — preferred for strict no-public-exposure runs: `http://<tailscale-host>:6080/vnc.html` with policy-limited sources.
2. **Daytona standard preview** — SDK `sandbox.get_preview_link(port)` returns a URL plus a separate `x-daytona-preview-token`; authenticated but routed through Daytona’s public proxy. Never print/persist the token.
3. **Daytona signed preview** — CLI `daytona preview-url ...` embeds a bearer token in the URL; exclude it when the manifest prohibits signed/publicly routable links.
4. **Daytona public sandbox preview** — requires `public=true`; prohibit unless separately approved.
5. **Tailscale Funnel** — public ingress; prohibit in a private-tailnet baseline.

Do not claim the CLI offers a separated standard preview URL/token pair when only the SDK does.

## Objective VNC and Computer Use probes

Validation should prove every layer independently:

- SDK `computer_use.start()` succeeds.
- `get_status()` plus per-process status shows `xvfb`, `xfce4`, `x11vnc`, and `novnc` running.
- SDK display info and an in-memory screenshot return coherent dimensions; hash decoded screenshot bytes without writing a file.
- Allowed source: `tailscale ping`, TCP 22, TCP 6080, and `GET /vnc.html` succeed.
- Concrete denied source: TCP 22 and 6080 fail.
- Human opens direct tailnet noVNC and confirms the same desktop.
- Only after separate desktop-mutation approval, perform a benign cursor move and verify the VNC observer sees it.

Starting Computer Use is itself a sandbox process mutation. Screenshots/status are read-only observations after that start. Click/type/drag/key actions remain separate approval gates. Never automate credentials, payments, 2FA, passkeys, or permission dialogs.

## Cleanup must be paired with create

Pre-authorize bounded cleanup with the paid create while still treating destructive fallback as explicit scope:

1. `tailscale logout` inside the sandbox.
2. Stop the sandbox; `auto-delete=0` should destroy it.
3. If it remains, delete only the exact sandbox ID/name—never `--all`.
4. List sandboxes and assert no matching name/run label remains.
5. Assert the Tailscale hostname is absent; if logout failed, allow the documented ephemeral inactivity window, then verify in the Machines page.
6. Reconcile dashboard per-sandbox spend after the documented billing delay.

Cleanup must run after partial installation/login failures too. Do not stop at “stop requested”; verify terminal absence in both Daytona and Tailscale control planes.

## Persistent browser context and credential-bearing state

When a Daytona plan needs browser profiles, cookies, or authenticated context to survive, distinguish four storage contracts rather than treating all persistence as interchangeable:

1. **Stopped or archived same sandbox** — smallest blast radius. A graceful browser exit followed by sandbox stop preserves filesystem-backed profile state while clearing container memory. A stopped container retains local disk and historically incurs disk-only cost; archiving moves the whole filesystem to object storage, frees disk quota, and restores more slowly. VM sandboxes do not support archive because stopping already offloads their filesystem state. Prefer one archived container when reuse of the same environment is sufficient.
2. **Cold snapshot from sandbox** — reusable credential-bearing template. It captures filesystem state from a stopped sandbox, including profile files flushed before stop. Every derived sandbox receives another copy of cookies/tokens, so prohibit automatic fan-out, keep the artifact private, cap concurrency at one unless separately approved, and require an explicit retention/deletion policy.
3. **Hot VM snapshot** — filesystem plus memory. Treat this as a materially higher secret class because browser processes, unlocked key material, and transient tokens may be copied. Require separate VM and memory-snapshot approval; do not infer Linux support from current prose when the pinned backend release supports memory snapshots only for Windows.
4. **Daytona Volume** — only the mounted subtree, not the sandbox root. Volumes are FUSE/S3-backed, slower, nontransactional, and documented as unsuitable for applications requiring database-table/block-storage behavior. Because browser profiles contain database-like state, do not recommend a live browser `user-data-dir` on a shared volume without a dedicated runtime test and explicit concurrency controls. A volume is not whole-filesystem capture.

Daytona does not document browser-cookie-specific semantics. Phrase capture as a filesystem consequence: profile/cookie files located on the captured filesystem are included, provided the browser exits cleanly and flushes them. Do not claim that deleting an archive or snapshot revokes server-side sessions; require account-session revocation or reauthentication where needed.

For zero-sandbox prestates, identify the bootstrap cycle explicitly: a custom snapshot containing authenticated browser state cannot exist until one sandbox has been created and used. A policy that every sandbox must originate from that custom snapshot therefore needs either one approved bootstrap exception or a pre-existing approved artifact. Never hide this exception.

### Stability checks for snapshot-from-sandbox

Audit the current hosted docs/OpenAPI and latest immutable release as separate axes:

- SDK methods whose public names contain `_experimental_` remain experimental even when the REST endpoint is documented without that label.
- Verify whether the installed CLI has a snapshot-from-sandbox verb; image/Dockerfile `snapshot create` is a different operation.
- Compare `includeMemory` support by sandbox class and required state. A hosted API ahead of the latest public release can document behavior that tagged backend source does not implement.
- If current OpenAPI exposes only a generic document version rather than the hosted service build version, do not claim release parity.
- Public pricing may list running CPU/RAM/disk while omitting snapshot/archive object-storage retention. Report omitted retention pricing as unbounded or requiring human confirmation rather than assuming it is free.

The smallest safe default for a one-sandbox browser plan is one non-ephemeral container, no linked children or shared profile volume, graceful browser shutdown, graceful sandbox stop, then archive the exact sandbox. If a literal reusable Daytona Snapshot is mandatory, gate one cold snapshot-from-sandbox as a separate experimental mutation and keep the source sandbox lifecycle explicit.

## Archive, snapshot, ephemeral identity, and HTTPS Serve compatibility

Treat Daytona persistence and Tailscale persistence as independent state machines:

- A Daytona container intended for archive/restore must have `ephemeral=false` and auto-delete disabled. `ephemeral=true` or `autoDeleteInterval=0` deletes it at the stop required for both cold snapshot and archive.
- The supported ordering is `Started -> graceful Stop -> Stopped -> cold snapshot-from-sandbox -> Stopped -> Archive -> Archived`. A cold snapshot requires `Stopped`; it cannot be taken directly from `Archived`. Starting an archive restores the same sandbox, whereas creating from the resulting Snapshot creates a new sandbox of the inherited class.
- Archive and cold snapshot preserve filesystem state, not running processes or container memory. Gracefully close browsers and flush database/profile state before stop. On restore, restart Computer Use and all other process services.
- With `tailscaled --state=mem:`, Daytona archive preserves installed files but not the live node identity. Daemon exit logs out/removes the ephemeral node; restore requires a fresh interactive login and may receive a different node ID, IP, and FQDN. Never promise same-node restore.
- Tailscale HTTPS certificates require a non-empty daemon var root. Bare `--state=mem:` leaves it empty, so pair ephemeral identity with a separately approved writable `--statedir=<dir>` when HTTPS Serve is required. Serve configuration is stored in the in-memory state store and must be reapplied after daemon restart.
- A filesystem-backed `--statedir` can place TLS private keys inside Daytona archives and snapshots. Either remove/classify those files before capture or treat every retained artifact as credential-bearing. CT records remain public even after node or artifact deletion.
- For a pinned explicit exit-node IP, verify the current peer both owns that IP and advertises exit-node capability. A customized tailnet policy must authorize `autogroup:internet`; merely granting connections to the exit-node device does not authorize gateway use. Keep `--exit-node-allow-lan-access=false` and `--accept-routes=false` separate and explicit.

For strict no-preview creation, do not use Daytona CLI `create` at `v0.190.0`: tagged source creates the sandbox and then unconditionally requests the standard web-terminal preview on port `22222`. A later preview failure can leave a successfully created sandbox. The tagged Dashboard create mutation calls the SDK create method without a preview lookup and defaults public preview off, but do not open Dashboard Terminal or VNC afterward. Revalidate the hosted Dashboard build when its API is newer than the latest public release.

The Daytona CLI/API mismatch warning is advisory, asymmetric, once-per-process, and suppressible in structured output. It proves neither schema compatibility nor successful version negotiation. When the hosted API is ahead of the latest public release, use current documented API/Dashboard surfaces, feature-detect experimental calls, and assert every postcondition.

Tagged Daytona Computer Use source should also be checked for listener binding, not just port numbers. At `v0.190.0`, x11vnc defaults to `5901` without an explicit loopback bind/password argument, and noVNC defaults to `6080` with a port-only listen argument while proxying to `localhost:5901`. HTTPS Serve does not close those raw listeners. Require runtime listener inspection plus loopback binding or an independent host/cloud firewall; tailnet grants do not firewall the workload's ordinary cloud interface.

## Approval gates

List later mutations concretely rather than hiding them in prose:

- tailnet policy save
- exact billable create/resources/deadline
- in-sandbox package install and tailnet join
- human browser authentication
- Computer Use input mutations
- destructive logout/stop/delete cleanup
- any exception: signed preview, public flag, Funnel, auth key, GPU/VM/volume, resize, top-up, upgrade, or deadline extension

A generic spend approval does not imply approval for new resource classes, automatic top-up, or public ingress.
