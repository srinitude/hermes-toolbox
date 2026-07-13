"""Direct profile packages inherit repository-wide identity policy."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from tests.support import add_scripts_path, profile_export_sources

add_scripts_path()
from candidate_policy import PolicyConfig  # noqa: E402
from profile_export import export_one_profile  # noqa: E402


class ProfilePackageSafetyTests(unittest.TestCase):
    def test_repository_author_is_rejected_before_profile_swap(self):
        base = Path(tempfile.mkdtemp(prefix='profile-package-safety-'))
        self.addCleanup(shutil.rmtree, base, True)
        repo, home = profile_export_sources(base)
        metadata = repo / 'plugins/other/plugin.yaml'
        metadata.parent.mkdir(parents=True)
        field = 'au' + 'thor'
        metadata.write_text(f'{field}: Jane Fixture\n')
        readme = home / 'profiles/pub-demo/README.md'
        readme.write_text(readme.read_text() + '\nRun Jane Fixture.\n')
        config = PolicyConfig((), None, None, ('pub-demo',))
        with self.assertRaises(SystemExit):
            export_one_profile(home, repo, 'pub-demo', config)
        self.assertFalse((repo / 'profiles/pub-demo').exists())
