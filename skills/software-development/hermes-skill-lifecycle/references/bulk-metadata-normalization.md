# Bulk skill metadata normalization

Use when the user asks to set or fix author (or other frontmatter fields) across many skills under `~/.hermes/skills/`. Pair with the authored size limits in the parent skill.

## Scope classes (classify first)

Walk every `SKILL.md` under `~/.hermes/skills/`, skipping dotdirs.

| Class | How to detect | Default action |
| --- | --- | --- |
| User-created (local) | Name/dir absent from `.bundled_manifest` and not under a `.hub/lock.json` `install_path` | In scope |
| User-edited bundled | Name in `.bundled_manifest` and directory MD5 ≠ manifest digest | In scope when the user said user-edited |
| Unmodified bundled | Name in `.bundled_manifest` and MD5 matches | Out of scope |
| Hub-installed | Dir matches a lock `install_path` | Out of scope unless content hash diverged and the user named hub changes |
| External-dir skills | Loaded via `skills.external_dirs` | Out of scope unless the user names that tree |

Loading a skill does not put it in scope. Keep profile identity and workspace policy files out of metadata-only work unless the user explicitly includes them.

## User author preference

For this profile, user-created and user-edited skills use:

```yaml
author: Kiren Srinivasan
```

When creating or bulk-fixing those skills, set that exact string. Leave unmodified bundled/hub upstream authors alone.

## Safe sequence

1. `hermes curator backup --reason "<short-reason>"` and record the snapshot path under `~/.hermes/skills/.curator_backups/`.
2. Classify the full tree into the table above; print target names before writing.
3. Patch only target `SKILL.md` frontmatter (and description fixes required by authored limits). Prefer multi-file `patch` with unique context around `author:` / `description:`.
4. If a description fails authored policy (`Use when ...`, length < 60), fix it in the same pass so the skill stays load-safe.
5. If a body is at the 200-line edge, compress blanks only when needed; keep every rule.
6. Diff live files against the pre-change snapshot. Expected mutations are the target `SKILL.md` set only. Ignore unrelated sidecar churn such as `.usage.json` unless you intentionally changed it.
7. For each target, assert:
   - `author == Kiren Srinivasan`
   - description starts with `Use when ` and length < 60
   - body non-empty, body lines < 200, full file ≤ 100,000 chars
   - frontmatter keys other than the intended fields match the snapshot
8. Bodies should match the snapshot except for intentional blank-line compression. If a concurrent change altered a body (another session or tool), keep that body and only keep the frontmatter fix. Never roll concurrent body work back to the snapshot.
9. Delete temporary `hermes-verify-*.py` helpers. Label the check as focused ad-hoc verification, not suite green.
10. Do not invent a new skill for a one-shot author pass. Update this lifecycle skill if the procedure improved.

## Classification snippets

Bundled digest (matches Hermes curator-style tree MD5 used in `.bundled_manifest`):

```python
import hashlib
from pathlib import Path

def md5_dir(path: Path) -> str:
    h = hashlib.md5()
    for file in sorted(path.rglob("*")):
        if file.is_file():
            h.update(str(file.relative_to(path)).encode())
            h.update(file.read_bytes())
    return h.hexdigest()
```

Hub content hash shape is lock-defined (`content_hash` on the install entry). Compare the live dir the same way the lock was produced; if unsure, treat matching `install_path` as hub and only include it when the user asked for hub changes or the hash clearly diverges.

## Pitfalls

1. **Changing all 80+ skills** — most are unmodified bundled/hub. Scope to local + user-edited only.
2. **Trusting description length alone** — author fixes often surface over-long descriptions; fix both before closeout.
3. **Strict whole-tree diff vs snapshot** — `.usage.json` and concurrent body/reference changes can appear without your hand. Scope equality checks to `**/SKILL.md` or to the planned path set.
4. **Overwriting concurrent body changes** — re-read before overwrite; keep foreign body changes when only author/description were requested.
5. **Skipping curator backup** — bulk frontmatter work is easy to reverse from `skills.tar.gz` if you snapshotted first.
6. **Calling the pass "suite green"** — it is targeted metadata verification only.
