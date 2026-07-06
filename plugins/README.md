# Public Plugin Packages

Public plugin packages are exported only from a configured
public-plugin-source profile. Each package must be generic, reusable,
sanitized, and accompanied by a manifest. Credentials, token stores, memory,
sessions, logs, caches, state databases, pairing state, cron outputs, and
runtime/private data are never included.
