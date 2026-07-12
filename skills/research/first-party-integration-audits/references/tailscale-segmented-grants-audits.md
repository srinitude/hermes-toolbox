# Tailscale segmented-grants audit notes

Use this reference for read-only audits that replace a default allow-all tailnet policy with a narrow tagged-workload segment while preserving existing user-owned devices.

Revalidate all live documentation and installed CLI help before reuse.

## Establish active policy without peer probes

- Hash the saved plan or candidate first.
- `tailscale status --json` is useful for visible node ownership, tags, sharing metadata, routes, and online state, but it cannot prove the complete admin-console inventory.
- `tailscale debug netmap` can expose the locally compiled `PacketFilter`, `PacketFilterRules`, and `SSHPolicy` without sending packets to peers. Reduce output in the pipe; do not dump keys or the full netmap.
- A compiled netmap can show consistency with allow-all semantics, but cannot reconstruct exact HuJSON, comments, tests, tag owners, auto-approvers, postures, or other top-level sections. Require an exact admin-console export and Machines-page comparison before finalizing a merge.
- Reading local control-plane metadata is not a live peer probe. Still record explicitly that no ping, TCP, SSH, or application request was sent to excluded machines.

## Grant semantics that matter

- Grants are additive. A narrow rule cannot override a broad wildcard. Remove every broad grant or legacy ACL whose union would cover the tagged workload.
- Applying a tag removes user identity. Therefore a tagged workload does not match user-owned `autogroup:member` devices.
- `autogroup:member -> autogroup:member -> ip:["*"]` preserves TCP, UDP, and ICMP among direct-member-owned devices, but does not preserve tagged, shared, subnet-only, or other exceptional nodes.
- Host aliases are valid source and destination selectors and are safer than a broad member selector for workload-controller access. A user selector can unintentionally include every device owned by that user, including phones, tablets, and excluded hosts.
- Tailnet grants constrain tailnet and approved-route traffic; they do not firewall a cloud workload's ordinary internet/LAN interface. Phrase isolation claims accordingly.
- Exit-node internet access is a separate `autogroup:internet` destination. Add it only when the active policy and preservation scope prove it is required.

## Policy-test structure

Tailscale policy tests have a singular `src` and optional singular `proto`.

- If `proto` is omitted, the test checks whether either TCP or UDP is allowed. It does not prove both.
- For an `ip:["*"]` preservation claim, emit separate tests for TCP, UDP, and ICMP. ICMP destinations use port `0`.
- `accept` and `deny` targets must be specific entities; no wildcard or CIDR destinations are allowed in tests.
- Add aliases for every concrete host named in tests, or use another documented specific identity. Do not claim a one-alias semantic diff while requiring tests for many aliases.
- Test every existing source class, tagged-workload ingress, tagged-workload egress, and a representative public destination to detect accidental exit-node access.
- Negative tests are compile-time policy assertions, not runtime reachability tests. They are appropriate evidence for excluded or offline devices.

Recommended matrix:

1. Each preserved current host as `src`, with TCP representative ports, UDP representative ports, and ICMP `:0` accepted to the preserved member identity set.
2. Each approved controller host to the workload tag: accept only intended TCP ports; explicitly deny unrelated TCP, UDP, and ICMP.
3. Each non-controller preserved host to the workload tag: deny intended and representative unrelated ports/protocols.
4. Workload tag to its one allowed destination: accept only the exact protocol/port; deny other ports on that host, representative ports on every other current host, UDP, ICMP, and a documentation-reserved public address.

## Serve, Funnel, HTTPS, VNC, and ephemeral nodes

