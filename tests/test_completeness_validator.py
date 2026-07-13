"""validate-package-completeness must run the native profile, personality,
and skill/reference gates, not only the legacy shallow package checks."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.plugin_runtime_cases import BROKEN_BEHAVIORS, plugin_source
from tests.support import FIXTURES, REPO, SCRIPTS, add_scripts_path

add_scripts_path()

from export_transaction import plugin_package_manifest  # noqa: E402
from profile_export import profile_package_manifest  # noqa: E402


def run_completeness(repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / 'validate-package-completeness.py'),
         '--repo', str(repo)], capture_output=True, text=True)


class CompletenessRepoCase(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='completeness-native-'))
        self.addCleanup(shutil.rmtree, self.base, True)
        self.repo = self.base / 'repo'
        self.repo.mkdir()

    def add_profile(self) -> Path:
        pkg = self.repo / 'profiles' / 'complete-profile'
        shutil.copytree(FIXTURES / 'complete-profile', pkg)
        (pkg / 'manifest.json').write_text(
            profile_package_manifest(pkg, 'complete-profile'), encoding='utf-8')
        return pkg

    def add_plugin(self) -> Path:
        pkg = self.repo / 'plugins' / 'complete-plugin'
        shutil.copytree(FIXTURES / 'complete-plugin', pkg)
        (pkg / 'manifest.json').write_text(
            plugin_package_manifest(pkg, 'complete-plugin'), encoding='utf-8')
        return pkg

    def add_personality(self) -> Path:
        pkg = self.repo / 'primitives' / 'personalities' / 'validator'
        shutil.copytree(REPO / 'primitives' / 'personalities' / 'validator', pkg)
        return pkg

    def add_skill(self) -> Path:
        pkg = self.repo / 'skills' / 'fixtures' / 'complete-skill'
        shutil.copytree(FIXTURES / 'complete-skill', pkg)
        return pkg


def write_plugin_source(pkg: Path, source: str) -> None:
    (pkg / '__init__.py').write_text(source)
    (pkg / 'manifest.json').unlink()
    (pkg / 'manifest.json').write_text(
        plugin_package_manifest(pkg, 'complete-plugin'), encoding='utf-8')


class PluginRuntimeGateTests(CompletenessRepoCase):
    def test_handler_exception_fails(self):
        pkg = self.add_plugin()
        plugin = pkg / '__init__.py'
        source = plugin.read_text().replace(
            'def fixture_echo(args: object) -> str:\n',
            'def fixture_echo(args: object) -> str:\n    raise RuntimeError("handler failed")\n')
        write_plugin_source(pkg, source)
        result = run_completeness(self.repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('handler failed', result.stderr)

    def test_broken_handler_results_fail(self):
        pkg = self.add_plugin()
        for label, normal, bad, command in BROKEN_BEHAVIORS:
            with self.subTest(label=label):
                write_plugin_source(pkg, plugin_source(normal, bad, command))
                self.assertNotEqual(run_completeness(self.repo).returncode, 0)


class PluginIdentityGateTests(CompletenessRepoCase):
    def test_handler_reported_identity_mismatch_fails(self):
        pkg = self.add_plugin()
        plugin = pkg / '__init__.py'
        source = plugin.read_text().replace(
            "PLUGIN_NAME = 'complete-plugin'", "PLUGIN_NAME = 'stale-plugin'")
        write_plugin_source(pkg, source)
        result = run_completeness(self.repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('declared plugin identity', result.stderr)


class PluginManifestGateTests(CompletenessRepoCase):
    def test_nested_manifest_is_included(self):
        pkg = self.add_plugin()
        nested = pkg / 'examples/manifest.json'
        nested.parent.mkdir()
        nested.write_text('{}\n')
        write_plugin_source(pkg, (pkg / '__init__.py').read_text())
        self.assertEqual(run_completeness(self.repo).returncode, 0)

    def test_included_files_mismatch_fails(self):
        pkg = self.add_plugin()
        manifest = pkg / 'manifest.json'
        data = json.loads(manifest.read_text())
        data['included_files'] = []
        manifest.write_text(json.dumps(data))
        result = run_completeness(self.repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('included files', result.stderr)


class NativeProfileGateTests(CompletenessRepoCase):
    def test_missing_native_required_file_fails(self):
        (self.add_profile() / 'config.yaml').unlink()
        result = run_completeness(self.repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('config.yaml', result.stderr)

    def test_credential_like_config_key_fails(self):
        pkg = self.add_profile()
        (pkg / 'config.yaml').write_text('demo:\n  api_key: ask-user\n', encoding='utf-8')
        result = run_completeness(self.repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('credential-like', result.stderr)

    def test_max_tokens_is_not_a_credential_key(self):
        pkg = self.add_profile()
        config = pkg / 'config.yaml'
        config.write_text('model:\n  max_tokens: 4096\n', encoding='utf-8')
        self.assertEqual(run_completeness(self.repo).returncode, 0)

    def test_missing_distribution_owned_path_fails(self):
        pkg = self.add_profile()
        shutil.rmtree(pkg / 'skills')
        result = run_completeness(self.repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('distribution_owned', result.stderr)


class ProfileCredentialVariantTests(CompletenessRepoCase):
    def test_client_secret_key_fails(self):
        pkg = self.add_profile()
        key = 'client_' + 'secret_key'
        (pkg / 'config.yaml').write_text(
            f'provider:\n  {key}: abcdef0123456789abcdef\n', encoding='utf-8')
        result = run_completeness(self.repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('credential-like', result.stderr)


class PersonalityGateTests(CompletenessRepoCase):
    def test_dangling_config_file_reference_fails(self):
        pkg = self.add_personality()
        manifest = pkg / 'manifest.json'
        data = json.loads(manifest.read_text(encoding='utf-8'))
        data['config_file'] = 'absent.yaml'
        manifest.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
        result = run_completeness(self.repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('config_file', result.stderr)


class SkillGateTests(CompletenessRepoCase):
    def test_missing_referenced_support_file_fails(self):
        pkg = self.add_skill()
        with (pkg / 'SKILL.md').open('a', encoding='utf-8') as fh:
            fh.write('\nRead references/setup-guide.md before applying this fixture.\n')
        result = run_completeness(self.repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('references/setup-guide.md', result.stderr)

    def test_short_skill_package_fails(self):
        skill_md = self.add_skill() / 'SKILL.md'
        lines = skill_md.read_text(encoding='utf-8').splitlines()[:20]
        skill_md.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        result = run_completeness(self.repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('too short', result.stderr)


class CompletenessAcceptanceTests(CompletenessRepoCase):
    def test_clean_repo_with_every_package_kind_passes(self):
        self.add_plugin()
        self.add_profile()
        self.add_personality()
        self.add_skill()
        result = run_completeness(self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
