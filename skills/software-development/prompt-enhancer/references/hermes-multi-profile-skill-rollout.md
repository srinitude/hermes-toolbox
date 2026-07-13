# Multi-Profile Hermes Skill Rollouts

Use this procedure when one skill contract must be introduced or reconciled across every live Hermes profile while preserving profile-local customization.

## Scope and authority

- Require explicit approval to write another profile's `skills/` tree.
- Treat the live profile inventory as authoritative; do not rely on a remembered profile list.
- Separate four decisions: patch existing profile copies, seed missing copies, change consumer enablement, and publish/export. Approval for one does not imply the others.
- Do not modify Hermes source checkouts, internal bundled/hub state, profile config, secrets, plugins, memories, cron definitions, or runtime stores unless separately in scope.

## Safety preflight

1. Read the approved plan or operative prompt as the exact scope.
2. Inventory profiles and resolve each profile home with live Hermes CLI output.
3. Classify each target skill as present, missing, protected/read-only, or profile-customized.
4. Inspect active TUI/gateway processes, cron jobs, filesystem watchers, export scripts, and downstream repositories.
5. Capture downstream repository HEAD and a hash of its complete porcelain status. A dirty baseline is acceptable; success means it remains byte-for-byte unchanged, not that it becomes clean.
6. Pause only automation that could observe a half-applied rollout. Record each job's prior state and resolve job IDs from a fresh list rather than guessing.
7. Create a targeted rollback archive containing only existing in-scope skill trees and a SHA-256 manifest.
8. Validate that the archive is non-empty and contains only approved paths.

### Archive pitfall

Do not use a blanket tar exclusion such as `*/.*` when the path itself contains `.hermes`; it can silently exclude every member. Validate member count and allowed prefixes immediately after archive creation, then verify the archive checksum independently.

## BOOTSTRAP and RED

Before changing any target skill, create a real filesystem verifier under `/tmp/hermes-verify-*` that:

- discovers profiles dynamically from the supplied Hermes root;
- supports profile/kind filters for vertical checks;
- validates frontmatter, declared skill name, non-empty body, character limits, marker counts, required phrases, and local references;
- compares marker-delimited contract blocks byte-for-byte across profile copies;
- skips builders or companion skills that are intentionally not installed;
- accepts a temporary root override so negative controls never touch live profiles.

Run it against the real profile trees and witness RED for the expected missing behavior. If RED contains unrelated failures, fix the verifier before production changes. In particular, validate only references declared as local by the skill's References section; an incidental cross-skill `references/...` mention must not be misclassified as a missing local file.

Keep verifier and migration scripts within the active coding contract: maximum file/construct size, shallow nesting, no test doubles, and real filesystem/CLI behavior.

## Rollout strategy

### Canonical copy

1. Select the approved canonical profile copy.
2. Add one uniquely named start/end marker pair around the shared contract.
3. Integrate the contract into the skill's actual intake, spec/template, execution, and verification surfaces; a detached policy paragraph alone is insufficient.
4. Run the targeted verifier and obtain GREEN for the canonical copy.

### Existing customized copies

- Extract the canonical marker block and insert it into each existing profile copy using a unique semantic heading as the anchor.
- Treat tool-rendered file content as a presentation, not automatically as source bytes: line-number prefixes or truncation markers must never be copied into a target. Obtain the block from a raw deterministic source path or the approved plan literal, hash it, and compare the inserted bytes with the canonical hash immediately.
- Patch in place; never replace the entire file merely because hashes differ.
- Support known structural variants with explicit fallback anchors. An absent preferred heading is a compatibility case, not permission for a broad rewrite.
- Apply one profile at a time and run targeted GREEN before continuing. The focused verifier must compare the full marker block byte-for-byte, not only search for required phrases, so decorated or partially corrupted insertions fail immediately.
- After each insertion family, remove only the approved marker block and its exact separator in a temporary comparison and prove the remaining bytes equal the baseline. This catches extra blank lines and other anchor-adjacent drift that an ordered-subsequence check can miss.
- Use an atomic temporary replacement only if the temporary file is removed immediately and the final scope scan proves no residue.

### Missing copies

- Seed a real profile-local directory rather than a symlink.
- Copy only `SKILL.md` and existing allowlisted support directories: `references/`, `templates/`, `scripts/`, and `assets/`.
- Reject hidden files, symlinks, secrets, plugins, caches, logs, sessions, databases, and runtime state.
- Compare source and target relative-path/SHA-256 manifests before CLI validation.

