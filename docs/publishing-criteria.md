# Publishing Criteria

A candidate is publishable only when all checks pass.

## Source gate

- Skills must be public-safe and reusable.
- Profile packages must be generic and sanitized.
- Plugin packages must come from the configured public-plugin-source profile,
  have generic names, and be sanitized.
- Personality primitives must be reusable custom `/personality` presets with
  public-safe config snippets and sanitized manifests.

## Completeness

- Skill frontmatter includes `name`, `description`, `version`, `author`, and
  `license`.
- Referenced files exist.
- Scripts pass syntax checks.
- Profile packages include a manifest.
- Plugin packages include a manifest.
- Personality primitives include a manifest and a relative `config_file` that
  resolves inside the primitive package.

## Public safety

- No credentials, auth stores, memories, sessions, logs, caches, state
  databases, pairing state, cron output, or runtime/private data.
- No private profile names, private plugin names, private paths, account
  identifiers, or personal examples.
- Approved authorship metadata in skill frontmatter is allowed.

## Meaningful change

The content fingerprint must differ from `inventory/source-fingerprints.json`,
and the update must not be only generated noise.
