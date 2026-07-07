# Public/private Hermes repository prompt patterns

Use this reference when enhancing prompts for splitting Hermes Agent configuration into public and private repositories.

## Public repository defaults

Public Hermes toolbox/config/profile repositories should be identity-neutral by default. Enhanced prompts should prohibit tracked public content that includes:

- private/person-specific profile names from the user's live Hermes home;
- personal plugin names or plugin contents that reveal personal details;
- raw memories, sessions, logs, caches, state DBs, auth stores, `.env`, or OAuth/token files;
- private email addresses in tracked content, private paths, family/contact details, or user-identifying prose;
- literal user identifiers such as a real name or `/home/<real-user>` unless the user explicitly approves publishing them.

Authorship metadata is a deliberate exception for the repository owner's public repos: public skill frontmatter should keep `author: <repo-author-name>` for repository-author-authored skills, and repo-local Git config / commit metadata should use `<repo-author-name> <<private-term>>` for both public and private repos. Identity-neutrality means “no private context or personal operational details,” not “erase approved author identity.” Do not substitute generic authors like `Hermes Toolbox Contributors`, do not use `noreply@example.com` for repo Git config, and never add AI co-authoring trailers such as `Co-authored-by:` or generated-by-AI authorship trailers.

Prefer placeholders:

- `$HERMES_HOME`
- `$HOME`
- `<profile>`
- `<repo>`
- `<user>`
- `<first-name>`
- `<role-or-use-case>`
- `<role-use-case-category-or-responsibility>`
- `example.com`
- `/path/to/hermes-home`

### Public reusable workflow/personality primitives

For public Hermes toolbox repos, workflow primitives that docs recommend must be packaged as installable artifacts, not merely mentioned in prose. For a custom `/personality` primitive:

- Store it under a generic path such as `primitives/personalities/<name>/`.
- Include `config.public.yaml` containing only the reusable `agent.personalities.<name>` snippet; do not include live `agent.system_prompt`, memories, sessions, logs, state DBs, auth stores, `.env`, or profile runtime data.
- Include `manifest.json` with `type: "personality"`, `sanitized: true`, `config_file`, and the standard excluded private/runtime categories.
- Installer support should write the snippet through `hermes config set agent.personalities.<name> ...`; activation of `agent.system_prompt` and `display.personality` must be an explicit opt-in flag, not the default install path.
- Public manifests/fingerprints should record the personality package and config hash, and validators should check personality package manifests just like sanitized profile/plugin manifests.

### Public reusable profile packages

For the repository owner's public Hermes toolbox/profile repos, profile publishability is prefix- and sanitization-based:

- `<first-name>-`-prefixed profiles are user-specific/private and must not be published to public repos.
- Profiles not prefixed `<first-name>-` may be published as reusable role/use-case/category/responsibility profile packages only after sanitization.
- A public profile package should contain declarative/reusable artifacts such as `PROFILE.md`, `config.public.yaml`, `manifest.json`, public-safe skill/plugin references, and generic usage docs.
- A public profile package must strip associated `.env`, auth/OAuth/token stores, memories, sessions, logs, caches, `state.db*`, pairing state, cron outputs, checkpoints, and any private/runtime profile data.
- The package `manifest.json` should record the source profile name, included public files, excluded private/runtime categories, and sanitization decisions.
- Public docs should describe person-specific prefixes generically as `<first-name>-`; pass `<first-name>-` as a local private prefix through CLI/env/untracked config or `.git/info` files rather than hardcoding it in tracked public docs/scripts.

### Public reusable plugin packages

For the repository owner's public Hermes toolbox/plugin repos, plugin publishability is source-gated as well as sanitization-based:

- Only plugins sourced from the `non-<first-name>-plugins` profile may be uploaded to public repos.
- Plugins from global/default Hermes homes, `<first-name>-plugins`, any `<first-name>-*` profile, or any other profile remain private unless the user explicitly changes the public-plugin-source gate.
- Public plugin packages must not be `<first-name>-`-prefixed and must be generic/reusable rather than personal, family, account, or private-workflow specific.
- A public plugin package should contain reusable plugin code/docs/metadata and `manifest.json`; it must strip associated `.env`, auth/OAuth/token stores, memories, sessions, logs, caches, `state.db*`, pairing state, cron outputs, checkpoints, and any private/runtime plugin data.
- Public tracked docs should describe this generically as a configured public-plugin-source profile; pass `non-<first-name>-plugins` through CLI/env/untracked config or `.git/info` files rather than hardcoding it in public prose.
- Validators should allow manifest-backed sanitized public plugin package names only when the manifest proves the source gate and private/runtime data exclusions.

For public artifacts derived from private Hermes state, require both:

1. public-safety validation: no secrets/private runtime state;
2. identity-neutrality validation: no private/person-specific profile names, personal plugin details, private paths, or personal identifiers outside approved authorship metadata, while allowing sanitized non-`<first-name>-` reusable profile package names.

When generating validators, explicitly allow `author: <repo-author-name>` in public `SKILL.md` frontmatter for repository-author-authored skills, allow manifest-backed sanitized non-`<first-name>-` profile package names, and verify repo-local Git config is `<repo-author-name> <<private-term>>`. Store any denylist of private profile/plugin names in an untracked local path such as `.git/info/private-profile-denylist.txt`, not in tracked public inventory files.

Public docs should explain deterministic workflow primitives generically: `/personality validator`, `/prompt-enhancer [prompt]`, `/profile-builder [goal]`, `/plugin-builder [goal]`, discovery, candidate classification, sanitized export, safety validation, identity-neutrality validation, fingerprinting, publish-or-silent-no-op behavior, and no-agent cron scheduling.

## Private repository defaults

Do not assume "private backup" means "archive the whole Hermes installation." First distinguish:

- **Non-reinstallable custom state**: user-authored config, `.env`, auth stores, profile state, memories, session/continuity DBs, cron jobs, local scripts, custom/local skills, custom/local plugins, gateway/pairing state, MCP config, shell hook allowlists, and user-created support files.
- **Reinstallable/generated state**: Hermes source checkouts, bundled/hub packages, virtualenvs, managed runtimes, dependency caches, `node_modules`, build outputs, `__pycache__`, generated logs, web/model caches, and other artifacts recreated by reinstalling Hermes Agent or rerunning setup.

Unless the user explicitly asks for a full disk-style archive, enhance the prompt so the private repo backs up non-reinstallable custom configuration/state only. Require a manifest that records:

- included paths;
- excluded reinstallable categories;
- the reason for each include/exclude decision;
- restore actions for excluded reinstallable items;
- version/source/commit where available.

Still require a hard preflight that verifies the private remote is actually private before any commit/push that may contain secrets.

## Common validation threshold

A good enhanced prompt for this class is complete only when it proves:

- public repo validation and identity-neutrality checks pass;
- sanitized profile packages, if present, are not `<first-name>-`-prefixed and have manifests proving env/auth/memory/session/log/cache/state/pairing/runtime data was excluded;
- sanitized plugin packages, if present, come only from the `non-<first-name>-plugins` source profile, are not `<first-name>-`-prefixed, and have manifests proving env/auth/token/memory/session/log/cache/state/pairing/runtime data was excluded;
- private repo remote visibility is private;
- private backup contains the non-reinstallable archive plus manifest;
- manifest includes excluded reinstallable artifacts with restore actions;
- public cron no-candidate path exits `0` with empty stdout;
- private backup cron and public candidate cron exist without duplicates.