## Semantic source audit before sealing

Byte-identical propagation proves that every profile received the same contract; it does not prove the contract is true. Before calling a rollout complete:

1. Pin the installed Hermes source/release and trace each externally observable semantic claim to the concrete handler, manager, response shape, approval path, and current first-party documentation. Pay special attention to names such as “search,” “read-back,” “delete,” “sync,” and “self-heal,” which may describe policy or docstrings rather than actual backend behavior.
2. Run an independent read-only semantic audit in parallel with implementation, but do not seal the report, remove the focused verifier, or tell the user completion is final until the audit returns and is reconciled against the current target bytes.
3. Keep structural and semantic evidence separate. Marker counts, required phrases, discovery, and exact plan-block identity can all pass while a plan-authored claim is materially false.
4. If the audit disproves a propagated claim after an initial GREEN, explicitly supersede the premature completion claim. Write a focused regression against the live fleet and witness RED; correct the canonical marker block; replace only the exact old marker block in each profile with compare-before-write behavior; then rerun fleet identity, fresh local/enabled-only discovery, disposable future-profile bootstrap, protected-boundary checks, and report hashing.
5. Preserve concurrent target/support drift rather than restoring the baseline. For a newly seeded canonical clone, re-synchronize only a changed allowlisted canonical support file needed to keep the seed manifest current. Do not force that support file across pre-existing customized profiles.
6. Amend the evidence report with the failed claim, pinned source lines, corrected wording/hash, RED→GREEN proof, any concurrent drift, and a refreshed final report digest.

Completion is valid only when both structural propagation and current-source semantic audits pass, or when an unresolved semantic blocker is stated plainly.

## Validation threshold

Require all of the following:

1. Full verifier passes with counts matching the fresh profile inventory.
2. Fresh `hermes -p <profile> skills list --source local` discovers every expected skill.
3. `--enabled-only` also discovers it, or the exact profile filter is reported as a blocker rather than edited silently.
4. Marker blocks are present exactly once and byte-identical where intended.
5. Existing profile-local support files remain unchanged; only planned guidance is removed or replaced.
6. Newly seeded trees match the canonical allowlisted manifest.
7. Downstream repository HEAD and full porcelain-status hash match the preflight baseline.
8. Public publishers remain in their approved state.
9. Previously active reversible automation is restored only after validation.
10. Temporary rollout/verifier files are removed when no longer needed.

## Adversarial controls

Run against temporary real copies, not mocks:

- remove one required phrase and prove failure;
- duplicate a marker and prove failure;
- delete one declared local reference and prove failure;
- add a temporary profile and prove dynamic discovery includes it.

Re-run the live verifier after negative controls to prove temporary mutations did not leak.

## Concurrent drift

Another session or watcher may change an in-scope or adjacent human-authored directory after rollback capture.

- Do not restore or overwrite the drift automatically.
- Compare archive/current hashes, mtimes, and focused diffs.
- Scan adjacent human-authored skill/config/plugin surfaces for mtimes at or after rollout start, not only the approved targets. An out-of-scope change is protected drift even when all target files remain GREEN.
- If a drifted path changes again while the final report is being sealed, record the observation sequence, re-hash it, and perform a short bounded stability check. Do not keep chasing or absorb the other writer's work into this rollout.
- Distinguish intentional rollout writes from independently timestamped drift in the final scope report.
- Preserve concurrent human-authored work by using targeted insertions.
- For profile-specific copies, verify old lines remain a subsequence of the new file except for explicitly approved replacements; also use exact baseline reconstruction after removing the shared block to catch whitespace-only rollout residue.
- Keep any publication/export automation paused until the drift is classified and the user separately approves publication.

Concurrent drift is not proof that the rollout failed, but it must be disclosed and excluded from claims about the agent's own writes. Compute report/artifact hashes only after the last report edit; if the report changes, refresh the delivered hash rather than citing stale evidence.

## Runtime activation

Skill-file validation proves disk and fresh-process behavior only. Existing sessions may retain previously loaded skill text. Report that users need `/reload-skills` followed by `/reset`, or a fresh process. Treat gateway/TUI restarts as a separate approval.

## Final report

Report coverage counts, witnessed RED, final PASS output, fresh CLI discovery, enabled-only status, negative controls, write-scope evidence, rollback paths/checksum, automation restoration, downstream immutability, concurrent drift, temporary cleanup, and the cached-session activation boundary.
