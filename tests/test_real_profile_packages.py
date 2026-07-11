"""Real profile installer contracts for public profile packages."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from tests.support import REPO, add_scripts_path

add_scripts_path()

from real_runtime import install_profile, run_hermes  # noqa: E402

TUTORIAL_PACKAGE = REPO / 'profiles' / 'hermes-agent-tutorial'
PROFILE_NAME = 'tutorial-under-test'


class InstalledProfileCase(unittest.TestCase):
    home: Path

    @classmethod
    def setUpClass(cls):
        base = Path(tempfile.mkdtemp(prefix='profile-install-'))
        cls.addClassCleanup(shutil.rmtree, base, True)
        cls.home = base / 'home'
        cls.home.mkdir()
        cls.install = install_profile(cls.home, TUTORIAL_PACKAGE, PROFILE_NAME)


class TutorialProfileInstallTests(InstalledProfileCase):
    def test_install_from_package_directory_succeeds(self):
        self.assertEqual(self.install.returncode, 0,
                         self.install.stdout + self.install.stderr)

    def test_installed_profile_contains_distribution_files(self):
        target = self.home / 'profiles' / PROFILE_NAME
        for filename in ['distribution.yaml', 'PROFILE.md', 'SOUL.md', 'README.md']:
            self.assertTrue((target / filename).is_file(), filename)


class InstalledProfileCommandTests(InstalledProfileCase):
    def test_profile_info_reports_installed_package(self):
        result = run_hermes(self.home, 'profile', 'info', PROFILE_NAME)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(PROFILE_NAME, result.stdout)

    def test_profile_config_check_passes(self):
        result = run_hermes(self.home, '-p', PROFILE_NAME, 'config', 'check')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_profile_skills_list_runs(self):
        result = run_hermes(self.home, '-p', PROFILE_NAME,
                            'skills', 'list', '--enabled-only')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class BrokenProfilePackageTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='profile-broken-'))
        self.addCleanup(shutil.rmtree, self.base, True)
        self.home = self.base / 'home'
        self.home.mkdir()
        self.package = self.base / 'no-manifest-package'
        self.package.mkdir()
        (self.package / 'README.md').write_text('# Not a distribution\n',
                                                encoding='utf-8')

    def test_package_without_manifest_cannot_install(self):
        result = install_profile(self.home, self.package, 'broken-under-test')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('distribution.yaml', result.stdout + result.stderr)

    def test_failed_install_leaves_no_profile_directory(self):
        result = install_profile(self.home, self.package, 'broken-under-test')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.home / 'profiles' / 'broken-under-test').exists())


if __name__ == '__main__':
    unittest.main()
