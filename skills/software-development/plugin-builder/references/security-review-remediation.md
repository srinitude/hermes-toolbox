# Security review remediation for local control plugins

Use this checklist after an independent review finds fail-closed or test-realism gaps in a local Hermes plugin.

## Dispatch boundaries

- Validate a stored command against the **complete canonical operation**, not merely an executable prefix or broad subcommand family.
- For every operation, compare the full fixed-list argv, including argument order and the complete child argv after `--`.
- Keep `shell=False`; reject extra, missing, reordered, or operation-inconsistent arguments before spawning.
- If an integration requires a literal child command form, test the entire vector. Example profile-aware resume contract:
  `['hermes', '-p', profile, '--resume', session]`.

## Output and timeout bounds

- A size check after `subprocess.run(capture_output=True)` is not a memory bound: the child output has already been buffered.
- Use `Popen` with incremental reads from stdout and stderr, enforce an aggregate byte ceiling while reading, and kill/reap immediately on overflow or timeout.
- Test the boundary with a real child process that writes beyond the limit; do not substitute a mocked process.

## Native-string sanitation

Treat every model-facing native string as untrusted, not only terminal text. Apply one shared sanitizer to:

- agent metadata and status fields;
- caller and service identity fields;
- topology labels and native error codes;
- terminal/pane text.

The sanitizer should remove CSI/OSC ANSI sequences, C0/C1/DEL controls, and Unicode format controls, then redact complete credential shapes. Include Basic/Bearer authorization, quoted secrets containing spaces, Cookie/Set-Cookie headers with multiple semicolon-separated values, and common token prefixes. Bound the result only after sanitation/redaction.

## Validation order

Validate the exact profile, socket, live service identity, and caller pane before filesystem checks, executable discovery, or operation construction. This prevents malformed operation inputs from becoming an oracle when the caller is absent or stale.

Exercise absent and stale caller contexts across every public inspect and preview operation, not only one representative path.

## Public schemas

Use closed operation-specific schemas:

- `oneOf` branches with an operation `const`;
- exact `required` fields per branch;
- `additionalProperties: false` per branch;
- bounded enums, strings, and integers.

Validate representative valid and invalid payloads through a fresh real PluginManager registration path.

## Real-test resource hygiene

- Generate unique session/resource names per test process.
- Probe for collision and abort; never delete a pre-existing fixed-name resource during setup.
- Use framework-private temporary paths for command-injection sentinels.
- Teardown only resources whose exact generated identity belongs to the test.
- Launch fresh probes with `sys.executable` **without calling `Path.resolve()`**. Resolving a virtualenv interpreter can follow its symlink to the base Python and silently drop the virtualenv dependency context.

## Review-to-commit gate

1. Translate every concrete review blocker into a focused real test.
2. Implement the smallest coherent fix and run focused tests.
3. Run the complete suite, structural limits, compilation, diff checks, prohibited-pattern scan, and generated-cache cleanup.
4. Stage the complete coherent diff.
5. Request a fresh independent review against the staged diff and the earlier blocker list.
6. Do not commit or install until that review passes and the staged tree remains quiescent.
