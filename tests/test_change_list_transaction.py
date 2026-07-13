"""Late change-list failures remain inside the outer transaction."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from tests.support import (
    FIXTURES, add_scripts_path, make_home, make_repo, run_exporter, tree_bytes,
)

add_scripts_path()
from batch_transaction import BatchTransaction  # noqa: E402


class ChangeListCase(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='change-list-rollback-'))
        self.addCleanup(shutil.rmtree, self.base, True)
        self.repo = make_repo(self.base)
        self.home = make_home(
            self.base, plugins={'demo-plugin': FIXTURES / 'complete-plugin'},
        )
        skill = self.home / 'skills/hermes-agent/hermes-config-audits'
        skill.parent.mkdir(parents=True)
        shutil.copytree(FIXTURES / 'complete-skill', skill)
        self.args = ('--public-skill', 'hermes-agent/hermes-config-audits',
                     '--public-plugin', 'demo-plugin',
                     '--public-plugin-profile', 'pub-src')
        baseline = run_exporter(self.repo, self.home, *self.args)
        self.assertEqual(baseline.returncode, 0, baseline.stderr)
        self.destination = self.repo / 'plugins/demo-plugin'
        self.original = tree_bytes(self.destination)


class ChangeListPathFailureTests(ChangeListCase):
    def test_change_list_parent_failure_restores_package(self):
        readme = self.home / 'profiles/pub-src/plugins/demo-plugin/README.md'
        readme.write_text(readme.read_text() + '\nUpdated safely.\n')
        blocked = self.base / 'blocked'
        blocked.write_text('not a directory')
        result = run_exporter(
            self.repo, self.home, *self.args,
            '--change-list', str(blocked / 'changes.txt'),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(tree_bytes(self.destination), self.original)


class UnsafeSkillOuterRollbackTests(ChangeListCase):
    def test_fenced_skill_payload_restores_repo_and_inventories(self):
        skill = self.home / 'skills/hermes-agent/hermes-config-audits/SKILL.md'
        field = 'au' + '\\u0074hor'
        skill.write_text(skill.read_text() + f'\n```yaml\n"{field}": Jane Private\n```\n')
        baseline = tree_bytes(self.repo)
        result = run_exporter(self.repo, self.home, *self.args)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(tree_bytes(self.repo), baseline)


class ChangeListCollisionTests(ChangeListCase):
    def test_inventory_change_list_collision_fails_without_mutation(self):
        baseline = tree_bytes(self.repo)
        manifest = self.repo / 'inventory/public-manifest.json'
        result = run_exporter(
            self.repo, self.home, *self.args, '--change-list', str(manifest),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(tree_bytes(self.repo), baseline)


class ProtectedChangeListTests(ChangeListCase):
    def assert_collision(self, path: Path):
        repo_before = tree_bytes(self.repo)
        home_before = tree_bytes(self.home)
        result = run_exporter(
            self.repo, self.home, *self.args, '--change-list', str(path),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(tree_bytes(self.repo), repo_before)
        self.assertEqual(tree_bytes(self.home), home_before)

    def test_repository_script_collision_fails(self):
        self.assert_collision(self.repo / 'scripts/validate-public-safety.py')

    def test_source_collision_fails(self):
        self.assert_collision(self.home / 'plugins/demo-plugin/README.md')

    def test_external_hardlink_collision_fails(self):
        alias = self.base / 'manifest-alias.json'
        alias.hardlink_to(self.repo / 'inventory/public-manifest.json')
        self.assert_collision(alias)


class OuterCacheExclusionTests(ChangeListCase):
    def test_pytest_cache_is_not_published(self):
        source = self.home / 'profiles/pub-src/plugins/demo-plugin'
        cache = source / '.pytest_cache/v/nodeids.txt'
        cache.parent.mkdir(parents=True)
        cache.write_text('private-cache-entry\n')
        readme = source / 'README.md'
        readme.write_text(readme.read_text() + '\nUpdated.\n')
        result = run_exporter(self.repo, self.home, *self.args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.repo / 'plugins/demo-plugin/.pytest_cache').exists())


class PartialChangeListRollbackTests(ChangeListCase):
    def test_partial_existing_change_list_is_restored(self):
        change_list = self.base / 'changes.txt'
        change_list.write_bytes(b'ORIGINAL-CHANGE-LIST\n')
        with self.assertRaises(RuntimeError):
            with BatchTransaction(self.repo, [self.destination, change_list]):
                (self.destination / 'README.md').write_text('updated\n')
                change_list.write_bytes(b'plugins/package-')
                raise RuntimeError('late write failure')
        self.assertEqual(tree_bytes(self.destination), self.original)
        self.assertEqual(change_list.read_bytes(), b'ORIGINAL-CHANGE-LIST\n')
