# Public Profile Distribution Example

A reusable public profile package is a native Hermes distribution and
includes:

- `distribution.yaml` — declares `name`, `version`, `description`,
  `hermes_requires`, `author`, `license`, and the `distribution_owned` paths,
  and never carries `source` or `installed_at`.
- `SOUL.md`
- `config.yaml` — only reusable, non-secret settings.
- `README.md`
- `manifest.json` — the sanitized package manifest naming the excluded
  private/runtime categories.

It must not include credentials, memory, sessions, logs, caches, state
databases, pairing state, or runtime files, and every `distribution_owned`
path must resolve inside the package.
