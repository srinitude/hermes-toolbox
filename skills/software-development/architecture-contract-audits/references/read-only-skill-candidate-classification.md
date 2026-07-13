# Read-only Hermes skill candidate classification

Use this procedure when classifying user-authored/local Hermes skills for public export without modifying source trees, profiles, allowlists, or the publication repository.

## 1. Separate provenance classes before evaluating quality

Inventory all relevant skill trees, then classify each package as:

- **bundled/hub**: byte-identical to an installed first-party or hub source; protected and not a local publication candidate;
- **canonical local**: the default-home package that owns the reusable workflow;
- **profile-only primitive**: a genuinely distinct skill that exists only under a named profile;
- **profile overlay/copy**: a stale, sanitized, or specialized copy of a canonical package; record its path/hash, but do not publish it as a second primitive;
- **locally modified bundled skill**: a derivative customization, not automatically user-authored public content.

Do not infer provenance from `created_by` alone. Compare deterministic tree hashes and exact files against bundled sources. Profile count is not candidate count: deduplicate identical packages and group variant hashes while preserving every exact source path.

## 2. Freeze exact source bytes

For each candidate, record:

- exact source directory;
- frontmatter name, version, author, license, platforms, prerequisites, and related skills;
- canonical tree SHA-256 over sorted `relative_path + NUL + bytes + NUL` entries;
- package file count and symlinks;
- initial and final hash when concurrent skill updates are possible.

Treat an existing candidate report as evidence, not authority. Recompute live hashes and call the report stale when its recorded digest differs.

### Concurrent source drift during an exact staged cleanup review

Keep the staged artifact verdict separate from its external-source evidence gate:

1. Freeze the staged patch digest, full-index digest, sorted index-manifest digest, and staged path/blob map.
2. Recompute every source digest named by the preflight/report at the start and end of review. A staged index can remain byte-stable while protected source packages change concurrently.
3. Alongside each source-tree digest, retain a sorted per-file manifest of `(relative path, mode/type, SHA-256 or symlink target, size)` and the newest file mtime. The aggregate proves drift; the manifest identifies added, deleted, mode-changed, link-target-changed, and content-changed paths without relying on mtime attribution. If the task names only a subset as “protected,” still hash every source whose classification or retained/withdrawn disposition is used by the candidate.
4. If a source changes, report two facts separately: whether the staged artifact remains internally correct, and whether the source-freeze/reclassification acceptance gate still passes. An unchanged withdrawal decision does not repair stale evidence when the authoritative plan requires restart on source drift. Timestamps can prioritize inspection, but never identify the writer or prove causation.
5. Reclassify the changed source in memory when useful. Reproduce the exporter’s inclusion and sanitization rules without writing a staging tree, and emit only compact defect counts or safe diffs. This can show that a withdrawal remains substantively justified while still returning `blocked` for stale freeze evidence. Never let a report’s old defect count certify replacement source bytes.
6. Do not spend time on a full sealing suite after a source-freeze blocker. Prior green results belong to the earlier source snapshot; rerun all sealing gates only after sources and reports are re-frozen.
7. At finalization, recheck the exact producer command for every digest. Record repository/index stability separately from source-tree drift, live remote base, and automation posture. A useful blocked seal still reports the stable candidate digest, exact staged/unstaged/untracked counts, scope equation, manifest/fingerprint equations, paused publisher state, and absence of an active writer—without presenting those passing surfaces as an overall PASS.
8. Treat a user-supplied protected-source digest as an exact acceptance boundary. If the first independently computed canonical digest already differs, the named snapshot was never observed and its prior projection/defect evidence cannot seal the review. Do not silently reclassify the replacement bytes under the old review request. If the replacement then changes again during the audit, report both observed digests and the changed per-file manifest entries, and stop before expensive suites.
9. Do not equate “no matching process in `ps`” with source quiescence. Another Hermes session, editor, service, or short-lived writer can mutate a skill tree without appearing in a narrow process filter. Source quiescence is proved by repeated canonical content hashes (and preferably per-file manifests) across the review interval; process and publisher checks are supporting evidence only.
10. Retain each frozen source tree, its per-file manifest, and its exact sanitized projection until **after** the final live-source rehash and drift comparison. Do not delete the disposable evidence root first: a late aggregate mismatch without the frozen manifest prevents path-level attribution. If final drift occurs, report the frozen snapshot's intrinsic disposition separately, classify the replacement candidate as `hold`, and do not promote a short post-drift double-hash into the plan's full-review quiet window.
11. When running repository-wide validators against a disposable projection, preserve the frozen repository's tracked-file semantics. A content-only directory without Git metadata can make helpers fall back to scanning every file and can produce diagnostics that differ from the real staged repository. Either reconstruct an isolated Git context from the literal base plus frozen index, or explicitly separate candidate-local validator results from fallback whole-tree diagnostics. In particular, an author value that is also a product name can expand identity scans repo-wide; report that collision as a pipeline gate, not as sanitizer-introduced byte corruption.
12. For sanitized-byte review, distinguish literal examples that intentionally demonstrate malformed placeholders from corruption newly introduced by the sanitizer. Require a source-to-projection diff before counting a placeholder witness as introduced semantic damage; unchanged documentation examples are not defects in the projection merely because they match the bad-output pattern.

