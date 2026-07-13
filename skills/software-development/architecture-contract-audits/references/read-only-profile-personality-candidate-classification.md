# Read-only profile distribution and personality classification

Use this when deciding whether local Hermes profiles or personality snippets are suitable for standalone public packaging without changing live profile trees, config, or the publication repository.

## Freeze the right source surface

For each profile, hash only the authored distribution surface: `distribution.yaml`, reusable `config.yaml`, and every declared `distribution_owned` path. Deduplicate overlapping paths and include relative path, type/mode, content hash or symlink target, and size. Hash at start and end. Keep full live-profile runtime data outside the candidate even when it exists beside authored files.

For a personality, separately hash the package tree, manifest, referenced config snippet, and normalized prompt text. Compare the prompt against the supported live config through a nonsecret read surface, but do not treat the currently active personality as the only supported preset.

## Fail closed before runtime installation

A missing `distribution.yaml` is deterministic rejection, not a hold. Attempt the native local-directory install in a disposable `HERMES_HOME` to prove the public failure contract and ensure no target profile remains.

For manifest-bearing profiles, run the repository's real profile staging/export helper against a disposable archive of the frozen repository. Keep two results separate:

1. whether the exact helper accepts the projection under current static/semantic gates;
2. whether a manually materialized pre-validation projection can be copied by the native installer.

A successful `hermes profile install`, `profile info`, `config check`, or discovery command does not rescue a projection rejected by package gates. Native installation proves copying and basic parsing, not public safety, dependency closure, or semantic usability.

## Detect sanitizer semantic corruption

Profile distributions often own bundled skill trees. Sanitizers that derive replacement terms from each `SKILL.md` author can rewrite product and workflow names throughout the body while preserving the author frontmatter line. Inspect exact staged bytes and discovery output for:

- skill names rewritten to placeholders such as `<repo-author-name>-guide`;
- lifecycle/profile/tool names rewritten inconsistently;
- unrelated product names rewritten because they overlap an author name;
- malformed email/SSH commands or doubled placeholder delimiters;
- required `skill_view` targets that no longer match discovery names.

Treat this as deterministic rejection even when the sanitized output is privacy-safe and the native installer exits zero.

## Audit standalone dependency closure

Trace the package as an independently installed profile, not only in its original dispatcher or profile fleet. Check:

- every mandatory `skill_view` target survives sanitization and is discovered;
- worker-only tools supplied dynamically by a dispatcher are declared as prerequisites or have a standalone fallback;
- configured plugins are distribution-owned, public sibling dependencies, or explicitly optional;
- MCP configuration survives the exporter's reusable-config allowlist;
- cron jobs remain opt-in and no install command starts them;
- model/provider metadata agrees with `env_requires`;
- reusable config has no private `terminal.cwd` or other machine-specific path;
- package-owned skills do not import credential examples, binaries, test doubles, or other content rejected by current public-package policy.

An ecosystem profile may be useful while still being rejected for **standalone** publication when its dispatcher identity, board context, plugins, MCPs, or peer profiles are not closed.

## Real disposable runtime packet

Use a separate clean home per candidate. For an accepted projection run:

```text
hermes profile install <staged-dir> --name export-install-check --yes
hermes profile info export-install-check
hermes -p export-install-check config check
hermes -p export-install-check skills list --source local --enabled-only
hermes -p export-install-check plugins list --plain --no-bundled
```

Record every exit code, migration notice, discovered mandatory skill, and nonbundled plugin. Inventory the disposable home for credentials, cron state, gateway state, caches, and databases. CLI startup may create logs and starter files; report these as disposable runtime artifacts rather than claiming the command was byte-side-effect-free.

## Personality acceptance

Require:

- manifest `type: personality` and `sanitized: true`;
- `config_file` resolves inside the package;
- manifest and config hashes match public inventory/fingerprints;
- the normalized live/public prompt bytes match when claiming `accepted-current`;
- clean-home installation adds only the named `agent.personalities.<name>` preset;
- `agent.system_prompt` and `display.personality` remain absent unless activation was explicitly requested;
- `hermes config check`, package validators, and focused nonactivation/activation tests pass.

Installation and activation are separate contracts. A preset can be accepted-current while the user's live home has it actively selected; the clean-home proof must still show that publication installation itself does not activate it.

## Side-effect accounting

Prefer static reads and disposable homes. Some nominally read-only Hermes commands initialize `SOUL.md` and append `logs/agent.log` or `logs/errors.log`. Never report an unqualified “no files changed.” Report separately:

- repository and protected-source stability;
- deliberate live config/profile/plugin/cron changes (normally none);
- disposable files created and removed;
- incidental Hermes/tool-managed log writes.

Remove only task-owned temporary roots. Do not delete or truncate live logs to hide incidental writes.
