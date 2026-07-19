# Commit-drift review (user-created skills)

Use when SOUL's Skill compatibility gate or this skill's invocation steps need a concrete inspection recipe.

## Classify

User-created only when all are true:

- Not in `~/.hermes/skills/.bundled_manifest`
- Not in `~/.hermes/skills/.hub/lock.json`
- Not loaded only through `skills.external_dirs`

## Resolve commits

```bash
git -C ~/.hermes/hermes-agent rev-parse HEAD
```

Read creation and review commits from `metadata.hermes` first. If missing there, read the skill's entry in `~/.hermes/skills/.usage.json`.

Never invent creation from `created_at` or file mtime. Use session evidence or a reflog interval that contains the creation event. Otherwise record `unknown`.

## Reuse vs inspect

- If `compatibility_reviewed_with_hermes_commit` equals current HEAD, reuse that review.
- Else inspect. Large commit distance or file-count is only a trigger.

On shallow clones, raw `rev-list --count A..B` can under-count or mislead. Prefer a path-scoped tree diff:

```bash
git -C ~/.hermes/hermes-agent diff --name-only "$CREATED" "$CURRENT" -- \
  tools/skill_manager_tool.py \
  tools/skill_usage.py \
  tools/skill_provenance.py \
  agent/skill_utils.py
```

Widen the path list to whatever source, tests, config, and live docs actually govern the skill under review.

## Meaningful delta

Patch skill guidance only when a change can break deterministic or correct execution:

- command, path, or CLI flag
- schema or config key
- safety boundary
- runtime contract
- verification step the skill tells the agent to run

Unrelated refactors, docs polish, or distant subsystems are not enough.

## Record result

1. Keep `created_with_hermes_commit` unchanged (immutable).
2. Set `compatibility_reviewed_with_hermes_commit` to current HEAD even when skill body content does not change.
3. Prefer `metadata.hermes` for both fields.
4. If two frontmatter lines would push SKILL.md over the authored line or character limit, write them on the skill's `.usage.json` entry instead.
5. After a sidecar write, re-open the skill with `skill_view` and re-read the usage entry so a later tool write did not drop the fields.

## Sidecar field names

On the skill key in `~/.hermes/skills/.usage.json`:

- `created_with_hermes_commit`
- `compatibility_reviewed_with_hermes_commit`

Do not store task SHAs, PR numbers, or one-off session outcomes there.
