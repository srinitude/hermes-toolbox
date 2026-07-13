"""Canonical profile manifest file-identity regressions."""
from __future__ import annotations

import json

from tests.support import add_scripts_path
from tests.test_completeness_validator import CompletenessRepoCase, run_completeness

add_scripts_path()
from profile_export import profile_package_manifest  # noqa: E402


class ProfileManifestGateTests(CompletenessRepoCase):
    def test_profile_included_files_match(self):
        pkg = self.add_profile()
        nested = pkg / 'nested/manifest.json'
        nested.parent.mkdir()
        nested.write_text('{}\n')
        (pkg / 'manifest.json').unlink()
        (pkg / 'manifest.json').write_text(
            profile_package_manifest(pkg, 'complete-profile'), encoding='utf-8')
        self.assertEqual(run_completeness(self.repo).returncode, 0)

    def test_profile_included_files_mismatch_fails(self):
        pkg = self.add_profile()
        manifest = pkg / 'manifest.json'
        data = json.loads(manifest.read_text())
        data['included_files'] = []
        manifest.write_text(json.dumps(data))
        result = run_completeness(self.repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('included files', result.stderr)
