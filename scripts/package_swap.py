"""Crash-aware package swap preserving the last-known-good destination."""
from __future__ import annotations

import os
import shutil
import tarfile
from pathlib import Path


def _paths(destination: Path) -> tuple[Path, Path, Path, Path]:
    base = destination.parent / f'.lkg.{destination.name}'
    return (base, base.with_suffix(base.suffix + '.tar'),
            base.with_suffix(base.suffix + '.tar.tmp'),
            base.with_suffix(base.suffix + '.partial'))


def _remove(path: Path) -> None:
    if not path.exists():
        return
    shutil.rmtree(path) if path.is_dir() else path.unlink()


def remove_artifact(path: Path) -> None:
    try:
        _remove(path)
        return
    except OSError:
        if not path.is_dir() or path.is_symlink():
            raise
    for root, directories, _ in os.walk(path):
        Path(root).chmod(0o700)
        for name in directories:
            child = Path(root) / name
            if not child.is_symlink():
                child.chmod(0o700)
    _remove(path)


def _archive(backup: Path, archive: Path, temporary: Path) -> None:
    _remove(temporary)
    try:
        with tarfile.open(temporary, 'x') as bundle:
            bundle.add(backup, arcname='payload')
        os.rename(temporary, archive)
    except BaseException:
        _remove(temporary)
        raise


def _extract(archive: Path, destination: Path) -> tuple[Path, Path]:
    restore = destination.parent / f'.restore.{destination.name}'
    _remove(restore)
    restore.mkdir()
    try:
        with tarfile.open(archive) as bundle:
            bundle.extractall(restore, filter='data')
    except BaseException:
        _remove(restore)
        raise
    return restore, restore / 'payload'


def _restore_archive(staging: Path, destination: Path, backup: Path,
                     archive: Path, partial: Path) -> None:
    restore, payload = _extract(archive, destination)
    try:
        if destination.exists():
            remove_artifact(staging)
            os.rename(destination, staging)
        if backup.exists():
            remove_artifact(partial)
            os.rename(backup, partial)
        os.rename(payload, destination)
        archive.unlink()
        remove_artifact(partial)
    finally:
        _remove(restore)


def _restore_backup(staging: Path, destination: Path, backup: Path) -> None:
    remove_artifact(staging)
    if destination.exists():
        os.rename(destination, staging)
    os.rename(backup, destination)


def recover_package(destination: Path) -> None:
    """Settle hidden crash artifacts before starting another transaction."""
    backup, archive, temporary, partial = _paths(destination)
    staging = destination.parent / f'.staging.{destination.name}'
    restore = destination.parent / f'.restore.{destination.name}'
    remove_artifact(restore)
    _remove(temporary)
    if archive.exists() and tarfile.is_tarfile(archive):
        _restore_archive(staging, destination, backup, archive, partial)
        remove_artifact(staging)
        return
    if archive.exists():
        if destination.exists():
            _remove(archive)
            remove_artifact(backup)
            remove_artifact(partial)
            return
        raise tarfile.ReadError(f'invalid last-known-good archive: {archive}')
    if backup.exists():
        _restore_backup(staging, destination, backup)
        remove_artifact(staging)
        remove_artifact(partial)
        return
    remove_artifact(partial)


def replace_package(staging: Path, destination: Path) -> None:
    """Swap staging into place and restore exact old bytes on failure."""
    recover_package(destination)
    backup, archive, temporary, partial = _paths(destination)
    if destination.exists():
        os.rename(destination, backup)
    try:
        os.rename(staging, destination)
    except BaseException:
        if backup.exists():
            _restore_backup(staging, destination, backup)
        raise
    if not backup.exists():
        return
    try:
        _archive(backup, archive, temporary)
        shutil.rmtree(backup)
        archive.unlink()
    except BaseException:
        if archive.exists():
            _restore_archive(staging, destination, backup, archive, partial)
        elif backup.exists():
            _restore_backup(staging, destination, backup)
        else:
            return
        raise
