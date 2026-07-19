---
name: hermes-skill-lifecycle
description: "Use when managing user-local Hermes skill lifecycle."
version: 1.2.12
author: Kiren Srinivasan
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [skills, lifecycle, prune, curator, skill-manage, residuals]
    related_skills: [hermes-agent-skill-authoring, plan, meaning-preserving-rewrite]
    created_by: agent
    created_with_hermes_commit: b27d8b6ac8c8eed4c995d1b92790d476eb6e7149
    compatibility_reviewed_with_hermes_commit: 5988fe6cd5547d3620df1de889ac6007f5463b4d
---

# Hermes User-Local Skill Lifecycle

## Overview

Own the **runtime skill library** under `~/.hermes/skills/` (and paired workspace active surfaces). In-repo authoring conventions stay in `hermes-agent-skill-authoring` (bundled). Hermes product config stays in `hermes-agent` (bundled). This skill covers **lifecycle operations** agents actually perform with `skill_manage` / Curator: create only when justified, absorb into umbrellas, and hard-prune without leaving active breadcrumbs.

## When to Use

- Permanently remove a bad or auto-created skill (explicit prune)
- Merge a narrow skill into a broader umbrella (`absorbed_into`)
- Create or patch a user-local / agent-created skill and enforce authored size limits
- Normalize author or other frontmatter across user-created and user-edited skills
- After `skill_manage` delete/create/patch, ensure catalogs, telemetry, reports, and cron stay consistent
- User asks whether a skill is still installed / why it still appears in a baseline report
- A user-created skill is invoked and needs the commit-drift compatibility gate
- Independent security, contradiction, or package-quality review of a live skill and its validation packet
- Read-only security, privacy, and scope review of a frozen Git tree or profile/distribution export (Toolbox-style staged payload)

**Don't use for:** in-repo `skills/` package authoring (use `hermes-agent-skill-authoring`); general Hermes install/config (use `hermes-agent`); session chronology recall (use `session_search`).

## Skill origin and commit drift

A **user-created** skill is local, absent from `.bundled_manifest` and `.hub/lock.json`, and not loaded through `skills.external_dirs`. A **curator-managed** skill is narrower: current Hermes marks only background-review creations with `created_by: agent`. Background curation must not mutate manual or foreground-created skills.

Run this gate whenever a user-created skill is invoked:

1. Read the creation and reviewed commits from `metadata.hermes` or `.usage.json`, then resolve installed Hermes `HEAD`.
2. Reuse a review only when its commit matches `HEAD`. Recover missing creation provenance from exact session or reflog evidence, never timestamps; otherwise record `unknown`.
3. On commit drift, inspect governing source, tests, config, and live docs. A changed command, path, schema, safety boundary, runtime contract, or verification step is meaningful; commit count alone is not.
4. Patch only affected guidance, then run size, provenance, link, and non-overlap checks. Leave guidance unchanged when no governing contract changed.
5. Preserve the creation commit and stamp the reviewed commit to current `HEAD`, even after a no-op body review. `unknown` creation provenance requires a full review at each new commit.

Record both fields at creation. Use `.usage.json` only when frontmatter would breach a Markdown limit. The creation commit is immutable; the reviewed commit is a compatibility cache.

`PD-003`: `references/commit-drift-review.md` owns commands, path lists, the comparison matrix, and sidecar fields. Load it when creation provenance is missing or the reviewed commit differs from installed `HEAD`. This section owns the universal trigger and stamp rule and links to that detail.

## Create / update gates (summary)

Prefer, in order: no change → patch governing skill → patch umbrella → one support file + pointer → new **class-level** skill only if no merge target.

Create only when: no owner can absorb; procedure is recurring, non-trivial, environment-stable; path was verified; trigger is distinct; reuse beats maintenance. Never skill one-off narratives, unrelated SHAs, or "tool X is broken." Creation and review commit metadata are provenance, not task history.

### Author field (this profile)

For user-created and user-edited skills under `~/.hermes/skills/`, set `author: Kiren Srinivasan`. Leave unmodified bundled or hub skill authors alone. Bulk author or description passes: `references/bulk-metadata-normalization.md`.

### Authored size limits (user-local and agent-created)

Platform validator still allows description ≤ 1024 chars and full SKILL.md ≤ 100,000 chars. Authored policy is stricter:

