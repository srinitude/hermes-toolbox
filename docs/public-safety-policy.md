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
sanitized, manifest-backed native distributions.

Plugin packages may be public only when they come from a configured
public-plugin-source profile, have generic names, are sanitized, and include a
manifest documenting included files and excluded private/runtime categories.

## Fail-closed publication

Safety is enforced before publication, not after. Every candidate is staged
and validated in isolation, and only an accepted candidate may replace its
destination; a failing candidate leaves the current public package
byte-for-byte unchanged. The publisher refuses to run from a dirty checkout,
stages only explicitly accepted paths, and exits silently when there is
nothing safe to publish. Rejected candidates remain local-only and are never
named in tracked public files.
