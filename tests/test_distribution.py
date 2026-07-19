import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import validate_distribution as validator  # noqa: E402
from scripts.manifest_checks import OWNED_PATHS  # noqa: E402


class SandboxCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory(prefix="toolbox-test-")
        self.root = Path(self.tempdir.name)

    def tearDown(self):
        self.tempdir.cleanup()

    def write(self, relative_path, content):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path


class RepositoryContractTests(SandboxCase):
    def test_repository_passes_contract(self):
        self.assertEqual([], validator.validate_staged(ROOT))

    def test_missing_distribution_files_fail(self):
        errors = validator.required_file_errors(self.root)
        self.assertTrue(any("distribution.yaml" in item for item in errors))
        self.assertTrue(any("SOUL.md" in item for item in errors))


class ExclusionTests(SandboxCase):
    def test_every_plugin_path_fails(self):
        self.write("plugins/arbitrary/plugin.yaml", "name: rejected\n")
        errors = validator.exclusion_errors(self.root)
        self.assertTrue(any("plugins are not allowed" in item for item in errors))

    def test_claude_and_profile_builder_skills_fail(self):
        for name in ("claude" + "-code", "profile" + "-builder", "plan-package-validation"):
            self.write(f"skills/x/{name}/SKILL.md", "placeholder\n")
        self.assertEqual(3, len(validator.exclusion_errors(self.root)))

    def test_plugins_config_fails(self):
        self.write("config.yaml", yaml.safe_dump({"plugins": {"enabled": ["arbitrary"]}}))
        errors = validator.config_errors(self.root)
        self.assertTrue(any("plugins" in item for item in errors))

    def test_nested_and_list_plugin_config_fails(self):
        configs = ({"nested": {"plugins": ["x"]}}, {"nested": [{"plugins": ["x"]}]})
        for config in configs:
            with self.subTest(config=config):
                self.write("config.yaml", yaml.safe_dump(config))
                self.assertTrue(any("plugins" in item for item in validator.config_errors(self.root)))


class PrivacyTests(SandboxCase):
    def test_private_paths_in_any_file_fail(self):
        self.write("scripts/.hermes/private.txt", "/" + "Users/private-user/project\n")
        self.write("LICENSE", "C:" + "\\Users\\private-user\\project\n")
        self.assertEqual(2, sum("user path" in item for item in validator.privacy_errors(self.root)))
        self.assertTrue(any("excluded path" in item for item in validator.manifest_errors(self.root)))

    def test_email_and_tokens_in_any_file_fail(self):
        self.write(".gitignore", "person" + "@example.com\n")
        token = "ghp_" + "A" * 36
        self.write("scripts/demo.py", f'TOKEN = "{token}"\n')
        errors = validator.privacy_errors(self.root)
        self.assertTrue(any("email" in item for item in errors))
        self.assertTrue(any("token" in item for item in errors))


class ContentPolicyTests(SandboxCase):
    def test_voice_checker_ignores_fenced_test_data(self):
        self.write("SOUL.md", "```text\nblocked words: robust\n```\nA robust profile.\n")
        errors = validator.voice_errors(self.root)
        self.assertEqual(1, len(errors))
        self.assertIn("SOUL.md:4", errors[0])

    def test_model_and_provider_choices_fail(self):
        config = {"model": "example", "memory": {"provider": "example"}}
        self.write("config.yaml", yaml.safe_dump(config))
        errors = validator.config_errors(self.root)
        self.assertTrue(any("model" in item for item in errors))
        self.assertTrue(any("provider" in item for item in errors))

    def test_nested_choices_and_hyphenated_aliases_fail(self):
        configs = ({"nested": [{"provider": "x"}]}, {"fallback": "x"}, {"api-key": "x"}, {"base-url": "x"}, {"API KEY": "x"})
        for config in configs:
            with self.subTest(config=config):
                self.write("config.yaml", yaml.safe_dump(config))
                self.assertTrue(validator.config_errors(self.root))


class SkillPolicyTests(SandboxCase):
    def test_frontmatter_and_size_are_checked(self):
        body = "\n".join("line" for _ in range(200))
        header = "---\nname: demo\ndescription: too broad\nauthor: Someone Else\n---\n"
        self.write("skills/x/demo/SKILL.md", header + body)
        errors = validator.skill_errors(self.root)
        self.assertTrue(any("author" in item for item in errors))
        self.assertTrue(any("description" in item for item in errors))
        self.assertTrue(any("body line" in item for item in errors))

    def test_missing_support_file_is_checked(self):
        header = "---\nname: demo\ndescription: Use when testing support files.\n"
        content = header + "author: Kiren Srinivasan\n---\nSee `references/missing.md`.\n"
        self.write("skills/x/demo/SKILL.md", content)
        self.assertTrue(any("missing linked file" in item for item in validator.skill_errors(self.root)))


