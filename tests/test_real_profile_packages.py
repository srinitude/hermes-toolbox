"""Real profile installer contracts for public profile packages."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from tests.support import add_scripts_path, profile_export_sources, run_exporter

add_scripts_path()

from real_runtime import install_profile, run_hermes  # noqa: E402

EXPORTED_NAME = 'exported-under-test'


class ExportedProfileCase(unittest.TestCase):
    home: Path

    @classmethod
    def setUpClass(cls):
        base = Path(tempfile.mkdtemp(prefix='profile-exported-'))
        cls.addClassCleanup(shutil.rmtree, base, True)
        repo, source_home = profile_export_sources(base)
        result = run_exporter(repo, source_home, '--public-skill', 'fixtures/complete-skill',
                              '--public-profile', 'pub-demo')
        if result.returncode != 0:
            raise AssertionError(result.stdout + result.stderr)
        cls.home = base / 'install-home'
        cls.home.mkdir()
        cls.install = install_profile(cls.home, repo / 'profiles' / 'pub-demo', EXPORTED_NAME)


class ExportedProfileInstallTests(ExportedProfileCase):
    def test_exported_package_installs_into_a_temporary_home(self):
        self.assertEqual(self.install.returncode, 0,
                         self.install.stdout + self.install.stderr)

    def test_profile_info_reports_exported_package(self):
        result = run_hermes(self.home, 'profile', 'info', EXPORTED_NAME)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(EXPORTED_NAME, result.stdout)

    def test_profile_config_check_passes(self):
        result = run_hermes(self.home, '-p', EXPORTED_NAME, 'config', 'check')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_enabled_only_skills_listing_runs(self):
        result = run_hermes(self.home, '-p', EXPORTED_NAME,
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
