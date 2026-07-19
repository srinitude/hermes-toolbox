# Frozen distribution / profile package review

Use when the user asks for a read-only security, privacy, and scope review of a **frozen Git tree** or staged export (Hermes Toolbox, profile distribution package, public install payload). Stay read-only unless the user asks for fixes. Prefer `git cat-file`, `git ls-tree`, `git rev-parse`, `read_file` / `search_files` equivalents on blobs, and non-mutating hash/compare commands.

This file extends `independent-skill-package-review.md`. That file owns live skill + validation-packet re-proof. This file owns **whole staged trees** whose primary artifact is a distribution packet and `config.yaml` / skills payload, not a single skill dir.

## Identity (prove first)

1. Resolve the frozen object: tree SHA or commit^{tree}. Recompute with `git rev-parse <id>^{tree}` (or equivalent) and match the claimed staged-tree ID.
2. Hash the review packet on disk (`review-packet.json` or named equivalent). Match the claimed packet SHA-256 exactly.
3. Inventory the tree: `git ls-tree -r -z --full-tree <tree>`. Compare path count, every path, mode, size, and blob SHA-256 to the packet file list.
4. Fail closed on any path/mode/hash/count mismatch. Do not treat packet summary strings as identity.

## Inventory and scope

Confirm against the stated public boundary:

| Expect | Fail when |
| --- | --- |
| Blob-only payload | Symlinks, submodules, or unexpected modes appear without an explicit allow rule |
| No plugins | Any `plugins/` path exists, or config carries a `plugins` key at any mapping depth (including list-contained mappings) / arbitrary plugin entries |
| No model/provider shipping | `config.yaml` (or siblings) define `model`, `models`, `provider`, `base_url`, `api_key`, singular `fallback`, `fallback_chain`, `fallback_providers`, or `reference_models` at any walked depth |
| Named exclusions gone | Herdr, failed goal plugin, Claude Code-only skills, profile-builder paths, or other named excludes still appear |
| Intended keepers present | Required skills, templates, LICENSE, CI, validators exist as claimed |

Do **not** accept "excluded" as true because a validator script only lists two plugin names. Re-scan the frozen path set yourself.

## Every-blob content scan

Scan **all** staged blobs, not only README/SOUL/config/skills:

- Secrets: PEM blocks, credential-bearing URLs (`user:pass@`), recognizable API token shapes, real emails
- Private host paths: `/Users/<name>/...`, `/home/<name>/...`, and `C:\Users\<name>\...` (or other drive-letter user roots) outside clearly synthetic fixtures
- High-risk defaults in shipped config (see below)
- Upload / share / exfil guidance that lacks redaction or consent steps when it runs by default

A repo privacy helper that only walks a subset of paths does **not** prove whole-tree cleanliness. Call that a logic error even if your independent full-tree scan is clean.

## Public security defaults (config)

Treat shipped `config.yaml` as installer defaults for strangers, not as one user's laptop prefs.

| Setting pattern | Verdict bias |
| --- | --- |
| `approvals.mode: off` with `terminal.backend: local` (or any non-isolated backend) | **BLOCKER** for public defaults. Live Hermes security docs: mode off disables approval checks and is for trusted environments only. Narrow deny globs do not restore a safe default. |
| `memory.write_approval: false` / `skills.write_approval: false` | Not automatic BLOCK alone, but **security_concern** when the package's only mutation protection is SOUL/skill prompt text. Prompt rules are not enforcement. |
| Dangerous-command deny lists only | Record what they cover; do not claim they replace approvals. |

README admissions ("this is powerful/dangerous") do not clear a public-default blocker. Prefer required_fixes: smart/manual approvals, isolation, or explicit high-autonomy opt-in.

## Packet claim verification

Independently verify each material claim. Classification:

| Claim type | Required evidence in scope |
| --- | --- |
| File inventory / hashes | Recomputed tree + per-blob hashes |
| Source-drift (N source files) | Re-hash every live path in the inventory against recorded SHA-256; do not trust `source_drift_note` or "all match" prose |
| Meaning ledger (N clauses) | Ledger contents or content-hash in scope; re-check source/target text membership when ledger claims 100% coverage |
| Tests / Ruff / actionlint / detect-secrets / install probes | Reproducible logs or artifacts bound to this tree+packet, or re-run when mutation is allowed |

### Source-inventory honesty (independent of tree freeze)

A perfect staged-tree match and packet SHA do **not** prove source-drift claims. Common fail:

