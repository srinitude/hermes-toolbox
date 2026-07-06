# Installation

Run a dry-run first:

```bash
./scripts/install-toolbox.sh
```

Apply public skills:

```bash
./scripts/install-toolbox.sh --apply --target "$HERMES_HOME"
```

Sanitized plugin packages require explicit installation with the plugin flag.
Sanitized profile packages are listed for review and are not installed as live
profiles by default.
