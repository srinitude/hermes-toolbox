# Sensitive Profile Design Reference

Use this reference when building Hermes profiles for sensitive life domains such as family, care, health, legal, finance, or other relationship-heavy contexts.

## Patterns learned

### Gateway is not always the domain transport

A messaging gateway such as Telegram, Discord, or Slack may be only the user's control/review/reminder interface. Do not infer that the same gateway should send the domain action.

For example, a family-relationship profile may use Telegram for:

- interacting with the profile;
- receiving reminders and briefings;
- reviewing drafts;
- approving or rejecting actions.

But outbound family messages may be reserved for future approved sender plugins/tools. Model this explicitly:

```yaml
gateway:
  telegram:
    role: control_review_reminder_surface
    not_for: direct family-message transport by default
outbound_actions:
  transport: approved_tool_plugins_only
  blocked_until: plugin exists, is approved, and validates
```

### Strict Honcho isolation for sensitive profiles

Standard profile-aware Honcho commonly shares a workspace/user peer and gives each profile a separate AI peer. That is convenient but may be too porous for sensitive relationship data.

When the user wants strict isolation, specify and validate all three:

```yaml
memory:
  external_provider: honcho
  honcho_isolation: strict
  workspace: hermes_<profile_slug>
  user_peer: <user>_<profile_slug>
  ai_peer: <profile_slug>
```

Validation must check `hermes -p <profile> honcho status` for the exact workspace, user peer, and AI peer values.

### Profile home vs operational cwd

A standard Hermes named profile should keep its profile home under the official profile path:

```text
~/.hermes/profiles/<profile-name>
```

The user may still want the profile's operational working directory elsewhere, e.g.:

```yaml
terminal.cwd: $HOME/hermes-workspaces/example-sensitive-profile
```

Keep these concepts distinct in final specs. Do not treat a desired working directory as a custom `HERMES_HOME` unless the user explicitly chooses a custom-home approach.

### Plugin-powered crons

If scheduled jobs depend on future plugins, do not create active plugin-dependent cron jobs before the plugins exist. Instead:

- record the intended cadence and purpose;
- create only non-plugin-dependent reminder/briefing jobs if safe and approved;
- mark plugin-powered jobs as blocked until the plugin is built, approved, enabled, and validated;
- keep cron prompts self-contained;
- never let cron auto-send sensitive/domain messages without explicit approval.

### Draft-to-send approval workflow

For sensitive outbound messages, use a staged flow:

```text
DRAFT — NOT READY TO SEND
→ voice/context pass
→ relationship/safety pass
→ READY TO SEND — AWAITING APPROVAL
→ explicit approval of exact message and transport
→ send through approved tool/plugin, or block/manual copy if no plugin exists
→ optional compact follow-up note/reminder
```

Safety checks should include wrong recipient, stale context, disclosure risk, pressure/guilt, boundary issues, timing, and unintended escalation.

### Validator overlay is not SOUL

If the active profile uses `/personality validator`, copy it as config overlay when profile-builder default says to do so:

```yaml
agent.personalities.validator: <source validator definition>
agent.system_prompt: <resolved validator prompt>
```

Still write a fresh profile-specific `SOUL.md`. Do not copy source `SOUL.md` wholesale to preserve validation posture.