For exact-index inventory checks, prefer in-memory equations over mutable worktree assumptions: derive the expected changed-path set from approved update surfaces plus every base file under withdrawn roots; verify manifest hashes and source fingerprints against index blobs (`git show :path`); compare tracked defaults, config selections, related-skill metadata, and package roots to the final manifest. When checking final-newline remediation, do not count raw `\\ No newline at end of file` patch markers: deleted prestate files legitimately retain such markers. Inspect the final staged blobs for added/modified retained paths and report unchanged legacy newline defects separately. When an accepted package intentionally diverges from the live export projection because of an approved public-only remediation, require the divergence to reduce to the named changes only, such as one metadata removal or final-newline normalization.

## 3. Run package-local completeness checks in memory

Apply the repository's real skill rules without staging or exporting:

- required frontmatter and size limits;
- minimum usable length and required section headings;
- allowed support directories;
- every extension-bearing `references/`, `templates/`, `scripts/`, or `assets/` token resolves inside the same package;
- no forbidden symlinks, binary/non-UTF-8 content, placeholders, or credential assignments.

A file existing in another skill does not satisfy a package-local reference. Record it as a cross-package dependency separately; a relative support-file token remains dangling.

### Verify executable documentation as behavior

For every newly added or materially changed command example, run the **exact documented token sequence** in a disposable, no-network home when safe. Help-text membership proves only that flags exist; it does not prove the example produces the claimed artifact. Validate semantic output as well as exit status because some CLIs print a usage or “not found” diagnostic and still return zero. Pair a failing documented shape with one corrected, minimally complete form, and cite both outputs.

Cross-check scheduler, daemon, heartbeat, retry, and timing claims against the current implementation or authoritative release docs. Do not preserve an older “wait one tick” explanation when the current scheduler records liveness before its first sleep; specify a bounded observable freshness condition instead of an implementation-age guess.

Compare frontmatter version metadata with the exact available preimage. A material workflow, safety, or runtime-contract change should carry the intended patch-version advance, or the review must record a concrete unreleased-version rationale; do not silently treat a content hash change as truthful version metadata.

## 4. Audit dependency closure, not only local references

Distinguish:

- package-local support files;
- bundled runtime skills/tools expected in every compatible Hermes install;
- public toolbox sibling skills;
- exact-version or marker dependencies;
- external services, credentials, CLIs, network access, paid operations, and fresh-session discovery requirements.

Read the body for mandatory `skill_view`, exact marker, copy/bootstrap, tool, and provider requirements. `metadata.hermes.related_skills` is advisory unless the body makes it mandatory. If candidate A requires content found only in a newer rejected candidate B, A passes local reference checks but is not standalone in the public bundle.

## 5. Simulate sanitization and review semantic output

Run deterministic sanitization in memory on every included text file, then validate both safety and meaning. Reproduce the **complete policy context**, not only the sanitizer function: frozen tracked base, private-prefix and public-source-profile arguments, approved-authorship input, identity/private deny terms from environment or local policy, and inclusion rules. A projection made without the active deny terms can appear valid while the real exporter rewrites an absolute interpreter command to `<private-term>/.hermes/...` before later `$HERMES_HOME` normalization can recognize it. For every candidate that passes staging, require the independently simulated projection tree hash to equal the actual disposable-export destination tree hash.

When the production exporter short-circuits on its first staging error and rolls the destination back, do not mistake that first diagnostic for the complete blocker set. Preserve the frozen source, materialize the exact included/sanitized bytes in a disposable location through the production staging helper—not a hand-reimplemented sanitizer—hash that projection, and run the remaining candidate-local and reconstructed-Git-context validators against it. Label this as an exact staging projection, not a successful export. This secondary lane is especially important for independent final-newline defects and repository-wide policy collisions that the exporter never reached.

Record:

- changed-line count and representative before/after lines;
- remaining identities, private profile/plugin names, emails, home paths, runtime paths, and secret-like assignments;
- malformed placeholders or commands introduced by replacement order;
- product names accidentally rewritten because an author name overlaps a product name;
- session-specific `/tmp`, cache, runtime, corpus, or profile paths that automated identity checks may miss.

Passing secret/identity regexes is insufficient. An output can be privacy-safe but unusable when a command becomes `<private-term>/...` or a product name becomes `<repo-author-name>`. Treat semantic corruption as a publication blocker or explicit human hold.

