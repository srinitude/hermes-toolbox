# Public Profile Packages

Public profile packages are reusable, declarative, and sanitized. Each package
must include a manifest describing included files and excluded private/runtime
categories. Live environment variables, credentials, memory, sessions, logs,
caches, state databases, and pairing state are never included.

## Native distribution contract

New profile packages are exported as native Hermes profile distributions and
must carry `distribution.yaml`, `SOUL.md`, `config.yaml`, `README.md`, and
`manifest.json`. The distribution manifest declares `name`, `version`,
`description`, `hermes_requires`, `author`, and `license`, and never carries
`source`, `installed_at`, or absolute local paths. `config.yaml` holds only
reusable non-secret settings; runtime counters, credentials, and profile
state stay local. Every `distribution_owned` path resolves inside the package.

## Export policy

Profiles are exported only through an explicit allowlist — a repeatable
`--public-profile` flag or the local, untracked
`.git/info/public-profile-allowlist.txt`. There is no default profile sweep.
Each candidate is staged, sanitized, validated, and installed into a
disposable Hermes home with the real `hermes profile install` before it may
replace its destination; a failing candidate leaves the existing public
package byte-for-byte unchanged.

## Install

```bash
hermes profile install profiles/<name> --name <profile-name> --yes
```
