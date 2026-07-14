"""Publisher-controlled real-handler policy contracts."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.support import add_scripts_path

add_scripts_path()

from plugin_checks import governed_registration_errors  # noqa: E402
from tests.plugin_runtime_cases import write_side_effect_plugin


class GovernedProbeCase(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='governed-probe-'))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.marker = self.root / 'handler-called'
        self.package = write_side_effect_plugin(self.root, self.marker)

    def write_policy(self, policy: object) -> None:
        inventory = self.repo / 'inventory'
        inventory.mkdir(exist_ok=True)
        (inventory / 'plugin-runtime-probes.json').write_text(
            json.dumps({'side-effect-plugin': policy}), encoding='utf-8')

    def errors(self, policy: dict) -> list[str]:
        self.write_policy(policy)
        return governed_registration_errors(
            self.package, 'plugins/side-effect-plugin', self.repo)

    def policy(self, *, normal=(), malformed=(), commands=(), skipped=()) -> dict:
        return {
            'normal_tools': list(normal),
            'malformed_tools': list(malformed),
            'call_commands': list(commands),
            'skip_commands': list(skipped),
            'payload': {'message': 'local probe'},
        }


class PolicyExecutionTests(GovernedProbeCase):
    def test_empty_policy_fails_before_handlers(self):
        errors = self.errors(self.policy())
        self.assertFalse(self.marker.exists())
        self.assertTrue(any('unprobed tools' in error for error in errors), errors)

    def test_normal_only_policy_calls_only_normal_handler(self):
        self.errors(self.policy(
            normal=['effect_tool'], skipped=['effect-status']))
        self.assertEqual(self.marker.read_text(), 'tool:object\n')

    def test_malformed_only_policy_calls_only_malformed_handler(self):
        self.errors(self.policy(
            malformed=['effect_tool'], skipped=['effect-status']))
        self.assertEqual(self.marker.read_text(), 'tool:malformed\n')


class PolicyValidationTests(GovernedProbeCase):
    def test_invalid_policy_fails_before_handlers(self):
        policy = self.policy(normal=['effect_tool', 'effect_tool'])
        errors = self.errors(policy)
        self.assertFalse(self.marker.exists())
        self.assertTrue(any('duplicates' in error for error in errors), errors)

    def test_hardlinked_policy_fails_before_handlers(self):
        source = self.root / 'shared-policy.json'
        source.write_text(json.dumps({
            'side-effect-plugin': self.policy(normal=['effect_tool'])}))
        target = self.repo / 'inventory/plugin-runtime-probes.json'
        target.parent.mkdir()
        target.hardlink_to(source)
        errors = governed_registration_errors(
            self.package, 'plugins/side-effect-plugin', self.repo)
        self.assertFalse(self.marker.exists())
        self.assertTrue(any('hardlink' in error for error in errors), errors)


if __name__ == '__main__':
    unittest.main()
