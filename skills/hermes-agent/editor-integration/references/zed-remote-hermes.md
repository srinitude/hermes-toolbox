# Zed remote Hermes on a headless VPS

Use this reference when a user wants Zed as `$EDITOR` on a headless Hermes host and also wants the local Zed GUI connected to that host.

## Validate current docs first

Re-check these before implementation because Zed remote behavior changes over time:

- Zed CLI Reference: `https://zed.dev/docs/reference/cli`
- Zed Remote Development: `https://zed.dev/docs/remote-development`
- Hermes ACP editor integration: `https://hermes-agent.nousresearch.com/docs/user-guide/features/acp`

Key current facts observed in this workflow class:

- Zed CLI uses `zed --wait` for blocking editor workflows when the GUI can run.
- Zed Remote Development runs the UI locally and a headless Zed server remotely over SSH.
- Hermes ACP starts with `hermes acp` / `hermes-acp`; `hermes acp --check` is the fast readiness check.
- Zed's remote terminal may not support `zed file` forwarding to the local GUI; validate current docs and do not promise it unless supported.

## Read-only preflight

Run equivalent checks on the remote host:

```bash
printf 'EDITOR=%q VISUAL=%q DISPLAY=%q WAYLAND_DISPLAY=%q TERM=%q\n' \
  "$EDITOR" "$VISUAL" "$DISPLAY" "$WAYLAND_DISPLAY" "$TERM"

for c in zed zeditor nano vim vi uv hermes ssh sshd; do
  if command -v "$c" >/dev/null 2>&1; then
    printf '%s=%s\n' "$c" "$(command -v "$c")"
    "$c" --version 2>/dev/null | head -1 || true
  fi
done

hermes acp --version || true
hermes acp --check || true
systemctl is-active ssh 2>/dev/null || systemctl is-active sshd 2>/dev/null || true
```

## Install Zed user-locally on Linux

Use the official installer only after confirming the user wants installation:

```bash
curl -fsSL https://zed.dev/install.sh -o /tmp/hermes-verify-zed-install.sh
sh /tmp/hermes-verify-zed-install.sh
rm -f /tmp/hermes-verify-zed-install.sh
```

Expected user-local result on Linux:

```text
~/.local/bin/zed
~/.local/zed.app/
```

Verify:

```bash
command -v zed
zed --version
```

## Safe headless `$EDITOR` wrapper

Do not set raw `EDITOR="zed --wait"` on a server until it has been tested. A safe wrapper:

```bash
mkdir -p ~/.local/bin
cat > ~/.local/bin/zed-editor <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

if command -v zed >/dev/null 2>&1 && { [ -n "${DISPLAY:-}" ] || [ -n "${WAYLAND_DISPLAY:-}" ]; }; then
  exec zed --wait "$@"
fi

fallback="${ZED_EDITOR_FALLBACK:-}"
if [ -z "$fallback" ]; then
  if command -v nano >/dev/null 2>&1; then
    fallback="nano"
  elif command -v vim >/dev/null 2>&1; then
    fallback="vim"
  elif command -v vi >/dev/null 2>&1; then
    fallback="vi"
  else
    fallback="ed"
  fi
fi

printf '%s\n' "zed-editor: no DISPLAY/WAYLAND_DISPLAY for GUI Zed; falling back to: $fallback" >&2
printf '%s\n' "zed-editor: use local Zed Remote Development over SSH to edit remote files in your local GUI." >&2
exec "$fallback" "$@"
EOF
chmod +x ~/.local/bin/zed-editor
```

Persist near the top of `~/.bashrc` or the user's shell startup file:

```bash
case ":$PATH:" in *":$HOME/.local/bin:"*) ;; *) PATH="$HOME/.local/bin:$PATH" ;; esac
export EDITOR="$HOME/.local/bin/zed-editor"
export VISUAL="$HOME/.local/bin/zed-editor"
export ZED_EDITOR_COMMAND="zed --wait"
```

Verify fresh shell state:

```bash
bash -lc 'printf "EDITOR=%s\nVISUAL=%s\n" "$EDITOR" "$VISUAL"; command -v zed; zed --version | head -1; command -v zed-editor'
ZED_EDITOR_FALLBACK=true ~/.local/bin/zed-editor /tmp/probe
```

## Local Zed Remote Development

From the local computer, first make sure SSH works without unresolved host-key/auth prompts:

```bash
ssh <user>@<host> 'pwd; hostname; command -v hermes; hermes acp --check'
```

Then in local Zed:

1. Open Remote Projects (`ctrl-cmd-shift-o` on macOS, `alt-ctrl-shift-o` on Linux/Windows).
2. Click **Connect New Server**.
3. Enter the normal SSH command, e.g.:
   ```bash
   ssh <user>@<host>
   ```
4. Open a specific project/workspace path, not `/` or a very large home directory.

Local CLI alternative:

```bash
zed ssh://<user>@<host>/absolute/project/path
zed ssh://<user>@<host>:~/project
```

## Local Zed Agent Panel -> remote Hermes ACP

Verify from the local computer first:

```bash
ssh <user>@<host> /path/to/hermes --profile <profile> acp --check
```

Expected:

```text
Hermes ACP check OK
```

Then add a local Zed custom agent server:

```json
{
  "agent_servers": {
    "hermes-remote-profile": {
      "type": "custom",
      "command": "ssh",
      "args": [
        "-T",
        "-o",
        "LogLevel=ERROR",
        "<user>@<host>",
        "/path/to/hermes",
        "--profile",
        "<profile>",
        "acp"
      ]
    }
  }
}
```

If the remote Hermes should use the default profile, omit `--profile <profile>` only after stating that assumption.

## Reporting

Final responses should distinguish:

- What was installed/configured on the remote host.
- What works as `$EDITOR` in headless shells.
- How to use local Zed GUI for remote file editing.
- How to use local Zed Agent Panel with remote Hermes ACP.
- What was verified with real command output.
