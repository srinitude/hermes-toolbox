"""Native public profile distribution export pipeline contracts."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from tests.support import profile_export_sources, run_exporter, tree_bytes

PROFILE = 'pub-demo'
SKILL_REL = 'fixtures/complete-skill'
NATIVE_FILES = ['distribution.yaml', 'SOUL.md', 'config.yaml', 'README.md', 'manifest.json']
RUNTIME_RELICS = ['.env', 'auth.json', 'state.db', 'memories', 'sessions',
                  'logs', 'cache', 'cron']
REQUIRED_FIELDS = ['name', 'version', 'description', 'hermes_requires', 'author', 'license']


def export(repo: Path, home: Path, *extra: str):
    return run_exporter(repo, home, '--public-skill', SKILL_REL,
                        '--private-profile-prefix', 'priv-', *extra)


class ExportedPackageCase(unittest.TestCase):
    dest: Path

    @classmethod
    def setUpClass(cls):
        base = Path(tempfile.mkdtemp(prefix='profile-export-'))
        cls.addClassCleanup(shutil.rmtree, base, True)
        repo, home = profile_export_sources(base)
        result = export(repo, home, '--public-profile', PROFILE)
        if result.returncode != 0:
            raise AssertionError(result.stdout + result.stderr)
        cls.dest = repo / 'profiles' / PROFILE


class NativePackageTests(ExportedPackageCase):
    def test_native_distribution_files_are_present(self):
        for name in NATIVE_FILES:
            self.assertTrue((self.dest / name).is_file(), name)
        self.assertTrue((self.dest / 'skills' / 'demo-guide' / 'SKILL.md').is_file())

    def test_provenance_fields_are_stripped(self):
        data = yaml.safe_load((self.dest / 'distribution.yaml').read_text(encoding='utf-8'))
        self.assertNotIn('source', data)
        self.assertNotIn('installed_at', data)
        for field in REQUIRED_FIELDS:
            self.assertTrue(data.get(field), field)
        self.assertEqual(data['name'], PROFILE)


class SanitizedPackageTests(ExportedPackageCase):
    def test_runtime_state_is_not_exported(self):
        for relic in RUNTIME_RELICS:
            self.assertFalse((self.dest / relic).exists(), relic)

    def test_config_keeps_only_reusable_settings(self):
        data = yaml.safe_load((self.dest / 'config.yaml').read_text(encoding='utf-8'))
        self.assertNotIn('_config_version', data)
        self.assertNotIn('paste_collapse_threshold', data)
        self.assertEqual(sorted(data), ['approvals', 'display', 'plugins', 'terminal', 'toolsets'])

    def test_manifest_records_staged_files(self):
        manifest = json.loads((self.dest / 'manifest.json').read_text(encoding='utf-8'))
        actual = sorted(p.relative_to(self.dest).as_posix() for p in self.dest.rglob('*')
                        if p.is_file() and p.name != 'manifest.json')
        self.assertEqual(manifest['type'], 'profile')
        self.assertIs(manifest['sanitized'], True)
        self.assertEqual(manifest['included_files'], actual)


class ProfileExportCase(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='profile-txn-'))
        self.addCleanup(shutil.rmtree, self.base, True)
        self.repo, self.home = profile_export_sources(self.base)
        self.source = self.home / 'profiles' / PROFILE
        self.dest = self.repo / 'profiles' / PROFILE

    def export_profile(self, *extra: str):
        return export(self.repo, self.home, '--public-profile', PROFILE, *extra)

    def entries(self, change_list: Path) -> list[str]:
        return [e for e in change_list.read_text(encoding='utf-8').split('\0') if e]


class ProfileSweepTests(ProfileExportCase):
    def test_source_profiles_are_not_swept_without_allowlist(self):
        result = export(self.repo, self.home)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.dest.exists())

    def test_unallowlisted_destination_is_retained_unchanged(self):
        baseline = self.export_profile()
        self.assertEqual(baseline.returncode, 0, baseline.stderr)
        before = tree_bytes(self.dest)
        result = export(self.repo, self.home)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(tree_bytes(self.dest), before)
        self.assertIn('retaining existing unallowlisted profile packages', result.stderr)


class ProfileTransactionCase(ProfileExportCase):
    def setUp(self):
        super().setUp()
        change_list = self.base / 'baseline.lst'
        baseline = self.export_profile('--change-list', str(change_list))
        self.assertEqual(baseline.returncode, 0, baseline.stderr)
        self.assertIn(f'profiles/{PROFILE}', self.entries(change_list))
        self.baseline = tree_bytes(self.dest)

    def assert_preserved(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(tree_bytes(self.dest), self.baseline)
        residue = [p for p in self.repo.rglob('*') if p.name.startswith(('.staging.', '.lkg.'))]
        self.assertEqual(residue, [])


class TransactionFailureTests(ProfileTransactionCase):
    def test_missing_owned_path_preserves_last_known_good(self):
        shutil.rmtree(self.source / 'skills')
        self.assert_preserved(self.export_profile())

    def test_missing_required_field_preserves_last_known_good(self):
        manifest = self.source / 'distribution.yaml'
        text = manifest.read_text(encoding='utf-8').replace('license: MIT\n', '')
        manifest.write_text(text, encoding='utf-8')
        self.assert_preserved(self.export_profile())

    def test_credential_config_preserves_last_known_good(self):
        with (self.source / 'config.yaml').open('a', encoding='utf-8') as fh:
            fh.write('display:\n  access_token: ' + 'a1b2c3d4e5f6a7b8c9d0\n')
        self.assert_preserved(self.export_profile())


class TransactionStabilityTests(ProfileTransactionCase):
    def test_unchanged_source_produces_empty_change_list(self):
        change_list = self.base / 'rerun.lst'
        result = self.export_profile('--change-list', str(change_list))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.entries(change_list), [])
        self.assertEqual(tree_bytes(self.dest), self.baseline)


if __name__ == '__main__':
    unittest.main()
