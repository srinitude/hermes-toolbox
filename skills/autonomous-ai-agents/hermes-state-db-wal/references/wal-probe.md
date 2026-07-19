# WAL probe notes for Hermes state.db

Paths (profile-aware):

```text
$HERMES_HOME/state.db
$HERMES_HOME/state.db-wal
$HERMES_HOME/state.db-shm
```

Default profile: `~/.hermes/`.

## Physical vs logical

| Quantity | How to read | Doctor uses it? |
|----------|-------------|-----------------|
| Physical WAL size | `stat` on `state.db-wal` | Yes (10 / 50 MiB thresholds) |
| Active frames | SHM `mxFrame` | No |
| Backfilled frames | SHM `nBackfill` | No |
| Logical active bytes | `32 + mxFrame * (page_size + 24)` | No |

When physical size is large and `mxFrame` is small, SQLite is reusing a large allocated WAL. PASSIVE checkpoint can lower `mxFrame` without changing physical size.

## WAL file header (big-endian)

First 32 bytes of `state.db-wal` (see https://sqlite.org/fileformat2.html#walformat):

- magic `0x377f0682` or `0x377f0683`
- file format version (commonly `3007000`)
- page size (if value is `1`, page size is 65536)
- checkpoint sequence number

Frame size = `page_size + 24`.
Capacity frames ≈ `(file_size - 32) // (page_size + 24)`.

Do not treat the second 32-bit field as page size; version and page size are distinct fields.

## SHM (wal-index) header (native endian)

`state.db-shm` is host endian. Useful fields in the first header copy:

- page size field near the start of the index header
- `mxFrame` — last valid frame in the current WAL cycle
- `nBackfill` — frames already copied into the main DB
- uncheckpointed estimate: `max(0, mxFrame - nBackfill)`

There are two copies of the header; if they match and `isInit` is set, the index is usable for a size explanation. Recovery details: https://sqlite.org/walformat.html

## Minimal Python probe (read-only)

```python
from pathlib import Path
import struct

home = Path.home() / ".hermes"  # or Path(os.environ["HERMES_HOME"])
wal, shm = home / "state.db-wal", home / "state.db-shm"
prev = None  # set if comparing before/after doctor --fix

out = {"physical_bytes": wal.stat().st_size if wal.exists() else 0}
if wal.exists() and wal.stat().st_size >= 32:
    magic, version, page_size, ckpt_seq = struct.unpack(">IIII", wal.read_bytes()[:16])
    if page_size == 1:
        page_size = 65536
    frame = page_size + 24
    out.update(
        magic=hex(magic),
        version=version,
        page_size=page_size,
        checkpoint_seq=ckpt_seq,
        capacity_frames=(wal.stat().st_size - 32) // frame,
    )
if shm.exists() and shm.stat().st_size >= 120:
    b = shm.read_bytes()[:120]
    # mxFrame at offset 16, nBackfill at 96 of first header (little-endian on Apple Silicon/x86)
    mx = struct.unpack_from("<I", b, 16)[0]
    n_back = struct.unpack_from("<I", b, 96)[0]
    page_field = struct.unpack_from("<H", b, 14)[0]
    page = 65536 if page_field == 1 else page_field
    out.update(
        mx_frame=mx,
        n_backfill=n_back,
        logical_bytes=32 + mx * (page + 24),
        uncheckpointed=max(0, mx - n_back),
    )
print(out)
```

Adjust endianness only if probing a foreign-architecture SHM copy. Live local probes on the machine running Hermes use native endian.

## Checkpoint modes (do not improvise)

| Mode | Typical use | Truncates WAL file? |
|------|-------------|---------------------|
| PASSIVE | `hermes doctor --fix` | No |
| FULL / RESTART | stronger flush; still may not free allocation the way users expect | No (unless later reset path removes file) |
| TRUNCATE | intentional reclaim when idle | Yes, on success |

Docs: https://sqlite.org/pragma.html#pragma_wal_checkpoint

## Open clients

```bash
lsof "$HERMES_HOME/state.db" "$HERMES_HOME/state.db-wal" "$HERMES_HOME/state.db-shm"
```

Multiple `python` PIDs with those files open explain why TRUNCATE or file removal is unsafe mid-session.

## Hermes source anchors (re-verify if paths move)

- WAL enable + macOS fsync helpers: `hermes_state.py` → `apply_wal_with_fallback`, `_apply_macos_checkpoint_barrier`, `_enforce_macos_synchronous_full`
- Doctor size advisory + PASSIVE fix: `hermes_cli/doctor.py` session DB / WAL section
- Kanban notes about concurrent manual checkpoints with `wal_autocheckpoint=0` apply to kanban paths, not as a default claim for `state.db`

## Example session pattern (2026-07)

Physical `state.db-wal` ~81 MiB; SHM showed ~541 then ~102 active frames after `hermes doctor --fix`; physical size unchanged at 85,275,792 bytes. Active content ~2 MiB then ~0.4 MiB. Treat as allocation high-water + PASSIVE behavior, not as failed fix unless frames fail to drop and errors appear.
