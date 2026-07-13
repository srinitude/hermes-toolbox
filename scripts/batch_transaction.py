#!/usr/bin/env python3
"""Whole-batch rollback for public exports: a late failure restores every
selected destination and both inventory files byte-for-byte."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from package_swap import recover_package, remove_artifact
from toolbox_common import sha, tree_sha

INVENTORY_FILES = ('public-manifest.json', 'source-fingerprints.json')
LKG_SUFFIXES = ('', '.tar', '.tar.tmp', '.partial')
ABSENT_SEAL = 'ABSENT'


def _residue_paths(target: Path) -> list[Path]:
    staging = target.parent / f'.staging.{target.name}'
    restore = target.parent / f'.restore.{target.name}'
    base = target.parent / f'.lkg.{target.name}'
    return [staging, restore,
            *(Path(str(base) + suffix) for suffix in LKG_SUFFIXES)]


def _remove_retry(path: Path) -> None:
    for attempt in range(3):
        try:
            remove_artifact(path)
            return
        except OSError:
            if attempt == 2:
                raise


def _copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target, symlinks=True)
    else:
        shutil.copy2(source, target)


def _snapshot_targets(targets: list[Path], backup: Path) -> None:
    try:
        for index, target in enumerate(targets):
            if target.exists():
                _copy(target, backup / str(index))
    except BaseException:
        remove_artifact(backup)
        raise


def _discard_partial(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def _snapshot_digest(path: Path) -> str:
    return tree_sha(path) if path.is_dir() else sha(path)


def _snapshot_complete(transaction: 'BatchTransaction') -> bool:
    if set(transaction.seals) != set(range(len(transaction.targets))):
        return False
    for index, seal in transaction.seals.items():
        snapshot = transaction.backup / str(index)
        if seal == ABSENT_SEAL:
            if snapshot.exists():
                return False
        elif not snapshot.exists() or _snapshot_digest(snapshot) != seal:
            return False
    return True


def _settle_success(transaction: 'BatchTransaction') -> None:
    try:
        _remove_retry(transaction.backup)
    except OSError:
        if not _snapshot_complete(transaction):
            _discard_partial(transaction.backup)
            return
        transaction._restore()
        raise


def _write_journal(transaction: 'BatchTransaction') -> None:
    data = {
        'targets': [str(target.resolve(strict=False)) for target in transaction.targets],
        'seals': transaction.seals,
    }
    temporary = transaction.backup / 'transaction.json.tmp'
    temporary.write_text(json.dumps(data, sort_keys=True), encoding='utf-8')
    temporary.replace(transaction.backup / 'transaction.json')


def _begin_snapshot(transaction: 'BatchTransaction') -> None:
    transaction.backup.mkdir(parents=True)
    try:
        present = {index for index, target in enumerate(transaction.targets)
                   if target.exists()}
        _snapshot_targets(transaction.targets, transaction.backup)
        transaction.seals = {
            index: (_snapshot_digest(transaction.backup / str(index))
                    if index in present else ABSENT_SEAL)
            for index in range(len(transaction.targets))}
        _write_journal(transaction)
    except BaseException:
        remove_artifact(transaction.backup)
        raise


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON member: {key}')
        result[key] = value
    return result


def _journal_seals(data: dict) -> dict[int, str]:
    raw = data['seals']
    if not isinstance(raw, dict):
        raise TypeError('seals must be a mapping')
    seals = {}
    for key, value in raw.items():
        index = int(key)
        if str(index) != key or not isinstance(value, str):
            raise ValueError('seal keys and values must be canonical strings')
        seals[index] = value
    return seals


def _recover_batch(transaction: 'BatchTransaction') -> None:
    if not transaction.backup.exists():
        return
    journal = transaction.backup / 'transaction.json'
    try:
        data = json.loads(journal.read_text(encoding='utf-8'),
                          object_pairs_hook=_unique_object)
        saved_targets = data['targets']
        transaction.seals = _journal_seals(data)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise RuntimeError(f'invalid retained batch rollback journal: {journal}') from exc
    current = [str(target.resolve(strict=False)) for target in transaction.targets]
    if saved_targets != current or not _snapshot_complete(transaction):
        raise RuntimeError(f'retained batch rollback does not match retry: {journal}')
    transaction._restore()
    remove_artifact(transaction.backup)


class BatchTransaction:
    def __init__(self, repo: Path, destinations: list[Path]) -> None:
        inventories = [repo / 'inventory' / name for name in INVENTORY_FILES]
        self.targets = list(dict.fromkeys(list(destinations) + inventories))
        self.backup = repo / '.git' / 'info' / 'toolbox-batch-rollback'
        self.seals: dict[int, str]

    def __enter__(self) -> 'BatchTransaction':
        _recover_batch(self)
        for target in self.targets:
            recover_package(target)
        _begin_snapshot(self)
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is not None:
            self._restore()
            remove_artifact(self.backup)
        else:
            _settle_success(self)
        return False

    def _restore(self) -> None:
        for index, target in enumerate(self.targets):
            remove_artifact(target)
            snapshot = self.backup / str(index)
            if snapshot.exists():
                _copy(snapshot, target)
            for residue in _residue_paths(target):
                _remove_retry(residue)
