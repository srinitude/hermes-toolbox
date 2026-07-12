"""Installer selection, dry-run, and personality activation contracts."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

from tests.support import FIXTURES, REPO

INSTALLER = REPO / 'scripts' / 'install-toolbox.sh'
SNIPPET_FILE = REPO / 'primitives' / 'personalities' / 'validator' / 'config.public.yaml'
MANIFEST = REPO / 'inventory' / 'public-manifest.json'
SKILL = 'hermes-agent/honcho-memory-provider'
OTHER_SKILL = 'hermes-agent/hermes-config-audits'
PLUGIN = 'complete-plugin'
OTHER_PLUGIN = 'other-plugin'
PROFILE = 'complete-profile'


def validator_snippet() -> str:
    data = yaml.safe_load(SNIPPET_FILE.read_text(encoding='utf-8'))
    return data['agent']['personalities']['validator'].strip()


class InstallerCase(unittest.TestCase):
    def setUp(self):
        self.target = Path(tempfile.mkdtemp(prefix='toolbox-target-'))
        self.addCleanup(shutil.rmtree, self.target, True)

    def run_installer(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ['bash', str(INSTALLER), '--target', str(self.target), *args],
            capture_output=True, text=True)

    def target_tree(self) -> list[str]:
        return sorted(p.relative_to(self.target).as_posix()
                      for p in self.target.rglob('*'))

    def target_config(self) -> dict:
        return yaml.safe_load((self.target / 'config.yaml')
                              .read_text(encoding='utf-8')) or {}


class DryRunTests(InstallerCase):
    def test_dry_run_makes_no_changes(self):
        result = self.run_installer('--skill', SKILL, '--personalities')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.target_tree(), [])

    def test_dry_run_prints_exact_destinations(self):
        result = self.run_installer('--skill', SKILL)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f'{self.target}/skills/{SKILL}', result.stdout)


class SkillSelectionTests(InstallerCase):
    def test_selected_skill_installs_alone(self):
        result = self.run_installer('--apply', '--skill', SKILL)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.target / 'skills' / SKILL / 'SKILL.md').is_file())
        self.assertFalse((self.target / 'skills' / OTHER_SKILL).exists())
        self.assertFalse((self.target / 'plugins').exists())

    def test_all_skills_installs_the_manifest_set(self):
        result = self.run_installer('--apply', '--all-skills')
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
        for entry in manifest['skills']:
            self.assertTrue((self.target / entry['path']).is_file(), entry['path'])

    def test_unknown_skill_selection_fails_before_writing(self):
        result = self.run_installer('--apply', '--skill', 'no-category/no-skill')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.target_tree(), [])


class PackageInstallerCase(InstallerCase):
    def setUp(self):
        super().setUp()
        self.fixture_repo = Path(tempfile.mkdtemp(prefix='installer-repo-'))
        self.addCleanup(shutil.rmtree, self.fixture_repo, True)
        (self.fixture_repo / 'scripts').mkdir()
        (self.fixture_repo / 'inventory').mkdir()
        shutil.copy2(INSTALLER, self.fixture_repo / 'scripts/install-toolbox.sh')
        shutil.copytree(FIXTURES / 'complete-plugin',
                        self.fixture_repo / 'plugins' / PLUGIN)
        shutil.copytree(FIXTURES / 'complete-profile',
                        self.fixture_repo / 'profiles' / PROFILE)
        manifest = {
            'skills': [],
            'plugins': [{'path': f'plugins/{PLUGIN}/plugin.yaml'}],
            'profiles': [{'path': f'profiles/{PROFILE}/distribution.yaml'}],
            'personalities': [],
        }
        (self.fixture_repo / 'inventory/public-manifest.json').write_text(
            json.dumps(manifest), encoding='utf-8')

    def run_installer(self, *args: str) -> subprocess.CompletedProcess:
        script = self.fixture_repo / 'scripts/install-toolbox.sh'
        return subprocess.run(['bash', str(script), '--target', str(self.target), *args],
                              capture_output=True, text=True)


class PluginAndProfileSelectionTests(PackageInstallerCase):
    def test_package_dry_run_is_side_effect_free(self):
        result = self.run_installer('--plugin', PLUGIN, '--profile', PROFILE)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.target_tree(), [])
        for rel in (f'plugins/{PLUGIN}', f'profiles/{PROFILE}'):
            self.assertIn(f'{self.target}/{rel}', result.stdout)

    def test_selected_plugin_installs_alone(self):
        result = self.run_installer('--apply', '--plugin', PLUGIN)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.target / 'plugins' / PLUGIN / 'plugin.yaml').is_file())
        self.assertFalse((self.target / 'plugins' / OTHER_PLUGIN).exists())

    def test_broad_plugin_flag_is_rejected(self):
        result = self.run_installer('--apply', '--plugins')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.target_tree(), [])

    def test_profile_installs_through_real_profile_installer(self):
        result = self.run_installer('--apply', '--profile', PROFILE)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        target_profile = self.target / 'profiles' / PROFILE
        self.assertTrue((target_profile / 'distribution.yaml').is_file())


class PersonalityTests(InstallerCase):
    def test_personalities_installs_without_activation(self):
        result = self.run_installer('--apply', '--personalities')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        config = self.target_config()
        agent = config.get('agent') or {}
        self.assertEqual((agent.get('personalities') or {}).get('validator'),
                         validator_snippet())
        self.assertNotIn('system_prompt', agent)
        self.assertNotIn('personality', config.get('display') or {})

    def test_activation_is_explicit_opt_in(self):
        result = self.run_installer('--apply', '--activate-validator')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        config = self.target_config()
        self.assertEqual(config['agent'].get('system_prompt'), validator_snippet())
        self.assertEqual((config.get('display') or {}).get('personality'), 'validator')


if __name__ == '__main__':
    unittest.main()
