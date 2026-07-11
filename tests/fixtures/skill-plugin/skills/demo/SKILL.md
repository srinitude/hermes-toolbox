---
name: demo
description: Fixture bundled skill proving real plugin skill registration.
version: 1.0.0
author: Kiren Srinivasan
license: MIT
---

# Demo Bundled Skill

This fixture skill ships inside the `skill-plugin` fixture package. The real
Hermes plugin manager registers it under the qualified name
`skill-plugin:demo`, and the toolbox tests assert that the registered path is
a real file named `SKILL.md` inside the package.

## When to Use

Use this skill fixture whenever a test needs a plugin package that bundles a
complete, resolvable skill. It carries full frontmatter and explicit usage
guidance so it passes the same static gates applied to public packages.

Concretely, the toolbox test suite exercises it in two directions:

- **Acceptance:** the package is copied into a temporary Hermes home,
  enabled through `plugins.enabled` in a temporary `config.yaml`, and probed
  with the real `PluginManager`. The probe must report the qualified skill
  `skill-plugin:demo` with a path that resolves to this file.
- **Rejection:** a copy of the package with this file deleted must fail real
  discovery, because `register_skill` refuses paths that do not exist. The
  registration-parity check must then report the declared skill as missing.

## How It Works

The package's `register` entry point calls `ctx.register_skill` with an
absolute `Path` built from the package's own location. Hermes resolves the
skill as `<plugin_name>:<skill_name>` and keeps it out of the flat skills
tree, so bundled skills are opt-in explicit loads only.

## Limitations

This fixture intentionally registers no tools and no commands, so the
registration-parity gate can prove that empty declarations stay empty under
the real manager. It is test data for the export pipeline, not a skill meant
for direct installation into a real Hermes home.
