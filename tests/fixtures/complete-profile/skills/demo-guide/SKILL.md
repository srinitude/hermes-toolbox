---
name: demo-guide
description: Fixture walkthrough skill bundled inside the complete-profile fixture.
version: 1.0.0
author: Kiren Srinivasan
license: MIT
---

# Demo Guide

This skill is the distribution-owned payload of the complete-profile fixture.
Profile export tests use it to prove that owned skill directories are copied
into the public package, sanitized, and registered by a real installed
profile without any private or runtime content coming along.

## When to Use

Use this skill whenever a test needs a profile package that bundles at least
one complete skill: full frontmatter, a body long enough to be useful, and
explicit guidance with no environment-specific content anywhere in the text.

## How it works

1. The fixture profile lists its `skills` directory as distribution-owned.
2. The exporter stages this file into the public profile package.
3. Sanitization runs over the text and finds nothing to rewrite.
4. The staged package installs into a disposable Hermes home.
5. An enabled-only skills listing runs against the installed profile.
6. Assertions confirm the skill file arrived intact inside the package.

## Steps

1. Copy the complete-profile fixture into a temporary Hermes home.
2. Export it through an explicit `--public-profile` allowlist entry.
3. Read the staged skill back from the exported package directory.
4. Keep this fixture free of names, hosts, emails, and absolute paths.

## Limitations

This skill carries no executable payload and no support files. Tests that
need richer bundled-skill coverage should synthesize additional files in a
temporary copy of the fixture rather than growing this one, because its
bytes anchor checksum comparisons used across the profile export suite.