- Serve access is governed by tailnet access controls and can reverse-proxy a loopback HTTP backend.
- HTTPS certificates publish the full machine FQDN in Certificate Transparency. Require a non-sensitive hostname and explicit disclosure acknowledgement; private reachability does not imply a private hostname.
- `tailscale funnel status` may display Serve configuration labeled `tailnet only` rather than return empty. Assert the explicit private classification and absence of a public listener, not empty output.
- Do not invent an `--ephemeral` flag for `tailscale up` or `tailscale login`. First-party Tailscale supports no-auth-key ephemeral nodes by starting `tailscaled --state=mem:` and then using the normal interactive authentication flow.
- Traditional OpenSSH over Tailscale is governed by network grants. Tailscale SSH is a separate feature and policy layer; a tagged workload cannot use Tailscale SSH to enter a user-owned untagged device, so a tag-to-member TCP/22 exception must explicitly require ordinary OpenSSH and keep the workload's `--ssh` disabled.
- A tailnet grant does not firewall a workload's ordinary cloud/LAN interface. For VNC/noVNC, prove the actual listener binds only to the Tailscale IP or enforce an independent host/cloud firewall; a correct `tag -> tcp:5901/6080` policy does not make a `0.0.0.0` listener private.
- Resolve “VNC” before writing the grant: native x11vnc commonly uses TCP/5901, while browser noVNC commonly uses TCP/6080. Open one, not both, unless both clients are explicitly required.
- `tcp:443` is only an L3/L4 restriction: it does not prove TLS or HTTP, and it intentionally excludes QUIC/HTTP3 on UDP/443. Strict HTTPS semantics require an L7 egress proxy or firewall.
- Exit-node DNS normally uses the exit node as resolver; public global resolvers may be upgraded to DoH on TCP/443. Recheck tailnet DNS settings before assuming TCP/443 alone suffices, because custom nameservers marked “Use with exit node” can require additional UDP/TCP 53 access.

## Auto exit-node selection, fail-closed routing, and `via`

- Current CLI syntax is `tailscale up --exit-node=auto:any` or `tailscale set --exit-node=auto:any`. It tracks the recommended exit node and re-evaluates as available nodes, network conditions, or policy change.
- Do not infer fail-closed behavior only from CLI prose. Pin a stable Tailscale release and inspect `ipn/prefs.go`: in v1.98.8, `AutoExitNode` installs a blackhole route until an exit node is selected, preventing ordinary local-network egress while auto-selection is unresolved. Keep this source-confirmed axis separate from the public support contract.
- For fresh Linux joins, set `--exit-node=auto:any` during `tailscale up` so unresolved selection is fail-closed, then reapply it with `tailscale set --exit-node=auto:any` after the node reaches `Running`; this avoids first-join selection timing races without intentionally opening a direct-egress interval.
- Verify `tailscale debug prefs` reports `AutoExitNode: "any"`, `ExitNodeAllowLANAccess: false`, and the intended DNS/route flags. Verify exactly one peer has `ExitNode: true` in `tailscale status --json`, then prove external egress identity or inspect exit-node flow logs. Policy tests cannot prove selected path or failover.
- The grant `dst:["autogroup:internet"]` authorizes use of exit nodes; granting access to the exit-node device itself only authorizes direct connections to that device.
- `via` accepts tags only. If the available exit nodes are untagged user-owned devices, adding `via` cannot select them without retagging; retagging removes user identity and can break the direct-member preservation invariant.
- Omitting `via` permits any configured exit node, including future ones. If strict exit-node allowlisting is required for a Linux tagged workload, prefer dedicated tagged exit nodes and `via:["tag:<exit-pool>"]`. Do not retrofit infrastructure tags onto personal member devices merely to satisfy `via`.
- `AllowedSuggestedExitNodes` is a system-policy allowlist, but its documented client support is Windows, macOS, and iOS; do not propose it as the Linux sandbox control unless live docs add Linux support.
- Keep `--exit-node-allow-lan-access=false` and `--accept-routes=false` explicit. Do not enable shields-up on a workload that must accept policy-authorized VNC: shields-up overrides the distributed packet filter and blocks all incoming connections.

## Stale-candidate handling

When multiple saved policy artifacts exist:

- Hash and classify each as active export, rollback representation, candidate, or unknown.
- Compare their semantics against the current request.
- Never treat a saved candidate as active merely because it is newer or more detailed.
- Flag old policies that expose raw service ports, preserve unrelated exit-node access, or use synthetic probe identities when the new design requires HTTPS-only ingress and complete current-host coverage.

## Read-only audit record

Return:

- immutable plan hash and local client version
- visible inventory and confidence limits
- compiled-policy observation versus exact-policy proof
- concrete blockers and exact corrected grant/test matrix
- first-party sources
- commands/read surfaces used
- excluded-device no-contact statement
- files modified, plus any tool-managed web caches created automatically
