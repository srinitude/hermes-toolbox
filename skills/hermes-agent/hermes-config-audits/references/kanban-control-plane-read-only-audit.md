# Read-only Hermes Project/Kanban control-plane audit

Use this reference when auditing profiles, Projects, boards, plugins, and Kanban worker-lane wiring without changing live state. Re-verify every source/schema claim against the installed Hermes version.

## Strict read-only boundary

- Use native read surfaces only: `hermes profile list/info`, `hermes project list/show`, `hermes kanban boards list/show`, `hermes kanban list/stats/assignees`, and `hermes plugins list --json`.
- Never run mutation verbs (`create`, `use`, `switch`, `bind-board`, `assign`, `complete`, `block`, `unblock`, `enable`, config setters) during an audit.
- Do not inspect `.env`, auth stores, token files, sessions, logs, caches, or SQLite files directly. Native CLI output may report DB paths; recording the path is not permission to open the DB.
- Under a literal “do not modify cache/runtime state” requirement, avoid `web_extract`: long-page extraction may write a tool-managed copy under `~/.hermes/cache/web/`. Prefer already-collected first-party evidence, live CLI help, and installed source reads.
- Set `PYTHONDONTWRITEBYTECODE=1` for read-only Python/CLI probes.

## Inventory sequence

1. Establish installed version, active profile, and complete profile list.
2. Recompute eligible consumers from the live list; do not reuse a plan’s stale list. Apply exclusion rules mechanically.
3. Inventory `project`/`kanban`/`plugins` help surfaces and important flags. In particular, distinguish global board scope (`kanban --board`) from command-specific filters.
4. Enumerate Projects in the intended profile universe. Project state is per-profile.
5. Enumerate all boards, current board, counts, assignees, and task summaries through native CLI JSON.
6. For each profile, parse `plugins list --json` and report user-plugin enablement plus whether the target plugin is discovered. Inspect only `plugins.entries` from config when tool-override state is required.
7. Inventory worker human-authored files (`config.yaml`, `SOUL.md`, `README.md`, `distribution.yaml`, and workflow `SKILL.md`) with paths and hashes; avoid treating every bundled/copied skill as phase-contract prose.
8. Compare worker instructions to live tool schemas and gating source before calling anything a mismatch.

## High-value contract checks

### Orchestrator surface vs task-worker surface

Inspect installed `tools/kanban_tools.py` and `model_tools.py`:

- `HERMES_KANBAN_TASK` normally injects lifecycle tools into dispatched workers, even if their profile does not persistently enable the `kanban` toolset.
- An explicit `kanban` toolset in an unscoped normal profile can expose orchestrator-style board routing.
- Check each tool’s actual `check_fn`; names mentioned in docs are not proof a task-scoped worker can call them.
- If a single-ingress policy exists, phase-worker guides should explicitly forbid creating/linking/routing sibling phases even when a broad tool happens to be visible.

### Dependency and review-gate liveness

Native child promotion normally requires all parents to reach `done`. Therefore:

- A linear DAG deadlocks if an upstream phase ends in `blocked` while its child depends on it.
- A later Review task cannot unblock upstream blocked parents if it depends on those parents becoming `done` first.
- Verify whether `kanban_unblock` is available to a dispatcher-scoped Review worker; in some installed versions it is orchestrator-only and hidden whenever `HERMES_KANBAN_TASK` is set.
- Prefer completing a phase with structured `summary` + `metadata` after its exit gate. Put human approval blocks before irreversible actions, or make an unscoped orchestrator own explicit review-required gates.

### Schema-level instruction validation

Check examples against live JSON schemas:

- `kanban_comment` may require both `task_id` and `body`, even when other lifecycle tools default to `HERMES_KANBAN_TASK`.
- Do not document arguments such as `scheduled_at` unless they are present in the installed `kanban_create` schema and CLI.
- `kanban_block.kind` is an enum; prose prefixes such as `review-required:` are not necessarily typed kinds.
- `kanban_complete(summary=..., metadata=...)` is the structured downstream handoff surface when verified by the installed schema.

### Conditional phase routing

A design-skip exception cannot be represented safely by pre-linking Plan permanently to Design. If routing depends on evidence collected after Brainstorm, create/link the next phase incrementally after the orchestrator records the decision. Keep the exception test and evidence in orchestrator-owned state.

### Cross-profile Projects, copied builders, and distribution drift

Treat these as separate compatibility planes:

- **Projects are per-profile; boards are shared.** A Project visible under default is not visible to a plugin bound to another profile. Record every `projects.db` path only as presence, enumerate through `hermes -p <profile> project list/show`, and treat a missing `board:` line from `project show` as unbound after checking the installed output contract. Never read or edit the DB directly.
- **Control-plane plugin copies and builder-skill copies have different drift models.** Hash plugin source files against each eligible consumer copy, excluding generated caches. Separately hash `profile-builder` and `plugin-builder` trees across profiles. Builder copies often carry intentional profile-specific references, so report missing/changed/extra files and prescribe a merge of canonical core files rather than a wholesale directory replacement.
- **Self-bootstrap must include the builder itself.** If a profile-builder claims the new profile can use the workflow that created it, its bootstrap set must include `profile-builder`, not only supporting skills. Do not blindly source bootstrap files from the active named profile; validate a canonical source first so stale copies do not propagate.
- **Installed distributions can be newer than their recorded source.** Compare `config.yaml`, `distribution.yaml`, `README.md`, `SOUL.md`, and the workflow `SKILL.md` against the recorded source path. If live files differ, flag reinstall/update regression risk and require a durable canonical source before rollout.
- **README toolsets are not config.** Compare documented toolsets to persisted `toolsets` and to dispatcher injection semantics. Worker READMEs that list persistent `kanban` while config intentionally relies on `HERMES_KANBAN_TASK` are misleading even if dispatched execution works.
- **Dependency blocks need an unfinished dependency.** A Review worker that calls `kanban_block(kind="dependency")` after all existing parents are done can immediately re-promote. Use a fail-closed human/orchestrator handoff until remediation is linked, then explicitly unblock/promote through the unscoped orchestrator.
- **Documentary recurrence is not automation.** A Maintain profile that says “weekly cron” is not scheduled unless a live cron job exists in the chosen owning profile.

### Publisher and cron preflight

When a source workshop is consumed by cron or publisher automation:

1. Run native cron listing for every plausible owner profile; the publisher may live under default rather than the source profile.
2. Locate the wrapper, scanner, exporter, and publisher scripts read-only.
3. Determine whether export scans every child directory or uses an explicit allowlist/opt-out.
4. Inspect repository status before recommending resume. A failed exporter may leave a dirty candidate tree even when no commit/push occurred.
5. Treat source creation, candidate export, commit, push, and publication as separate approvals. A paused publisher should remain paused until both repository drift and package inclusion policy are resolved.
6. If the inspection runtime auto-spools oversized output to `/tmp` or another cache, disclose the exact path and do not delete it under a strict read-only scope.

## Reporting discipline

Separate:

- current inventory;
- observed state drift relative to the proposed policy;
- concrete tool/schema contradictions;
- optional alignments.

Do not label old tasks “wrong” merely because they predate a new policy. Report them as drift, preserve history, and recommend orchestrator-led remediation rather than silent reassignment.

End with an explicit mutation statement. If a managed tool created a cache artifact despite the boundary, disclose it rather than claiming a perfectly side-effect-free audit.