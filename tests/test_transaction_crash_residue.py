"""Crash-residue and transaction-entry cleanup contracts."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.support import add_scripts_path

add_scripts_path()
import batch_transaction as batch_module  # noqa: E402
from batch_transaction import BatchTransaction  # noqa: E402
from package_swap import recover_package, remove_artifact  # noqa: E402


class RestoreResidueTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='transaction-restore-'))
        self.addCleanup(shutil.rmtree, self.base, True)

    def test_stale_restore_tree_is_settled(self):
        destination = self.base / 'demo'
        destination.mkdir()
        (destination / 'value.txt').write_text('old\n')
        restore = self.base / '.restore.demo'
        restore.mkdir()
        (restore / 'residue.txt').write_text('residue\n')
        recover_package(destination)
        self.assertEqual((destination / 'value.txt').read_text(), 'old\n')
        self.assertFalse(restore.exists())


class LockedBackupRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='transaction-backup-'))
        self.addCleanup(shutil.rmtree, self.base, True)

    def test_visible_destination_settles_locked_backup_and_archive(self):
        destination = self.base / 'demo'
        destination.mkdir()
        (destination / 'value.txt').write_text('current\n')
        backup = self.base / '.lkg.demo'
        locked = backup / 'locked'
        locked.mkdir(parents=True)
        locked.chmod(0)
        (self.base / '.lkg.demo.tar').write_bytes(b'stale')
        recover_package(destination)
        self.assertEqual((destination / 'value.txt').read_text(), 'current\n')
        self.assertFalse(any(self.base.glob('.lkg.demo*')))


class BatchEntryCleanupTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='transaction-enter-'))
        self.addCleanup(shutil.rmtree, self.base, True)

    def test_snapshot_is_removed_when_entry_copy_fails(self):
        target = self.base / 'repo/packages/demo'
        target.mkdir(parents=True)
        (target / 'value.txt').write_text('old\n')
        transaction = BatchTransaction(self.base / 'repo', [target])
        target.chmod(0)
        try:
            with self.assertRaises(OSError):
                transaction.__enter__()
        finally:
            target.chmod(0o700)
        self.assertFalse(transaction.backup.exists())


class BatchRestoreRetryTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='transaction-retry-'))
        self.addCleanup(shutil.rmtree, self.base, True)

    def test_failed_rollback_retains_snapshot_for_retry(self):
        target = self.base / 'repo/packages/demo'
        target.mkdir(parents=True)
        value = target / 'value.txt'
        value.write_text('old\n')
        transaction = BatchTransaction(self.base / 'repo', [target])
        try:
            with self.assertRaises(OSError):
                with transaction:
                    value.write_text('new\n')
                    target.parent.chmod(0)
                    raise RuntimeError('late failure')
        finally:
            target.parent.chmod(0o700)
        self.assertEqual(value.read_text(), 'new\n')
        self.assertTrue(transaction.backup.exists())
        with BatchTransaction(self.base / 'repo', [target]):
            self.assertEqual(value.read_text(), 'old\n')
            value.write_text('retry\n')
        self.assertEqual(value.read_text(), 'retry\n')
        self.assertFalse(transaction.backup.exists())


class BatchExitCleanupTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='transaction-exit-'))
        self.addCleanup(shutil.rmtree, self.base, True)

    def test_clean_body_cleanup_failure_rolls_back(self):
        target = self.base / 'repo/packages/demo'
        target.mkdir(parents=True)
        value = target / 'value.txt'
        value.write_text('old\n')
        transaction = BatchTransaction(self.base / 'repo', [target])
        failures = 0

        def fail_backup_cleanup(path):
            nonlocal failures
            if path == transaction.backup and failures < 3:
                failures += 1
                raise OSError('injected cleanup failure')
            return remove_artifact(path)

        with self.assertRaises(OSError), patch.object(
                batch_module, 'remove_artifact', side_effect=fail_backup_cleanup):
            with transaction:
                value.write_text('new\n')
        self.assertEqual(value.read_text(), 'old\n')
        self.assertTrue(transaction.backup.exists())
        remove_artifact(transaction.backup)


class PartialCleanupRetryTests(unittest.TestCase):
    def test_partial_cleanup_retry_commits_without_false_failure(self):
        base = Path(tempfile.mkdtemp(prefix='transaction-partial-cleanup-'))
        self.addCleanup(shutil.rmtree, base, True)
        target = base / 'repo/packages/demo'
        target.mkdir(parents=True)
        value = target / 'value.txt'
        value.write_text('old\n')
        transaction = BatchTransaction(base / 'repo', [target])
        failed = False

        def fail_after_entry(path):
            nonlocal failed
            if path == transaction.backup:
                if not failed:
                    failed = True
                    remove_artifact(path / '0/value.txt')
                raise OSError('injected persistent partial cleanup')
            return remove_artifact(path)

        with patch.object(batch_module, 'remove_artifact', side_effect=fail_after_entry):
            with transaction:
                value.write_text('new\n')
        self.assertEqual(value.read_text(), 'new\n')
        self.assertFalse(transaction.backup.exists())


class LockedBatchResidueTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='transaction-locked-'))
        self.addCleanup(shutil.rmtree, self.base, True)

    def test_locked_partial_is_removed_after_batch_rollback(self):
        target = self.base / 'repo/packages/demo'
        target.mkdir(parents=True)
        (target / 'value.txt').write_text('old\n')
        partial = target.parent / '.lkg.demo.partial'
        with self.assertRaises(RuntimeError):
            with BatchTransaction(self.base / 'repo', [target]):
                partial.mkdir()
                locked = partial / 'locked'
                locked.mkdir()
                locked.chmod(0)
                raise RuntimeError('late failure')
        self.assertEqual((target / 'value.txt').read_text(), 'old\n')
        self.assertFalse(partial.exists())
