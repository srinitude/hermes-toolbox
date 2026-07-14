"""Adversarial publisher-policy authority and completeness contracts."""
from __future__ import annotations

import json
import os
import unittest

from tests.support import REPO, add_scripts_path

add_scripts_path()

from plugin_checks import governed_registration_errors  # noqa: E402
from tests.test_plugin_probe_policy import GovernedProbeCase

POLICY_ENV = 'HERMES_TOOLBOX_PLUGIN_PROBE_POLICY'
REL = 'plugins/side-effect-plugin'


class EnvironmentPolicyTests(GovernedProbeCase):
    def test_environment_path_cannot_delegate_policy_authority(self):
        candidate = self.package / 'candidate-policy.json'
        candidate.write_text(json.dumps({
            'side-effect-plugin': self.policy(
                normal=['effect_tool'], skipped=['effect-status'])}))
        previous = os.environ.pop(POLICY_ENV, None)
        os.environ[POLICY_ENV] = str(candidate)
        self.addCleanup(self.restore_env, previous)
        errors = governed_registration_errors(self.package, REL, self.repo)
        self.assertFalse(self.marker.exists())
        self.assertTrue(any('missing publisher' in error for error in errors), errors)

    def restore_env(self, previous: str | None) -> None:
        if previous is None:
            os.environ.pop(POLICY_ENV, None)
        else:
            os.environ[POLICY_ENV] = previous


class FilesystemPolicyTests(GovernedProbeCase):
    def test_dangling_local_symlink_blocks_tracked_fallback(self):
        self.write_policy(self.policy(
            normal=['effect_tool'], skipped=['effect-status']))
        local = self.repo / '.git/info/public-plugin-handler-allowlist.json'
        local.parent.mkdir(parents=True)
        local.symlink_to(self.root / 'missing-policy')
        errors = governed_registration_errors(self.package, REL, self.repo)
        self.assertFalse(self.marker.exists())
        self.assertTrue(any('symlink' in error for error in errors), errors)

    def test_symlinked_policy_ancestor_is_rejected(self):
        external = self.root / 'external'
        external.mkdir()
        (external / 'plugin-runtime-probes.json').write_text(json.dumps({
            'side-effect-plugin': self.policy(
                normal=['effect_tool'], skipped=['effect-status'])}))
        (self.repo / 'inventory').symlink_to(external, target_is_directory=True)
        errors = governed_registration_errors(self.package, REL, self.repo)
        self.assertFalse(self.marker.exists())
        self.assertTrue(any('symlink' in error for error in errors), errors)


class PolicyDocumentTests(GovernedProbeCase):
    def write_raw(self, text: str) -> None:
        inventory = self.repo / 'inventory'
        inventory.mkdir()
        (inventory / 'plugin-runtime-probes.json').write_text(text)

    def test_duplicate_top_level_name_is_rejected(self):
        value = json.dumps(self.policy(
            normal=['effect_tool'], skipped=['effect-status']))
        self.write_raw(
            f'{{"side-effect-plugin":{value},"side-effect-plugin":{value}}}')
        errors = governed_registration_errors(self.package, REL, self.repo)
        self.assertFalse(self.marker.exists())
        self.assertTrue(any('duplicate' in error for error in errors), errors)

    def test_invalid_unselected_entry_is_rejected(self):
        self.write_raw(json.dumps({
            'side-effect-plugin': self.policy(
                normal=['effect_tool'], skipped=['effect-status']),
            'other-plugin': {'unknown': True},
        }))
        errors = governed_registration_errors(self.package, REL, self.repo)
        self.assertFalse(self.marker.exists())
        self.assertTrue(any('unknown fields' in error for error in errors), errors)


class PolicyCoverageTests(GovernedProbeCase):
    def test_unselected_command_fails_before_tool_handler(self):
        errors = self.errors(self.policy(normal=['effect_tool']))
        self.assertFalse(self.marker.exists())
        self.assertTrue(any('unprobed commands' in error for error in errors), errors)

    def test_explicitly_skipped_command_allows_selected_tool(self):
        self.errors(self.policy(
            normal=['effect_tool'], skipped=['effect-status']))
        self.assertEqual(self.marker.read_text(), 'tool:object\n')

    def test_missing_result_identity_is_rejected(self):
        source = self.package / '__init__.py'
        text = source.read_text().replace(
            ', "plugin": "side-effect-plugin"', '')
        source.write_text(text)
        errors = self.errors(self.policy(
            normal=['effect_tool'], malformed=['effect_tool'],
            skipped=['effect-status']))
        self.assertTrue(any('identity' in error for error in errors), errors)


class TrackedPolicyTests(unittest.TestCase):
    def test_policy_is_deployed_for_all_public_source_plugins(self):
        path = REPO / 'inventory/plugin-runtime-probes.json'
        policies = json.loads(path.read_text())
        holds = {
            'brand-chaos-oracle', 'impeccable-workflow',
            'kanban-workflow-control-plane', 'link-agent-wallet',
            'taste-skill-workflow', 'toolcraft-workflow',
        }
        self.assertEqual(len(policies), 29)
        self.assertEqual({name for name, policy in policies.items()
                          if not policy['normal_tools']}, holds)
        for name, policy in policies.items():
            if name in holds:
                self.assertFalse(policy['normal_tools'] or policy['malformed_tools'])
                self.assertFalse(policy['call_commands'])
            else:
                self.assertEqual(policy['normal_tools'], policy['malformed_tools'])
                self.assertFalse(policy['skip_commands'])


if __name__ == '__main__':
    unittest.main()
