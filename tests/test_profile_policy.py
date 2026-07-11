"""Fail-closed selection gates for public profile distribution candidates."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from tests.support import add_profile, add_scripts_path, make_home

add_scripts_path()

from candidate_policy import PolicyConfig, decide_profile, profile_candidate  # noqa: E402

PROFILE = 'pub-demo'


def make_policy(**overrides) -> PolicyConfig:
    values = {'public_plugins': (), 'public_plugin_profile': 'pub-src',
              'private_profile_prefix': 'priv-', 'public_profiles': (PROFILE,)}
    values.update(overrides)
    return PolicyConfig(**values)


class ProfilePolicyCase(unittest.TestCase):
    def setUp(self):
        base = Path(tempfile.mkdtemp(prefix='profile-policy-'))
        self.addCleanup(shutil.rmtree, base, True)
        self.home = make_home(base)
        self.repo = base / 'repo'
        add_profile(self.home, PROFILE)

    def decide(self, name: str = PROFILE, **overrides):
        candidate = profile_candidate(self.home, self.repo, name)
        return decide_profile(candidate, make_policy(**overrides))


class ProfileGateTests(ProfilePolicyCase):
    def test_profile_requires_explicit_allowlist_entry(self):
        decision = self.decide(public_profiles=())
        self.assertFalse(decision.accepted)
        self.assertTrue(any('allowlist' in r for r in decision.reasons))

    def test_private_prefix_profile_is_rejected(self):
        add_profile(self.home, 'priv-demo')
        decision = self.decide(name='priv-demo', public_profiles=('priv-demo',))
        self.assertFalse(decision.accepted)
        self.assertTrue(any('private prefix' in r for r in decision.reasons))

    def test_plugin_source_profile_is_not_a_distribution(self):
        decision = self.decide(name='pub-src', public_profiles=('pub-src',))
        self.assertFalse(decision.accepted)
        self.assertTrue(any('plugin source' in r for r in decision.reasons))


class ProfileSourceGateTests(ProfilePolicyCase):
    def test_profile_without_distribution_manifest_is_rejected(self):
        (self.home / 'profiles' / 'bare').mkdir()
        decision = self.decide(name='bare', public_profiles=('bare',))
        self.assertFalse(decision.accepted)
        self.assertTrue(any('distribution manifest' in r for r in decision.reasons))

    def test_traversal_profile_name_is_rejected(self):
        decision = self.decide(name='../escape', public_profiles=('../escape',))
        self.assertFalse(decision.accepted)

    def test_complete_allowlisted_profile_is_accepted(self):
        decision = self.decide()
        self.assertEqual(decision.reasons, ())
        self.assertTrue(decision.accepted)


if __name__ == '__main__':
    unittest.main()
