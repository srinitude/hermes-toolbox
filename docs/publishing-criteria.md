# Publishing Criteria

A candidate is publishable only when all checks pass.

## Source gate

- Skills must be public-safe and reusable.
- Profile packages must be generic and sanitized.
- Plugin packages must come from the configured public-plugin-source profile,
  have generic names, and be sanitized.

## Completeness

- Skill frontmatter includes `name`, `description`, `version`, `author`, and
  `license`.
- Referenced files exist.
- Scripts pass syntax checks.
- Profile packages include a manifest.
- Plugin packages include a manifest.

## Public safety

- No credentials, auth stores, memories, sessions, logs, caches, state
  databases, pairing state, cron output, or runtime/private data.
- No private profile names, private plugin names, private paths, account
  identifiers, or personal examples.
- Approved authorship metadata in skill frontmatter is allowed.

## Meaningful change

The content fingerprint must differ from `inventory/source-fingerprints.json`,
and the update must not be only generated noise.
