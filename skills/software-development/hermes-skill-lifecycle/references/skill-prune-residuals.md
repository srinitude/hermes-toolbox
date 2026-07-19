# Skill prune residual cleanup

Pair with permanent prune: `skill_manage(action='delete', name=<skill>, absorbed_into='')`.

## Active search surfaces (default profile + paired workspace)

Search for the **skill name**, display-title variants, and **unique reference basenames** (e.g. `references/foo.md` → `foo`) under:

| Surface | Where to look |
| --- | --- |
| Skill tree | Profile skills root (package must be gone; drop empty category dirs) |
| Usage telemetry | Profile skills `.usage.json` |
| Prompt snapshot / catalog | Profile-generated skills prompt snapshot file if present |
| Profile identity / settings | Active profile home for name-only mentions (read/search; no drive-by rewrites) |
| Plugins / cron / pending | Profile plugins tree, `cronjob action=list`, pending queue |
| Workspace reports / plans | Paired workspace `.hermes/reports/`, `.hermes/plans/` |
| Archive / curator backup | Only if already present — pure prune must **not create** these |

**Out of scope by default:** session transcripts, FTS/session DB, immutable logs.

## CLI checks

```bash
hermes skills list      # name absent
hermes curator status   # name absent
```

In-session: `skill_view(name=...)` misses; `skills_list` omits; cron `skills` arrays lack the name.

## Report / hash consistency

If a baseline JSON lists the skill and a sibling manifest (e.g. `final-validation.json`) stores SHA-256 of that baseline, update both: strip mentions, recompute hash, write manifest field.

## Minimal ad-hoc verifier sketch

```python
import hashlib, json
from pathlib import Path

# HOME = profile skills parent; FORBIDDEN = name + unique reference basenames
assert not (skills_root / "category" / "skill-name").exists()
usage = json.loads((skills_root / ".usage.json").read_text())
assert "skill-name" not in usage
# For each edited active report: json.loads + no FORBIDDEN substrings
# If manifest hashes a baseline: sha256(file) == manifest field
```

Prefer an OS temp script with a `hermes-verify-` prefix, run, then delete. Label results **ad-hoc verification**, not suite green.

## Absorb reminder

Merge durable procedure into the umbrella **before** `absorbed_into='<umbrella>'`. Never invent a tombstone skill as the absorb target.