1. Packet freezes adapted skill copies under `skills/…`.
2. `inventory.json` (or equivalent) maps those copies to **live** source paths under `~/.hermes/skills/…` (or a workspace) and asserts all hashes still match.
3. Live sources move on after freeze; inventory note still says "all N sources match."
4. Mid-review skill/lifecycle patches (including updates to this umbrella) change inventory-mapped live files while the staged tree stays frozen → tree PASS + inventory FAIL on the same packet.

At review time: for every `source_sha256` (or equivalent) entry, hash the live file now. Any missing path or hash mismatch → **BLOCKER** on packet integrity / stale evidence, even when every frozen blob matches the packet and local CI / install probes already passed. Required fix: regenerate inventory from current live sources (or record honest per-path drift), rebuild evidence hashes + remediations + `review-packet.json`, re-freeze if staged content must change, and re-review on the new packet SHA only.

**Final gate before PASS:** re-hash every inventory source path again as the last integrity step, after CI, secret scans, ledger, install probe, and nested-config RED. An early green inventory does not survive a later live edit. Do not write PASS, then "also note" drift.

**Operational freeze:** while a packet is open (create → independent review → verdict), do not patch inventory-mapped live sources unless you immediately regenerate inventory + packet and restart review on the new SHA. Prefer patching the live lifecycle skill only after the distribution packet is closed or deliberately re-baselined.

`distribution.yaml` byte mismatch after install is expected (installer rewrites name/source/installed_at). Assert presence and recorded source, not SHA identity with the staged manifest.

If the packet only prints summary strings (`tests: ok`) without outputs or hashes:

- When the task forbids re-running commands → list under **blockers** or **unverified** (never invent PASS).
- When re-run is allowed → execute against the frozen tree and bind results to tree+packet IDs.

Never mark whole-package PASS while identity, scope, secret scan, source-inventory honesty, or public-default security remains open.

## Validator and test honesty

When the package ships `scripts/validate_distribution.py` (or similar), read it as a claim about enforcement:

1. **Named-only excludes** (only Herdr / one goal plugin) while docs promise "no plugins" → logic_error + required_fix: reject any `plugins/` path and any plugins/model-provider config; add arbitrary-name fixtures.
2. **Privacy scan path allowlist** shorter than the staged set → logic_error; require every staged blob. Require Unix and Windows private-path shapes, emails, PEM/key blocks, assignment forms, and common token prefixes when the package claims whole-repo privacy.
3. **YAML load that maps non-mapping roots to `{}`** → fail-open schema hole; reject non-mapping and malformed config.
4. **Config key walker that only descends mappings** → fail-open for lists of mappings. Require recursion through dicts **and** lists/tuples of dicts. A top-level-only `plugins` check is not enough; reject `plugins` at every mapping depth (including `nested: {plugins: ...}` and `nested: [{plugins: ...}]`).
5. **Incomplete forbidden-key set** → reject the full public boundary, not a subset. At minimum: `model`, `models`, `provider`, `base_url`, `api_key`, singular `fallback`, `fallback_chain`, `fallback_providers`, `reference_models`. When any of those names is forbidden, also reject common YAML spellings after **normalize**: casefold, then map `-` and spaces to `_` (so `api-key`, `api_key`, `API_KEY`, and `base-url` collide). A snake_case-only allowlist fails open on kebab-case config. Missing singular `fallback` while only listing `fallback_chain` / `fallback_providers` is a BLOCKER when the boundary forbids fallback choices.
6. **Tests that only cover named or top-level fixtures** → do not treat as proof of the general boundary. Need negatives for: arbitrary plugin path, top-level and nested `plugins`, list-contained plugin/provider mappings, singular `fallback`, hyphen aliases (`api-key`, `base-url`), unsafe/duplicate manifest paths, and oversized Python constructs.
7. **`distribution_owned` vs live install** → when Hermes copies every repository root entry on profile install/update (prove against installed Hermes version, e.g. 0.18.2 `hermes_cli/profile_distribution.py`), every root name must be deliberately listed, type-safe, path-safe, duplicate-free, and equal to the actual source root set. A short owned list that omits CI, tests, or lockfiles is a BLOCKER if those paths install anyway.
8. **Construct / Markdown size claims** → re-prove with AST or byte counts bound to this tree. Policy text alone is not evidence. For physical line limits, use `text.splitlines()` (or equivalent). Do not use newline-count-plus-one on raw bytes: a trailing newline inflates the count and can false-fail a file at the 200-line edge.

### Frozen-code RED for config gates

