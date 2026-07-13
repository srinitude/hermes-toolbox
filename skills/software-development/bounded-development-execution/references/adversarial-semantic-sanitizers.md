# Adversarial Semantic Sanitizer Checkpoints

Use this when a public-export sanitizer must preserve valid source-language constructs while rejecting privacy leaks and executable placeholders at a transactional staging boundary.

## Model the Languages; Do Not Accumulate Regex Exceptions

- Parse YAML with `yaml.compose()` when field identity, source location, aliases, tags, anchors, block scalars, or merge keys affect policy.
- Treat YAML as a graph. Distinguish a shared DAG node from a cycle by tracking the **active recursion path**, removing a node on return. A global visited set falsely classifies repeated aliases as cycles.
- Traverse mappings and sequences. Reject `author` keys outside the one permitted top-level metadata location, including nested and flow mappings.
- Reject aliases where an author scalar's source mark points outside its field; otherwise identity bytes in the anchor declaration can be accidentally exempted.
- For source-mark replacement, preserve scalar decorations: anchors/tags, quote style, and block-scalar header/indentation. Reparse the projected YAML before accepting it.
- Residual private identifiers outside the replaced scalar—especially comments—must fail the staging semantic gate, not merely a later repository-wide validator.

## Shell Paths Require Word-Local Symbolic Projection

- Analyze shell words, not whole lines, so unrelated `$HOME` and command substitutions do not combine into a false path.
- Normalize escaped newlines before tokenization.
- Project both unset and dynamic outcomes for parameter expansion and balanced nested command substitutions.
- Compose literal `printf` fragments; separate substitutions can form one placeholder root.
- Avoid finite variant enumeration with silent caps. It creates both fail-open truncation and harmless-input false positives.
- Mask URL spans before shell-path analysis so Markdown links, autolinks, and HTML URL attributes are not interpreted as executable paths.
- Require an exact executable segment (`python`, versioned Python, `node`, `bash`, `sh`, `hermes`), preserving near misses such as `python-config` and `python.`.

## Placeholder vs Markup Compatibility

- Candidate matching must require exact known-token boundaries; prefix-related custom elements remain markup.
- Find HTML tag terminators quote-aware. The first `>` may occur inside an attribute value.
- Validate attribute syntax; unmatched quotes must not fall through an unquoted-value branch.
- Preserve multiline/boolean attributes, self-closing tags, URLs, and C++ pointer/reference/template arguments. C++ compatibility probes must include both spaced and compact array references (`path const(&)[3]`, `path(&)[3]`, and rvalue forms) plus expression contexts such as `return x<path ? 1 : 0;`; whitespace-only template heuristics miss valid compact syntax.
- Reject doubled/nested openings and damaged known tokens in prose. Keep contextual guards so comparisons and quoted example scalars remain valid.

## Identity Matching

- Match configured identities case-insensitively and with normalized internal whitespace (`Li Wei` must match `LI   WEI`).
- Exempt only the YAML scalar source span, not the complete line; comments remain subject to privacy checks.
- Universal checks such as private email/path detection still apply inside otherwise permitted author metadata.

## Transaction and Review Loop

1. Add minimal real-export RED probes, not helper-only tests.
2. Require rejected candidates to preserve the last-known-good destination and leave no staging/backup residue.
3. Run focused GREEN, canonical suite, public-safety/identity validators, parser-based structure checks, compilation, diff checks, and added-line scans.
4. Stage an explicit path list and seal `git diff --cached --binary` with SHA-256.
5. Freeze both index and worktree during independent specification and security/quality reviews.
6. A review-failed digest is retired. Fix through a new RED→GREEN generation and reseal.
7. Do not rerun an identical temporary verifier merely because an external tracker still lists its already removed path; distinguish stale tracker state from current concrete evidence.

## Credential Semantics Need Parsed Values and Targets

Credential policy must classify the decoded semantic key and the complete value—not a convenient substring or one serialization form.

- Structured YAML/JSON/TOML checks and raw assignment checks must agree. Cover quoted, triple-quoted, block-scalar, escaped-key, and fenced payload forms.
- Placeholder approval is an exact grammar. Accept simple environment references and approved whole-value markers; reject shell expansions that embed literal defaults and realistic values that merely contain words like `sample`, `example`, or `placeholder`.
- Python requires AST target coverage: names, attributes, subscripts, destructuring, annotated/augmented assignments, dictionary keys, keyword arguments, and `setattr` calls.
- Resolve only statically knowable string or byte-string expressions, including literal f-strings, literal concatenation, and `bytes` constants decoded conservatively for classification. Dynamic runtime construction is code, not embedded credential material. If parseable Python is excluded from raw fallback scanning, a static `b"..."` assignment must still be classified through AST evaluation.
- If raw Python scanning is disabled to prevent policy-source false positives, AST coverage must replace every assignment form the raw scanner previously caught.
- Add adversarial cases through the real exporter and canonical validator; helper-level classification alone does not prove pre-mutation rejection.

## Real Runtime Probes Must Enforce Semantics

Registration evidence is insufficient when the probe already invokes handlers.

- Static package, manifest, structure, and text-safety gates run before importing or invoking the package.
- A normal tool probe must return parseable structured output with explicit success; a deliberately bad input must return an explicit failure rather than success, malformed output, or an exception.
- Commands must return nonempty text when that is the runtime contract.
- If handler output reports a plugin/package identity, require it to equal the declared manifest identity. Do not require an identity field from plugins whose public output contract does not define one.
- Apply the same real-manager result checks at direct publication and canonical retained-package validation.
- Keep probes credential-free, isolated under temporary HOME, and incapable of paid, network, destructive, or live-service mutation.

