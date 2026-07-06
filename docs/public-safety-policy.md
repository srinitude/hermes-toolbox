# Public Safety Policy

Public artifacts must be reusable and safe to share.

Never publish:

- `.env` files, API keys, tokens, OAuth stores, auth databases, or credential
  caches.
- Raw memories, sessions, logs, caches, state databases, pairing state,
  checkpoints, or backups.
- Person-specific profile names, family-specific profile names, private
  plugin names, account identifiers, private paths, or private examples.
- Plugin runtime state, plugin credentials, plugin cache files, cron output,
  or profile-local private data.

Profile packages may be public only when they are generic, declarative,
sanitized, and manifest-backed.

Plugin packages may be public only when they come from a configured
public-plugin-source profile, have generic names, are sanitized, and include a
manifest documenting included files and excluded private/runtime categories.