- Description: **< 60** characters. Start with `Use when ...`. Name one exact trigger class only. Exclude unrelated tasks so the skill is not loaded by mistake.
- Body after the closing frontmatter `---`: **< 200** physical lines (count blanks). Keep the body non-empty.
- If the body would hit 200 lines, split into `references/`, `templates/`, or `scripts/` and keep a short pointer in SKILL.md.
- Before finishing create/edit/patch, parse frontmatter and assert:

```python
import pathlib, yaml
content = pathlib.Path("SKILL.md").read_text()
assert content.startswith("---\n")
frontmatter, body = content[4:].split("\n---\n", 1)
fm = yaml.safe_load(frontmatter)
assert len(str(fm["description"])) < 60
assert body.strip() and len(body.splitlines()) < 200
assert len(content) <= 100_000
```

Do not rewrite platform-limit docs as if the validator itself rejected at 60/200. Keep those as authoring rules.

## Absorb vs permanent prune

| Intent | Call | Do |
| --- | --- | --- |
| Merge into existing umbrella | `skill_manage(action='delete', name=NAME, absorbed_into='UMBRELLA')` | Put durable content in `UMBRELLA` **first**; then delete. Target must exist. |
| Permanent prune, no successor | `skill_manage(action='delete', name=NAME, absorbed_into='')` | Hard delete. **No** archive, curator backup, forwarding skill, or tombstone. Empty-string `absorbed_into` makes prune intent explicit. |

Pinned skills: pin blocks curator auto-delete; user-directed prune may require unpin first. Do not invent a stub skill as an absorb target.

## Permanent prune procedure

1. **Confirm scope:** skill name, pin state, profile (`~/.hermes` vs other profile — never cross-profile without explicit direction), cron `skills` attachments, active references.
2. **Delete:** `skill_manage(action='delete', name=NAME, absorbed_into='')`.
3. **Package:** confirm `~/.hermes/skills/<category>/<name>/` is gone; remove empty category directory if it only held that skill.
4. **Telemetry:** remove key from `~/.hermes/skills/.usage.json` if present.
5. **Snapshot/catalog:** scrub `~/.hermes/.skills_prompt_snapshot.json` (or current skills prompt snapshot) of name/description entries.
6. **Active workspace surfaces:** search paired `~/hermes-profiles/<profile>/` and profile home for skill name, title variants, and unique reference basenames. Edit active reports/baselines (e.g. `.hermes/reports/**`); keep hash/manifest siblings consistent when a report is content-hashed.
7. **Cron / config / SOUL / plugins / pending:** zero active matches.
8. **CLI / in-session:** `hermes skills list`, `hermes curator status`, `skills_list`, and `skill_view(name=...)` must not resolve it.
9. **Plans:** delete one-shot implementation plans under `.hermes/plans/` that only existed to drive this prune (after success), so the plan is not an active mention.
10. **Historical boundary:** leave session transcripts / session DB alone unless the user explicitly expands scope.

Detailed search matrix and verifier sketch: `references/skill-prune-residuals.md`.

## Completion criteria (prune)

- [ ] Delete used with explicit `absorbed_into=''` (or real umbrella if absorb)
- [ ] Skill dir absent; empty category cleaned if needed
- [ ] No active mentions of name or unique reference filenames in profile + workspace (historical logs exempt)
- [ ] Telemetry + snapshot/catalog clean
- [ ] Cron does not attach the skill
- [ ] Fresh CLI + `skill_view` + curator do not list/resolve it
- [ ] No archive, backup, forwarding skill, or tombstone for a pure prune

## Common Pitfalls

