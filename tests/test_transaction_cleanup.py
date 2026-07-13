"""Real cleanup-failure rollback tests for package publication."""
from __future__ import annotations

import os
import shutil
import tarfile
import tempfile
import unittest
from pathlib import Path

from tests.support import add_scripts_path, tree_bytes

add_scripts_path()
from batch_transaction import BatchTransaction  # noqa: E402
from export_transaction import run_transaction  # noqa: E402
from package_swap import recover_package, replace_package  # noqa: E402


def _populate_before_locked(root: Path, locked: Path) -> None:
    for index in range(512):
        (root / f'old-{index:03}.txt').write_text(f'old-{index}\n')
        entries = list(os.scandir(root))
        locked_index = next(i for i, entry in enumerate(entries)
                            if entry.name == locked.name)
        if any(entry.is_file() for entry in entries[:locked_index]):
            return
    raise AssertionError('filesystem supplied no removable entry before locked directory')


class CleanupFailureRollbackTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='transaction-cleanup-'))
        self.addCleanup(shutil.rmtree, self.base, True)

    def test_backup_cleanup_failure_restores_old_destination(self):
        destination = self.base / 'package'
        staging = self.base / '.staging.package'
        destination.mkdir()
        (destination / 'value.txt').write_text('old\n')
        staging.mkdir()
        (staging / 'value.txt').write_text('new\n')
        destination.chmod(0o500)
        try:
            with self.assertRaises(OSError):
                replace_package(staging, destination)
        finally:
            destination.chmod(0o700)
        self.assertEqual((destination / 'value.txt').read_text(), 'old\n')
        self.assertFalse((self.base / '.lkg.package').exists())
        self.assertFalse(any(self.base.glob('.lkg.package*')))
        self.assertEqual((staging / 'value.txt').read_text(), 'new\n')


class PartialCleanupFailureTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='transaction-partial-'))
        self.addCleanup(shutil.rmtree, self.base, True)

    def test_partial_backup_cleanup_restores_exact_old_tree(self):
        destination = self.base / 'package'
        staging = self.base / '.staging.package'
        destination.mkdir()
        locked = destination / 'locked'
        locked.mkdir()
        (locked / 'b.txt').write_text('old-b\n')
        _populate_before_locked(destination, locked)
        old_tree = tree_bytes(destination)
        staging.mkdir()
        (staging / 'a.txt').write_text('new-a\n')
        locked.chmod(0)
        try:
            with self.assertRaises(OSError):
                replace_package(staging, destination)
        finally:
            for root in (destination, self.base / '.lkg.package'):
                candidate = root / 'locked'
                if candidate.exists():
                    candidate.chmod(0o700)
        self.assertEqual(tree_bytes(destination), old_tree)
        self.assertFalse(any(self.base.glob('.lkg.package*')))


class ArchiveRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='transaction-archive-'))
        self.addCleanup(shutil.rmtree, self.base, True)

    def test_corrupt_archive_does_not_consume_exact_backup(self):
        destination = self.base / 'package'
        backup = self.base / '.lkg.package'
        backup.mkdir()
        (backup / 'value.txt').write_text('old\n')
        archive = self.base / '.lkg.package.tar'
        archive.write_bytes(b'not a tar archive')
        with self.assertRaises(tarfile.TarError):
            recover_package(destination)
        self.assertEqual((backup / 'value.txt').read_text(), 'old\n')
        self.assertFalse(destination.exists())


class BatchResidueCleanupTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='transaction-residue-'))
        self.addCleanup(shutil.rmtree, self.base, True)

    def test_rollback_removes_all_hidden_lkg_suffix_states(self):
        repo = self.base / 'repo'
        target = repo / 'packages' / 'demo'
        target.mkdir(parents=True)
        (target / 'value.txt').write_text('old\n')
        with self.assertRaises(RuntimeError):
            with BatchTransaction(repo, [target]):
                (target / 'value.txt').write_text('new\n')
                for suffix in ('.tar', '.tar.tmp', '.partial'):
                    (target.parent / f'.lkg.demo{suffix}').write_text('residue')
                raise RuntimeError('late failure')
        self.assertEqual((target / 'value.txt').read_text(), 'old\n')
        self.assertFalse(any(target.parent.glob('.lkg.demo*')))


class CrashRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='transaction-recovery-'))
        self.addCleanup(shutil.rmtree, self.base, True)

    def test_hidden_backup_is_restored_before_staging_validation(self):
        destination = self.base / 'package'
        backup = self.base / '.lkg.package'
        backup.mkdir()
        (backup / 'value.txt').write_text('old\n')

        def invalid_build(staging: Path) -> list[str]:
            staging.mkdir()
            (staging / 'value.txt').write_text('invalid\n')
            return ['invalid candidate']

        with self.assertRaises(SystemExit):
            run_transaction(destination, invalid_build, 'candidate')
        self.assertEqual((destination / 'value.txt').read_text(), 'old\n')
        self.assertFalse(backup.exists())
        self.assertFalse((self.base / '.staging.package').exists())


class CrashStateSettlementTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='transaction-settlement-'))
        self.addCleanup(shutil.rmtree, self.base, True)

    def test_batch_rollback_preserves_recovered_lkg(self):
        destination = self.base / 'plugins' / 'package'
        backup = destination.parent / '.lkg.package'
        backup.mkdir(parents=True)
        (backup / 'value.txt').write_text('old\n')

        def invalid_build(staging: Path) -> list[str]:
            staging.mkdir()
            return ['invalid candidate']

        with self.assertRaises(SystemExit):
            with BatchTransaction(self.base, [destination]):
                run_transaction(destination, invalid_build, 'candidate')
        self.assertEqual((destination / 'value.txt').read_text(), 'old\n')
        self.assertFalse(backup.exists())


class StaleBackupSettlementTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='transaction-stale-'))
        self.addCleanup(shutil.rmtree, self.base, True)

    def test_existing_destination_discards_stale_lkg(self):
        destination = self.base / 'package'
        backup = self.base / '.lkg.package'
        destination.mkdir()
        backup.mkdir()
        (destination / 'value.txt').write_text('current\n')
        (backup / 'value.txt').write_text('old\n')

        def unchanged_build(staging: Path) -> list[str]:
            shutil.copytree(destination, staging)
            return []

        self.assertFalse(run_transaction(destination, unchanged_build, 'candidate'))
        self.assertFalse(backup.exists())


if __name__ == '__main__':
    unittest.main()
