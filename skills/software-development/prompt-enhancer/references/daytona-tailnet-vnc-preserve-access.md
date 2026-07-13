# Ephemeral Sandbox VNC on a Permissive Tailnet

Use this pattern when a cloud sandbox must join a Tailscale network and expose a private browser desktop while existing user-owned devices retain their current unrestricted mutual access.

## Core policy transformation

Tailscale grants are additive. A narrow rule cannot constrain a node while a wildcard rule such as `src: ["*"]`, `dst: ["*"]`, `ip: ["*"]` remains active. Replace the wildcard rather than supplementing it.

When every pre-existing device is direct-member-owned and untagged, preserve their behavior with:

```hujson
{
  "tagOwners": {
    "tag:ephemeral-sandbox": ["autogroup:admin"],
  },
  "hosts": {
    "control-host": "<TAILSCALE_IP>",
  },
  "grants": [
    {
      "src": ["autogroup:member"],
      "dst": ["autogroup:member"],
      "ip": ["*"],
    },
    {
      "src": ["autogroup:member"],
      "dst": ["tag:ephemeral-sandbox"],
      "ip": ["tcp:443"],
    },
    {
      "src": ["tag:ephemeral-sandbox"],
      "dst": ["control-host"],
      "ip": ["tcp:22"],
    },
  ],
}
```

Merge this into the exported active policy. Preserve unrelated `ssh`, `sshTests`, `nodeAttrs`, `autoApprovers`, groups, postures, IP sets, network options, comments, host aliases, and tag owners.

Treat `autogroup:member` in the inbound Serve grant as a template choice, not a default entitlement. If only named controller devices are approved, create exact host aliases for those controllers and use them as `src`; keep `autogroup:member → autogroup:member → *` solely for preserving existing direct-member behavior. Inventory aliases used only by static policy tests do not contact those devices.

## Why the selectors work

- Applying a tag removes user identity from the tagged node.
- `autogroup:member` covers direct-member user identities, not tagged service devices.
- Existing direct-member devices therefore retain full mutual access while the tagged sandbox receives only explicit grants.
- Stop and revise the policy if any pre-existing device is tagged, shared, subnet-only, or otherwise outside `autogroup:member`. Inventory offline devices in the admin console; CLI peer output alone is insufficient.

## Private VNC publication

Keep noVNC on loopback and publish it with Tailscale Serve. Choose the front door explicitly:

```bash
# Tailnet HTTPS; requires accepting Certificate Transparency hostname disclosure.
tailscale serve --bg --https=443 http://127.0.0.1:6080

# Tailnet-private HTTP; still encrypted in transit by Tailscale/WireGuard and avoids CT.
tailscale serve --bg --http=80 http://127.0.0.1:6080
```

Validate installed CLI syntax first. Require:

- The exact approved Serve port succeeds only from approved tailnet controllers.
- Raw TCP/5900, TCP/5901, and TCP/6080 fail from the tailnet.
- `tailscale serve status --json` targets loopback.
- `tailscale funnel status` shows no public exposure.
- No public or signed cloud preview exists.
- A real browser establishes the noVNC WebSocket and renders the desktop.

Tailscale Serve is preferable to rebinding noVNC to `0.0.0.0`: it keeps the backend private and applies tailnet policy to the front door. Tailnet-private HTTP is the privacy-minimizing choice when avoiding public hostname disclosure is the primary criterion, but require strict Host allowlisting. For a retained credential-bearing browser profile, prefer HTTPS when browser-recognized endpoint authentication, secure WebSockets, and DNS-rebinding resistance outweigh permanent public CT disclosure of an opaque hostname. This inbound Serve choice is orthogonal to how destination websites classify outbound browser requests; CT does not improve or harm outbound reputation.

