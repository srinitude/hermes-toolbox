# Executing Saved Plans Against Temporary Workspaces

Use this reference when the user asks to execute a previously saved plan that edits an extracted archive, profile bundle, or other temporary workspace while forbidding writes to live Hermes homes.

## Pattern

1. **Read the saved plan first.** Treat it as the source-of-truth scope, especially its allowed/prohibited write surfaces and validation threshold.
2. **Restate boundaries internally before writes.** Typical safe edit root is a `/tmp/.../extracted/...` package. Do not mutate the downloaded archive, `$HERMES_HOME`, profile homes, or runtime/credential stores unless the plan explicitly allows it.
3. **Create a baseline manifest outside the package.** Store hashes in `/tmp/hermes-verify-<slug>-baseline.json` so later comparison proves added/removed/changed files.
4. **Patch only files named by the plan.** For profile bundles, normalize docs/configs/manifests/installer scripts together so documentation and executable behavior agree.
5. **Exercise only safe execution paths.** For installers, run `--dry-run` or equivalent and confirm it prints intended commands without creating backup dirs, profiles, config mutations, or runtime state.
6. **Use a focused verifier under `/tmp/hermes-verify-*.py`.** Check exactly the plan's acceptance criteria: parse YAML/frontmatter, scan stale strings, compare docs/toolsets/configs, check placeholder-only credential examples, and fail nonzero on any issue.
7. **Generate a final manifest and compare.** Report added/removed/changed files and verify all changes are under the allowed temp workspace.
8. **Clean up temporary verifier scripts after capturing output.** Keep baseline/final manifests if useful for audit unless the user asked for cleanup.

## Verifier checklist for Hermes profile/archive corrections

- YAML files parse with `yaml.safe_load`.
- `SKILL.md` files have parseable frontmatter with required keys.
- Installer is `$HERMES_HOME`-aware and dry-run capable.
- Installer avoids direct profile copying, direct config YAML rewrites, and `|| true` error suppression.
- Any `SOUL.md` that invokes `skill_view` has `skills` in the matching `config.yaml` toolsets.
- Orchestrator profiles stay narrowly scoped: include `skills` if they load a guide, but omit implementation toolsets unless explicitly intended.
- Env-var names match actual model/provider defaults; credential examples are placeholders only.
- Stale contradiction strings from the review are gone.

## Reporting format

Final report should include:

- Changed file list from baseline/final manifest comparison.
- Mapping from each original issue to its correction.
- Exact validation command outputs or concise excerpts with exit status.
- Explicit safety statement: no real install/config/profile mutation occurred.
- Remaining artifacts and risks, if any.