1. **Omitting `absorbed_into` on delete** — set `''` for prune or the real umbrella name for merge so Curator and dependents get correct intent.
2. **Stopping after package delete** — baselines, `.usage.json`, and prompt snapshots can keep the name alive for later agents.
3. **Creating a tombstone/forwarding skill** after prune — defeats permanent removal.
4. **Rewriting history** — do not scrub session DB "for completeness" unless asked.
5. **Editing another profile's skills** — only with explicit user direction; respect profile/workspace pairing.
6. **Forgetting hash/manifest pairs** — when a report is hashed in `final-validation.json` (or similar), update content and hash together.
7. **Leaving the implementation plan** — a plan that documents the removed skill is still an active workspace mention if the goal was full active purge.
8. **Confusing platform limits with authoring limits** — validator allows description ≤ 1024 and file ≤ 100,000. Authored skills still need description < 60 and body < 200 lines after frontmatter.
9. **Broad or long descriptions** — a description that names two unrelated triggers loads on the wrong tasks. Keep one exact class under 60 characters.
10. **write_file into system temp for verifiers** — on macOS, `write_file` can refuse `/private/var/folders/...`. For size/hash gates after skill edits, create a `hermes-verify-` temp script via `execute_code` or `terminal`, run it, then delete it. Keep platform limits intact while asserting authored 60/200 bounds.
11. **Leaving review packet scripts or cron after validation** — temporary review helpers under `~/.hermes/scripts/`, `/tmp`, or one-shot cron jobs must be removed when the gate finishes so they do not become permanent lifecycle clutter.
12. **Trusting commit count on a shallow clone** — `rev-list --count` can understate drift. Use path-scoped `git diff --name-only CREATED CURRENT -- <governing paths>` and inspect contracts, not distance alone. See `references/commit-drift-review.md`.
13. **Skipping the review stamp when content is unchanged** — a no-op body review still sets `compatibility_reviewed_with_hermes_commit` to current HEAD. Otherwise every later invocation redoes the same inspection.
14. **Adding commit fields that break the 200-line body budget** — prefer `.usage.json` sidecar fields when frontmatter would push SKILL.md over the authored limit. After writing the sidecar, re-read it and `skill_view` so a later skill tool write did not drop the keys.
15. **Guessing creation from timestamps** — `created_at` and file mtime are not provenance. Use session evidence, reflog interval, or record `unknown`.
16. **Coupling skill gates to `skills.write_approval`** — staging config is separate from prompt-level gates. When the user or governing skill takes write_approval out of the equation, strip every mention, inspect, set, dependency, and validation claim. Don't reintroduce the flag through residual steps, evidence fields, or SOUL-adjacent checklist items.
17. **Background curator vs manual skills** — autonomous background review may patch only agent-created local skills. Manual skills (`created_by` unset) need a foreground session or explicit user direction. Don't treat a blocked manual-skill patch as permission to fork a near-duplicate.
18. **Shipping a skill validator without orphan-graph negatives** — pass fixtures alone prove little. Include forged checks, missing evidence, failed gates, incomplete risks/cleanup, unexpected files, invalid waivers, and orphan or unknown IDs for every collection the schema defines.
19. **Stale review packet after a fix** — any post-review edit to skill files or evidence requires a fresh packet and recomputed integrity hashes before the next review cycle or final PASS. Live-correct files with stale packet metadata are still BLOCKED.
20. **Acting on delayed reviews of old packets** — async reviewers finish out of order. Match returned packet SHA, ledger count, fixture count, and scoped sizes to the current freeze. Discard mismatches. Re-check live text before re-applying a fix. Only a current-packet PASS closes whole-change review.
21. **Component PASS sold as whole-skill PASS** — focused fixture or file checks never prove the full mutation. Keep subtask and whole-change status separate in the final report.
22. **Copying another task's fixtures** — generate fixtures from the skill's current schema. Don't reuse plan-skill-hardening or other session fixtures as if they were generic.
23. **Treating missing reviewer checksum as failure** — read-only reviewers may lack a hash tool. Main-session `packet-integrity.json` already proves packet identity. Don't block solely because the reviewer could not recompute SHA-256.
24. **Patching a fail-open hole without RED** — write the negative fixture that is accepted today, record the exit or traceback, then patch. A fix without a failing fixture is not closed. Full class matrix: `references/skill-mutation-validation.md`.
25. **Requiring active override == installed source** — bundled-skill hardening through the profile override must leave installed Hermes source unchanged. Active files should diverge. Assert `installed_source_unchanged`, not byte identity with the override.
26. **Green fixture matrix without fail-open classes** — a passing case count does not prove path confinement, `type(exit_code) is int` (bool equals 0/1), reverse `evidence.validator_id` reciprocity, residual-risk orphans/duplicates, content-bound human/machine match, or producer-bound aggregates. Independent review must probe live code for those holes and add RED fixtures before any PASS. Full matrix: `references/skill-mutation-validation.md`.
27. **Independent reviewer trusts packet counts** — re-count ledger IDs and validator cases on disk. Count `"id": "PREFIX-###"` for ledger size; do not use `"source_file"` alone. Reconcile exit-0 / exit-1 / other exit distributions against `validator-tests.json`. Reviewer procedure: `references/skill-mutation-validation.md` (Acting as the independent reviewer).
28. **Fancy regex in read-only review** — default ripgrep rejects lookahead. Use simple counts and `read_file` slices instead of PCRE lookarounds when verifying enums or absence claims.
29. **Whole-change PASS before post-review freeze check** — when an async review returns PASS, re-hash the live packet and every `review_scope` path, write `independent-review.json`, re-run the full fixture matrix, then set whole-change PASS. Never flip PASS while review is still pending, and never skip the post-return integrity recheck. Sequence: `references/skill-mutation-validation.md` (Main session after independent review returns).
30. **Bulk author rewrite without classification** — local and user-edited bundled skills are in scope; unmodified bundled and hub skills stay upstream. Snapshot with `hermes curator backup` first. Full recipe: `references/bulk-metadata-normalization.md`.
31. **Snapshot equality over the whole skills tree** — `.usage.json` and concurrent body/reference changes can drift. Assert the planned `SKILL.md` set and intended frontmatter fields only; keep concurrent body changes.
32. **Independent package review shortcuts** — do not trust packet `equal:` hashes without re-hashing live files; do not accept open disposition taxonomies or conflicting audit counts; do not treat prompt text as secret isolation under bypass + broad tools; do not treat skills-guard hits on inspection-only foreign settings paths as automatic blockers. Full checklist: `references/independent-skill-package-review.md`.
33. **Frozen review shortcuts** — re-prove identity, every blob, and nested config. See `references/frozen-distribution-package-review.md`.
34. **Stale source inventory** — freeze mapped sources while open; re-hash last. Drift blocks. See `references/frozen-distribution-package-review.md`.
35. **Reusing BLOCKED** — fix, re-freeze, rebuild, and review a new SHA before push. See `references/frozen-distribution-package-review.md`.

