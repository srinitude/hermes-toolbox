# Semantic Public Sanitizer Review

Use this reference when an enhanced prompt asks for public-safe export of skills, plugins, profiles, personalities, or configuration derived from private Hermes state.

## Review posture

Treat sanitization as a semantic boundary, not search-and-replace. Require both unsafe-content rejection and compatibility for legitimate prose, markup, language syntax, paths-as-data, and configuration.

## Required matrices

### Identity and authorship

- Protect complete approved identities in frontmatter and repository-local metadata only.
- Keep personal/private context out of package bodies and tracked inventories.
- Avoid global denial of ambiguous ordinary first-name words.
- Use role-based public prose and untracked local deny/source-gate policy.

### Placeholders and markup

- Define a closed whole-value placeholder grammar.
- Test valid tokens, missing/doubled/asymmetric delimiters, case changes, punctuation boundaries, wrappers, and multiline contexts.
- Preserve HTML, SVG, custom elements, autolinks, comparisons, nested templates, and compiler-valid C++.
- Keep exact malformed synthetic payloads in tests; public audit prose may identify them by neutral case ID.

### Shell paths

- Analyze each shell word under quoting, variables, parameter operators, command substitutions, literal composition, brace expansion, and operators.
- Bound depth and branch count; fail closed only when an unsupported form could resolve to a protected executable.
- Pair every rejection with URLs, literal strings, arguments, near-miss executable names, and other benign controls.

### Structured and static values

- Decode strict JSON, YAML, TOML, and frontmatter keys/values.
- Cover aliases, merges, escaped keys, multiline scalars, and duplicate raw JSON members.
- For Python, cover all target forms and bounded static strings, formatted literals, concatenation, and bytes.
- Recognize complete approved placeholders without exempting values that merely contain marker words.
- Detect private-key blocks independently of assignments.

### Package and transaction behavior

- Run static/completeness checks before importing plugins.
- Require declaration/registration and handler-result semantics with the real Hermes manager.
- Require exact included-file manifests and canonical forbidden-path policy.
- Reject before destination mutation and preserve last-known-good bytes.
- Exercise rollback, interruption, retained retry, malformed journals, complete present/absent sealing, and cleanup residue.

## Evidence threshold

A candidate passes only when direct and canonical gates agree, valid controls survive byte-for-byte, unsafe synthetic fixtures reject before mutation, source fingerprints are exact, structure/runtime checks pass, the exact staged digest is independently reviewed, and no audit-owned residue remains.
