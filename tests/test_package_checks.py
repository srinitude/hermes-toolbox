"""Static completeness contracts for public toolbox packages."""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.support import FIXTURES, SCRIPTS, add_scripts_path

add_scripts_path()

from export_transaction import plugin_package_manifest  # noqa: E402
from package_checks import check_profile_hygiene, find_placeholders  # noqa: E402

BASE_MANIFEST = (
    'name: demo-profile\n'
    'version: 0.1.0\n'
    'description: Demo public profile package.\n'
    'author: Example Maintainer\n'
    'license: MIT\n'
)


class PlaceholderCase(unittest.TestCase):
    def setUp(self):
        self.pkg = Path(tempfile.mkdtemp(prefix='pkg-checks-'))
        self.addCleanup(shutil.rmtree, self.pkg, True)

    def write(self, rel: str, text: str) -> None:
        path = self.pkg / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')


class TestDoubleDetection(PlaceholderCase):
    def test_fakectx_reference_is_flagged(self):
        self.write('tests/test_contract.py', 'ctx = FakeCtx()\n')
        self.assertTrue(any('FakeCtx' in e for e in find_placeholders(self.pkg)))

    def test_mock_import_is_flagged(self):
        self.write('tests/test_contract.py', 'from unittest.mock import MagicMock\n')
        self.assertTrue(find_placeholders(self.pkg))

    def test_monkeypatch_is_flagged(self):
        self.write('tests/test_contract.py',
                   'def test_home(monkeypatch):\n    monkeypatch.setenv("A", "1")\n')
        self.assertTrue(find_placeholders(self.pkg))

    def test_stub_identifier_is_flagged(self):
        self.write('helper.py', 'stub_client = object()\n')
        self.assertTrue(find_placeholders(self.pkg))

    def test_spy_identifier_is_flagged(self):
        self.write('helper.py', 'call_spy = []\n')
        self.assertTrue(find_placeholders(self.pkg))


class PlaceholderMarkerDetection(PlaceholderCase):
    def test_todo_marker_is_flagged(self):
        self.write('README.md', '# Package\n\nTODO: document installation.\n')
        self.assertTrue(any('TODO' in e for e in find_placeholders(self.pkg)))

    def test_pass_only_function_body_is_flagged(self):
        self.write('module.py', 'def handler(args):\n    pass\n')
        self.assertTrue(any('placeholder body' in e for e in find_placeholders(self.pkg)))

    def test_ellipsis_only_body_is_flagged(self):
        self.write('module.py', 'def handler(args):\n    ...\n')
        self.assertTrue(any('placeholder body' in e for e in find_placeholders(self.pkg)))

    def test_skip_marker_is_flagged(self):
        self.write('tests/test_contract.py',
                   'def test_later(self):\n    self.skipTest("not yet")\n')
        self.assertTrue(find_placeholders(self.pkg))

    def test_xfail_marker_is_flagged(self):
        self.write('tests/test_contract.py',
                   '@pytest.mark.xfail\ndef test_broken():\n    raise AssertionError\n')
        self.assertTrue(find_placeholders(self.pkg))


class PlaceholderPrecision(PlaceholderCase):
    def test_guarded_fallback_pass_is_not_flagged(self):
        self.write('module.py',
                   'def load():\n    try:\n        return 1\n'
                   '    except Exception:\n        pass\n    return 0\n')
        self.assertEqual(find_placeholders(self.pkg), [])

    def test_real_handler_module_is_not_flagged(self):
        self.write('module.py',
                   'def handler(args):\n'
                   '    if not isinstance(args, dict):\n'
                   '        return "rejected"\n'
                   '    return "ok"\n')
        self.assertEqual(find_placeholders(self.pkg), [])

    def test_complete_plugin_fixture_is_clean(self):
        self.assertEqual(find_placeholders(FIXTURES / 'complete-plugin'), [])


class ProfileHygieneCase(unittest.TestCase):
    def setUp(self):
        self.profile = Path(tempfile.mkdtemp(prefix='profile-hygiene-'))
        self.addCleanup(shutil.rmtree, self.profile, True)

    def hygiene(self, manifest_text: str) -> list[str]:
        (self.profile / 'distribution.yaml').write_text(manifest_text, encoding='utf-8')
        return check_profile_hygiene(self.profile, 'profiles/demo-profile')


class ProfileManifestFieldTests(ProfileHygieneCase):
    def test_source_field_is_rejected(self):
        errors = self.hygiene(BASE_MANIFEST + 'source: https://example.com/demo.git\n')
        self.assertTrue(any('source' in e for e in errors), errors)

    def test_installed_at_field_is_rejected(self):
        errors = self.hygiene(BASE_MANIFEST + "installed_at: '2026-07-11T00:00:00+00:00'\n")
        self.assertTrue(any('installed_at' in e for e in errors), errors)

    def test_missing_manifest_is_rejected(self):
        errors = check_profile_hygiene(self.profile, 'profiles/demo-profile')
        self.assertTrue(any('distribution.yaml' in e for e in errors), errors)

    def test_clean_manifest_passes(self):
        self.assertEqual(self.hygiene(BASE_MANIFEST), [])


class ProfilePathHygieneTests(ProfileHygieneCase):
    def test_absolute_home_path_is_rejected(self):
        home_path = '/'.join(('', 'Users', 'someone', 'work'))
        errors = self.hygiene(BASE_MANIFEST + f'notes: staged from {home_path}\n')
        self.assertTrue(any('absolute' in e for e in errors), errors)

    def test_temporary_path_in_config_is_rejected(self):
        (self.profile / 'config.yaml').write_text(
            'workspace: /tmp/hermes-stage-1234\n', encoding='utf-8')
        errors = self.hygiene(BASE_MANIFEST)
        self.assertTrue(any('absolute' in e for e in errors), errors)


def run_completeness(repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / 'validate-package-completeness.py'),
         '--repo', str(repo)], capture_output=True, text=True)


class CompletenessCase(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='completeness-'))
        self.addCleanup(shutil.rmtree, self.base, True)
        self.repo = self.base / 'repo'
        self.pkg = self.repo / 'plugins' / 'complete-plugin'
        shutil.copytree(FIXTURES / 'complete-plugin', self.pkg)
        self.write_manifest()

    def write_manifest(self) -> None:
        (self.pkg / 'manifest.json').write_text(
            plugin_package_manifest(self.pkg, 'complete-plugin'), encoding='utf-8')


class CompletenessAcceptanceTests(CompletenessCase):
    def test_clean_package_passes(self):
        result = run_completeness(self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_bundled_skill_file_fails(self):
        with (self.pkg / 'plugin.yaml').open('a', encoding='utf-8') as fh:
            fh.write('provides_skills:\n- demo\n')
        self.write_manifest()
        result = run_completeness(self.repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('SKILL.md', result.stderr)


class CompletenessRejectionTests(CompletenessCase):
    def test_public_python_structure_violation_fails(self):
        (self.pkg / 'big.py').write_text(
            '\n'.join(f'value_{i} = {i}' for i in range(210)) + '\n', encoding='utf-8')
        self.write_manifest()
        result = run_completeness(self.repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('spans', result.stderr)

    def test_package_with_test_double_fails(self):
        (self.pkg / 'tests' / 'test_double.py').write_text('ctx = FakeCtx()\n',
                                                           encoding='utf-8')
        self.write_manifest()
        result = run_completeness(self.repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('FakeCtx', result.stderr)


if __name__ == '__main__':
    unittest.main()
