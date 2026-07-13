# Standalone Public Primitive Publication

Use this reference when a user asks to publish every public-safe Hermes primitive that can operate independently of private state.

## Define the candidate universe before scanning

Inventory intentional custom surfaces, not every file under `$HERMES_HOME`:

1. local custom skills from `hermes skills list --source local`; exclude bundled and Hub-installed skills;
2. plugins only from the configured public-plugin-source profile;
3. non-private profile candidates, excluding `default`, the plugin-source profile, and private-prefix profiles;
4. explicitly supported reusable personalities or other tracked primitive classes.

Record exact counts and names privately. Also reconcile provenance across the installed tree: byte-identical bundled/Hub skills are exclusions, a locally modified bundled skill is derived rather than automatically public, and profile-only skill families or noncanonical overlays require explicit private/phase-specific/standalone dispositions. Do not infer a separate primitive from every installed copy. A broad “publish all possible” request authorizes publication of passing candidates, not a filesystem sweep, source remediation, or publication of rejected names.

## Define “standalone” operationally

A candidate is standalone only when:

- it contains no dependency on private profile data, runtime state, credentials, personal paths, or untracked local files;
- all package-local references resolve inside the package;
- every hard peer-skill dependency is bundled by the pinned Hermes release or present as a valid public package in the same final manifest;
- plugin declarations match real `PluginManager` registration in a disposable Hermes home;
- profile distributions install through real `hermes profile install` and include all required `distribution_owned` paths;
- any required command, environment variable, or external service is explicitly declared and missing prerequisites fail clearly;
- an install into a clean Hermes home proves discovery and expected activation behavior.

Do not equate valid frontmatter, a clean copy, or a passing static scan with standalone operation.

## Reuse cryptographically unchanged decisions

A prior accepted/rejected decision may be carried forward only when all of these are unchanged:

- candidate source digest, using a stable generated/runtime exclusion policy;
- exporter, policy, validator, and real-runtime probe digests;
- pinned Hermes runtime/release;
- the objective contract that produced the prior decision.

Otherwise re-run the candidate. A stale report's automation state is never authoritative; live cron/process state wins.

## Audit the public bytes, not only the source package

A static source/export pass is necessary but not sufficient. Deterministic sanitizers can preserve secrecy while corrupting behavior—for example, rewriting an executable interpreter path to an invalid placeholder, replacing ordinary product names because an author field matches them, leaving doubled placeholders, or hiding a cross-package marker/version mismatch.

Before retaining or updating any public package, run a focused semantic verifier against the exact staged/tracked public bytes. Check at least:

- command examples remain executable and contain no invalid identity/private-term placeholders;
- ordinary product/CLI names retain their meaning after author and identity sanitization;
- package-local references resolve and disallowed user-home/runtime paths are absent;
- hard peer-skill versions, files, and marker contracts exist in the final public dependency closure;
- the already-public package is judged separately from a newer failing source.

When the repository's validators do not encode these semantics, create a temporary test-first verifier, witness RED on known defects, and require GREEN on the final candidate. Do not call a candidate standalone merely because the exporter and current CI are green.

### Build semantic sanitizers from explicit grammars

Treat sanitizer output as a security-sensitive language transformation, not a sequence of broad string substitutions.