Do not assume a cloud provider's built-in VNC/Computer Use action binds raw listeners safely. Inspect the current implementation and witness a no-listener RED before startup. If the provider defaults x11vnc/noVNC to wildcard interfaces or omits authentication, do not start it and “fix it afterward”; there is an exposure window. Prefer supervised processes with explicit loopback binding, such as Xvfb with `-nolisten tcp`, x11vnc with `-localhost`, and websockify bound to `127.0.0.1`. Validate the installed flags and web root before running, then prove ports `5900`, `5901`, and `6080` are loopback-only before joining Tailscale. Dashboard Terminal/VNC surfaces and private Tailscale Serve are separate paths; strict no-preview work must avoid the former.

For ephemeral Tailscale identity plus HTTPS Serve, bare `tailscaled --state=mem:` can be insufficient because certificate support needs a writable var root. Use a volatile mode-`0700` directory such as `/dev/shm/tailscale-varroot` with `--state=mem: --statedir=<volatile-dir>`, then remove it before archive/snapshot capture. Serve configuration and certificates must be recreated after daemon restart. Never capture the TLS private key merely to make restoration convenient.

## Exit-node egress is a separate decision

VNC transport and sandbox Internet egress are orthogonal. To let a tagged sandbox make ordinary browser web requests through configured exit nodes, add a least-privilege grant:

```hujson
{
  "src": ["tag:ephemeral-sandbox"],
  "dst": ["autogroup:internet"],
  "ip": ["tcp:80", "tcp:443"],
}
```

TCP/80 supports ordinary redirects to HTTPS; TCP/443 carries HTTPS. Add `udp:443` only when HTTP/3 is a current acceptance requirement. Use `ip: ["*"]` only when the present workload demonstrably requires unrestricted Internet protocols—do not broaden browser egress by default. Tailscale-provided exit-node DNS is a separate client behavior; validate name resolution in the real sandbox rather than opening arbitrary public UDP speculatively.

Do not grant access to the exit-node device itself; that permits connections to the machine, not use of it as an Internet gateway. Configure the sandbox client with `--exit-node=<name-or-IP>` or the currently supported automatic selector and keep `--exit-node-allow-lan-access=false` unless local-LAN reachability is an explicit requirement.

For browser profiles whose sessions may react to source-IP or location changes, prefer a pinned, stable exit node and fail closed when it is unavailable. Use automatic selection only when availability is more important than deterministic egress identity. A suggested/automatic exit node can change the website-visible public IP; prove the selected mode with a non-secret equality comparison rather than printing public IPs into evidence. Keep macOS exit nodes awake, and treat ISP-address stability as an assumption to observe, not a guarantee.

## Policy TDD

Before saving the policy, add built-in policy tests:

1. Positive tests for representative ports between every pre-existing member-host alias.
2. Separate preservation tests for TCP, UDP, ICMPv4, and ICMPv6. IPv4-only aliases do not prove IPv6 preservation; add exact IPv6 aliases or literals and a distinct matrix. A test with no `proto` only proves that either TCP or UDP is allowed, not both.
3. Approved-controller-to-sandbox acceptance on the selected Serve port and denial on `22`, `80`, `5900`, `5901`, `6080`, the unselected Serve transport port, and a high unrelated port. Every non-approved member needs the full denial set, not merely denial of the approved Serve port.
4. Sandbox-to-control-host acceptance on the required port and denial on other control-host ports.
5. If exit-node web egress is required, positive `autogroup:internet` tests for TCP/80 and TCP/443 plus negative public UDP, ICMP, DNS 53, raw-VNC, SSH, and unrelated high TCP-port tests. Do not use a broad `ip: ["*"]` merely to make DNS or browser acceptance easy.
6. Sandbox denial to representative ports on every other pre-existing host.

Witness RED with an intentionally incomplete candidate in the editor without saving. Complete the grants and require all tests GREEN before the human Save gesture. Immediately re-export the active policy after Save and prove it canonically equals the approved candidate using a deterministic HuJSON standardizer or exact Admin revision identifier; a local candidate hash plus broad live probes is not proof that the saved policy is identical.

## Human and secret gates

