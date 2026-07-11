"""Fail-closed checks applied to candidate source trees before staging."""
from __future__ import annotations

from pathlib import Path


def reject_source_symlinks(src: Path) -> None:
    links = [src] if src.is_symlink() else []
    links += [path for path in sorted(src.rglob('*')) if path.is_symlink()]
    if links:
        names = [str(path.relative_to(src)) if path != src else '.' for path in links]
        raise ValueError('source contains forbidden symlink: ' + ', '.join(names))