- Scope metadata identities separately from product prose. An author value that is also a product or organization name must not rewrite ordinary product text. If the final safety validator derives identity terms from author metadata, use an explicit normalized non-person-author set and default unknown multiword authors to identity-protected; lexical suffix/word heuristics such as `team`, `labs`, or `software` are bypassable and produce false positives.
- Replace configured profile/source identifiers only at token boundaries and before any overlapping private-prefix rewrite. Test exact tokens, embedded larger identifiers, and prefixes that occur inside public names; ambiguous embedded forms should remain unchanged for the denylist/final validator rather than becoming partially sanitized garbage.
- Validate placeholders using an explicit set of public placeholder tokens and balanced delimiter grammar. Reject doubled, asymmetric, unclosed, empty, and case-mutated forms of known tokens, but do not treat arbitrary angle-bracket text as a placeholder: valid HTML, C++ templates, and comparison prose must remain usable.
- Restrict placeholder-bearing executable-path detection to approved placeholder roots plus `$HOME`, `$HERMES_HOME`, and braced equivalents. Cover quoted path segments and run the check at the real package-staging boundary before last-known-good replacement.
- Exercise every semantic rule twice: a focused pure projection/grammar test and a real exporter transaction test. The latter must prove final public-safety/identity validators, rollback bytes, and staging-residue behavior; add the equivalent profile-export boundary when profiles share the gate.
- Treat each review-driven correction as a new staged-diff generation. Witness the specific reviewer repro RED, obtain focused and full GREEN, reseal the digest, and rerun both specification and security reviews. One favorable reviewer does not override the other reviewer’s blocker.

## Last-known-good and withdrawal behavior

Keep source state and public-package state separate. Use explicit statuses:

- `accepted-current`: current source and staged public bytes pass every current static, semantic, dependency, and real-runtime gate;
- `retained-last-known-good`: newer source fails, but the exact existing public bytes still pass every current gate;
- `hold`: static source/export checks pass but semantic, dependency, provenance, or public-byte proof is unresolved;
- `rejected`: source fails a hard gate and has no public package eligible for retention;
- `withdraw`: exact existing public bytes fail current hardened semantic/standalone gates.

A source-level failure alone never justifies deleting a valid LKG package. Conversely, an already-public package that contains sanitizer corruption or broken dependency closure must not be retained merely because its source is unchanged or current repository validators still pass.

If the exporter lacks first-class withdrawal support, perform only an exact reviewed package-root deletion on the publication branch, include it in the authoritative staging/rollback list, and regenerate manifest and fingerprint inventories after accepted exports and withdrawals are final. Never silently retain stale invalid packages.

## Focused newest-version upload requests

When the user asks to upload the newest version of one named primitive, do not treat the narrow request as implicit permission to repair its source. First pin the live source version/tree digest, currently published version/digest, package-local reference closure, sanitizer result, and downstream publisher state.

If upload is blocked by one repairable source defect, present bounded choices before writing: approve the exact minimal source remediation and semantic version bump, keep the current public LKG, or update the saved plan only. A plan-only choice supersedes earlier blanket publication language for the current turn: modify only the existing plan path, record the exact future approval packet and rollback preimage, and perform no source edit, branch, export, commit, PR, or upload.

Prefer a one-line cross-skill wording correction over duplicating another skill's support file when the candidate merely refers readers to that peer skill. If a later user request explicitly authorizes the library repair, bump the patch version, preserve only the exact intended hunk, and rerun package-local reference validation before treating the candidate as newest/publishable.

## Disposable reclassification pattern

For changed candidates, export from a fresh archive of the frozen repository revision into a disposable root. Select exactly one candidate class. For plugin/profile cases, also select one **semantically accepted** baseline skill so default skill fallback cannot introduce an unrelated failing source. A baseline that passes static staging but contains corrupted public commands or unresolved dependency closure is not acceptable.

Use the real transactional exporter and capture exit status plus concise reasons. The exporter path must cross real plugin/profile runtime probes. Remove each disposable root after evidence is sealed.

## Close the complete withdrawal blast radius

Package-root deletion and manifest regeneration are not sufficient. Before sealing a withdrawal, inspect every tracked operational surface, including non-Markdown examples and test constants:

- tracked clean-clone/default candidate lists must equal the final manifest rather than relying on `.git/info` overrides;
- public YAML/config examples must use the current Hermes schema and must not select withdrawn packages;
- `metadata.hermes.related_skills` is discovery metadata and must not advertise withdrawn toolbox packages, even when ordinary prose may still discuss an optional external/custom workflow;
- installer-selection tests must use another retained manifest package as the unselected sentinel; a deleted package makes the assertion vacuous;
- every new or changed support file must have normal final-newline hygiene before inventories are regenerated;
- regenerate fingerprints after the last code, test, example, metadata, or newline edit—not merely after package-tree edits.

