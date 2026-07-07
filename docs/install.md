# Installation

Run a dry-run first:

```bash
./scripts/install-toolbox.sh
```

Apply public skills. Optional flags such as `--personalities` and `--plugins`
are additive; `--apply` always installs public skills first.

```bash
./scripts/install-toolbox.sh --apply --target "${HERMES_HOME:-$HOME/.hermes}"
```

Install public custom `/personality` presets, including `validator`:

```bash
./scripts/install-toolbox.sh --apply --personalities --target "${HERMES_HOME:-$HOME/.hermes}"
```

Then restart Hermes and run:

```text
/personality validator
```

If you explicitly want the validator overlay persisted as the active default,
install with activation:

```bash
./scripts/install-toolbox.sh --apply --personalities --activate-validator --target "${HERMES_HOME:-$HOME/.hermes}"
```

Sanitized plugin packages require explicit installation with the plugin flag.
Sanitized profile packages are listed for review and are not installed as live
profiles by default.
