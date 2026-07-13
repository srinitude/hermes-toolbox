# Tailnet-only SSH cutover with deadman rollback

Use this reference when a remote-thin-client plan requires removing public SSH exposure while preserving Tailscale-backed administration.

## Preconditions

- Verify the VPS Tailscale IPv4 address and interface live.
- Prove inbound SSH over the Tailscale hostname from every approved recovery client before changing listeners.
- Identify whether OpenSSH is owned by `ssh.socket`, `ssh.service`, or both. On socket-activated Debian/Ubuntu systems, `sshd_config` notes that listener changes require `systemctl daemon-reload` and `systemctl restart ssh.socket`.
- Confirm an out-of-band provider console exists or use the automatic rollback pattern below.
- Never request, type, log, or replay the administrator's sudo password.

## Smallest coherent mutation

Prefer one dedicated drop-in such as:

```text
/etc/ssh/sshd_config.d/90-<purpose>-tailnet-only.conf
```

with exactly:

```text
ListenAddress <live-tailscale-ipv4>
```

This removes the public listener without rewriting the distribution-owned `sshd_config` or changing unrelated authentication policy. Refuse to overwrite an existing target drop-in; an unknown prestate needs separate review.

## Deadman apply pattern

Prepare a root-run apply script and a separate exact rollback script. The apply script should:

1. Require root and verify the target drop-in is absent.
2. Resolve the operator UID dynamically with `id -u <user>`; never assume UID `1000`.
3. Derive its confirmation marker under `/run/user/<resolved-uid>/`.
4. Resolve and validate the live Tailscale IPv4 address.
5. Install the single drop-in, then run `/usr/sbin/sshd -t`.
6. Reload systemd and restart the owning SSH socket/service.
7. Assert the only TCP/22 listener is `<tailscale-ip>:22`.
8. Wait a short bounded interval for a non-root confirmation marker.
9. On any error, signal, or confirmation timeout, remove only the new drop-in, reload systemd, and restore the SSH listener automatically.
10. Commit only after the marker appears; write a timestamped, credential-free root log.

The non-root orchestrator creates the marker only after all external probes pass. This lets a human enter sudo once while preventing a lost agent/session from leaving the host inaccessible.

## External acceptance

From each approved independent client, run both:

- Two strict-host-key SSH round trips to the Tailscale hostname.
- A direct TCP probe to the VPS public IP on port 22, which must fail.

Also verify locally:

- the listener is only the Tailscale IP;
- `ssh.socket`/`ssh.service` are active as applicable;
- the durable Herdr session remains compatible;
- no unrelated public service ports changed.

Only then create the confirmation marker. Re-read the root log and drop-in afterward to prove the cutover committed rather than timing out and rolling back.

## Rollback

The rollback script removes only the dedicated drop-in, validates `sshd`, reloads systemd, restarts the owning socket/service, and records resulting listeners. Keep its exact path and checksum in the mutation ledger.

## Pitfalls

- A locally successful private SSH probe does not prove public TCP/22 is closed; probe the public IP from outside the VPS.
- A firewall can be active while a wildcard listener remains externally reachable. Verify effective reachability, not only configuration.
- Hard-coded UIDs make otherwise safe scripts abort or target the wrong runtime directory.
- A user saying the command is "running" is not evidence that sudo completed; poll the listener and treat unchanged state as no mutation.
- Do not confirm the deadman timer until every approved recovery path passes.