- Export and hash the exact active policy before mutation; keep it private and mode `0600`.
- Present the exact semantic diff and candidate hash for approval.
- For no-auth-key ephemeral identity, start `tailscaled --state=mem:` with an approved volatile certificate `--statedir` when HTTPS is required, then use ordinary interactive login with the approved tag and hostname. Do not search for or require an `--ephemeral` flag on `tailscale up` or `tailscale login`.
- Keep browser-login URLs in the human-controlled first-party channel that initiated authentication; never replay them through the agent. Scope “no secret in panes/prompts” to model-facing and non-approved surfaces: the initiating human-local terminal/UI must be allowed to display its own one-time login URL.
- When cloud Dashboard Terminal/VNC surfaces are prohibited because they create preview paths, define an executable human-only alternative before claiming authentication is possible. For Daytona, use an approved computer's **native local terminal** with a locally authenticated first-party CLI and `daytona ssh <recorded-sandbox-name> --expires <bounded-minutes>`. The Daytona API key, generated SSH token, Tailscale URL, and login code remain local to the human. Do not route this flow through Hermes, a remote control pane, SDK/MCP output, or Dashboard Terminal/VNC.
- Do not describe a terminal-to-local-browser authentication flow as “same process” or “same UI.” Name both surfaces explicitly: the native terminal generates the URL and the human opens it in a local browser. Audit every normative summary/open-gate sentence for stale wording after selecting the channel.
- Browser cookies and tokens may persist only when the approved private archive/snapshot is explicitly classified as a credential-bearing secret store. Do not make an absolute “no credential in files” claim while intentionally retaining a browser profile.
- If the human requires an ephemeral auth key instead, treat that as a separate no-echo credential gate; never handle the key through the agent.
- HTTPS Serve certificates publish the randomized machine FQDN through Certificate Transparency. Place a recorded approval check immediately before the first `serve --https`, certificate, or HTTPS-enable command; a risk note or end-of-plan gate is not operational protection.
- Keep policy approval, paid sandbox creation, Tailscale package/root mutation, custom VNC process start, human credential entry, persistent-snapshot retention, and visual VNC acceptance as separate gates.

## Persistent browser context and snapshots

Treat environment reproducibility, exact-session continuity, and reusable snapshots as different contracts:

- Start the bootstrap sandbox from a class-compatible base snapshot.
- Keep browser profiles, cookies, and request context on the sandbox's normal local filesystem during the run.
- When the goal is to resume one trusted browser identity, prefer stopping and archiving the exact container sandbox after graceful browser shutdown. This retains one filesystem copy, uses stable CLI/API lifecycle operations, and avoids cloning replayable session state.
- When a literal reusable snapshot is mandatory, close the browser cleanly, log Tailscale out, reset Serve, stop the in-memory daemon, scrub transient state, stop the sandbox, and capture exactly one cold whole-filesystem snapshot. Never fan it out; allow at most one derived sandbox at a time.
- For a VM, choose cold filesystem or hot filesystem-plus-memory capture explicitly; do not retain memory merely because the platform supports it. Avoid hot snapshots for authenticated browsers because they can retain unlocked keys and in-memory tokens.
- Keep `tailscaled --state=mem:` so archive/snapshot persistence cannot silently retain the tailnet identity.
- Treat an archive or snapshot containing browser cookies as a secret-bearing private artifact with an exact ID, allowed site/account classes, retention deadline, deletion owner, and session-revocation plan.

A zero-sandbox prestate makes “every sandbox originates from a custom snapshot containing its own cookies” circular. Record one bootstrap sandbox as an explicit exception. If snapshot restoration must be proved, change the resource bound from “one sandbox total” to “one concurrent, at most two sequential,” and recalculate the paid cap before creation.

Do not assume a generic FUSE/object-store volume is a safe Chromium profile backend: browser profiles use locking and transactional databases, while shared volumes may be slower and non-transactional. A volume can hold exported artifacts, but use the normal local profile unless a real restore test proves the mounted profile contract.

