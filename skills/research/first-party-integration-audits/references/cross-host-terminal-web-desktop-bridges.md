# Cross-Host Terminal, Web, and Desktop-Control Bridges

Use this reference when one host runs the agent/process plane while another host supplies the native terminal, browser, or graphical desktop.

## Start by separating traffic directions

Never treat “remote access,” “forward all web traffic,” or “use the local browser” as one feature. Audit each lane independently:

| Lane | Typical direction | Primitive to prove |
|---|---|---|
| Native terminal UI | local client → remote process host | product thin-client protocol over SSH |
| Local browser preview | local browser → remote loopback service | SSH LocalForward or private reverse proxy |
| Remote access to a local service | remote host → local loopback service | SSH forwarding over a private network |
| Selected remote egress through local network | remote process → local network → internet | SSH DynamicForward/SOCKS |
| System-wide remote egress | remote host → local exit node → internet | VPN exit-node/default-route primitive |
| Remote agent controlling local desktop | remote agent → local GUI driver | authenticated MCP/stdio or equivalent desktop-control protocol |
| Public collaborator ingress | internet → remote/local service | separately approved public ingress; never conflate with private preview |

For each lane record: initiator, listener, bind address, transport, authentication, DNS side, host that opens the final connection, persistence owner, and rollback.

## Prove where `localhost` and URL opening resolve

`127.0.0.1` always belongs to the process interpreting it. Explicitly name whether a callback or preview URL is interpreted by the local browser, remote service, SSH client, SSH server, or proxy.

For terminal-host products, inspect source or public docs to determine where URL activation runs. A remote pane can render a URL while the local thin client invokes the local OS browser. This is useful only when a matching tunnel or private endpoint exists; URL opening is not itself port forwarding.

For OAuth loopback, preserve the exact callback port whenever possible:

```text
local browser 127.0.0.1:P → SSH LocalForward → remote process 127.0.0.1:P
```

Test cookies, Host, Origin, CORS, CSRF, WebSocket, SSE, and hot-reload behavior separately. A private HTTPS reverse proxy changes hostname and scheme even when it reaches the same remote loopback service.

## Do not hide missing network primitives behind a terminal product

A terminal thin client may reuse SSH without exposing arbitrary TCP forwarding as a product primitive. Inspect whether it:

- includes user SSH configuration
- launches several probe/bootstrap connections
- clears configured forwards
- owns a private control socket
- exposes any supported LocalForward/RemoteForward/DynamicForward surface

If generic forwarding is absent, state that SSH/VPN is the data plane and the terminal product is the UI/orchestration plane. Prefer a separate SSH alias or tunnel master; putting fixed forwards on a host alias used for probes can create duplicate-listener failures.

## Remote desktop-control audit pattern

For a remote agent controlling a real local desktop, prove the complete chain:

```text
agent tool/MCP client
→ authenticated remote command or private network
→ local GUI-driver protocol
→ local daemon in the logged-in graphical session
→ OS accessibility/capture/input APIs
```

Check:

1. Whether the GUI driver controls a real host or a disposable sandbox.
2. Whether its public contract is stdio, HTTP, WebSocket, local IPC, or CLI.
3. How an SSH-spawned proxy reaches the logged-in graphical session.
4. OS permission attribution (for example macOS TCC bundle identity).
5. Whether a persistent daemon is required and who starts it.
6. Sleep, lock, logout, reboot, and user-session behavior.
7. Whether the agent framework’s built-in computer-use tool targets its own host only.
8. Whether a remote composition appears as raw MCP tools or needs a user-local adapter with a distinct tool name.
9. Screenshot/privacy flow to the model provider.
10. Concurrency: one controller lease for any shared real desktop.

Prefer stdio MCP over restricted SSH for one agent/one desktop when supported. A full-control HTTP service should remain loopback-bound and tunneled unless parallel clients genuinely require it.

On macOS, distinguish standard Remote Login over a private network from a VPN product’s own SSH server. They may have different platform support and policy semantics.

## Security defaults

- Bind preview, proxy, CDP, MCP-HTTP, and control listeners to loopback unless tailnet/public exposure is deliberate.
- Use separate SSH identities for terminal access, previews, and desktop control when their privilege differs.
- Restrict a desktop-control SSH key to a forced command where practical; disable PTY, shell, agent, X11, and generic forwarding.
- Keep permission grants human-only.
- Separate capture/list tools from click/type/drag mutators.
- Require fail-closed approval for desktop mutation.
- Never automate passwords, API keys, payment approval, passkeys, 2FA, permission dialogs, or security-policy changes.
- Keep screenshots and accessibility trees out of durable memory and ordinary terminal logs.
- Do not expose a real-desktop control server publicly.

## Acceptance matrix

A documentary audit should specify, but not claim to have run:

- local and remote OS/release/protocol compatibility
- local URL activation opens the intended browser host
- remote service remains loopback-bound
- SSH tunnel binds only to local loopback and fails on collision
- WebSocket/SSE/hot reload/upload/download behavior
- exact OAuth callback-port behavior
- private reverse-proxy reachability and public denial
- selected-process egress public-IP and DNS comparison
- system exit-node activation and rollback
- desktop-driver permissions and health report
- read-only desktop capture before any mutation
- harmless approved action with no foreground/cursor theft
- daemon loss and MCP reconnect
- one-controller lease
- lock/logout/sleep failure behavior
- denial of credential/payment/permission-dialog operations
- absence of secrets and screen data from argv, logs, events, and durable memory

## Reporting rule

Classify the complete composition independently from its components. “Product A supports SSH,” “Product B supports MCP,” and “a private network connects the hosts” do not by themselves prove that `A → SSH → B MCP → local GUI daemon` is a first-party end-to-end contract. Label such a path as a supported composition or proposal until exercised.