Add focused contract coverage for tracked defaults, public config schema/selections, withdrawn discovery metadata, and any sentinel whose existence gives a negative assertion meaning. Distinguish contextual ecosystem prose from actual install, discovery, `skill_view`, mandatory-load, or runtime dependencies rather than deleting neutral terminology mechanically.

## Seal one exact generation at a time

Identify each candidate generation by the SHA-256 of `git diff --cached --binary` plus its exact staged path set. A late review fix, added reference, metadata correction, test-oracle strengthening, or newline normalization creates a new generation and invalidates every earlier review, hash, and sealing claim. Fully stage the corrected candidate, prove zero unstaged/untracked paths, rerun affected inventory and validation gates, then dispatch reviewers with the literal new digest.

Reviewers should hash the candidate and protected sources at both the start and end. If a live source changes during review, treat the review as stale even when the staged diff is unchanged. Re-freeze and reclassify only the affected source in a fresh disposable export, record the new digest and current defect evidence, and rerun exact-candidate sealing. Do not keep stacking new reviews on a moving index or moving source snapshot; finish all parent-owned corrections and source reclassification first, then dispatch one final review generation.

For withdrawn sources, current drift does not silently change the public disposition: prove again that the fresh sanitized projection still fails the exact semantic contract. If the source keeps changing faster than one review can complete, stop before commit and report the source-freeze blocker rather than weakening the saved plan's freeze gate. After repeated in-review drift, require a bounded quiescence window or explicit confirmation that the external writer has stopped before spending another full review cycle; do not reclassify and redispatch indefinitely. Writer-stop confirmation is not proof that already-started writes have drained: anchor the quiet interval to the newest protected-file mtime observed after confirmation, then re-freeze only after that interval elapses without another hash or mtime change.

Treat a parallel review batch as one fail-closed unit. If reviewers disagree about the protected source hash or whether it stayed stable, the batch is BLOCK even when one reviewer reports PASS. The parent must recompute the canonical tree hash directly, inspect the newest changed path and mtime, and reconcile both reports against that live evidence; never choose the favorable verdict or average conflicting observations. Reclassify the new source and rerun the whole independent batch so every final reviewer names the same source digest at both boundaries.

A delivered review PASS seals only the exact interval and source snapshot it observed. Recheck every protected source immediately after commit and again before push. If a source drifts after review or commit, keep the commit local and unpushed, reclassify only the affected source from a fresh disposable export, rerun the post-commit validation affected by the freeze gate, and obtain a fresh independent review against the unchanged commit plus the new source digest. Do not amend or recreate an unchanged public commit merely to encode untracked drift evidence; update the local plan/report evidence instead. Push or open a PR only after the post-commit/pre-push source check matches the reviewed snapshot.

## Verification command hygiene

Keep verification failures about the artifact rather than the shell harness:

