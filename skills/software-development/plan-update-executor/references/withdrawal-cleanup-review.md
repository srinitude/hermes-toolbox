# Drift-safe review of withdrawal and cleanup changes

Use this checklist when a plan removes public packages, commands, plugins, profiles, skills, or catalog entries.

## Freeze before independent review

1. Complete edits and regenerate every derived manifest/fingerprint.
2. Stage additions, modifications, and deletions.
3. Require zero unstaged and zero untracked paths.
4. Record staged path count and SHA-256 of `git diff --cached --binary`.
5. Require each reviewer verdict to identify that exact digest.
6. Any subsequent index or worktree change invalidates the verdict. Re-run validation and dispatch fresh reviewers against the replacement digest.

## Repository-wide closure

Audit beyond package roots and Markdown inventories:

- tracked default/fallback allowlists and selection policy;
- YAML/JSON/TOML examples;
- install/activation instructions;
- generated manifests and fingerprints after the final edit;
- discovery metadata such as `related_skills`;
- tests whose “other package” sentinel becomes vacuous after withdrawal;
- newly referenced support files that must be staged;
- hard `skill_view`, install, load, bootstrap, and runtime dependencies;
- final-newline and generated-residue hygiene.

Neutral prose describing optional external workflows may remain when it is neither discovery metadata nor a mandatory load/install/runtime dependency. Record that distinction explicitly.

## Useful RED → GREEN contracts

- Tracked default selections equal the final public manifest.
- Public config examples use the current schema and name only available packages.
- Retained discovery metadata does not advertise withdrawn packages.
- Installer isolation tests use a second package that actually remains in the manifest.
- Withdrawn selections fail before writing.

## Verification order

1. Witness focused RED.
2. Apply the minimal fix.
3. Witness focused GREEN.
4. Regenerate inventory/fingerprints.
5. Run structure/static gates and the full suite.
6. If recognized evidence is required, run a focused OS-tempfile `/tmp/hermes-verify-*.py` probe and remove it afterward.
7. Stage the exact candidate, then request independent specification and security/quality review.
