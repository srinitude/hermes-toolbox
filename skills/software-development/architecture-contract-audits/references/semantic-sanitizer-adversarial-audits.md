# Semantic Sanitizer Adversarial Audits

Use this reference when a public-package sanitizer recognizes identity terms, placeholders, shell paths, structured credentials, markup, or language syntax.

## Placeholder grammar

Treat approved placeholders as a closed whole-value grammar. Test exact valid tokens, missing or doubled delimiters, asymmetric delimiters, adjacent punctuation, quoted prose, Markdown wrappers, markup attributes, autolinks, and language identifiers. Delimiter checks must run before markup or language exceptions.

Do not publish the literal malformed probes in reusable documentation. Keep exact synthetic fixtures in repository tests and report them by neutral case ID in public audit summaries.

## Shell-word analysis

Analyze shell words rather than whole lines. Model quoting, escaping, variables, parameter expansion, command substitution, adjacent substitutions, supported literal `printf` composition, brace expansion, and control operators. Bound symbolic branching and depth; fail closed only when an unsupported form could resolve to a protected executable root.

Pair every rejection with controls for URLs, quoted literals, near-miss executable names, arguments that contain paths as data, and ordinary environment-variable prose. Verify symbolic outcomes with a controlled shell that prints expansions without executing them.

## Structured credentials and authorship

Decode YAML/JSON/TOML/frontmatter values and keys before classification. Cover aliases, merges, escaped keys, multiline scalars, and strict JSON parsing. For Python, evaluate a bounded set of static string and byte expressions across every assignment-target form. Dynamic runtime construction remains code, not embedded configuration data.

Approve placeholders only when the complete value matches the approved grammar. Treat private-key blocks independently of assignment syntax. Keep ordinary compatibility fields and policy prose valid.

Protect complete approved identities in metadata while avoiding global denial of ambiguous first-name words. Public package bodies use role language and approved placeholders rather than personal identities or machine-specific paths.

## Markup and language controls

Require real compiler or parser evidence for valid C++ templates, qualifiers, pointers, references, arrays, function types, comparisons, and ternary expressions. Preserve standard/custom HTML and SVG with quoted, unquoted, boolean, multiline, and self-closing attributes. Reject malformed delimiters without treating every angle-bracket expression as a placeholder.

## Transactional proof

Helper-level errors are insufficient. For each case, run the real direct package exporter and canonical retained-package validator. Record return status, destination mutation, exact byte preservation, inventory state, and residue. Unsafe acceptance and deterministic false rejection are separate blockers.

## Review matrix

- exact known-token boundaries and delimiter integrity;
- shell quoting/expansion/operator branches and bounded failure behavior;
- decoded structured values and static Python forms;
- complete identity terms versus ordinary prose;
- Markdown, markup, SVG, URLs, and compiler-valid language syntax;
- direct versus canonical context parity;
- package manifest and forbidden-path parity;
- no-write and cleanup seals.

A review passes only when exact-candidate identity is stable, every unsafe synthetic case rejects before mutation, every valid control survives byte-for-byte, and the audit leaves no repository or fixture residue.
