---
name: hermes-state-db-wal
description: "Use when diagnosing Hermes state.db WAL advisories."
version: 1.0.0
author: Kiren Srinivasan
metadata:
  hermes:
    tags: [hermes, sqlite, wal, doctor, state.db, troubleshooting]
    related_skills: [hermes-agent]
    created_by: agent
    created_with_hermes_commit: unknown
    compatibility_reviewed_with_hermes_commit: 5988fe6cd5547d3620df1de889ac6007f5463b4d
---

# Hermes state.db WAL diagnosis

Use when:

- `hermes doctor` warns about a large `state.db-wal` (often >50 MiB)
- the user asks what WAL is or why doctor flagged session storage
- after `hermes doctor --fix`, the user asks whether the WAL shrank
- session search or multi-process Hermes use may be holding the session DB open

Do not treat a large physical WAL alone as corruption or as a failed plan or policy validation. Session-store maintenance is separate from SOUL, AGENTS, and workspace-policy correctness unless `state.db` integrity or lock errors block work.

## Core model

Hermes keeps the canonical session store at `$HERMES_HOME/state.db` (default `~/.hermes/state.db`) with SQLite **Write-Ahead Logging**:

| Path | Role |
|------|------|
| `state.db` | Main DB (sessions, FTS, messages) |
| `state.db-wal` | Committed changes not yet fully absorbed or still allocated for reuse |
| `state.db-shm` | Shared-memory WAL index and locks (not the primary content) |

Writers append to the WAL. Readers can proceed concurrently. A **checkpoint** copies eligible WAL pages into `state.db`. After reset or reuse, the physical `-wal` file often stays at its high-water size even when little content is still active.

Upstream: https://sqlite.org/wal.html

## Doctor thresholds (physical size only)

Hermes Doctor checks the **on-disk byte size** of `state.db-wal`, not active frames:

- informational above ~10 MiB
- warning above ~50 MiB

Source of truth in a git install: `hermes_cli/doctor.py` (WAL size check near the session-store health section). Re-open that file if numbers drift.

**Pitfall:** Doctor can keep warning while logical active content is only a few MiB.

## What `hermes doctor --fix` does

Doctor fix runs approximately:

```sql
PRAGMA wal_checkpoint(PASSIVE);
```

PASSIVE:

- copies frames that can be checkpointed without waiting hard for every reader or writer
- does **not** truncate the allocated WAL file to zero
- can leave physical size unchanged while reducing active frames

So after `--fix`:

1. Measure physical size again.
2. Measure active frames from the SHM index (below).
3. Report both. Do not claim disk was reclaimed if only `mxFrame` dropped.

To shrink the physical file, SQLite needs either:

- all clients closed cleanly so the last close can remove `-wal` and `-shm`, or
- a controlled `TRUNCATE` (or RESTART + truncate path) with no active multi-process use

Never delete `state.db-wal` while any Hermes process has the DB open. Committed data may still depend on it.

## Safe read-only inspection (preferred first)

Do not issue checkpoint PRAGMAs while explaining size unless the user asked for cleanup.

1. Confirm open clients: `lsof $HERMES_HOME/state.db $HERMES_HOME/state.db-wal $HERMES_HOME/state.db-shm`
2. Record physical sizes of `state.db`, `state.db-wal`, `state.db-shm`
3. Parse the WAL header for page size and frame capacity (see `references/wal-probe.md`)
4. Parse the SHM header for `mxFrame` and `nBackfill` (native endian on the host)
5. Active logical size ≈ `32 + mxFrame * (page_size + 24)` when page_size is 4096 (frame header is 24 bytes)
6. Compare active MiB to physical MiB; if active ≪ physical, the advisory is mostly high-water allocation

Hermes session code sets `journal_mode=WAL` with macOS durability helpers; it does **not** custom-set `wal_autocheckpoint` on `state.db` in normal setup. SQLite’s default auto-checkpoint is 1000 pages. Confirm in `hermes_state.py` (`apply_wal_with_fallback`) if behavior changes.

## Urgency rubric

Low urgency when:

- SHM headers consistent (`isInit`, matching dual header copies)
- integrity and doctor schema checks pass
- Hermes still reads and writes sessions
- active frames are modest relative to allocation

Escalate when:

- active frames stay large and keep growing
- `database is locked`, malformed schema, or I/O errors appear
- disk is constrained and physical WAL keeps climbing after real load

## Controlled reclaim (only when user wants disk back)

1. Tell the user every Hermes surface must stop: CLI/TUI, desktop, gateway, dashboard, other profiles using the same `$HERMES_HOME` if shared incorrectly.
2. Back up `state.db` (and preferably the trio of db/wal/shm if present).
3. With no other clients, run a TRUNCATE-style checkpoint under SQLite, or allow a clean last-close.
4. Verify sizes and a quick integrity check before restarting Hermes.
5. Do not invent “delete the wal file” as the default fix.

## Response shape for users

Lead with the answer (shrank or not), then a small before/after table: physical size, active frames, estimated active MiB. Separate “logical checkpoint progress” from “disk reclaimed.” Keep WAL mechanics short unless the user asked for a full lesson.

## References

- `references/wal-probe.md` — header fields, probe snippets, PASSIVE vs TRUNCATE