- After any delegated audit, disposable `HERMES_HOME`, or shell-based classification lane, explicitly preflight `HOME`, `HERMES_HOME`, `PATH`, `Path.home()`, and the real Hermes runtime path before running repository tests. Persistent shell snapshots can outlive a disposable home and make otherwise-valid real-runtime tests resolve a deleted virtualenv. Run authoritative suites with an explicit known-good `HOME`; if the environment was stale, discard the entire affected run as harness-invalid, restore only the environment, and rerun the complete required proof. Do not patch tests or runtime code to accommodate the contaminated shell.
- For tracker-facing ad-hoc proof, allocate the verifier with `tempfile` or `mktemp` under `/tmp/hermes-verify-*`, make it invoke the exact focused behavior tests and structural checker, report it explicitly as ad-hoc rather than suite green, and remove it afterward. A prior full-suite PASS remains separate evidence; do not expect a later generic semantic probe to satisfy a command-shape-sensitive code verifier.
- Run at most one equivalent tracker-facing verifier per sealed digest. If the tracker repeats stale output or continues listing an already removed verifier after an exact successful run, preserve the command, zero exit, digest, and cleanup proof, then stop retrying. A stale tracker does not invalidate real evidence, and repeated equivalent temporary scripts create noise without improving the candidate.
- Do not pipe a verbose producer such as `hermes skills list` directly into `grep -q` under `set -o pipefail`; an early grep match can close the pipe, give the producer `SIGPIPE`, and turn a valid result into a false failure. Capture the complete output first, then inspect the captured text with Python or a non-early-exit check.
- Read the actual manifest schema before writing ad-hoc assertions. In the toolbox manifest, skill rows are path/hash records, not guaranteed `name` records; derive the public skill identifier from the canonical path or use the repository helper that owns the schema.
- When a verifier fails after earlier gates passed, isolate the first failing command and inspect its real output before rerunning the complete packet. Correct the harness and rerun the affected proof; do not reinterpret a partial run as artifact failure or success.
- Keep ignored workspace plan files and local `.git/info` evidence outside the staged public candidate. If an exact-path staging helper rejects an ignored plan, first verify whether the plan is intentionally untracked; do not force-add it merely to make the helper pass. Candidate identity is the tracked staged diff, while the saved plan remains the operative local scope document.

## Bounded private-evidence transport

Preflight and candidate ledgers can easily exceed tool stdout caps when they embed every profile-owned path, plugin declaration, or source hash. Do not make a large JSON stdout stream the only copy and then attempt to parse it after the tool may have truncated or spooled it.

- Write the complete private evidence through an approved top-level file tool under `.git/info/` or an allowlisted `/tmp` path, then read it back with pagination when needed.
- Keep command stdout to a bounded summary: schema version, candidate counts, evidence path, top-level digests, and validation result.
- For large deterministic path sets, store the full list in the private ledger while reporting only count plus a digest in summaries. Never discard the actual list when withdrawal scope or provenance needs later reconstruction.
- Validate the live manifest schema before mapping package hashes. Skill rows may identify `SKILL.md` with `sha256`, while personality rows can carry separate manifest/config hashes; do not assume one generic `content_sha256` field across primitive classes.
- If a JSON parse fails near an output-size boundary, diagnose truncation first. Narrow the emitted summary or read the saved evidence directly instead of retrying the same oversized command.

## Publication sequence

1. Freeze local/remote main, active writers, publisher state, candidate sources, and pipeline digests.
2. Create a unique branch from literal remote main; do not reuse stale worktrees.
3. Classify every candidate, reconcile provenance exclusions, and prove dependency closure.
4. Update only untracked explicit allowlists with `accepted-current` sources.
5. Run one transactional export and map every changed path to an accepted candidate.
6. Run the focused semantic verifier against exact staged/tracked public bytes; independently assign every existing held package `retained-last-known-good` or `withdraw`.
7. Apply only proven withdrawals, include deletions in the exact change list, and regenerate inventories.
8. Run the identical export/inventory sequence again; require an empty second change list and stable diff digest.
9. Run public-safety, identity-neutrality, completeness, structure, full tests, semantic verification, and clean-home install/discovery.
10. Obtain separate spec-compliance and security/package-quality reviews; reproduce material findings.
11. Stage exact accepted/withdrawn change-list paths plus inventory—never repository-wide `git add`.
12. Commit once, push a branch, open a PR, require exact-head CI, merge, and verify from a fresh remote clone.
13. Keep the automatic publisher paused unless the user separately approves a hardening-and-resume plan.

## Drift and rollback

Hash selected source trees before classification, before export, after idempotence, and before commit. Any unexplained drift invalidates classification for affected candidates.

Before merge, abandon the branch or restore only accepted/withdrawn destinations to the frozen base. After merge, use a normal revert PR; never rewrite public history.

## Completion evidence

Report actual candidate counts by kind/status, published public artifact names, changed paths, source/pipeline/diff hashes with producer commands, local and remote test results, clean-home install results, PR/CI/merge URLs and SHAs, protected-boundary integrity, and publisher-paused state. Do not report success until fresh-clone verification of merged remote main passes.