## 6. Assign one primary status

Use these fail-closed states:

- **accepted**: explicitly approved/allowlisted, complete, safe after sanitization, dependency-closed for the declared runtime, and semantically usable;
- **approval-required**: deterministic package gates pass, but selection/provenance approval or a human-reviewed dependency/sanitization decision is still outstanding;
- **rejected**: any objective completeness, privacy, provenance, portability, or semantic-output failure exists;
- **unchanged-last-known-good**: only for an older public package that independently passes the current full gates while the latest source is rejected.

Do not use `approval-required` to hide a deterministic failure. Approval cannot make a dangling reference, private session corpus, or broken exported command valid unchanged.

## 7. Audit withdrawals as repository-wide contract changes

When a public primitive is withdrawn, do not stop after deleting its package root and manifest row. Search the complete tracked candidate—including files unchanged by the cleanup—for every exact package name and path. Classify each hit rather than deleting blindly:

- **public selection/runtime dependency**: installer examples, config examples, exporter defaults, allowlists, manifests, `skill_view` instructions, or required peer-skill prose; these must be removed, guarded with a real missing-dependency fallback, or proven bundled at the pinned compatible runtime;
- **advisory/history/negative test**: explanatory prose or a test that deliberately asserts the withdrawn name is rejected; retain only when its purpose is explicit and it does not advertise availability;
- **unrelated substring/product concept**: do not treat a product feature or suffixed fixture name as the withdrawn package without semantic inspection.

Inspect non-Markdown surfaces explicitly. Documentation-contract tests often scan only `*.md` and can miss stale YAML examples, shell defaults, Python fallback lists, and generated inventories. For exporter policy, compare four sets: final manifest names, clean-clone defaults, local untracked allowlists, and package roots actually present. A local `.git/info` allowlist can mask a broken clean-clone fallback. Parse the tracked fallback without importing or executing the exporter, and report both set differences (`fallback - manifest` and `manifest - fallback`); a locally matching allowlist does not repair either difference.

Audit public configuration examples as executable documentation, including YAML, TOML, and JSON files that enable or select skills. Compare every concrete enabled package against the final manifest. Check what the repository's documentation tests actually enumerate: a green Markdown-only contract test does not cover stale `examples/*.yaml` selections. Distinguish two conclusions in the report: the changed-path scope equation may pass with zero unauthorized edits while the candidate still blocks because required withdrawal surfaces were left unchanged.

Audit withdrawal and installer-isolation tests semantically. A test such as “install retained package A alone, then assert withdrawn package B is absent” becomes vacuous once B is absent from the manifest and candidate tree; it cannot catch accidental installation of another retained package. Require the negative comparator to be a different retained manifest member, or compare the complete installed set exactly with the requested selection. When a concurrent actor repairs such a test and updates its fingerprint during an exact-index audit, preserve the original tree and patch digest as the requested candidate, classify the newly staged index as a replacement candidate, and do not use a mixed-state green suite to seal either one.

Treat dependency closure semantically. Restating another skill's procedure does not make a package standalone if it still instructs the agent to load the absent peer. Require either a guarded “if the skill exists” path with usable fallback behavior, proof that the exact dependency is bundled in the pinned compatible runtime, or inclusion in the same public manifest.

Finally, include untracked files under retained package roots in the reviewed candidate. If manifests, fingerprints, or `SKILL.md` references name those files, record them as a staging gate: the exact staged path set must contain them before commit, or the committed package will be internally inconsistent.

## 8. Report canonical candidates and overlays separately

The main matrix should list every distinct primitive with exact source path, version, tree hash, missing references/dependencies, runtime requirements, safety concerns, and reasoned status. Put profile copies/overlays in a separate deduplication ledger grouped by relative skill name and hash, with every exact profile path preserved.

Also report:

- publication repository HEAD/status;
- allowlist membership and current public package/LKG version;
- stale report/hash mismatches;
- which validators were run and what they do not prove;
- handlers, installers, model calls, and writes explicitly not performed;
- incidental tool-managed temporary/log artifacts separately from source/config/repository modifications.

For a strict no-runtime-write classification lane, inventory tool side effects before choosing evidence collectors. `web_extract` may persist a page in the Hermes web cache, and `skill_view` may update skill-usage metadata even though both are logically read-only. Prefer already-frozen local docs, non-persisting browser snapshots, or static CLI help when they satisfy the contract. If a mandatory skill load or materially necessary docs fetch writes tool-managed metadata/cache, do not hide it or claim “no side effects”: identify the exact path as created/refreshed, keep it separate from candidate/repository/source mutations, and do not remove it unless that runtime path is explicitly in cleanup scope.

Recompute candidate hashes at the end. If bytes changed, classify the final bytes or label the earlier result as a superseded snapshot.
