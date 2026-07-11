"""Real contract tests for the complete-plugin fixture handlers."""
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parents[1]


def load_plugin_module():
    spec = importlib.util.spec_from_file_location('complete_plugin_fixture',
                                                  PLUGIN_DIR / '__init__.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FixtureEchoContract(unittest.TestCase):
    def test_echo_returns_success_json(self):
        module = load_plugin_module()
        result = json.loads(module.fixture_echo({'message': 'hello'}))
        self.assertTrue(result['success'])
        self.assertEqual(result['plugin'], 'complete-plugin')
        self.assertEqual(result['echo'], 'hello')

    def test_echo_rejects_non_object_arguments(self):
        module = load_plugin_module()
        result = json.loads(module.fixture_echo('not-an-object'))
        self.assertFalse(result['success'])

    def test_status_command_returns_text(self):
        module = load_plugin_module()
        self.assertIn('complete-plugin', module.fixture_status(''))


if __name__ == '__main__':
    unittest.main()
