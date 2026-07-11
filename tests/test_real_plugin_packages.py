"""Real Hermes PluginManager contracts for public plugin packages."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from tests.support import FIXTURES, add_scripts_path

add_scripts_path()

from package_checks import check_registration_parity  # noqa: E402
from real_runtime import probe_plugin_package  # noqa: E402

_PROBES: dict[str, dict] = {}


def declared(pkg: Path) -> dict:
    return yaml.safe_load((pkg / 'plugin.yaml').read_text(encoding='utf-8'))


def fixture_probe(name: str) -> dict:
    if name not in _PROBES:
        _PROBES[name] = probe_plugin_package(FIXTURES / name)
    return _PROBES[name]


class FixtureDiscoveryTests(unittest.TestCase):
    def test_plugin_is_discovered_and_enabled(self):
        plugin = fixture_probe('complete-plugin')['plugin']
        self.assertTrue(plugin['enabled'], plugin)

    def test_disabled_plugin_registers_no_tools(self):
        probe = fixture_probe('complete-plugin')
        self.assertFalse(probe['baseline_plugin']['enabled'], probe['baseline_plugin'])
        self.assertNotIn('fixture_echo', probe['baseline']['tools'])

    def test_registered_tools_match_declaration(self):
        self.assertEqual(fixture_probe('complete-plugin')['new_tools'], ['fixture_echo'])

    def test_registered_commands_match_declaration(self):
        self.assertEqual(fixture_probe('complete-plugin')['new_commands'],
                         ['fixture-status'])

    def test_parity_accepts_matching_package(self):
        errors = check_registration_parity(
            declared(FIXTURES / 'complete-plugin'), fixture_probe('complete-plugin'),
            'plugins/complete-plugin')
        self.assertEqual(errors, [])


class HandlerBehaviourTests(unittest.TestCase):
    def test_tool_handler_returns_success_json(self):
        call = fixture_probe('complete-plugin')['tool_calls']['fixture_echo']
        self.assertTrue(call['registered'], call)
        self.assertIs(call['output'].get('success'), True)
        self.assertEqual(call['output'].get('plugin'), 'complete-plugin')

    def test_tool_handler_rejects_bad_input(self):
        call = fixture_probe('complete-plugin')['tool_calls']['fixture_echo']
        self.assertIs(call['bad_input'].get('success'), False)

    def test_command_handler_returns_text(self):
        call = fixture_probe('complete-plugin')['command_calls']['fixture-status']
        self.assertIn('complete-plugin', call['output'])


class DeclarationMismatchTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='mismatch-plugin-'))
        self.addCleanup(shutil.rmtree, self.base, True)
        self.pkg = self.base / 'complete-plugin'
        shutil.copytree(FIXTURES / 'complete-plugin', self.pkg)

    def redeclare(self, **changes) -> dict:
        data = declared(self.pkg)
        data.update(changes)
        (self.pkg / 'plugin.yaml').write_text(
            yaml.safe_dump(data, sort_keys=False), encoding='utf-8')
        return data

    def test_declared_tool_without_real_registration_is_reported(self):
        data = self.redeclare(provides_tools=['fixture_echo', 'ghost_tool'])
        errors = check_registration_parity(
            data, probe_plugin_package(self.pkg), 'plugins/complete-plugin')
        self.assertTrue(any('ghost_tool' in e for e in errors), errors)

    def test_undeclared_registered_command_is_reported(self):
        data = self.redeclare(provides_commands=[])
        errors = check_registration_parity(
            data, probe_plugin_package(self.pkg), 'plugins/complete-plugin')
        self.assertTrue(any('fixture-status' in e for e in errors), errors)


class BundledSkillTests(unittest.TestCase):
    def test_registered_skill_resolves_to_real_skill_file(self):
        entry = fixture_probe('skill-plugin')['skills'].get('skill-plugin:demo')
        self.assertIsNotNone(entry, fixture_probe('skill-plugin')['skills'])
        self.assertTrue(entry['is_skill_file'], entry)

    def test_parity_accepts_bundled_skill_package(self):
        errors = check_registration_parity(
            declared(FIXTURES / 'skill-plugin'), fixture_probe('skill-plugin'),
            'plugins/skill-plugin')
        self.assertEqual(errors, [])

    def test_missing_skill_file_breaks_real_load(self):
        base = Path(tempfile.mkdtemp(prefix='missing-skill-'))
        self.addCleanup(shutil.rmtree, base, True)
        pkg = base / 'skill-plugin'
        shutil.copytree(FIXTURES / 'skill-plugin', pkg)
        (pkg / 'skills' / 'demo' / 'SKILL.md').unlink()
        probe = probe_plugin_package(pkg)
        self.assertFalse(probe['plugin']['enabled'], probe['plugin'])
        errors = check_registration_parity(declared(pkg), probe, 'plugins/skill-plugin')
        self.assertTrue(any('demo' in e for e in errors), errors)


if __name__ == '__main__':
    unittest.main()
