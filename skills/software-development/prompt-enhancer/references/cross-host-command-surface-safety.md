# Cross-host command-surface safety

Use this when a user operates through a local thin client while Hermes tools execute on a remote control host.

## Before remediation

1. Label every human command block with its exact execution surface, such as **local MacBook Terminal** or **VPS shell**.
2. Put a non-mutating host/platform assertion before any command that can change SSH trust, config, or credentials.
3. When a command fails, first establish where it actually ran and whether the original command still fails on its intended machine.
4. Treat message origin, UI renderer, terminal backend, and computer-use backend as separate facts.

## SSH host-key failures

- Do not mutate the control host's `known_hosts` to repair a thin-client-only path.
- Verify host keys out of band before pinning them.
- If the user says the original local command works, withdraw unnecessary remediation rather than continuing from the wrong-host failure.
- After an accidental wrong-host command, inspect the alleged target file's timestamp and exact hostname entry before rollback. A fail-closed command may have made no change.
- Never remove a `known_hosts` entry without proving that the current session added that exact entry.

## Active-policy export handoff

When a user must export current policy from an authenticated admin UI:

1. The human copies the complete active policy from the first-party UI.
2. The agent never substitutes a reconstructed default and calls it active.
3. A zero-byte destination means the export is incomplete or a `cat > file` process is waiting; do not proceed.
4. Require nonzero size, private mode, and a recorded hash before parsing or deriving a candidate.
5. If the user asks the agent to “reply with the active policy” but the agent lacks authenticated source access, state the blocker instead of fabricating content.

## Verification packet

Record:

- intended execution surface;
- observed execution surface;
- whether a mutation actually occurred;
- exact file/entry evidence;
- rollback necessity or `no rollback needed`;
- successful rerun on the intended surface.
