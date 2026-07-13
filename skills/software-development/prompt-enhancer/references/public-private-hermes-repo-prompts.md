# Public and Private Hermes Repository Prompt Patterns

Use this reference when enhancing prompts that separate Hermes configuration into public and private repositories.

## Public repository defaults

Public toolbox, config, profile, plugin, skill, and personality repositories are identity-neutral by default. Prohibit tracked content containing private profile/plugin names, memories, sessions, logs, caches, databases, auth stores, environment files, private paths, contact/family details, or personal operational context.

Approved authorship frontmatter and repository-local Git metadata are narrow exceptions. Represent them in reusable templates as `<repo-author-name>` and `<repo-author-email>`; resolve the actual values from approved project/user context before writing. Never invent an author or add AI co-authoring trailers.

Use portable forms such as `$HERMES_HOME`, `$HOME`, role-based profile names, `example.com`, and `/path/to/hermes-home`.

## Reusable personality packages

A custom personality must be an installable package rather than prose only:

- use a generic package path under `primitives/personalities/`;
- include only the reusable personality config snippet;
- exclude live system prompts unless explicitly part of the package contract;
- include a manifest with package type, config file, sanitization state, included files, and excluded private/runtime categories;
- make activation an explicit opt-in;
- validate manifest and config hashes.

## Reusable profile packages

Profile publishability is provenance-, allowlist-, completeness-, and sanitization-based:

- deployment-configured private-prefix profiles remain private;
- other profiles are candidates, not automatically publishable;
- require an explicitly allowlisted first-party distribution;
- include only `distribution.yaml`, `SOUL.md`, reusable `config.yaml`, `README.md`, declared distribution-owned paths, and package manifest content required by the installed contract;
- strip environment/auth stores, memories, sessions, logs, caches, databases, pairing state, cron outputs, checkpoints, timestamps, temporary paths, and runtime/private data;
- validate with the real profile installer in a disposable Hermes home;
- keep concrete source names, deny terms, and rejection evidence in untracked local metadata.

A previous package remains only when it passes the current complete contract. “Last known good” does not exempt it from a new hard safety or completeness gate.

## Reusable plugin packages

Plugin publication is source-gated as well as sanitization-gated:

- accept only the deployment-configured public plugin source profile supplied through CLI, environment, or untracked config;
- keep other source profiles private unless the user changes the gate explicitly;
- require reusable, identity-neutral package content and exact manifest lists;
- exclude environment/auth stores, memories, sessions, logs, caches, databases, pairing state, cron outputs, checkpoints, and runtime/private data;
- run static safety/completeness checks before real Hermes discovery;
- require declaration/registration parity and reviewed, no-side-effect runtime probes;
- apply repository structural and test-quality gates.

External-service plugins without an approved isolated no-side-effect probe remain blocked.

## Private repository defaults

Do not equate a private backup with a whole installation archive. Separate:

- **non-reinstallable custom state** — user-authored config, approved credential stores, profiles, memories, continuity state, cron definitions, local scripts/skills/plugins, gateway/pairing state, MCP config, and user support files;
- **reinstallable/generated state** — source checkouts, bundled/hub packages, virtual environments, managed runtimes, dependency caches, build outputs, bytecode, generated logs, and model/web caches.

Unless the user requests a disk-style archive, back up only non-reinstallable custom state. Require a manifest of included paths, excluded categories, reasons, restore actions, and versions/source commits. Verify the remote is private before any push containing protected state.

## Latest-complete refreshes

When asked to publish every latest complete primitive:

1. Define completeness with current package, reference, safety, identity, structure, runtime, and test gates.
2. Separate classification from source remediation unless remediation is explicitly authorized.
3. Compare source-tree hashes and projected public packages rather than raw private/public diffs.
4. Use explicit local allowlists plus currently published packages as the candidate universe.
5. Keep publisher automation quiescent during manual branch/PR work.
6. Export transactionally on a feature branch, prove second-run no-op, obtain exact-digest independent review, and verify post-merge state.
7. Bound every changed path to the candidate matrix.
8. Recheck protected source hashes before export, after review, and before push.

## Acceptance threshold

A complete prompt requires:

- public-safety and identity-neutrality validation;
- manifest-backed profile/plugin/personality packages with exact included-file lists;
- deployment-configured source/private gates kept outside tracked public files;
- real disposable installer/runtime checks;
- private-remote visibility proof before protected backup publication;
- non-reinstallable backup manifest and restore instructions;
- idempotent public export with clean no-candidate output;
- preserved automation state and exact source/digest seals.