Snapshot-from-sandbox availability is time-sensitive. Check the live Dashboard, installed CLI, current SDK/OpenAPI, and the pinned client release separately; if only an experimental SDK/REST method exists, gate it separately rather than representing it as a stable CLI capability. A list-snapshots call does not prove snapshot-from-sandbox support. Inventory pre-existing custom snapshot IDs before creation, then scope “exactly one snapshot” to the delta derived from the recorded source sandbox ID; an organization can already contain unrelated snapshots.

For Daytona container snapshots, do not confuse `daytona snapshot create` with snapshot-from-sandbox: the CLI command builds from an image or Dockerfile. A cold capture from an existing sandbox currently requires the experimental REST/SDK surface. Preserve the supported order exactly: `Started → graceful browser/process shutdown → Stop → Stopped → cold snapshot(includeMemory=false) → wait complete/source still Stopped → Archive → Archived`. A snapshot is a reusable template for creating a new sandbox; starting an archive restores the same sandbox. Set `ephemeral=false` and disable auto-delete or the required Stop can destroy the source. Daytona container auto-archive has no disabled state: `0` means the maximum 30-day interval, while omission uses the documented default. Do not confuse this with auto-delete, where `-1` disables deletion and `0` deletes immediately after Stop. When creating from a fixed resource snapshot such as `daytona-small`, do not add resource overrides if the current API rejects them; select the snapshot and verify its resulting class/resources instead.

For a literal snapshot, prove persistence first with a harmless non-secret cookie/profile marker. Prefer restoring and re-archiving the same source sandbox when exact-session continuity is the primary contract; do not instantiate the recovery snapshot merely to verify it unless a second sequential sandbox is explicitly approved. Archive restore preserves filesystem state, not memory, processes, Tailscale identity/IP/FQDN, Serve configuration, or TLS certificates. A memory-state Tailscale node therefore requires a fresh human login after restore.

Give every retained archive and snapshot the same explicit retention deadline when they contain the same browser state, name the deletion owner, and require a verifiable reminder or deletion-control channel before creation. Split reminder evidence into two stages: before creation, approve the owner, deadline, and notification channel; after the platform returns exact archive/snapshot IDs, immediately update and verify the reminder with those IDs before declaring completion. Never require nonexistent future IDs in a pre-create gate. Merely writing a deadline into a manifest does not enforce it. In a local-only TUI with a stopped gateway, a local cron that cannot notify the user is not acceptable reminder evidence. Distinguish archive billing from snapshot-storage billing and validate both against current first-party terms; do not assume they share one storage rate.

## Recipient-side legitimacy and anti-abuse signals

When the user wants ordinary, legitimate browser traffic—not bot-control evasion—optimize for consistency and transparency rather than “stealth”:

- Prefer one resumed/archived sandbox and one browser profile over reusable snapshot clones.
- Pin one stable, human-approved exit node when account/device continuity matters; automatic exit-node failover trades continuity for availability and can change the website-visible IP or location.
- Use a normal visible browser with genuine headers and TLS behavior. Do not add fingerprint spoofing, stealth plugins, header rewriting, or challenge bypasses.
- Keep logins, MFA, consent, payments, and challenges human-operated. Use conservative rates, ordinary navigation, and official APIs when available.
- Never promise that a residential or home exit IP makes automation look human. Receiving services can combine IP/network reputation, TLS fingerprints, header order, JavaScript/browser signals, cookies, trusted-device history, request volume, and behavior. Commercial residential-proxy ranges may themselves be risk signals.
- Treat CT and inbound noVNC HTTP/HTTPS as unrelated to outbound reputation: destination sites see the browser's outbound TLS characteristics and the exit node's public IP, not the private Serve certificate.

If the task is an identified crawler or agent rather than user-driven browsing, prefer honest identification and site-authorized/verified-bot mechanisms over impersonating a human browser. Respect terms, robots directives, and rate limits.

## Acceptance and cleanup

Use one bounded concurrently running sandbox with automatic stop and an external hard deadline. Prove:

- exact tag identity and no user identity;
- sandbox reaches only the required control-host port inside the tailnet;
- approved controllers reach only the Serve port;
- Internet traffic uses the selected exit-node mode when required;
- existing-member behavior remains equivalent before and after policy application;
- public-negative access;
- one harmless GUI interaction with no credentials, payments, 2FA, passkeys, or permission dialogs;
- persistence according to the approved artifact model: restore/re-archive the same sandbox for exact-session continuity, or instantiate a recovery snapshot only when a second sequential sandbox and its spend are explicitly approved.

For an ephemeral-only run, cleanup in exact-ID order and verify zero sandbox/node/Serve/Funnel residue. For an explicitly persistent run, define the terminal invariant by artifact class: zero **running** sandboxes, zero tailnet nodes, zero Serve/Funnel handlers, exactly the allowlisted archived source sandbox when same-instance continuity is required, and exactly the allowlisted private recovery snapshot IDs. Prove persistence by restoring and re-archiving the same source sandbox when possible; do not create a second derived sandbox merely to verify a marker unless the paid/concurrency gate explicitly allows it. Record every intentional archive/snapshot as residue-by-design; never claim total zero residue. Calculate cost from current first-party pricing and elapsed active time rather than delayed billing telemetry, and separately gate any unpriced retention class.

## Pitfalls

- A specific grant never overrides a broader grant; capabilities are unioned.
- Do not assume visible online peers are the full preservation set.
- Do not tag user devices merely to simplify policy.
- `tailscale funnel status` can display configured Serve handlers marked `tailnet only`; non-empty output alone is not public exposure. Classify exposure from explicit current markers and corroborate with Serve/Funnel configuration.
- Do not treat dashboard VNC success as proof that the tailnet-private path works; test the private Serve URL and WebSocket.
- For public-negative probes, do not assume an outbound IP-discovery service returns the host's inbound public interface address. Derive the configured interface/provider address first. If TCP/22 answers with a host key that does not match the control host, classify it as a distinct provider/NAT endpoint rather than falsely attributing it to the control host.
- Do not use a live probe against an excluded machine merely to prove preservation; static policy tests can cover it.
- Label every human command with its execution surface (`Mac native terminal`, `VPS shell`, or `sandbox shell`). A message typed from a Mac does not prove Hermes tools or pasted commands are running there. Before host-key enrollment or local-file mutation, verify the target host explicitly and stop if the shell identity is wrong.
- A host-key pinning packet belongs on the initiating client only. If it is accidentally run on the server, inspect whether `known_hosts` actually changed before proposing cleanup; do not delete an old entry or infer damage from the attempted command alone.
- Listing snapshots can expose organization metadata and may refresh server-side `lastUsedAt` fields. Query only the minimum scoped snapshot information needed for the manifest, and never treat a list operation as proof that snapshot-from-sandbox is supported.
- Do not identify an exit node by guessed DNS normalization of its display name. In live `tailscale status --json`, verify the exact peer by Tailscale IP, `Online`, `ExitNodeOption`, and advertised default routes (`0.0.0.0/0`, `::/0`); display hostnames can contain capitalization, punctuation, or Unicode that differs from a CLI-safe label. Pin the verified IP in the runtime packet when deterministic egress matters.
- A Daytona CLI/API version-mismatch warning is not proof that a matching public CLI release exists. Check the official release feed and installed help independently. If the API is ahead of the latest public CLI, do not invent or install an unavailable version; keep read-only compatible probes, use the reviewed Dashboard/API path for gated operations, and classify unsupported commands separately.
- When reconciling a saved plan after persistence or egress requirements change, preserve the original plan path, remove contradictory ephemeral/zero-residue language throughout, update dependent evidence hashes only after the final plan edit, and run a semantic verifier for stale aliases, grant counts, lifecycle invariants, and hashes. A new top-level paragraph that merely “supersedes” contradictory later tasks is not a coherent plan.
