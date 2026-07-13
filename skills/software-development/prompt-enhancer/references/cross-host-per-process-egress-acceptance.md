# Cross-host per-process egress acceptance

Use this pattern when a remote control host must route only selected TCP traffic through a specifically approved client host over SSH SOCKS, while leaving ordinary host egress unchanged.

## Gate and sequencing boundary

- Finish or explicitly decline persistent preview/Serve gates before starting the egress slice.
- Treat per-process SOCKS and system-wide exit-node routing as separate decisions. A passing SOCKS test should normally make the exit-node gate `not needed` unless a named workload demonstrably cannot use the proxy.
- Do not reuse Cua, browser-MCP, preview, generic-shell, or other capability keys.

## Safe SSH identity staging

1. Capture whether the SSH config, known-host entry, and egress keypair already exist; hash existing files and create exact rollback copies before mutation.
2. Resolve the approved peer from live private-network state; do not infer authenticated shell access from reachability.
3. Fetch the peer SSH host key and compare its SHA-256 fingerprint with an independently observed fingerprint before adding it to `known_hosts`.
4. Generate a dedicated Ed25519 egress key with private mode `0600`; keep its public key and comment capability-specific.
5. Create a strict SSH alias with the exact peer/user/key, `IdentitiesOnly yes`, `BatchMode yes`, `RequestTTY no`, strict host-key checking, `ExitOnForwardFailure yes`, `ControlMaster no`, and no agent forwarding.
6. Do **not** set `ClearAllForwardings yes` on an alias that must accept command-line `-D`; it can clear the dynamic forward being tested.

## Mac authorized-key restriction

A dynamic-forward key needs TCP forwarding but not shell authority. Use an independently reviewed equivalent of:

```text
command="/usr/bin/false",restrict,port-forwarding,from="<exact-control-host-private-IP>" ssh-ed25519 <public-key> <capability-comment>
```

The forced false command blocks requested shell/command sessions; `restrict` disables broad SSH features; `port-forwarding` intentionally re-enables TCP forwarding; `from` binds the credential to the exact control host. Verify this contract against the installed OpenSSH version before use.

Install it from a genuinely local terminal with an idempotent comment check. Back up an existing `authorized_keys`, preserve mode `0600`, and never ask the user to return its contents.

## RED before GREEN

Before Mac installation, run the exact dynamic-forward command and require:

- authentication failure;
- nonzero exit;
- no local SOCKS listener.

This proves the later success depends on the intended Mac authorization rather than an unrelated credential.

## Real acceptance after installation

1. Prove shell, command, PTY, agent forwarding, and unrelated forwarding attempts fail.
2. Start `ssh -NT -D 127.0.0.1:<port> <exact-egress-alias>` and prove the listener is loopback-only.
3. Compare direct and `socks5h` public-IP results without publishing raw addresses; hashes or equality/difference booleans are sufficient.
4. Use `socks5h`, not `socks5`, when remote DNS resolution is part of the claim.
5. Exercise one disposable real HTTP client/browser through the proxy and show an unconfigured control process still uses normal egress.
6. Record that SOCKS is TCP-only and does not provide transparent UDP/QUIC routing.
7. Stop SSH, prove the listener disappears, and prove proxied requests fail while ordinary direct egress still works.
8. Update fleet health only after objective pass evidence.

## Rollback

- Remove the capability-commented Mac `authorized_keys` line or restore the exact backup.
- Remove the dedicated control-host keypair and SSH alias only if they were created by this slice.
- Restore `known_hosts` from its pre-state only when no concurrent legitimate edits occurred.
- Confirm no SOCKS listener, control socket, or background SSH process remains.
