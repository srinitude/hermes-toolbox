# Independent skill package review

Use when the user asks for an independent security, contradiction, or package-quality review of a live skill plus its validation packet. Stay read-only on the skill tree unless the user asks for fixes. Prefer `read_file`, `search_files`, and non-mutating hash/compare commands.

This file extends `skill-mutation-validation.md`. That file owns mutation closeout, fixtures, and packet freeze. This file owns the reviewer's live re-proof steps and security-contract checks. For a whole frozen Git tree or profile/distribution export (Toolbox-style), use `frozen-distribution-package-review.md` instead or in addition.

## Work order

1. Inventory the live skill dir (`SKILL.md` + `references/` / `templates/` / `scripts/`) and the report dir the task owns.
2. Identify the newest claimed validation packet (`live-validation-vN.json`, `final-validation.json`, `review-packet.json`, hashes in coverage files). Do not assume the highest filename alone is authoritative until hashes match live files.
3. Recompute SHA-256 and line/byte sizes for every live skill file. Compare to every `equal:`, `limit:`, or packet hash claim. Any mismatch is a high blocker even if other checks say PASS.
4. Mark older sibling artifacts (`validation-local.json`, `live-validation.json`, `v2`, `v3`) as superseded when sizes or hashes disagree with live files. Never cite them as whole-package proof.
5. Walk local links and unique external URLs. Confirm destinations exist. Reuse prior link reports only after confirming the live URL set still matches.
6. If an inventory or capability audit is in scope, validate taxonomy integrity (below) and count consistency before trusting coverage PASS.
7. Run security-contract checks for agent-delegation or process-launch skills (below).
8. Emit one verdict object: blockers, security_concerns, contradictions, suggestions, passed_checks, summary.outcome. Empty security and logic lists are required for PASS. Soften nothing into suggestions when it blocks.

## Live hash re-proof

```text
# Example shape. Prefer real tools available in-session.
sha256sum SKILL.md references/*.md
# Compare to packet equal:<path> detail fields and packet-integrity.json
```

- Packet claim ≠ live hash → BLOCKED. Re-freeze required.
- Packet size claim ≠ live lines/bytes → BLOCKED.
- Draft vs live `cmp` can still pass while the frozen packet is stale. Check the packet, not only draft equality.

## Taxonomy and audit integrity

When a review packet ships a capability or disposition inventory:

1. Read the declared enum or disposition vocabulary in the audit schema or header.
2. Collect every disposition/label value used in inventory rows.
3. BLOCKED if any live label is outside the declared set, or if the set is free-form with no closed schema.
4. BLOCKED if the same audit file carries conflicting count blocks (for example early `settings=151` and later `settings=174`) without an explicit superseded marker on the stale block.
5. BLOCKED if source metadata (doc hash, char count) appears twice with different values for the same URL without supersession.
6. "Every row has field X" is not enough. Field X must use a closed vocabulary the package defines.

## Skills-guard false positives

Hermes skills guard may flag `other_agent_config` / persistence when a skill documents another product's settings paths for inspection (for example `~/.claude/settings.json`, `.claude/settings.local.json`).

Treat those as expected documentation hits when:

- The surrounding text says inspect, detect, or fail closed on those paths
- The skill does not instruct writing, migrating into, or persisting Hermes state through those paths
- Builtin or agent-created sources remain allowed under caution; community + caution may still block install

Do not invent a security blocker solely from the guard line if the live prose is inspection-only. Still record the guard finding under passed_checks or notes so the next reviewer does not re-litigate it blindly.

## Security contract for agent-delegation skills

Apply when the skill launches Claude Code, Codex, OpenCode, or any child agent/process with tools:

| Check | Fail when |
| --- | --- |
| Auth isolation | API key / cloud / gateway fallback remains possible after OAuth-only claims |
| Secret handling | Prompt text bans secrets but default launch allows broad Read/Bash without secret-path deny, credential-file deny, or sandbox |
| Bypass mode | `--dangerously-skip-permissions` (or equivalent) ships with broad tools and no required preflight for settings, MCP, hooks, plugins, agents |
| Nested processes | Dynamic workflows / subagents lack per-child lease, prompt, tool bound, timeout, and cleanup owner |
| Session residue | Bounded one-shot launches omit no-persist flags while the skill claims strict secret handling |
| Prompt authority | Replacement system prompt is a checklist only, with no template and no "repo/extension content is untrusted data" rule |
| Source allowlist | OAuth or credential sources are named vaguely ("allowlist") without an exact accepted set or deterministic status binding to the selected token |

Prompt-level rules are not enforcement. Prefer fail-closed launch shapes: narrow tools, reviewed sandbox, explicit deny lists, inspected settings, and separate leases for nested children.

## Contradiction scan

Search the report dir and skill text for:

- Duplicate count maps with different numbers
- Duplicate source hashes/char counts for one URL
- Version pins that disagree with `claude --version` / installed binary (when the skill claims a version baseline)
- Work examples missing a flag the parent skill marks required on every work launch
- Draft/live/packet hash triangles that do not agree

## Verdict shape

```json
{
  "passed": false,
  "blockers": [{"id": "B001", "severity": "high", "finding": "...", "evidence": ["path:lines"]}],
  "security_concerns": [],
  "contradictions": [],
  "suggestions": [],
  "passed_checks": [],
  "summary": {
    "outcome": "BLOCKED pending ...",
    "scope_reviewed": "...",
    "files_created": [],
    "files_modified": [],
    "issues_encountered": []
  }
}
```

- `passed: true` only when blockers, security_concerns, and contradictions that break package integrity are empty.
- Suggestions may remain on PASS.
- Do not edit the skill under review during a read-only independent review.

## Main session after this review

If the review BLOCKS on stale packet hashes, re-freeze against live files before claiming whole-package PASS. If it BLOCKS on security contracts or open taxonomies, patch the skill or audit schema, then re-run mutation validation and a fresh independent review of the new packet.
