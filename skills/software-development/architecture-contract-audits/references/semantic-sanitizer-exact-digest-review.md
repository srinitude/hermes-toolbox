# Semantic Sanitizer Exact-Digest Review

Use this reference for an independent, read-only verdict on an exact staged sanitizer/exporter candidate.

## Candidate identity

Before reading implementation details, record:

- literal HEAD/base;
- the exact staged-diff producer and SHA-256;
- staged path count;
- sorted index blob manifest;
- unstaged and untracked counts;
- ignored-artifact path/content manifest;
- immutable reconstructed index directory.

Run probes only in the reconstruction or disposable fixture homes. Recheck every seal afterward. Any byte drift retires the verdict.

## Required review surfaces

### Structured configuration

Test strict JSON separately from YAML. Exercise frontmatter, mappings, sequences, aliases, merges, escaped keys, multiline scalars, binary tags, and repeated object members. Require source-marked diagnostics and fail-closed handling of duplicate raw JSON members before ordinary parsing can collapse them.

### Static values

Cross each synthetic configuration form independently through direct and canonical gates. Include provider-shaped fields, authorization families, private-key blocks, short values, exact approved placeholders, marker-word substrings, Python target forms, literal formatted strings, concatenated constants, byte literals, and TOML multiline values. Pair with benign operational controls.

### Shell paths

Compare production symbolic outcomes with a controlled shell expansion oracle. Cover quoted/unquoted variables, parameter operators, nested and adjacent substitutions, supported `printf` composition, control operators, brace/range expansion, escaped newlines, URLs, and bounded-depth or bounded-branch cases. Unsupported forms fail closed only when they could resolve to a protected executable.

### Markup and language syntax

Compile complete C++ controls with the available compiler. Cover nested templates, cv/ref qualifiers, pointers, lvalue/rvalue array references, function types, comparisons, and ternary expressions. Preserve HTML/SVG/custom elements, multiline attributes, self-closing variants, and URL/autolink contexts while rejecting malformed placeholder delimiters.

### Package and runtime semantics

Check direct and canonical parity for exact manifests, nested manifest files, forbidden paths, declaration/registration agreement, handler normal and bad-input behavior, tool JSON, nonempty command output, and optional reported identity. Use the real Hermes manager in an isolated home.

### Batch transaction integrity

Build a target universe containing present and absent destinations plus inventories. Require one canonical seal per target. Reject missing, extra, duplicated, aliased, reordered, malformed, type-invalid, digest-altered, or present/absent-contradictory state before restoration. Verify normal rollback, interruption rollback, valid retained retry, cleanup failure, damaged snapshots, and auxiliary-path protection.

### Inventory exactness

Independently derive expected paths and hashes from the staged index. Compare the checked-in source fingerprint map for missing, extra, and mismatched entries and canonical serialized bytes. Confirm stale fingerprints fail the production validator.

## Adversarial probe design

- Use one independent trigger per fixture.
- Use synthetic, non-secret values and neutral machine-output labels.
- Avoid network, paid, destructive, or live-service mutations.
- Record destination and journal bytes before and after every rejected case.
- Keep valid controls adjacent to each rejection class.
- Remove only audit-owned temporary paths.

## Structural and quality checks

Require repository validators, package completeness, tutorial/runtime checks when present, Python compilation, structural limits, diff checks, and concise KISS/DRY review. Inspect added lines for debugging residue, unsafe subprocess patterns, silent cleanup, broad exception swallowing, unexplained markers, and duplicated policy logic.

## Verdict contract

Begin with `PASS` only when all required surfaces pass against the exact same digest and the no-write seal is intact. Otherwise begin with `FAIL` and provide only reproducible blockers containing exact path, behavior, expected result, observed result, and residue/mutation evidence. A provider-filtered or incomplete run is neither PASS nor FAIL and must be redispatched.