class SizePolicyTests(SandboxCase):
    def test_repository_code_size_is_checked(self):
        self.write("scripts/large.py", "line\n" * 201)
        self.assertTrue(any("code line limit" in item for item in validator.size_errors(self.root)))

    def test_construct_size_is_checked(self):
        content = "@decorator\n" * 3 + "def too_large():\n" + "    value = 1\n" * 27
        self.write("scripts/construct.py", content)
        self.assertTrue(any("construct line limit" in item for item in validator.size_errors(self.root)))

    def test_nesting_depth_is_checked(self):
        content = "def too_deep():\n    for a in ():\n        for b in ():\n            if b:\n                return a\n            else:\n                if a:\n                    return b\n"
        self.write("scripts/nested.py", content)
        self.assertTrue(any("nesting depth" in item for item in validator.size_errors(self.root)))
        allowed = "def boundary():\n    for a in ():\n        for b in ():\n            if b:\n                return a\n            elif a:\n                return b\n"
        self.write("scripts/boundary.py", allowed)
        self.assertFalse(any("boundary.py" in item for item in validator.size_errors(self.root)))


class ManifestPolicyTests(SandboxCase):
    def test_missing_owned_paths_fail(self):
        manifest = {"name": "hermes-toolbox", "distribution_owned": ["SOUL.md"]}
        self.write("distribution.yaml", yaml.safe_dump(manifest))
        self.assertTrue(any("skills/" in item for item in validator.manifest_errors(self.root)))

    def test_unsafe_and_unexpected_owned_paths_fail(self):
        owned = sorted(OWNED_PATHS) + ["../secret", "/tmp/file", "SOUL.md"]
        self.write("distribution.yaml", yaml.safe_dump({"name": "hermes-toolbox", "distribution_owned": owned}))
        errors = validator.manifest_errors(self.root)
        self.assertTrue(any("unsafe" in item for item in errors))
        self.assertTrue(any("duplicate" in item for item in errors))
        self.assertTrue(any("unexpected" in item for item in errors))

    def test_owned_paths_must_be_a_list(self):
        self.write("distribution.yaml", "name: hermes-toolbox\ndistribution_owned: SOUL.md\n")
        self.assertTrue(any("must be a list" in item for item in validator.manifest_errors(self.root)))


class ManifestRootEntryTests(SandboxCase):
    def test_owned_paths_match_root_entries(self):
        self.write("distribution.yaml", yaml.safe_dump({"name": "hermes-toolbox", "distribution_owned": sorted(OWNED_PATHS)}))
        self.write("extra.txt", "unexpected\n")
        errors = validator.manifest_errors(self.root)
        self.assertTrue(any("undeclared root entry: extra.txt" in item for item in errors))
        self.assertTrue(any("declared root entry is missing: SOUL.md" in item for item in errors))

    def test_hidden_root_entries_fail(self):
        hidden = (".git", ".hermes", ".ruff_cache", ".venv", "__pycache__")
        self.write("distribution.yaml", yaml.safe_dump({"name": "hermes-toolbox", "distribution_owned": sorted(OWNED_PATHS)}))
        for name in hidden:
            self.write(f"{name}/marker", "unexpected\n")
        errors = validator.manifest_errors(self.root)
        self.assertTrue(all(any(name in item for item in errors) for name in hidden))


class ManifestFilesystemTests(SandboxCase):
    def test_symlinked_entries_fail(self):
        target = self.root / "outside"
        target.mkdir()
        (self.root / "skills").symlink_to(target, target_is_directory=True)
        errors = validator.manifest_errors(self.root)
        self.assertTrue(any("symlink" in item for item in errors))

    def test_executable_files_fail(self):
        path = self.write("SOUL.md", "text\n")
        path.chmod(0o755)
        errors = validator.manifest_errors(self.root)
        self.assertTrue(any("executable mode" in item for item in errors))


class YamlPolicyTests(SandboxCase):
    def test_scalar_config_fails(self):
        self.write("config.yaml", "plain text\n")
        self.assertTrue(any("mapping" in item for item in validator.config_errors(self.root)))

    def test_invalid_manifest_yaml_fails(self):
        self.write("distribution.yaml", "[invalid\n")
        self.assertTrue(any("invalid YAML" in item for item in validator.manifest_errors(self.root)))


if __name__ == "__main__":
    unittest.main()