## Multi-file mutation closeout

After a non-trivial skill rewrite that adds or changes support files, schemas, or scripts, run the package in `references/skill-mutation-validation.md`. Use a meaning ledger when prior rules must survive. Generate pass and negative fixtures from the current schema, including fail-closed classes for schema shape, path confinement, strict integer exit codes, evidence provenance, reverse producer links, residual-risk orphans, whole-plan scope, producer-bound aggregates, content-bound human/machine match, and waivers. RED each fail-open hole before the fix. Freeze a review packet, then re-hash it after every fix. Discard delayed reviews of older packets. After a current-packet PASS, re-check freeze integrity, persist the verdict, re-run fixtures, then separate subtask and whole-change PASS. For read-only security, contradiction, and packet-quality review of a live skill, follow `references/independent-skill-package-review.md`. For frozen Toolbox/profile distribution trees, follow `references/frozen-distribution-package-review.md`.

## Support files

- `references/skill-prune-residuals.md` — prune search matrix and verifier sketch
- `references/commit-drift-review.md` — invocation compatibility gate: classify, diff, sidecar, stamp
- `references/skill-mutation-validation.md` — multi-file skill rewrite closeout: ledger, RED/GREEN fixtures, fail-closed matrix, frozen packet, independent-reviewer procedure, main-session post-review PASS sequence, honest PASS labels
- `references/independent-skill-package-review.md` — read-only security/contradiction/packet review: live hash re-proof, closed taxonomies, delegation security contracts, guard false positives
- `references/frozen-distribution-package-review.md` — frozen distribution: identity, privacy, nested config RED, root-copy install/update, and remediation re-review
- `references/bulk-metadata-normalization.md` — classify local vs edited-bundled vs hub; bulk author/description fix; curator backup; scoped snapshot verify

## Verification Checklist

- [ ] Pre: pin, cron, profile scope confirmed
- [ ] Post: package / telemetry / snapshot / reports / cron / CLI checks pass
- [ ] Hash-backed reports recomputed if edited
- [ ] Ad-hoc verify treated as targeted, not "suite green"
- [ ] After create/edit/patch: description < 60 chars, body after frontmatter < 200 lines, full file ≤ 100,000 chars
- [ ] Description starts with `Use when ...` and names only the exact trigger class
- [ ] User-created and user-edited skills use `author: Kiren Srinivasan`
- [ ] Temporary hermes-verify / review-packet scripts and one-shot review cron cleaned up
- [ ] After a user-created skill compatibility review: creation commit preserved, reviewed commit equals installed HEAD, sidecar re-read if used
- [ ] No residual `skills.write_approval` coupling when the governing skill or user removed that flag from the equation
- [ ] Multi-file rewrites: mutation-validation package complete; packet integrity matches the latest live files; independent review matches the current packet; post-review freeze recheck and fixture re-run done before whole-change PASS; subtask and whole-change status reported separately
- [ ] Completion-report validators: fail-closed matrix covers bool exit codes, report-dir path confinement, reverse producer links, residual-risk orphans, content-bound human/machine equality, and producer-bound aggregates
- [ ] Bulk metadata passes: curator backup taken; only classified targets changed; concurrent body changes kept
