# complete-profile

Fixture profile distribution used by the export pipeline tests. It carries the
exact file set a reusable public profile package must ship, so tests can copy
it into temporary Hermes homes, decorate the copy with runtime state, and then
prove that the exporter emits only the reusable distribution-owned content.

## Files

- `distribution.yaml` — manifest read by `hermes profile install`.
- `config.yaml` — reusable toolset, terminal, display, and approval settings.
- `SOUL.md` — profile identity loaded at spawn.
- `skills/demo-guide/SKILL.md` — the bundled walkthrough skill.
- `README.md` — this file.

## Install

```bash
hermes profile install <package-path> --name <profile-name> --yes
```
