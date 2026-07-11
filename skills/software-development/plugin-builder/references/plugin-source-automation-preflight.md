# Plugin source automation preflight

Use this before creating or refreshing a plugin inside a shared workshop, distribution, or public-source profile.

## Why this matters

A file write can have an external side effect even when the current task never runs `git push`, an upload command, or a publishing API. Cron jobs, filesystem watchers, CI agents, and export scripts may mirror every child directory from a source profile into a public repository or distribution channel.

Treat the source directory's downstream automation as part of the plugin's write boundary.

## Preflight

Before the first plugin-source write:

1. Resolve the exact source-owner profile and target directory.
2. Inspect configured cron jobs in every plausible owner profile; publisher automation may run under the default profile even when it consumes another profile's plugin tree.
3. Locate the wrapper, scanner, exporter, validator, and publisher scripts read-only. Determine whether automation selects explicit packages or scans every child directory, and whether exclusion is prefix-only or package-specific.
4. Inspect the destination repository's status before any write or resume decision. A failed export can leave modified, deleted, and untracked candidate files even when validation prevented commit/push.
5. Record whether the user approved only local creation, consumer installation, candidate export, commit, push, or actual publication. These are separate approvals.
6. If unapproved automation would consume the new directory, stop it before the write using the narrowest reversible control, normally pausing only the relevant publisher. Record its prior state and do not resume it until the user approves the downstream action or an explicit package allowlist/opt-out exists.
7. Before resuming a publisher, reconcile any dirty candidate repository independently; never let a new package be bundled into an unrelated failed-export diff.
8. Keep source ownership separate from consumer enablement. A workshop/source profile may contain the package while remaining disabled as a consumer.

## Post-write validation

Before reporting success:

- verify no public/distribution copy appeared;
- verify no commit, push, release, or upload occurred;
- verify excluded profiles did not receive consumer copies;
- report any publisher left paused and why;
- state the exact user decision needed before resuming it;
- if publication was approved, sanitize and validate the exported package separately rather than treating source creation as publication approval.

## Long-lived process note

Enabling a plugin in config proves future discovery, not that every already-running gateway or TUI process reloaded it. Use a fresh-process `PluginManager` probe for non-disruptive validation, then report any restart or reload still needed. Do not restart active gateways merely to make a smoke test pass unless disruption was included in the approved scope.

## Pitfalls

- Assuming “reusable” means “approved for public release.”
- Looking only for active publisher processes while missing scheduled cron jobs or a publisher owned by a different profile.
- Checking only whether a publisher is paused while ignoring a dirty destination repository left by an earlier failed export.
- Treating a prefix exclusion as a package allowlist; a generic reusable plugin may still be swept automatically.
- Resuming a paused publisher automatically after creating a package that still lacks publication approval.
- Calling a source-owner profile an installed consumer.
- Claiming all running sessions loaded a newly enabled plugin based only on `plugins list` output.
