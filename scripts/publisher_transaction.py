#!/usr/bin/env python3
"""Whole-publisher rollback and exact path staging helpers."""
from __future__ import annotations

import subprocess
from pathlib import Path


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(['git', *args], cwd=repo, text=True,
                          capture_output=True, check=False)


def restore_clean(repo: Path, baseline: str) -> None:
    reset = git(repo, 'reset', '--hard', baseline)
    cleaned = git(repo, 'clean', '-fdx')
    status = git(repo, 'status', '--porcelain')
    if reset.returncode != 0:
        raise RuntimeError(f'publisher rollback reset failed: {reset.stderr.strip()}')
    if cleaned.returncode != 0:
        raise RuntimeError(f'publisher rollback clean failed: {cleaned.stderr.strip()}')
    if status.returncode != 0 or status.stdout:
        raise RuntimeError('publisher rollback did not restore a clean worktree and index')


def stage_paths(repo: Path, paths: list[str]) -> None:
    for rel in paths:
        target = repo / rel
        if target.exists() or target.is_symlink():
            result = git(repo, 'add', '--', rel)
        else:
            result = git(repo, 'rm', '-r', '--cached', '--ignore-unmatch', '--', rel)
        if result.returncode != 0:
            raise RuntimeError(f'could not stage accepted path {rel}: {result.stderr.strip()}')


class PublisherTransaction:
    """Restore the clean starting commit unless publication completes."""

    def __init__(self, repo: Path):
        self.repo = repo
        result = git(repo, 'rev-parse', 'HEAD')
        if result.returncode != 0:
            raise RuntimeError('could not capture publisher starting HEAD')
        self.baseline = result.stdout.strip()
        self.complete = False

    def __enter__(self) -> 'PublisherTransaction':
        return self

    def finish(self) -> None:
        self.complete = True

    def __exit__(self, exc_type, exc, traceback) -> bool:
        if not self.complete:
            restore_clean(self.repo, self.baseline)
        return False
