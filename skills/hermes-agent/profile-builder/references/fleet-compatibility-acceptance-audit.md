# Fleet Compatibility and Acceptance Audits

Use this procedure when reviewing profile-wide skill propagation, installed profile-builder copies, or a completed multi-profile rollout. It is an independent, read-mostly acceptance audit: do not repair findings unless separately authorized.

## Scope discovery

1. Run `hermes profile list` twice with a short delay and require identical profile-name sets.
2. Map `default` to the active Hermes root and named profiles to `profiles/<name>`; do not trust a planning snapshot.
3. Discover installed builder copies independently under each live profile's `skills/` tree. Report unexpected duplicates and profiles where the builder is absent; absence is not permission to install it.
4. Record profile count, prompt-enhancer count, builder count, and all target paths before evaluating content.

## Independent static checks

For every target `SKILL.md`, validate:

- UTF-8 text and YAML frontmatter beginning at byte zero;
- expected `name`, description length, nonempty body, size limit, and balanced Markdown fences;
- exactly one start/end marker pair;
- marker bytes identical across the fleet and byte-for-byte equal to the authoritative plan or canonical source—not merely equal to each other;
- semantic anchor placement;
- declared local references exist;
- the whole target tree contains no symlinks or hidden support files.

Compute both shared block hashes and whole-file hashes. Group whole-file hashes by profile so shared contracts can coexist with preserved profile-local customizations.

## Baseline preservation

When a pre-rollout inventory exists:

1. Prove each pre-existing file reconstructs its exact baseline bytes after removing only the approved marker block and separator. Ordered-line subsequence checks are useful but weaker than exact reconstruction.
2. Compare complete support-file relative-path/SHA-256 manifests, including detection of added files.
3. For a newly seeded tree, compare source and target allowlisted manifests and reject symlinks, hidden files, credentials, config, plugins, logs, sessions, caches, and runtime state.

## Fresh-process discovery

For every live profile, run fresh processes serially:

```bash
hermes -p <profile> skills list --source local
hermes -p <profile> skills list --source local --enabled-only
```

Require prompt-enhancer in both outputs. For profiles with an installed profile-builder, require it in both outputs too. A disabled result is a blocker, not authorization to alter config.

## Future-profile propagation proof

Audit every installed builder for exact canonical wording covering blank, clone, clone-all, clone-from, distribution, and `--no-skills` paths; allowlisted copying; provider non-enablement; disposable testing; and fresh discovery.

A real future-profile simulation must use a disposable `HERMES_HOME`, never live memory or Honcho writes. Preserve durable evidence before cleanup: command, exit status, profile inventory, source/target manifests, block hash, and local/enabled-only discovery output. After cleanup, an independent auditor can validate the retained evidence but cannot re-run discovery without authorization to recreate the disposable profile; report that evidence boundary explicitly.

## Adversarial coverage

Require negative controls for at least:

- missing skill;
- missing required phrase;
- duplicate marker;
- divergent marker bytes;
- missing declared reference;
- dynamically added profile;
- symlinked tree and nested support-file symlink;
- known denied semantic claims.

The verifier should compare blocks to the authoritative canonical text, not only enforce fleet identity and a few phrases. It should reject nested symlinks rather than silently omit them from manifests. If the production verifier lacks either check, run an independent recursive/canonical comparison and report the verifier gap separately from current-state results.

## Evidence and reporting

Report:

- stable counts and fresh-discovery pass rates;
- shared block hashes plus grouped whole-file hashes;
- structural/reference/tree-safety results;
- baseline/customization preservation;
- unit and adversarial-control counts;
- future-profile proof and its cleanup boundary;
- rollback archive/member counts and hashes;
- blockers versus verifier-hardening caveats;
- exact commands used;
- files created or modified by the audit.

Do not call paid models for this class of audit. Read-only CLI discovery may create ordinary runtime logs; distinguish that from direct target/config/profile mutation and avoid claiming filesystem-wide immutability without a baseline.
