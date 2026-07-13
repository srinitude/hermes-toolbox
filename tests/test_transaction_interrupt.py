"""Interruptions during package replacement restore the last-known-good tree."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.support import add_scripts_path

add_scripts_path()
import package_swap as package_module  # noqa: E402
from export_transaction import run_transaction  # noqa: E402
from package_swap import recover_package, replace_package  # noqa: E402


def archive_unlink_interrupt(archive: Path):
    original = Path.unlink
    calls = 0

    def interrupted(path, *args, **kwargs):
        nonlocal calls
        if path == archive:
            calls += 1
            if calls == 1:
                raise OSError('trigger rollback')
            if calls == 2:
                raise KeyboardInterrupt
        return original(path, *args, **kwargs)

    return interrupted


def retry_build(staging: Path) -> list[str]:
    staging.mkdir()
    (staging / 'value.txt').write_text('retry\n')
    return []


class ArchiveDisposalInterruptionTests(unittest.TestCase):
    def test_interrupted_archive_restore_is_retryable(self):
        base = Path(tempfile.mkdtemp(prefix='transaction-archive-interrupt-'))
        self.addCleanup(shutil.rmtree, base, True)
        destination = base / 'package'
        staging = base / '.staging.package'
        destination.mkdir()
        staging.mkdir()
        (destination / 'value.txt').write_text('old\n')
        (staging / 'value.txt').write_text('new\n')
        archive = base / '.lkg.package.tar'
        interrupted_unlink = archive_unlink_interrupt(archive)

        with patch.object(Path, 'unlink', new=interrupted_unlink):
            with self.assertRaises(KeyboardInterrupt):
                replace_package(staging, destination)
        self.assertEqual((destination / 'value.txt').read_text(), 'old\n')
        self.assertTrue(run_transaction(destination, retry_build, 'fixture'))
        self.assertEqual((destination / 'value.txt').read_text(), 'retry\n')


class RunTransactionInterruptionTests(unittest.TestCase):
    def test_interrupted_locked_staging_is_clean_and_retryable(self):
        base = Path(tempfile.mkdtemp(prefix='transaction-interrupt-retry-'))
        self.addCleanup(shutil.rmtree, base, True)
        destination = base / 'package'
        destination.mkdir()
        (destination / 'value.txt').write_text('old\n')

        def locked_build(staging):
            locked = staging / 'locked'
            locked.mkdir(parents=True)
            (locked / 'value.txt').write_text('new\n')
            locked.chmod(0)
            return []

        with patch.object(package_module, '_archive', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                run_transaction(destination, locked_build, 'fixture')
        self.assertEqual((destination / 'value.txt').read_text(), 'old\n')
        self.assertFalse((base / '.staging.package').exists())

        def clean_build(staging):
            staging.mkdir()
            (staging / 'value.txt').write_text('retry\n')
            return []

        self.assertTrue(run_transaction(destination, clean_build, 'fixture'))
        self.assertEqual((destination / 'value.txt').read_text(), 'retry\n')


class InterruptionRollbackTests(unittest.TestCase):
    def test_keyboard_interrupt_restores_old_destination(self):
        base = Path(tempfile.mkdtemp(prefix='transaction-interrupt-'))
        self.addCleanup(shutil.rmtree, base, True)
        destination = base / 'package'
        staging = base / '.staging.package'
        destination.mkdir()
        staging.mkdir()
        (destination / 'value.txt').write_text('old\n')
        (staging / 'value.txt').write_text('new\n')
        with patch.object(package_module, '_archive', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                replace_package(staging, destination)
        self.assertEqual((destination / 'value.txt').read_text(), 'old\n')
        self.assertEqual((staging / 'value.txt').read_text(), 'new\n')
        recover_package(destination)
        self.assertEqual((destination / 'value.txt').read_text(), 'old\n')
