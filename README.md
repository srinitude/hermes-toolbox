# Hermes Toolbox

Public, reusable building blocks for Hermes Agent users: validated skills, the
`validator` custom `/personality` preset, public validation scripts, and
documented operating patterns. `inventory/public-manifest.json` is the source
of truth for what is published; the documentation and installer are tested
against it.

Repository: https://github.com/srinitude/hermes-toolbox/

Compatible Hermes release: `hermes-agent` 0.18.2 (release `v2026.7.7.2`).

## Current public manifest

- Skills: 12
- Plugin packages: 0
- Profile packages: 0
- Personality presets: 1

Skills under `skills/`:

- `autonomous-ai-agents/openrouter-mcp-server`
- `hermes-agent/editor-integration`
- `hermes-agent/hermes-config-audits`
- `hermes-agent/honcho-memory-provider`
- `hermes-agent/profile-builder`
- `research/first-party-integration-audits`
- `software-development/architecture-contract-audits`
- `software-development/bounded-development-execution`
- `software-development/goal-prompt`
- `software-development/plan-update-executor`
- `software-development/plugin-builder`
- `software-development/prompt-enhancer`

Personality presets under `primitives/personalities/`:

- `validator` — a validation-focused `/personality` overlay, installed as a
  config snippet and never activated implicitly.

### Why the plugin and profile inventories are empty

Publication is fail-closed. A package is published only while its current
source passes every provenance, privacy, completeness, real-runtime, and
structural gate; a newer-but-failing candidate never replaces a
last-known-good public package. The previously published tutorial plugin
suite and tutorial profile package failed the hardened completeness gates
themselves, so they were unpublished rather than patched in place, and no
current plugin or profile candidate has passed every gate yet. Rejected
candidates stay local-only and are not named here. The `--plugin` and
`--profile` installer flags become usable again as soon as the manifest
lists packages.

## Installation

The installer is manifest-driven and dry-run by default: without `--apply` it
prints the exact proposed destinations and writes nothing, and with no
selection it lists the installable packages and exits.

```bash
git clone https://github.com/srinitude/hermes-toolbox.git "$HOME/hermes-toolbox"
cd "$HOME/hermes-toolbox"
./scripts/install-toolbox.sh
```

Install skills explicitly — a repeatable `--skill <category/name>` flag, or
`--all-skills` for every manifest-listed skill:

```bash
./scripts/install-toolbox.sh --apply --all-skills --target "${HERMES_HOME:-$HOME/.hermes}"
./scripts/install-toolbox.sh --apply --skill hermes-agent/hermes-config-audits
```

Install the validator personality preset without activating it, then use it
per session:

```bash
./scripts/install-toolbox.sh --apply --personalities --target "${HERMES_HOME:-$HOME/.hermes}"
```

```text
/personality validator
```

Activation is a separate, explicit step. `--activate-validator` (which
implies `--personalities`) also persists the overlay as the active default:

```bash
./scripts/install-toolbox.sh --apply --personalities --activate-validator --target "${HERMES_HOME:-$HOME/.hermes}"
```

`--plugin <name>` and `--profile <name>` are repeatable flags that accept only
manifest-listed packages; profiles install through the real
`hermes profile install`. Both inventories are currently empty, so the
installer rejects any plugin or profile selection. There is no broad
plugin flag and no enable-everything step.

See `docs/install.md` for the full flag reference.

## Hermes Agent install prompt

Give this prompt to a Hermes Agent instance to install the toolbox for you:

```markdown
Install the public Hermes Toolbox from https://github.com/srinitude/hermes-toolbox/
into `${HERMES_HOME:-$HOME/.hermes}` unless I name a different target.

1. Clone or update the repository under `$HOME/hermes-toolbox`.
2. Run `python3 scripts/validate-public-safety.py`,
   `python3 scripts/validate-identity-neutrality.py`, and
   `python3 scripts/validate-package-completeness.py`; stop on any failure.
3. Run `./scripts/install-toolbox.sh --apply --all-skills --personalities
   --target "${HERMES_HOME:-$HOME/.hermes}"`. Do not pass any plugin or
   profile selection unless `inventory/public-manifest.json` lists packages,
   and do not activate the validator personality unless I ask.
4. Prove the result with `hermes skills list --source local` and
   `hermes config check`; report commands run and any blockers.

Never read or copy credentials, memories, sessions, logs, caches, state
databases, pairing state, or runtime files.
```

## Recommended Hermes workflow

1. Start each session with `/personality validator`.
2. Use `/hermes-config-audits` for public-safe Hermes configuration audits.
3. Use `/honcho-memory-provider` for current Honcho memory-provider guidance.
4. Use `/first-party-integration-audits` when integration claims need
   first-party verification.
5. Validate every result against explicit source-of-truth checks before handoff.

## Publishing model

- Candidates are selected only through explicit, repeatable exporter flags or
  local untracked allowlists under `.git/info/`; there is no default sweep.
- Exports are transactional per package: a candidate is staged, sanitized,
  and fully validated before it atomically replaces its destination, so a
  failing candidate leaves the current public package byte-for-byte
  unchanged.
- The publisher fails closed on a dirty checkout, stages only accepted
  paths, and exits silently with no output when there is nothing to publish.

## Validation

Before publishing or installing from a checkout, run the full packet:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 scripts/validate-public-safety.py
python3 scripts/validate-identity-neutrality.py
python3 scripts/validate-package-completeness.py
python3 scripts/validate-tutorial-suite.py
python3 scripts/verify-python-structure.py scripts tests plugins
bash -n scripts/install-toolbox.sh scripts/publish-public-candidates.sh
```

## Safety model

This repository is intentionally public. It must not contain credentials, raw
memory, sessions, logs, state databases, private profile content, private
plugin state, runtime caches, pairing data, or user-specific paths. Profile
and plugin packages are shareable only after sanitization, completeness, and
manifest checks.

See:

- `docs/install.md`
- `docs/recommended-hermes-workflow.md`
- `docs/public-safety-policy.md`
- `docs/identity-neutrality.md`
- `docs/deterministic-workflow-primitives.md`
- `docs/publishing-criteria.md`
- `docs/customization-inventory.md`
