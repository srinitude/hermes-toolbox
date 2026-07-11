"""Fail-closed selection policy contracts for public toolbox candidates."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from tests.support import (
    FIXTURES, add_scripts_path, make_home, make_repo, run_exporter, tree_bytes,
)

add_scripts_path()

from candidate_policy import (  # noqa: E402
    PolicyConfig, decide_plugin, plugin_candidate, read_allowlist,
    stale_plugin_destinations,
)
from export_transaction import plugin_package_manifest  # noqa: E402


def make_config(**overrides) -> PolicyConfig:
    values = {
        'public_plugins': ('complete-plugin',),
        'public_plugin_profile': 'pub-src',
        'private_profile_prefix': 'priv-',
    }
    values.update(overrides)
    return PolicyConfig(**values)


class PolicyCase(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='toolbox-policy-'))
        self.addCleanup(shutil.rmtree, self.base, True)
        self.home = make_home(self.base, plugins={'complete-plugin': FIXTURES / 'complete-plugin'})
        self.repo = self.base / 'repo'
        (self.repo / 'plugins').mkdir(parents=True)

    def candidate(self, name='complete-plugin', profile='pub-src'):
        return plugin_candidate(self.home, self.repo, name, profile)


class PluginGateTests(PolicyCase):
    def test_plugin_requires_explicit_allowlist_entry(self):
        decision = decide_plugin(self.candidate(), make_config(public_plugins=()))
        self.assertFalse(decision.accepted)
        self.assertTrue(any('allowlist' in reason for reason in decision.reasons))

    def test_private_prefix_is_rejected(self):
        shutil.copytree(FIXTURES / 'complete-plugin',
                        self.home / 'profiles' / 'pub-src' / 'plugins' / 'priv-secret')
        decision = decide_plugin(self.candidate(name='priv-secret'),
                                 make_config(public_plugins=('priv-secret',)))
        self.assertFalse(decision.accepted)
        self.assertTrue(any('private prefix' in reason for reason in decision.reasons))

    def test_wrong_source_profile_is_rejected(self):
        decision = decide_plugin(self.candidate(profile='other-profile'), make_config())
        self.assertFalse(decision.accepted)
        self.assertTrue(any('source profile' in reason for reason in decision.reasons))


class PluginSourceTests(PolicyCase):
    def test_missing_real_tests_is_rejected(self):
        shutil.rmtree(self.home / 'profiles' / 'pub-src' / 'plugins' / 'complete-plugin' / 'tests')
        decision = decide_plugin(self.candidate(), make_config())
        self.assertFalse(decision.accepted)
        self.assertTrue(any('real tests' in reason for reason in decision.reasons))

    def test_missing_source_is_rejected(self):
        decision = decide_plugin(self.candidate(name='ghost-plugin'),
                                 make_config(public_plugins=('ghost-plugin',)))
        self.assertFalse(decision.accepted)
        self.assertTrue(any('missing' in reason for reason in decision.reasons))

    def test_complete_allowlisted_candidate_is_accepted(self):
        decision = decide_plugin(self.candidate(), make_config())
        self.assertEqual(decision.reasons, ())
        self.assertTrue(decision.accepted)

    def test_traversal_plugin_name_is_rejected(self):
        decision = decide_plugin(self.candidate(name='../escape'),
                                 make_config(public_plugins=('../escape',)))
        self.assertFalse(decision.accepted)


class AllowlistInputTests(PolicyCase):
    def test_duplicate_allowlist_entries_error(self):
        allowlist = self.base / 'plugin-allowlist.txt'
        allowlist.write_text('alpha\nbeta\nalpha\n', encoding='utf-8')
        with self.assertRaises(SystemExit):
            read_allowlist(allowlist, 'public plugin')

    def test_traversal_allowlist_entry_errors(self):
        allowlist = self.base / 'plugin-allowlist.txt'
        allowlist.write_text('../outside\n', encoding='utf-8')
        with self.assertRaises(SystemExit):
            read_allowlist(allowlist, 'public plugin')

    def test_stale_unallowlisted_destination_is_reported(self):
        (self.repo / 'plugins' / 'kept').mkdir()
        (self.repo / 'plugins' / 'stale').mkdir()
        self.assertEqual(stale_plugin_destinations(self.repo, ('kept',)), ['stale'])


class ExporterCase(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='toolbox-export-'))
        self.addCleanup(shutil.rmtree, self.base, True)
        self.repo = make_repo(self.base)
        self.home = make_home(self.base, plugins={'demo-plugin': FIXTURES / 'complete-plugin'})

    def add_skill(self) -> str:
        shutil.copytree(FIXTURES / 'complete-skill',
                        self.home / 'skills' / 'fixtures' / 'complete-skill')
        return 'fixtures/complete-skill'


class ExporterSweepTests(ExporterCase):
    def test_source_plugins_are_not_swept_without_allowlist(self):
        result = run_exporter(self.repo, self.home,
                              '--public-skill', self.add_skill(),
                              '--public-plugin-profile', 'pub-src')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.repo / 'plugins' / 'demo-plugin').exists(),
                         'unallowlisted source plugin must not be exported')

    def test_unallowlisted_destination_is_retained_unchanged(self):
        retained = self.repo / 'plugins' / 'retained-plugin'
        shutil.copytree(FIXTURES / 'complete-plugin', retained)
        (retained / 'manifest.json').write_text(
            plugin_package_manifest(retained, 'retained-plugin'), encoding='utf-8')
        before = tree_bytes(retained)
        result = run_exporter(self.repo, self.home,
                              '--public-skill', self.add_skill(),
                              '--public-plugin-profile', 'pub-src')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(tree_bytes(retained), before)


class ExporterSelectionTests(ExporterCase):
    def test_selected_plugin_requires_source_profile_flag(self):
        result = run_exporter(self.repo, self.home, '--public-plugin', 'demo-plugin')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('--public-plugin-profile', result.stderr)

    def test_selected_allowlisted_plugin_is_exported(self):
        result = run_exporter(self.repo, self.home,
                              '--public-skill', self.add_skill(),
                              '--public-plugin', 'demo-plugin',
                              '--public-plugin-profile', 'pub-src')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.repo / 'plugins' / 'demo-plugin' / 'manifest.json').is_file())

    def test_rejected_candidate_fails_closed(self):
        shutil.copytree(FIXTURES / 'incomplete-plugin',
                        self.home / 'profiles' / 'pub-src' / 'plugins' / 'incomplete-plugin')
        result = run_exporter(self.repo, self.home,
                              '--public-skill', self.add_skill(),
                              '--public-plugin', 'incomplete-plugin',
                              '--public-plugin-profile', 'pub-src')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('real tests', result.stderr)
        self.assertFalse((self.repo / 'plugins' / 'incomplete-plugin').exists())


class ExporterOutputTests(ExporterCase):
    def test_change_list_records_accepted_destinations(self):
        change_list = self.base / 'accepted-changes.lst'
        result = run_exporter(self.repo, self.home,
                              '--public-skill', self.add_skill(),
                              '--public-plugin', 'demo-plugin',
                              '--public-plugin-profile', 'pub-src',
                              '--change-list', str(change_list))
        self.assertEqual(result.returncode, 0, result.stderr)
        entries = [e for e in change_list.read_text(encoding='utf-8').split('\0') if e]
        self.assertEqual(entries, ['plugins/demo-plugin', 'skills/fixtures/complete-skill'])

    def test_default_skill_fallback_is_logged_to_stderr(self):
        result = run_exporter(self.repo, self.home)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('falling back to the tracked default skill list', result.stderr)


if __name__ == '__main__':
    unittest.main()
