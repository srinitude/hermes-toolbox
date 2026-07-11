# Public Plugin Packages

Public plugin packages are exported only from a configured
public-plugin-source profile, and only through an explicit allowlist — a
repeatable `--public-plugin` exporter flag or the local, untracked
`.git/info/public-plugin-allowlist.txt`. There is no default plugin sweep.
Each package must be generic, reusable, sanitized, and accompanied by a
manifest. Credentials, token stores, memory, sessions, logs, caches, state
databases, pairing state, cron outputs, and runtime/private data are never
included.

Each candidate is staged, sanitized, and validated — including real
`PluginManager` discovery in a disposable Hermes home, completeness and
placeholder checks, and structural gates — before it may replace its
destination. A failing candidate leaves the existing public package
byte-for-byte unchanged.

## Current inventory

This inventory is currently empty. The previously published tutorial plugin
suite failed the hardened completeness gates (test doubles, oversized
modules, and placeholder content), so it was unpublished rather than patched
in place, and no current candidate has passed every gate yet. Rejected
candidates stay local-only and are not named here. Packages reappear in
`inventory/public-manifest.json` — and become installable with
`--plugin <name>` — as soon as a current source candidate passes all gates.
