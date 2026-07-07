# Primitives Quick Start

```text
start session -> /personality validator -> /prompt-enhancer [prompt] -> decide whether to use /profile-builder [goal] or /plugin-builder [goal] -> execute with validation

discover source -> classify candidate -> export sanitized copy -> validate public safety -> validate identity neutrality -> fingerprint -> publish or silent no-op
```

See `docs/deterministic-workflow-primitives.md` for the full primitive list.

Installable personality primitives live under `primitives/personalities/`.
The `validator` package contains the public-safe `agent.personalities.validator`
config snippet plus manifest metadata.
