#!/usr/bin/env python3
"""Whole-batch rollback for public exports: a late failure restores every
selected destination and both inventory files byte-for-byte."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

INVENTORY_FILES = ('public-manifest.json', 'source-fingerprints.json')
RESIDUE_PREFIXES = ('.staging.', '.lkg.')


def _remove(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()


def _copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target, symlinks=True)
    else:
        shutil.copy2(source, target)


class BatchTransaction:
    def __init__(self, repo: Path, destinations: list[Path]) -> None:
        inventories = [repo / 'inventory' / name for name in INVENTORY_FILES]
        self.targets = list(dict.fromkeys(list(destinations) + inventories))

    def __enter__(self) -> 'BatchTransaction':
        self.backup = Path(tempfile.mkdtemp(prefix='toolbox-batch-'))
        for index, target in enumerate(self.targets):
            if target.exists():
                _copy(target, self.backup / str(index))
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        try:
            if exc_type is not None:
                self._restore()
        finally:
            shutil.rmtree(self.backup, ignore_errors=True)
        return False

    def _restore(self) -> None:
        for index, target in enumerate(self.targets):
            for prefix in RESIDUE_PREFIXES:
                _remove(target.parent / f'{prefix}{target.name}')
            _remove(target)
            snapshot = self.backup / str(index)
            if snapshot.exists():
                _copy(snapshot, target)
