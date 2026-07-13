"""Side-effect boundaries for real Hermes plugin probes."""
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
    _probe_report, probe_plugin_package, run_probe, write_enabled_config,
)
from tests.plugin_runtime_cases import write_cli_plugin, write_side_effect_plugin


def declared(package: Path) -> dict:
    return yaml.safe_load((package / 'plugin.yaml').read_text(encoding='utf-8'))


class RestrictedProbeTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='restricted-plugin-'))
        self.addCleanup(shutil.rmtree, self.base, True)
        self.marker = self.base / 'handler-called'
        self.package = write_side_effect_plugin(self.base, self.marker)

    def test_registration_only_never_calls_handlers(self):
        probe = probe_plugin_package(
            self.package, normal_tools=[], malformed_tools=[], call_commands=[])
        self.assertEqual(probe['tool_calls'], {})
        self.assertEqual(probe['command_calls'], {})
        self.assertFalse(self.marker.exists())

    def test_malformed_only_never_calls_normal_handler(self):
        probe = probe_plugin_package(
            self.package, normal_tools=[], malformed_tools=['effect_tool'],
            call_commands=[])
        call = probe['tool_calls']['effect_tool']
        self.assertNotIn('output', call)
        self.assertIs(call['bad_input'].get('success'), False)
        self.assertEqual(self.marker.read_text(encoding='utf-8'), 'tool:malformed\n')


class DuplicateSelectionTests(unittest.TestCase):
    def test_parent_rejects_duplicate_command_before_invocation(self):
        with tempfile.TemporaryDirectory(prefix='duplicate-call-') as base:
            root = Path(base)
            marker = root / 'handler-called'
            package = write_side_effect_plugin(root, marker)
            with self.assertRaisesRegex(SystemExit, 'duplicate command selection'):
                probe_plugin_package(
                    package, normal_tools=[], malformed_tools=[],
                    call_commands=['effect-status', 'effect-status'])
            self.assertFalse(marker.exists())

    def test_child_rejects_duplicate_commands_before_invocation(self):
        with tempfile.TemporaryDirectory(prefix='duplicate-child-') as base:
            root = Path(base)
            marker = root / 'handler-called'
            package = write_side_effect_plugin(root, marker)
            home = root / 'home'
            (home / 'plugins').mkdir(parents=True)
            shutil.copytree(package, home / 'plugins' / package.name)
            write_enabled_config(home, [package.name])
            with self.assertRaisesRegex(SystemExit, 'plugin probe failed'):
                run_probe(home, {'call_commands': ['effect-status', 'effect-status']})
            self.assertFalse(marker.exists())


class ExtendedSurfaceParityTests(unittest.TestCase):
    def test_undeclared_hook_and_cli_command_are_reported(self):
        with tempfile.TemporaryDirectory(prefix='surface-plugin-') as base:
            root = Path(base)
            package = write_side_effect_plugin(root, root / 'handler-called')
            probe = probe_plugin_package(
                package, normal_tools=[], malformed_tools=[], call_commands=[])
            errors = check_registration_parity(
                declared(package), probe, 'plugins/side-effect-plugin')
            self.assertFalse((root / 'handler-called').exists())
        self.assertTrue(any("hook 'pre_tool'" in error for error in errors), errors)
        self.assertTrue(any("CLI command 'effect'" in error for error in errors), errors)

    def test_duplicate_declaration_is_reported(self):
        with tempfile.TemporaryDirectory(prefix='duplicate-plugin-') as base:
            root = Path(base)
            package = write_side_effect_plugin(root, root / 'handler-called')
            probe = probe_plugin_package(
                package, normal_tools=[], malformed_tools=[], call_commands=[])
            manifest = declared(package)
            manifest['provides_commands'] = ['effect-status', 'effect-status']
            errors = check_registration_parity(
                manifest, probe, 'plugins/side-effect-plugin')
        self.assertTrue(any('duplicate declared command' in error for error in errors), errors)


class CliAttributionTests(unittest.TestCase):
    def test_cli_command_reports_final_registered_owner(self):
        with tempfile.TemporaryDirectory(prefix='cli-owner-') as base:
            home = Path(base) / 'home'
            plugins = home / 'plugins'
            plugins.mkdir(parents=True)
            write_cli_plugin(plugins, 'same', 'shared-command')
            category = plugins / 'category'
            category.mkdir()
            write_cli_plugin(category, 'same', 'shared-command')
            write_enabled_config(home, ['same', 'category/same'])
            report = run_probe(home, {})
        self.assertEqual(report['cli_commands']['shared-command']['key'], 'same')


class AmbiguousCliAttributionTests(unittest.TestCase):
    def test_external_setup_callback_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix='cli-external-') as base:
            home = Path(base) / 'home'
            plugins = home / 'plugins'
            plugins.mkdir(parents=True)
            write_cli_plugin(
                plugins, 'same', 'shared-command', mixed_setup=True)
            write_enabled_config(home, ['same'])
            report = run_probe(home, {})
        self.assertEqual(report['cli_commands']['shared-command']['key'], '')

    def test_duplicate_module_roots_fail_closed(self):
        with tempfile.TemporaryDirectory(prefix='cli-ambiguous-') as base:
            home = Path(base) / 'home'
            plugins = home / 'plugins'
            for category in ('cat-a', 'cat_a'):
                root = plugins / category
                root.mkdir(parents=True)
                write_cli_plugin(root, 'same', 'shared-command')
            write_enabled_config(home, ['cat-a/same', 'cat_a/same'])
            report = run_probe(home, {})
        self.assertEqual(report['cli_commands']['shared-command']['key'], '')


class CliDeltaTests(unittest.TestCase):
    def probe(self, home: Path, enabled: list[str]) -> dict:
        write_enabled_config(home, enabled)
        return run_probe(home, {})

    def test_real_cli_delta_requires_a_registration_change(self):
        with tempfile.TemporaryDirectory(prefix='cli-delta-') as base:
            home = Path(base) / 'home'
            plugins = home / 'plugins'
            category = plugins / 'category'
            category.mkdir(parents=True)
            write_cli_plugin(category, 'same', 'shared-command')
            write_cli_plugin(plugins, 'same', 'shared-command')
            absent = self.probe(home, [])
            flat = self.probe(home, ['same'])
            nested = self.probe(home, ['category/same'])
            both = self.probe(home, ['category/same', 'same'])
        self.assertEqual(
            _probe_report('same', absent, flat)['new_cli_commands'],
            ['shared-command'])
        self.assertEqual(
            _probe_report('same', both, both)['new_cli_commands'], [])
        self.assertEqual(
            _probe_report('same', nested, both)['new_cli_commands'],
            ['shared-command'])


if __name__ == '__main__':
    unittest.main()
