# Publishing Criteria

A candidate is publishable only when all checks pass. Publication is
fail-closed: the newest candidate that passes every gate is published
("latest passing"), and a newer-but-failing candidate never replaces the
existing public package ("last known good"). When a previously published
package itself stops passing a hardened gate, it is unpublished rather than
patched in place. Rejected candidates stay local-only and are never named in
tracked public files.

## Explicit selection

- Candidates enter the exporter only through repeatable CLI flags or local,
  untracked allowlists under `.git/info/`; there is no default sweep.
- Plugins must come from the configured public-plugin-source profile.
- Private-prefix profile names are rejected outright.

## Source gate

- Skills must be local, public-safe, and reusable.
- Profile packages must be generic, non-private, and exported as native
  distributions.
- Personality primitives must be reusable custom `/personality` presets with
  public-safe config snippets and sanitized manifests.

## Completeness

- Skill frontmatter includes `name`, `description`, `version`, `author`, and
  `license`; referenced support files resolve inside the package.
- Native profile packages carry `distribution.yaml`, `SOUL.md`, `config.yaml`,
  `README.md`, and `manifest.json`, declare `name`, `version`, `description`,
  `hermes_requires`, `author`, and `license`, and never carry `source`,
  `installed_at`, credential-like config keys, or absolute local paths.
- Plugin and profile packages include a sanitized `manifest.json` naming the
  excluded private/runtime categories.
- No package contains TODO markers, placeholder bodies, mocks, stubs, fakes,
  spies, skipped tests, or xfail tests.
- Every public Python file satisfies the structural gates: 200-line files,
  30-line named constructs, nesting depth of three.

## Real behavior

- Plugin discovery and registration are proven with the real Hermes
  `PluginManager` in a disposable Hermes home; declared tools, commands, and
  bundled skills must match what the real manager registers.
- Profile packages must install with the real `hermes profile install` into a
  disposable Hermes home.

## Public safety

- No credentials, auth stores, memories, sessions, logs, caches, state
  databases, pairing state, cron output, or runtime/private data.
- No private profile names, private plugin names, private paths, account
  identifiers, or personal examples.
- Approved authorship metadata in skill frontmatter is allowed.

## Meaningful change

The content fingerprint must differ from `inventory/source-fingerprints.json`,
and the update must not be only generated noise. When nothing qualifies, the
publisher exits silently with no commit.
