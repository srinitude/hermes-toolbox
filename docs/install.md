# Installation

The installer reads `inventory/public-manifest.json` and refuses any selection
that is not listed there. Without `--apply` it is a dry run: it prints the
exact proposed destination for every selection and writes nothing. With no
selection at all it lists the installable packages and exits.

```bash
./scripts/install-toolbox.sh                # list installable packages
./scripts/install-toolbox.sh --all-skills   # dry-run every manifest-listed skill
```

## Skills

Select skills explicitly. `--skill <category/name>` is repeatable;
`--all-skills` selects every manifest-listed skill.

```bash
./scripts/install-toolbox.sh --apply --skill hermes-agent/hermes-config-audits
./scripts/install-toolbox.sh --apply --all-skills --target "${HERMES_HOME:-$HOME/.hermes}"
```

## Personality presets: install versus activation

`--personalities` installs the public presets by writing only the
`agent.personalities.validator` config snippet. Nothing is activated; each
session opts in:

```bash
./scripts/install-toolbox.sh --apply --personalities --target "${HERMES_HOME:-$HOME/.hermes}"
```

```text
/personality validator
```

Activation is a separate, explicit step. `--activate-validator` (which
implies `--personalities`) additionally persists the overlay as the active
default by setting `agent.system_prompt` and `display.personality`:

```bash
./scripts/install-toolbox.sh --apply --personalities --activate-validator --target "${HERMES_HOME:-$HOME/.hermes}"
```

## Plugin and profile packages

`--plugin <name>` and `--profile <name>` are repeatable flags that accept only
manifest-listed packages; there is no implicit all-plugins or all-profiles
install. Profile packages install through the real `hermes profile install`.

Both inventories are currently empty because no current candidate passes the
publication gates (see `docs/publishing-criteria.md`), so the installer
rejects every plugin or profile selection until the manifest lists packages
again.
