# Validator Personality Primitive

This package provides a public-safe custom Hermes `/personality` preset named
`validator`. It is intended to make validation standards explicit before a task
starts.

Official Hermes behavior: custom `/personality` presets are defined in
`$HERMES_HOME/config.yaml` under `agent.personalities`, and can then be activated
with `/personality <name>`. See the Hermes Personality & SOUL.md documentation
for details.

## Install

Preview available personalities:

```bash
./scripts/install-toolbox.sh --personalities
```

Install the `validator` personality into a Hermes home:

```bash
./scripts/install-toolbox.sh --apply --personalities --target "$HERMES_HOME"
```

Then start or restart Hermes and run:

```text
/personality validator
```

To also persist the validator overlay as the active default for that Hermes home,
use the explicit activation flag:

```bash
./scripts/install-toolbox.sh --apply --personalities --activate-validator --target "$HERMES_HOME"
```

That activation path writes `agent.system_prompt` and `display.personality` via
`hermes config set` in addition to installing `agent.personalities.validator`.

## Public-safety notes

This package contains only a reusable config snippet plus manifest metadata. It
must not include `.env`, auth/OAuth/token stores, memories, sessions, logs,
caches, state databases, pairing state, cron outputs, checkpoints, or other
runtime/private Hermes data.
