"""Recoverable retained batch-journal regressions."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.support import add_scripts_path

add_scripts_path()
from batch_transaction import BatchTransaction  # noqa: E402


class RetainedBatchJournalCase(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='transaction-journal-'))
        self.addCleanup(shutil.rmtree, self.base, True)
        self.repo = self.base / 'repo'
        self.target = self.repo / 'packages/demo'
        self.target.mkdir(parents=True)
        (self.target / 'value.txt').write_text('old\n')

    def retain_failed_rollback(self) -> BatchTransaction:
        transaction = BatchTransaction(self.repo, [self.target])
        transaction.__enter__()
        (self.target / 'value.txt').write_text('new\n')
        with patch.object(transaction, '_restore', side_effect=OSError('blocked')):
            with self.assertRaises(OSError):
                transaction.__exit__(RuntimeError, RuntimeError('late'), None)
        return transaction


class SealKeyCanonicalityTests(RetainedBatchJournalCase):
    def test_duplicate_raw_seal_key_is_rejected(self):
        transaction = self.retain_failed_rollback()
        journal = transaction.backup / 'transaction.json'
        data = json.loads(journal.read_text())
        member = f'"0": "{data["seals"]["0"]}"'
        journal.write_text(journal.read_text().replace(member, f'{member}, {member}'))
        with self.assertRaises(RuntimeError):
            BatchTransaction(self.repo, [self.target]).__enter__()
        self.assertEqual((self.target / 'value.txt').read_text(), 'new\n')

    def test_noncanonical_seal_key_is_rejected(self):
        transaction = self.retain_failed_rollback()
        journal = transaction.backup / 'transaction.json'
        data = json.loads(journal.read_text())
        data['seals']['00'] = data['seals'].pop('0')
        journal.write_text(json.dumps(data))
        with self.assertRaises(RuntimeError):
            BatchTransaction(self.repo, [self.target]).__enter__()
        self.assertEqual((self.target / 'value.txt').read_text(), 'new\n')


class RetainedBatchJournalTests(RetainedBatchJournalCase):
    def test_missing_seal_cannot_accept_corrupted_bytes(self):
        transaction = self.retain_failed_rollback()
        journal = transaction.backup / 'transaction.json'
        data = json.loads(journal.read_text())
        data['seals'].pop('0')
        journal.write_text(json.dumps(data))
        (transaction.backup / '0/value.txt').write_text('damaged\n')
        with self.assertRaises(RuntimeError):
            BatchTransaction(self.repo, [self.target]).__enter__()
        self.assertEqual((self.target / 'value.txt').read_text(), 'new\n')

    def test_damaged_snapshot_is_not_consumed(self):
        transaction = self.retain_failed_rollback()
        (transaction.backup / '0/value.txt').write_text('damaged\n')
        with self.assertRaises(RuntimeError):
            BatchTransaction(self.repo, [self.target]).__enter__()
        self.assertEqual((self.target / 'value.txt').read_text(), 'new\n')
        self.assertTrue(transaction.backup.exists())

    def test_mismatched_retry_is_rejected(self):
        transaction = self.retain_failed_rollback()
        other = self.repo / 'packages/other'
        with self.assertRaises(RuntimeError):
            BatchTransaction(self.repo, [other]).__enter__()
        self.assertTrue(transaction.backup.exists())
