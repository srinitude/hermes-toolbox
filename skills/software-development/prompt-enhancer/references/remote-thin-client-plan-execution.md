# Remote Thin-Client Plan Execution

Use this reference when the user interacts through a local thin client while Hermes, terminal tools, or computer-use run on another host.

## Separate the execution loci

Record these independently before issuing host-specific commands:

1. **Message origin** — where the user typed the message.
2. **UI renderer** — where the terminal/browser window is displayed.
3. **Terminal backend** — where shell and file tools execute.
4. **Computer-use backend** — which desktop `computer_use` can actually inspect or control.

A local message or native renderer does not prove local tool execution. A remote Herdr client can render a VPS session while every Hermes tool still runs on the VPS.

## Verification sequence

1. Run a read-only terminal host probe (`uname`, hostname, cwd).
2. Inspect the computer-use app/process inventory without mutation.
3. Inspect the owning thin-client/server status through first-party CLI output.
4. Record which required facts are available locally, remotely, or not at all.
5. Treat network reachability, SSH authentication, GUI access, and local command execution as separate capabilities.

Do not claim a local-device probe passed because the remote server, encrypted network path, or thin client is healthy.

## Bidirectional SSH trust and account proof

For a thin client that SSHes to a control host while the control host also manages the client, validate each direction independently:

1. Discover the server host key, compare its fingerprint with an out-of-band value, and only then persist it. Avoid `StrictHostKeyChecking=accept-new` unless an immediate independent fingerprint comparison follows; remove the entry on mismatch.
2. Confirm the intended remote account with `ssh -G`, the device's native account probe, or an explicit user statement. Adding a public key to one account does not authorize another.
3. Verify the exact public key is present in that account's `authorized_keys`, with `~/.ssh` mode `0700` and `authorized_keys` mode `0600`.
4. Run a non-interactive `BatchMode=yes` command in each required direction. A verified host key proves identity, not user authentication.
5. For remote wrapper scripts, record the prestate, refuse to overwrite an unknown file, write a fixed argv launcher rather than a generated shell fragment, run a shell syntax check, hash the final file, and perform a bounded real attach that proves server survival after detach.
6. When the user explicitly removes a host from scope, record the approved exception and remove that host from acceptance, rollout, rollback, and blocker lists. Do not keep treating it as a failed required target.

## Safe bootstrap when local execution is absent

- Prefer a short user-run local probe with bounded, non-secret output.
- Never request or type the user's password.
- Do not install a broad shell key merely to avoid a local probe.
- If the governing plan permits a restricted bootstrap identity, bind it to one forced command, no PTY, no forwarding, a verified host key, and explicit rollback.
- Verify the SSH host-key fingerprint out of band before persistent trust; a key scan alone is discovery, not identity proof.
- Preserve every plan gate. A user's request to “try it here” authorizes read-only diagnosis, not permission/security/UI changes or later gated mutations.

## User-visible delivery

Tool results may be hidden in the active interface. When the user asks to see an artifact or says they cannot see prior output, put the requested text in the assistant's user-visible response or provide an explicit attachment. For large verbatim artifacts, use lossless user-visible chunks or an exact attachment; never claim that hidden tool output was delivered.

## Completion evidence

Report:

- each execution locus,
- connectivity versus authenticated access,
- host-key verification state,
- exact completed gate/task boundary,
- remaining human action,
- files or settings actually changed,
- confirmation that hidden tool output was not used as the deliverable.
