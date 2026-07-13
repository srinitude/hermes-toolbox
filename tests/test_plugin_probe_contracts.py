"""Exhaustive selector and declaration contracts for plugin probing."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from tests.support import add_scripts_path

add_scripts_path()

from package_checks import check_registration_parity  # noqa: E402
from real_runtime import (  # noqa: E402
    probe_plugin_package, run_probe, write_enabled_config,
)
from tests.plugin_runtime_cases import write_side_effect_plugin

FIXTURES = Path(__file__).parent / 'fixtures'


def declared(package: Path) -> dict:
    return yaml.safe_load((package / 'plugin.yaml').read_text(encoding='utf-8'))


def child_home(root: Path, marker: Path) -> Path:
    package = write_side_effect_plugin(root, marker)
    home = root / 'home'
    (home / 'plugins').mkdir(parents=True)
    shutil.copytree(package, home / 'plugins' / package.name)
    write_enabled_config(home, [package.name])
    return home


class SelectedCallTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='selected-call-'))
        self.addCleanup(shutil.rmtree, self.base, True)
        self.marker = self.base / 'handler-called'
        self.package = write_side_effect_plugin(self.base, self.marker)

    def test_normal_only_calls_only_normal_handler(self):
        probe_plugin_package(
            self.package, normal_tools=['effect_tool'],
            malformed_tools=[], call_commands=[])
        self.assertEqual(self.marker.read_text(encoding='utf-8'), 'tool:object\n')

    def test_command_only_calls_only_selected_command(self):
        probe_plugin_package(
            self.package, normal_tools=[], malformed_tools=[],
            call_commands=['effect-status'])
        self.assertEqual(self.marker.read_text(encoding='utf-8'), 'command\n')

    def test_one_explicit_empty_selector_disables_legacy_calls(self):
        probe_plugin_package(self.package, malformed_tools=[])
        self.assertFalse(self.marker.exists())


class LegacyRawCallTests(unittest.TestCase):
    def test_legacy_raw_tool_calls_both_paths(self):
        with tempfile.TemporaryDirectory(prefix='legacy-call-') as base:
            root = Path(base)
            marker = root / 'handler-called'
            home = child_home(root, marker)
            run_probe(home, {'call_tools': ['effect_tool']})
            events = marker.read_text(encoding='utf-8')
        self.assertEqual(events, 'tool:object\ntool:malformed\n')


class ParentDuplicateToolSelectorTests(unittest.TestCase):
    def assert_parent_rejects(self, selector: str):
        with tempfile.TemporaryDirectory(prefix='duplicate-parent-') as base:
            root = Path(base)
            marker = root / 'handler-called'
            package = write_side_effect_plugin(root, marker)
            selections = dict(normal_tools=[], malformed_tools=[], call_commands=[])
            selections[selector] = ['effect_tool', 'effect_tool']
            with self.assertRaisesRegex(SystemExit, 'duplicate'):
                probe_plugin_package(package, **selections)
            self.assertFalse(marker.exists())

    def test_parent_rejects_normal_and_malformed_duplicates(self):
        for selector in ('normal_tools', 'malformed_tools'):
            with self.subTest(selector=selector):
                self.assert_parent_rejects(selector)


class ChildDuplicateToolSelectorTests(unittest.TestCase):
    def assert_child_rejects(self, selector: str):
        with tempfile.TemporaryDirectory(prefix='duplicate-child-tool-') as base:
            root = Path(base)
            marker = root / 'handler-called'
            home = child_home(root, marker)
            spec = {selector: ['effect_tool', 'effect_tool']}
            with self.assertRaisesRegex(SystemExit, 'plugin probe failed'):
                run_probe(home, spec)
            self.assertFalse(marker.exists())

    def test_child_rejects_all_tool_selector_duplicates(self):
        for selector in ('call_tools', 'normal_tools', 'malformed_tools'):
            with self.subTest(selector=selector):
                self.assert_child_rejects(selector)


class SurfaceParityDirectionTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='surface-direction-'))
        self.addCleanup(shutil.rmtree, self.base, True)
        self.package = write_side_effect_plugin(
            self.base, self.base / 'handler-called')
        self.probe = probe_plugin_package(
            self.package, normal_tools=[], malformed_tools=[], call_commands=[])
        self.manifest = declared(self.package)

    def test_exact_hook_and_cli_declarations_pass(self):
        self.manifest['provides_hooks'] = ['pre_tool']
        self.manifest['provides_cli_commands'] = ['effect']
        errors = check_registration_parity(
            self.manifest, self.probe, 'plugins/side-effect-plugin')
        self.assertEqual(errors, [])

    def test_declared_unregistered_hook_and_cli_are_reported(self):
        self.manifest['provides_hooks'] = ['pre_tool', 'missing-hook']
        self.manifest['provides_cli_commands'] = ['effect', 'missing-cli']
        errors = check_registration_parity(
            self.manifest, self.probe, 'plugins/side-effect-plugin')
        self.assertTrue(any('missing-hook' in error for error in errors), errors)
        self.assertTrue(any('missing-cli' in error for error in errors), errors)


class DuplicateSurfaceDeclarationTests(unittest.TestCase):
    def assert_rejected_before_handlers(self, field: str, value: str):
        with tempfile.TemporaryDirectory(prefix='duplicate-surface-') as base:
            root = Path(base)
            marker = root / 'handler-called'
            package = write_side_effect_plugin(root, marker)
            manifest = declared(package)
            manifest[field] = [value, value]
            (package / 'plugin.yaml').write_text(
                yaml.safe_dump(manifest, sort_keys=False), encoding='utf-8')
            with self.assertRaisesRegex(SystemExit, 'duplicate declared'):
                probe_plugin_package(package)
            self.assertFalse(marker.exists())

    def test_duplicate_declarations_fail_before_handlers(self):
        surfaces = {
            'provides_tools': 'effect_tool',
            'provides_commands': 'effect-status',
            'provides_hooks': 'pre_tool',
            'provides_cli_commands': 'effect',
            'provides_skills': 'demo',
        }
        for field, value in surfaces.items():
            with self.subTest(field=field):
                self.assert_rejected_before_handlers(field, value)


class DuplicateSkillDeclarationTests(unittest.TestCase):
    def test_duplicate_skill_declaration_is_reported(self):
        package = FIXTURES / 'skill-plugin'
        probe = probe_plugin_package(package)
        manifest = declared(package)
        manifest['provides_skills'] = ['demo', 'demo']
        errors = check_registration_parity(
            manifest, probe, 'plugins/skill-plugin')
        self.assertTrue(any('duplicate declared skill' in error for error in errors), errors)


if __name__ == '__main__':
    unittest.main()