Before PASS on a shipping validator, execute the frozen module against synthetic configs (import from an archived tree or `sys.path` insert of the freeze; write each case as `config.yaml` under a disposable temp dir). Minimum cases that must error when the public boundary forbids plugins, providers, fallbacks, or credentials:

- nested mapping plugins
- list-contained plugins
- list-contained provider
- singular fallback
- hyphen aliases `api-key` and `base-url` (after normalize)
- optional deeper nests the package claims to walk (tuples of mappings if the walker accepts tuples)

Empty error lists on those inputs while docs promise no plugins, no provider, no fallback, or no credentials → BLOCKER with `path:line` on the walker and the forbidden set. Do not rely on unit tests alone if those tests never built nested, list-contained, or hyphen-alias cases. After a second-round BLOCK on walker depth, re-run this RED set on the new freeze before claiming the gate is closed.

## Remediation and re-review cycle (main session)

After an independent review returns **BLOCKED**:

1. Fix every `required_fixes` item with tests first where behavior changes. Do not commit or push on a blocked packet.
2. Re-freeze: `git write-tree` (or commit^{tree}). Working tree must match the freeze for the claimed staged set.
3. Re-run local validation bound to that tree: CI entrypoint, secret scans, source inventory, meaning ledger if claimed, disposable `HERMES_HOME` install/update probe under OS temp. Recheck tree identity after probes. Install probe recipe:
   - `git -C <repo> archive <tree> | tar -x -C <tmp/source>` (always pass `-C` / workdir on the repo; archiving from `$HOME` fails before install and is not a package defect).
   - `HERMES_HOME=<tmp/home> hermes profile install <tmp/source> --name <probe> --yes`, then mutate local `config.yaml`, a memory file, and a custom root file; append markers to source `SOUL.md` / `README.md` and overwrite source `config.yaml`; run `hermes profile update`.
   - Assert: every source root entry present on the profile; README/SOUL markers applied; config + memory + custom root preserved; `distribution.yaml` records source; `plugins/` absent on the profile.
   - Prove temp dirs are removed after the trap (or explicit cleanup). Do not leave probe homes under the real Hermes home.
   - Optional secret scan on the archive: call `uvx --from detect-secrets detect-secrets scan --all-files` via the resolved `uv`/`uvx` binary path when `mise` trust would block an extracted `mise.toml`. Empty `results` is evidence; "tool missing" is environment setup, not a package PASS.
4. Rebuild `review-packet.json` from live artifacts. Include at least:
   - `staged_tree`, full path/mode/size/sha256 inventory
   - content hashes of evidence files (inventory, ledger, validation JSON, prior BLOCKED review summaries)
   - `remediations` list (what changed since the blocked review)
   - `review_authorization` (read-only tree, temp-only writes, allowed commands, no repo writes)
   - `required_verdict` shape (PASS/BLOCKED with path:line evidence)
5. Hash the new packet. Dispatch fresh independent reviews against **this** packet SHA and tree only. Attach prior BLOCKED summary paths so reviewers re-check each closed blocker.
6. Prefer two parallel reviewers when both apply: (a) security/privacy/scope/packet integrity, (b) Hermes distribution correctness, install/update, code/Markdown limits, actionlint/tooling pins.
7. On reviewer return: match returned tree + packet SHA to the current freeze. Discard stale packets. Only current-packet PASS unlocks commit/push work.
8. Label local `hermes-verify-*` scripts and `mise run ci` as **focused ad-hoc / local validation**, never remote suite-green. Create verify scripts via `tempfile` + `hermes-verify-` prefix, run, delete.

## Verdict shape

```json
{
  "status": "PASS | BLOCKED",
  "staged_tree": "<tree sha>",
  "packet_sha256": "<hex>",
  "passed_checks": ["..."],
  "blockers": ["..."],
  "security_concerns": ["..."],
  "logic_errors": ["..."],
  "required_fixes": ["..."],
  "suggestions": ["..."]
}
```

- `PASS` only when blockers and integrity-breaking logic errors are empty and every material packet claim is re-proved or explicitly out-of-scope with no silent pass-through.
- Before writing `PASS`, re-hash every live source-inventory path one last time. If any path drifts, status is `BLOCKED` even when tree, packet, CI, and install probes already passed.
- Cite exact paths and line numbers from frozen blobs (`path:line`) in evidence.
- Do not create or modify files during a read-only review; say so in suggestions if the workspace was already dirty.

## Relation to skill-only review

If the frozen tree is only one skill package, still start with identity + every-blob scan, then apply `independent-skill-package-review.md` security-contract and taxonomy rules. If the tree is a multi-skill profile distribution, this file is primary; skill-level deep dives are secondary.