## Canonical and Direct Inventory Parity

Any package kind that emits `included_files` must have exact canonical equality checked later.

- Compare the manifest list with every package file except the root manifest itself.
- A nested `examples/manifest.json` is package content and must remain included; exclude by exact root path, not by basename.
- Share this check between direct and canonical plugin/profile gates so retained packages cannot bypass generation-time integrity.
- Preserve gate ordering: static/inventory checks first, staged semantic safety second, real runtime behavior third, destination mutation last.

## Recoverable Batch Rollback Journals

An anonymous temporary snapshot is not sufficient when rollback itself can fail: the next normal retry cannot discover it.

- Store the rollback snapshot at a deterministic private transaction path and write an atomic journal containing the exact ordered target set and content seals.
- Seal **every target index**, not only targets that were present. Use a distinguished absent-state seal for missing targets, then require the seal-key set to equal the complete target-index set before examining or restoring bytes. Otherwise deleting one seal can silently remove corrupted retained bytes from validation.
- Validate the raw JSON representation before converting seal keys: reject duplicate object members with a duplicate-detecting `object_pairs_hook`, then require each key to equal the canonical decimal rendering of its parsed index. Ordinary `json.loads()` collapses duplicate `"0"` members, while conversion before canonicality checks collapses aliases such as `"00"`; either can bypass exact-key evidence.
- For present targets, require both snapshot existence and exact digest equality. For absent targets, require the snapshot path to remain absent. Reject missing keys, extra keys, present/absent inversions, digest drift, and target-list drift before the first destination mutation.
- On entry, recover a retained complete snapshot before creating a new one. Require the retry target set to match exactly.
- Never consume a damaged, incomplete, malformed, or target-mismatched journal. Leave the visible destination and retained evidence untouched and fail closed.
- If rollback fails because permissions or interruption prevent restoration, preserve the old bytes in the journal. After the obstacle is removed, a normal new transaction must restore old bytes, start a fresh snapshot, and permit immediate retry.
- Test real permission loss plus normal retry, content corruption, deletion of a seal paired with retained-byte corruption, missing/extra seals, canonical aliases (`"00"` versus `"0"`), duplicate raw JSON members at top-level and nested objects, present/absent inversion, target mismatch, cleanup failure, and interruption-class exceptions.

## Release Fingerprints Are a Derived Contract

If the repository publishes a source-fingerprint inventory, sanitizer implementation and test additions make that inventory stale even before public packages change.

- Regenerate fingerprints only after the candidate bytes are stable, excluding the fingerprint file itself to avoid recursion.
- Share one deterministic `build_fingerprints()` implementation between the writer and validator; do not let reviewers reconstruct a stricter topology than CI checks.
- Compare exact path sets and digests, reporting missing, extra, and mismatched counts. Add a regression proving current bytes pass and a tracked-byte mutation fails.
- Run fingerprint validation after inventory regeneration inside the outer transaction and before commit/push. Include the fingerprint file hash in the exact candidate seal.
- Any later code or test edit invalidates the generated inventory and requires regeneration before resealing.

## Verification Hygiene for Generated Caches

Avoid verification commands that mutate fixtures. `compileall` writes `__pycache__` even in workflows that otherwise set `PYTHONDONTWRITEBYTECODE`; copied fixtures can then fail canonical cache-path checks. Prefer in-memory `compile(source, filename, 'exec')` for syntax validation, or remove only proven generated caches before sealing. Inventory ignored cache paths explicitly before claiming residue-free evidence.

When the complete canonical suite exceeds one command's hard runtime ceiling, partition the sorted `test_*.py` module set into deterministic, disjoint shards and run them concurrently in separate processes. Print each shard's module count, require every shard to exit zero, and prove the union equals the full discovered module set with no overlap; sum the reported test counts. Describe this as a complete sharded canonical run, not as one successful discovery command, and do not treat a timed-out monolithic attempt as failure evidence when no test failed.

## Probe Matrix

Include at least:

- YAML: spaced keys, tags, anchors, aliases, continuation/block scalars, nested/flow authors, mapping and sequence merges, repeated aliases, cycles, comments, duplicate keys, non-scalars.
- Shell: quoted/unquoted variables, `${...}` operators, nested substitutions, split roots, split executable names, escaped newlines, URLs, exact executable near misses.
- Markup/languages: standard/custom HTML, multiline SVG, URL attributes, C++ `template<>`, pointer/reference/`const*` forms, spaced and compact array references, return/ternary comparisons, and malformed nested/doubled placeholders.
- Credentials: decoded compound keys, short realistic values, authorization/cookie/provider variants, exact placeholders, parameter-expansion fallbacks, embedded marker words, Python AST target/value forms including static bytes, and TOML triple quotes.
- Runtime packages: declared/registered parity, static-before-import tripwires, normal and bad-input outcomes, malformed JSON, empty commands, thrown handlers, and reported identity mismatch.
- Inventories: direct and canonical plugin/profile equality, root-manifest exclusion, nested-manifest inclusion, corrupted retained lists, byte-preserving regeneration, and exact release-fingerprint path/digest parity.
- Transactions: skill, plugin, and profile exporters; multi-candidate rollback; forced rename failure; interruption and permission-blocked rollback; normal retry; damaged/mismatched journals; missing/extra/aliased/duplicate raw seal keys; staging/LKG residue checks.
