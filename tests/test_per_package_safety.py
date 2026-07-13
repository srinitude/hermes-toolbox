"""Per-package validation before any destination mutation."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from tests.credential_cases import credential_cases
from tests.plugin_runtime_cases import BROKEN_BEHAVIORS, plugin_source
from tests.support import FIXTURES, add_scripts_path, make_home, make_repo, tree_bytes

add_scripts_path()
from candidate_policy import PolicyConfig  # noqa: E402
from export_transaction import export_one_plugin  # noqa: E402


class PackageSafetyCase(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='package-safety-'))
        self.addCleanup(shutil.rmtree, self.base, True)
        self.repo = make_repo(self.base)
        self.home = make_home(
            self.base, plugins={'demo-plugin': FIXTURES / 'complete-plugin'},
        )
        self.source = self.home / 'profiles/pub-src/plugins/demo-plugin'
        self.destination = self.repo / 'plugins/demo-plugin'
        self.config = PolicyConfig(('demo-plugin',), 'pub-src', None)
        self.assertTrue(export_one_plugin(self.home, self.repo, 'demo-plugin', self.config))
        self.baseline = tree_bytes(self.destination)

    def assert_rejected_before_mutation(self) -> None:
        with self.assertRaises(SystemExit):
            export_one_plugin(self.home, self.repo, 'demo-plugin', self.config)
        self.assertEqual(tree_bytes(self.destination), self.baseline)


class YamlStagingSafetyTests(PackageSafetyCase):
    def test_invalid_yaml_is_rejected_before_package_swap(self):
        (self.source / 'config.yaml').write_text('service: [broken\n')
        self.assert_rejected_before_mutation()

    def test_yaml_compatible_invalid_json_is_rejected(self):
        (self.source / 'notes.json').write_text("{'valid_yaml': yes}\n")
        self.assert_rejected_before_mutation()

    def test_nested_metadata_basename_has_no_author_exemption(self):
        nested = self.source / 'nested/plugin.yaml'
        nested.parent.mkdir()
        field = 'au' + 'thor'
        nested.write_text(f'{field}: Example Person\n')
        self.assert_rejected_before_mutation()

    def test_decoded_identity_is_rejected_before_package_swap(self):
        info = self.repo / '.git/info'
        info.mkdir(parents=True, exist_ok=True)
        (info / 'identity-denylist.txt').write_text('PrivateName\n')
        (self.source / 'notes.yaml').write_text('description: "\\u0050rivateName"\n')
        self.assert_rejected_before_mutation()


class CredentialSafetyTests(PackageSafetyCase):
    def test_decoded_and_spaced_credentials_are_rejected(self):
        cases = credential_cases()
        for name, payload in cases.items():
            with self.subTest(name=name):
                path = self.source / name
                path.write_text(payload)
                self.assert_rejected_before_mutation()
                path.unlink()

    def test_documented_placeholder_credential_is_accepted_once(self):
        notes = self.source / 'notes.md'
        notes.write_text('password: this-is-a-placeholder\n'
                         'password: ${PASSWORD}\n'
                         'password: <password>\n')
        self.assertTrue(export_one_plugin(self.home, self.repo, 'demo-plugin', self.config))


class PrivateKeySafetyTests(PackageSafetyCase):
    def test_private_key_block_is_rejected(self):
        markers = ('OPENSSH ', 'ENCRYPTED ')
        path = self.source / 'example.pem'
        for kind in markers:
            with self.subTest(kind=kind):
                marker = '-----BEGIN ' + kind + 'PRIVATE KEY-----'
                path.write_text(marker + '\nabcdef0123456789abcdef\n')
                self.assert_rejected_before_mutation()


class PythonCredentialSafetyTests(PackageSafetyCase):
    def test_python_string_assignments_are_rejected(self):
        key = 'api' + '_key'
        credential_name = 'github' + '_token'
        payloads = (
            f'{key} = """abcdef0123456789abcdef"""\n',
            f'{key} = "abcdef0123" "456789abcdef"\n',
            f'if ({key} := "abcdef0123456789abcdef"): pass\n',
            f'{key}, other = ("abcdef0123456789abcdef", "safe")\n',
            f'config["{key}"] = "abcdef0123456789abcdef"\n',
            f'{credential_name} = "abcdef0123456789abcdef"\n',
        )
        for index, payload in enumerate(payloads):
            with self.subTest(index=index):
                path = self.source / f'credential_{index}.py'
                path.write_text(payload)
                self.assert_rejected_before_mutation()
                path.unlink()


class RepositoryAuthorSafetyTests(PackageSafetyCase):
    def test_existing_repository_author_is_protected_before_swap(self):
        metadata = self.repo / 'plugins/other/plugin.yaml'
        metadata.parent.mkdir(parents=True)
        field = 'au' + 'thor'
        metadata.write_text(f'{field}: Jane Fixture\n')
        readme = self.source / 'README.md'
        readme.write_text(readme.read_text() + '\nRun Jane Fixture.\n')
        self.assert_rejected_before_mutation()


class PluginRuntimeParityTests(PackageSafetyCase):
    def test_declaration_registration_mismatch_is_rejected(self):
        manifest = self.source / 'plugin.yaml'
        manifest.write_text(
            manifest.read_text().replace('- fixture_echo', '- ghost_tool'))
        self.assert_rejected_before_mutation()

    def test_handler_identity_mismatch_is_rejected(self):
        plugin = self.source / '__init__.py'
        plugin.write_text(plugin.read_text().replace(
            "PLUGIN_NAME = 'demo-plugin'", "PLUGIN_NAME = 'complete-plugin'"))
        self.assert_rejected_before_mutation()

    def test_handler_exception_is_rejected(self):
        plugin = self.source / '__init__.py'
        plugin.write_text(plugin.read_text().replace(
            'def fixture_echo(args: object) -> str:\n',
            'def fixture_echo(args: object) -> str:\n    raise RuntimeError("handler failed")\n'))
        self.assert_rejected_before_mutation()

    def test_broken_handler_results_are_rejected(self):
        plugin = self.source / '__init__.py'
        for label, normal, bad, command in BROKEN_BEHAVIORS:
            with self.subTest(label=label):
                plugin.write_text(plugin_source(normal, bad, command))
                self.assert_rejected_before_mutation()


class PluginCompletenessSafetyTests(PackageSafetyCase):
    def test_cache_is_excluded(self):
        cache = self.source / '.pytest_cache/v/nodeids.txt'
        cache.parent.mkdir(parents=True)
        cache.write_text('private-cache-entry\n')
        backup = self.source / 'backups/snapshot.txt'
        backup.parent.mkdir()
        backup.write_text('private-backup-entry\n')
        readme = self.source / 'README.md'
        readme.write_text(readme.read_text() + '\nUpdated.\n')
        self.assertTrue(export_one_plugin(
            self.home, self.repo, 'demo-plugin', self.config))
        self.assertFalse((self.destination / '.pytest_cache').exists())
        self.assertFalse((self.destination / 'backups').exists())

    def test_todo_is_rejected_before_mutation(self):
        readme = self.source / 'README.md'
        readme.write_text(readme.read_text() + '\nTODO: replace before publication.\n')
        self.assert_rejected_before_mutation()


class AuthorNameCompatibilityTests(PackageSafetyCase):
    def test_common_first_name_word_is_not_globally_denied(self):
        metadata = self.repo / 'plugins/other/plugin.yaml'
        metadata.parent.mkdir(parents=True)
        field = 'au' + 'thor'
        metadata.write_text(f'{field}: May Lee\n')
        readme = self.source / 'README.md'
        readme.write_text(readme.read_text() + '\nUsers may configure this option.\n')
        self.assertTrue(export_one_plugin(
            self.home, self.repo, 'demo-plugin', self.config))


class OrdinaryAuthorSafetyTests(PackageSafetyCase):
    def test_author_fields_outside_metadata_are_rejected(self):
        field = 'au' + 'thor'
        escaped = 'au' + '\\u0074hor'
        cases = {
            'notes.yaml': f'"{field}": "Jane Private"\n',
            'escaped.yaml': f'"{escaped}": "Jane Private"\n',
            'notes.json': f'{{"{field}": "Jane Private"}}\n',
            'fenced.md': f'```yaml\n"{field}": Jane Private\n```\nRun Jane Private.\n',
            'escaped-fence.md': f'```yaml\n"{escaped}": Jane Private\n```\nRun Jane Private.\n',
        }
        for filename, payload in cases.items():
            with self.subTest(filename=filename):
                path = self.source / filename
                path.write_text(payload)
                self.assert_rejected_before_mutation()
                path.unlink()
