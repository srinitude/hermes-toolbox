# External Repo Context for Profile Customization

Use this reference when a profile-building request says an external repository should guide the new profile's conversations, identity, workspace, or future plugins.

## Objective

Convert the external repo from vague background context into validated profile primitives without copying unsafe/runtime material or stuffing the whole repo into `SOUL.md`.

## Read-only intake pattern

1. Clone or inspect the repo in a temporary/read-only workspace first, not inside the target profile before approval.
2. Verify the source and exact revision:
   - `git ls-remote origin HEAD`
   - `git rev-parse HEAD`
3. Enumerate tracked content with `git ls-tree -r --name-only HEAD`.
4. Read every tracked file byte-for-byte when the user asks for complete repo ingestion.
5. Produce a manifest with at least: path, line count, byte count, SHA-256, total file count, total bytes, total lines, and commit SHA.
6. Exclude `.git/` internals from repo-content claims unless the user explicitly asks to inspect git metadata.
7. Prefer deterministic extraction over broad summarization: chapter maps, index tables, headers, warnings, metadata notes, repeated domain terms, and candidate workflows.

## Profile-spec integration

Map repo-derived context across the profile primitive set:

- `profile`: name/description says the profile uses the repo as a source corpus or operating context.
- `identity`: `SOUL.md` gets only durable role/stance. Do not dump raw repo material into SOUL.
- `configuration`: set `terminal.cwd` to a profile workspace containing the repo when approved.
- `terminal`: if a fixed local cwd is required, patch/validate the profile alias wrapper to `cd` into the workspace before `exec hermes -p <profile> "$@"`.
- `capabilities`: ensure file/search skills/tools can inspect the repo; add relevant domain skills only if they are reusable.
- `memory`: save only stable decisions, not a diary or raw corpus.
- `automation`: mark repo-derived cron/gateway/plugin actions blocked until explicitly designed and approved.
- `security`: avoid publishing private/person-specific `<first-name>-*` profile repos or copying secrets/runtime artifacts.
- `performance`: use a concise workspace `.hermes.md` plus a profile-local skill/reference, rather than injecting a large corpus into every prompt.
- `validation`: prove the target clone commit, file count, and profile smoke chat can see the workspace.
- `portability`: record source URL/revision and whether the profile is private or distributable.

## Recommended write shape after approval

When approved, create:

1. A profile workspace under the approved convention, e.g. `~/hermes-profiles/<private-term>/<profile>/` for user-specific profiles.
2. A full repo clone under that workspace.
3. A concise workspace `.hermes.md` that points Hermes at the repo, states citation expectations, warns about known corpus caveats, and defines how to use the material.
4. A profile-local class-level skill when the repo represents a durable operating system for the profile. Put distilled workflow/rubrics in `SKILL.md`; put corpus-specific manifests, maps, and detailed notes in `references/`.

## Pitfalls

- Do not present the final approval spec before complete-read validation when the user explicitly said every file must be read.
- Do not call the repo authoritative if internal files show title/content/metadata mismatches; encode the caveat in `.hermes.md`, the profile-local skill, and validation notes.
- Do not include generated plugins just because the repo implies future automation. Treat plugins as candidates that require separate `/plugin-builder` design and explicit approval.
- Do not copy `.env`, auth stores, caches, logs, sessions, `state.db*`, checkpoints, or plugin runtime state into the target profile or public artifacts.
