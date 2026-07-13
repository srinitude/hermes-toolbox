# Public Export Transaction Adversarial Review

Use this reference when reviewing a public exporter that combines source sanitization, package staging, runtime checks, inventory generation, destination replacement, and whole-batch rollback.

## Freeze the candidate

Record the literal base, exact staged-diff producer and digest, sorted staged path count, index blob manifest, unstaged/untracked state, and ignored-artifact manifest. Recheck every seal after the probes. Reconstruct the index into a disposable directory for execution; do not audit mutable live files after freezing.

## Static-value and structured-data safety

Exercise every supported serialization and assignment form independently through the real direct exporter:

- decoded YAML, JSON, TOML, and frontmatter keys;
- Python names, attributes, subscripts, mappings, keyword arguments, `setattr`, augmented assignments, literal formatted strings, concatenated constants, and byte literals;
- recognized provider and authorization field families, short realistic values, and private-key blocks;
- complete approved placeholder values versus values that merely contain marker words;
- valid multiline strings and escaped structured keys.

Use one synthetic, non-secret trigger per fixture. Require rejection before destination mutation and require the last-known-good package, inventory files, and transaction artifacts to remain byte-identical.

Pair every rejection with benign controls such as token-count configuration, tokenizer metadata, cookie-policy prose, password-policy metadata, and ordinary authorization documentation. Unsafe acceptance and deterministic false rejection are independent blockers.

## Markup and language compatibility

Compile complete language controls with the real compiler where available. Cover nested templates, cv/ref qualifiers, pointers, arrays, compact and spaced array references, function types, comparisons, and ternary expressions. Cross the compiler-valid fixtures through both the direct exporter and canonical validator. Preserve ordinary HTML/SVG/custom elements while rejecting malformed placeholder delimiters.

## Package completeness and runtime contracts

Verify direct and canonical gates agree on:

- exact manifest file lists, with only the package-root manifest excluded from its own list;
- nested files named `manifest.json` retained as ordinary content;
- forbidden cache, backup, runtime, session, credential, and database paths absent;
- declared versus registered tools and commands;
- callable handlers, valid normal results, bad-input rejection, JSON tool payloads, nonempty command output, and reported identity consistency;
- static checks running before any plugin import.

Use the real Hermes manager in a disposable home. Test doubles do not prove registration or handler behavior.

## Transaction and recovery matrix

The batch journal must bind the complete ordered target list. Every present snapshot uses a content digest; every absent target uses an explicit absence seal. Reject before restoration when any target, seal, snapshot, digest, journal member, or type is missing, extra, duplicated, noncanonical, reordered, damaged, or contradictory.

Exercise:

1. ordinary rollback after a normal exception;
2. interruption-class rollback;
3. retained-journal retry that restores exact old state before entering the new body;
4. present and absent targets in one transaction;
5. stale staging and archive cleanup;
6. cleanup failures at each residue location;
7. target-list mismatch and auxiliary-path collisions;
8. hardlink aliases and protected-root overlap;
9. repeated no-op publication.

A damaged retained snapshot must remain untouched for diagnosis. A valid retry must restore old state, commit new bytes, remove the journal, and leave no residue.

## Fingerprints and inventory

Derive the expected fingerprint universe independently from the staged index. Compare expected and checked-in path sets and digests exactly, then compare canonical serialized bytes. Verify the validator rejects a stale map. Regenerate inventories only after all code and package bytes are stable.

## Probe hygiene

Use OS-created disposable paths with an owned prefix. Isolate HOME and Hermes state, disable bytecode writes, avoid network/paid/destructive operations, and remove only audit-owned fixtures. Print compact neutral case IDs and booleans. Restore exported Git environment variables before deleting reconstructed repositories.

## Acceptance threshold

Pass only when:

- exact candidate identity is reproduced;
- all required direct and canonical boundaries reject unsafe content before mutation;
- valid operational and compiler controls publish byte-for-byte;
- package/runtime/manifest checks agree;
- transaction recovery passes the complete malformed-journal matrix;
- fingerprints are exact;
- source/index/status/ignored-state seals remain unchanged;
- all disposable fixtures are removed.
