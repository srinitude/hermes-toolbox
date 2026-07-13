# Exact candidate sealing and blocker remediation

Use this reference when a staged security-sensitive candidate must be independently sealed before commit.

## Candidate lifecycle

1. Complete focused RED→GREEN remediation before staging.
2. Stage the whole candidate and record literal base HEAD, the exact binary-diff producer command/digest, index-manifest digest, and zero unstaged/untracked paths.
3. Build/install/package-test only that tree; compare packaged members byte-for-byte with staged blobs.
4. Run the uninterrupted authoritative suite.
5. Dispatch multiple read-only reviewers that independently verify the digest before inspection and before verdict.
6. Any edit or restaging creates a new generation. Prior suite, wheel, and audit evidence is historical only.
7. A concrete blocker overrides a green suite. Reject, remediate, reseal, and rerun all stages.

## One-writer review discipline

- The implementation session is the only writer.
- Reviewer agents inspect complete relevant files and pinned upstream sources; they never edit, stage, install, deploy, commit, or mutate external state.
- Do not delegate fixes merely because a generic review workflow suggests an auto-fix agent. The original writer validates each finding, creates a public RED where deterministic, and applies the smallest coherent fix.

## High-value adversarial checks

- Operation ledger truth: no aggregate call or hidden write under a simple-read ID; use an explicit compatibility hold instead of false parity.
- Boundary cardinality: exercise N-1/N/N+1 around every preload, response, or retention bound.
- Replay: test after in-memory registry loss/restart and after capacity pressure; preserving bounded rows must not erase exactly-once fingerprints.
- Deadlines: one absolute budget spans every retry, connect, send, read, and acknowledgement replay.
- Authenticity: delete every related chain/tip/checkpoint structure together; partial-deletion tests are insufficient.
- Startup ownership: a second process must establish exclusive lifetime ownership before reconciliation can kill or terminalize anything.
- Cross-store recovery: assert both sidecar terminal state and released native task/run claims.
- Threaded I/O: capture terminal thread exceptions; a dead thread is not proof of successful drain.
- Identity: bind UID, PID, start time, primary GID, and canonical supplementary groups wherever DAC memberships carry authority.

## Reporting

Name rejected generations explicitly. Report only current exact identifiers as sealing evidence, and keep protected-upstream drift separate from candidate drift.
