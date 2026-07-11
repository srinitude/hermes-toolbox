---
name: complete-skill
description: Fixture skill proving the shape of a complete public skill package.
version: 1.0.0
author: Kiren Srinivasan
license: MIT
---

# Complete Skill

This fixture is a structurally complete public skill package. The export
pipeline tests copy it into temporary source trees to exercise acceptance
paths, and into temporary repositories to exercise retention paths.

## When to Use

Use this fixture whenever a test needs a skill candidate that passes every
public gate: full frontmatter, a body long enough to be useful, explicit
usage guidance, and no private or environment-specific content anywhere.

## How it works

1. The test copies this directory into a temporary Hermes skills tree.
2. The exporter selects it through an explicit skill allowlist entry.
3. Sanitization runs over the text and finds nothing to rewrite.
4. Validators confirm frontmatter, length, and section requirements.
5. The transactional export replaces only this package's destination.
6. Checksum comparisons prove no other destination changed at all.

## Steps

1. Reference the fixture through its relative path under the fixtures root.
2. Never edit it inside a test; copy it first and edit the copy instead.
3. Assert on export outcomes, not on incidental formatting details.
4. Keep the fixture free of names, hosts, emails, and absolute paths.

## Limitations

This fixture carries no executable payload and no support files. Tests that
need support-directory coverage should synthesize a references directory in
their temporary copy rather than growing this fixture. It exists only to be
a stable, known-good input for pipeline behavior assertions, so changes to
its content invalidate recorded checksums used across the test suite.
