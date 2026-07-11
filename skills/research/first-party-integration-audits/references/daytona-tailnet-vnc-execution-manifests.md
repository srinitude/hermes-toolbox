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