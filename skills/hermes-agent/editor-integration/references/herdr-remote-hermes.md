# Herdr Remote Hermes Pattern

Use this reference when the user wants Hermes running on a VPS/headless host to communicate with a local computer through Herdr, or wants Herdr to coordinate Hermes alongside other terminal agents.

## Validated sources from the research session

- Herdr docs: `https://herdr.dev/docs/agents/`, `/integrations/`, `/agent-skill/`, `/socket-api/`, `/persistence-remote/`, `/windows-beta/`.
- Herdr official repository: `https://github.com/ogulcancelik/herdr`. Pin the exact reviewed release tag or commit before relying on these repository paths:
  - `website/agent-detection/hermes.toml`
  - `src/integration/assets/hermes/plugin.yaml`
  - `src/integration/assets/hermes/__init__.py`
  - `src/integration/targets.rs`
  - `src/integration/env.rs`
  - `src/integration/registry.rs`
  - `src/integration/tests.rs`
- Hermes docs: Desktop remote backend, API server, gateway, MCP, tools, profiles, configuration.

## Recommended architecture

```text
Local computer terminal
  └─ herdr --remote <vps-ssh-alias> --session hermes
       └─ SSH
          └─ VPS Herdr server
             ├─ Hermes TUI/CLI panes
             ├─ Hermes gateway / serve / logs panes
             ├─ other agents such as Claude, Codex, OpenCode
             └─ Herdr socket API for pane/agent/session orchestration
```

Use Herdr as the persistent terminal and multi-agent orchestration substrate. Do not replace Hermes primitives: Hermes still owns tools, memory, skills, cron, gateway, profiles, MCP, API server, approvals, and safety policy.

## VPS ↔ local computer communication

- macOS/Linux local host: prefer `herdr --remote <ssh-host> --session hermes` from the local terminal. Herdr runs a thin local client over SSH to the remote Herdr server; this keeps local keybindings and can bridge local clipboard/image paste.
- Windows local host: native Windows `herdr --remote` is not supported in Herdr Windows beta. Use SSH into the VPS and run `herdr --session hermes`, or use WSL2/Linux-side Herdr if available.
- Hermes Desktop GUI: use Hermes Desktop remote backend separately (`hermes serve` on the VPS, protected by VPN/basic-auth/OAuth as appropriate). Herdr can host/monitor that process, but Desktop talks to Hermes directly.
- Mobile/control plane: use Hermes gateway for chat, approvals, cron, and notifications. Herdr can supplement terminal visibility, but should not replace the gateway.

## Hermes integration in Herdr

Herdr’s official Hermes integration installs a Hermes plugin:

```bash
herdr integration install hermes
```

The plugin is installed under `~/.hermes/plugins/herdr-agent-state/` and enabled in `~/.hermes/config.yaml`. It reports lifecycle, tool, approval state, and session id while Hermes runs inside a Herdr pane. Reported session ids let Herdr restore Hermes panes with `hermes --resume <session>` after server restart.

Implementation facts from source:

- `src/integration/env.rs` currently computes the Hermes config directory as `HOME/.hermes`; it does not use `HERMES_HOME`.
- `src/integration/assets/hermes/__init__.py` only reports when `HERDR_ENV=1`, `HERDR_PANE_ID`, and `HERDR_SOCKET_PATH` are present.
- Hooks registered by the plugin include `on_session_start`, `pre_llm_call`, `pre_api_request`, `pre_tool_call`, `post_tool_call`, `pre_approval_request`, `post_approval_response`, `post_llm_call`, and `on_session_end`.
- The source marker is `herdr:hermes`; the agent label is `hermes`.

## Profile caveat

Because the upstream Herdr integration targets `HOME/.hermes`, it cleanly covers the default Hermes profile. For named Hermes profiles, do not assume `herdr integration install hermes` installs into the profile’s `$HERMES_HOME`. Prefer one of:

1. Ask for/prepare an upstream Herdr patch to respect `HERMES_HOME` or a profile-aware install target.
2. With explicit approval, copy the same plugin into the target profile’s `$HERMES_HOME/plugins/herdr-agent-state/` and enable it in that profile config.
3. State the limitation and use Herdr screen detection until profile-aware integration is available.

## Agent-control surfaces

Options, from safest to most ergonomic:

1. **Skill/CLI pattern:** teach Hermes to use Herdr CLI only when `HERDR_ENV=1`. Use `herdr agent list`, `agent read`, `agent wait`, `pane read`, `pane run`, `wait output`, `workspace/tab/pane` commands.
2. **MCP wrapper:** a reviewed Herdr MCP server can expose Herdr methods as tools. `herdr-mesh` is promising but third-party; review before granting it broad control.
3. **First-party wrapper/plugin:** best long-term: a constrained Hermes plugin or MCP exposing only safe Herdr actions.

## Useful use cases

- Persistent remote Hermes/operator workspace from a laptop or phone.
- Blocked-agent triage: Herdr shows which Hermes/agent pane is blocked; Hermes gateway can notify or collect approval.
- Hermes as orchestrator: read a Claude/Codex/OpenCode pane, send a handoff, wait for idle/done, summarize.
- Long-running build/test handback: run tests in a pane, wait for `PASS`/`FAIL`, read failures.
- Profile operations center: one Herdr workspace per important Hermes profile, with gateway/serve/log panes.
- Incident console: service logs and shells remain visible while Hermes reasons and reports via gateway.

## Pitfalls

- Herdr is not a sandbox. Keep Hermes terminal backend/approvals/security policy authoritative.
- Do not install unreviewed Herdr marketplace plugins or third-party MCPs without source review.
- Do not use Herdr to bypass Hermes approval prompts or type into secrets/payment prompts.
- Treat Herdr version/protocol differences as live facts to validate with `herdr status` and `herdr --help`; do not assume docs-only commands exist on the installed binary.
