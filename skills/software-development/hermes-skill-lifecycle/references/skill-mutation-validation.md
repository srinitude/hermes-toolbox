# Multi-file skill mutation validation

Use after a non-trivial create/patch of a user-local skill that adds or rewrites `SKILL.md`, `references/`, `templates/`, or `scripts/`. This is focused ad-hoc validation, not suite green.

For policy prose rewrites and meaning ledgers, load `meaning-preserving-rewrite` and keep one ledger owner. This file owns skill-package closeout: fixtures, review packets, and honest PASS labels.

## When this package is required

Require the full package when any of these are true:

- A mechanical validator or schema is added or changed
- Progressive disclosure moves rules across support files
- Independent review is used
- The change claims behavioral compatibility with an earlier skill version

A one-line pitfall patch can stay on description, body limits, and a re-read. Don't invent a ledger for that.

## Artifacts

Write under the paired workspace `.hermes/reports/<task-slug>/` (or the active report dir the task already owns):

| File | Role |
| --- | --- |
| `backups/` | Pre-edit copies of every rewritten skill file |
| `baseline.json` | Pre-edit hashes plus intended support paths |
| `meaning-ledger.json` | Clause map when wording must preserve prior rules |
| `fixtures/` | Pass fixture plus negative cases for every mechanical checker |
| `validator-tests.json` | Exit-code matrix for fixtures and the incomplete template |
| `voice-scan.json` | Optional prose scan for banned words and dash characters on Markdown only |
| `review-packet.json` | Frozen file list, hashes, and claims sent to review |
| `packet-integrity.json` | SHA of the frozen packet and per-file hashes |
| `focused-validation.json` | Subtask checks only |
| `final-validation.json` | Whole-change PASS or BLOCKED with separate subtask vs whole fields |
| `independent-review.json` | Read-only reviewer verdict; start BLOCKED until current-packet PASS |

## Mechanical validators and scripts

1. Compile or parse every new script and schema before claiming READY.
2. Seed one true PASS fixture and negative fixtures that match the real failure classes.
3. For ID-graph or completion reports, negative cases must include forged checks, omitted keys, extra keys, wrong types, missing evidence, failed gates, incomplete risks, unexpected files, missing artifacts, incomplete cleanup, invalid waivers, and orphan or unknown links for each collection (`task`, `gate`, `artifact`, `evidence`, and peers the schema defines).
4. Run the skill's own validator on every fixture and on the incomplete starter template. Expect exit 0 only on true PASS fixtures. The starter template itself must stay a truthful BLOCKED report.
5. Do not copy fixtures from an unrelated hardening task into a later plan or skill. Generate fixtures from the current schema.

### RED before each fail-open fix

When a review or local probe finds a fail-open hole:

1. Write a fixture that is accepted today and must become BLOCKED.
2. Record the actual exit code and any traceback as RED evidence.
3. Patch the smallest validator path that closes that hole.
4. Re-run the full fixture matrix. GREEN means that fixture and every older case match expected exits with no traceback.

Never patch first and invent the negative later. A hole without a failing fixture is not closed.

### Fail-closed classes for structured completion validators

Require negatives (and validator enforcement) for every class that applies:

| Class | Must BLOCKED |
| --- | --- |
| Schema shape | Missing or extra top-level keys; missing or extra nested keys; wrong collection types |
| IDs and enums | Invalid stable ID format; unknown status/scope/kind/enum values; duplicate residual-risk IDs when residual risks share the risk prefix |
| Malformed input | Wrong scalar types including `bool` where `int` is required (`False==0` / `True==1` is fail-open); unhashable or broken link values; non-UTF-8 file bytes; exit 1 with no traceback |
| Path and FS errors | Absolute paths; `../` traversal outside the report dir; symlink escapes; embedded-NUL or other path strings that raise before read; every `is_file`/`stat`/`read` path must fail closed without traceback |
| Graph integrity | Missing reciprocal links both directions, including `evidence.validator_id` listed in that validator's `evidence_ids`; orphan or unknown node IDs; residual-risk records with no risk link or no required evidence/aggregate participation when the schema claims them |
| Evidence provenance | Missing file; SHA-256 mismatch; missing kind, producer, or covered structured IDs; producer-only assertion without reverse link |
| Scope separation | Task-local evidence used for whole-plan aggregate checks |
| Aggregate coverage | Whole-plan check lacks check-specific structured coverage IDs; aggregate proof that is only self-asserted `covers_ids` on an arbitrary hashed file with no producer-owned binding to the named check result |
| Human vs machine | `human_and_machine_reports_match` that passes on status/ID/hash metadata alone without a canonical content or derivation relationship |
| Waivers | Waiver on a PASS requirement; unknown waiver ID; unused waiver record; non-requirement waiver target |
| Safety and size | No `eval`/`exec`/`subprocess`/`os.system`/`shell=True`/`pickle.loads`; no unconstrained arbitrary-file read via report paths; stay within authored line limits (file ≤200, function ≤30 when that policy applies) |

Also keep at least one positive requirement-waiver PASS fixture when waivers are in scope, so the matrix is not all-negative.

Independent reviewers of a completion-report validator must re-check these classes against live code and fixtures, not only against a green 59-case (or similar) matrix. A green matrix that never includes bool exit codes, path confinement, reverse producer links, residual-risk orphans, content-bound human/machine equality, or producer-bound aggregates does not prove those classes.

### Source boundary for bundled-skill overrides

When the task hardens a bundled skill through the active profile override:

- Keep installed Hermes source read-only and byte-identical to the pre-edit backup.
- Do not require active override files to match installed source. Divergence is expected.
- Focused checks should assert `installed_source_unchanged`, not `active_matches_installed_source`.
- New support files belong under the active override path only.

## Meaning ledger (when prior rules must survive)

1. Baseline and backup first. Hash only files that exist.
2. Enumerate prior clauses from the backup, not from memory.
3. Prefer `targets[]` with live `new_file` + exact `new_text` substrings after splits.
4. Acceptance: unique IDs, unique meanings, every target present in the live file, no silent drops.
5. After any wording fix, update matching ledger target text in the same edit, then re-check substring presence.

## Frozen review packet

1. Build `review-packet.json` from live skill files and validation evidence only.
2. Hash the packet bytes into `packet-integrity.json` with per-file hashes.
3. Independent review is read-only. Prefer search/read tools only. No write, patch, mutating terminal, or `skill_manage`.
4. After every fix from review or local validation, refresh the packet contents and recompute integrity hashes before the next review cycle or final PASS.
5. Stale packet metadata after a fix is BLOCKED even if the live skill is already correct.
6. Record the current packet SHA-256, ledger entry count, fixture or validator-case count, and scoped file sizes in the reviewer context. When the review returns, match those identity fields to the live packet before acting.
7. Late async reviews of older packets are discarded. Do not mutate from findings whose packet SHA, entry count, fixture count, or scoped sizes disagree with the current frozen packet.
8. Before applying a delayed finding, confirm the claimed gap still exists in live text. Skip fixes already present.
9. Keep `independent-review.json` BLOCKED until a review of the current frozen packet returns PASS with empty `failed` and `required_fixes`.
10. Independent hash recomputation by a read-only reviewer is optional for packet-identity only. Main-session `packet-integrity.json` is enough when the reviewer cannot recompute SHA-256. Missing recomputation alone is not a blocker. When hash tools are available, still re-hash live skill files against every `equal:` / size claim; live mismatch is BLOCKED even if the packet file hashes itself. See `references/independent-skill-package-review.md`.

## Acting as the independent reviewer

For security, contradiction, and whole-package quality review of a live skill plus mixed validation artifacts (not only a frozen mutation packet), follow `references/independent-skill-package-review.md` first: re-hash live files, reject stale sibling reports, close open taxonomies, and apply agent-delegation security contracts.

When the user (or main session) hands you `review-packet.json` and says verify every `required_check` and `review_scope` path:

1. **Read the packet first.** Treat `required_checks`, `review_scope`, claimed ledger count, and claimed validator-case count as the work order. Do not invent extra scope or skip a named check.
2. **Stay read-only.** Use `read_file` and `search_files` (or equivalent search/read). Do not write, patch, run mutating terminal, or call `skill_manage`. Record `mutation_tools_available: false` and `skill_writing_tools_available: false`.
3. **Re-count live evidence.** Do not trust wrapper claims alone.
   - Ledger entries: count stable `"id": "PREFIX-###"` hits in `meaning-ledger.json`. Prefer that over counting `"source_file"` (split/meta entries may omit or share fields).
   - Validator cases: count case `"name"` (or equivalent) in `validator-tests.json`.
   - Results: count `"result": "PASS"` (or FAIL) and confirm every case has expected and actual exit codes.
   - Exit-code matrix: count `expected_exit_code` / `actual_exit_code` for 0, 1, and other codes separately. PASS fixtures and the incomplete template should be the only exit-0 cases when the suite is all-negative plus one pass.
4. **Walk every `review_scope` path.** Confirm each file is readable. Spot-check raw backups against ledger `original` text and live targets against `new_text` / `targets[].new_text` when a ledger is in scope.
5. **Inspect the validator source** for each fail-closed class in the table above. A green case count does not prove bool-vs-int exit codes, report-dir path confinement, reverse producer links, residual-risk orphans, content-bound human/machine match, or producer-bound aggregates unless those classes appear in code and fixtures.
6. **Search-tool limits.** Default `search_files` / ripgrep rejects lookahead/lookbehind. Use simple literal or character-class patterns and paginated reads. Do not block the review solely because a fancy regex failed.
7. **Hash tools optional.** If you cannot recompute SHA-256, rely on main-session `packet-integrity.json` and still verify file presence and content claims.
8. **Emit one verdict object** (save as `independent-review.json` when you can write; otherwise return it as the review body):

```json
{
  "status": "PASS",
  "reviewer_toolset": ["read_file", "search_files"],
  "mutation_tools_available": false,
  "skill_writing_tools_available": false,
  "checks": {
    "<each required_check name>": "PASS"
  },
  "failed": [],
  "required_fixes": [],
  "security_concerns": [],
  "logic_errors": [],
  "suggestions": []
}
```

On BLOCKED, set `status` to `BLOCKED`, put failing check names in `failed`, and give concrete, file-scoped `required_fixes`. Keep `checks` entries as `PASS` or `BLOCKED` (or false) per name. Do not soften BLOCKED into suggestions.

9. **End on the verdict.** When the ask is packet review, deliver the JSON (and a short failure list if BLOCKED). Do not expand into a reimplementation plan unless asked.

## Main session after independent review returns

When an async or leaf reviewer returns a verdict:

1. Match packet SHA, ledger count, fixture or case count, and scoped sizes to the current freeze. Discard mismatches. Do not mutate from a stale packet.
2. On BLOCKED, keep `independent-review.json` and whole-change status BLOCKED. RED any new fail-open hole, patch, refresh the packet, and re-dispatch review against the new freeze only.
3. On PASS, require empty `failed`, `required_fixes`, `security_concerns`, and `logic_errors`, and every named `checks` entry PASS.
4. Re-hash the live packet and every `review_scope` path. Scope drift after the review started is BLOCKED until a new freeze and review.
5. Write `independent-review.json` with the verdict, `packet_sha256`, and `delegation_id` when present. Then write `final-validation.json` with separate subtask PASS and whole-change PASS.
6. Re-run the full fixture matrix plus installed-source and packet-integrity checks once more after those writes. Only then report whole-change PASS to the user.
7. Never flip whole-change to PASS in the same artifact set that still says independent review is pending.

## Subtask vs whole-change labels

- `focused-validation.json` may PASS while whole-change is still BLOCKED.
- Whole-change PASS needs live skill reload (`skill_view`), ledger/fixture/packet evidence, and independent review PASS when review was required.
- Never describe component-only evidence as whole-skill or whole-plan completion.
- Label results **focused ad-hoc verification**, not suite green.

## Ad-hoc verifier hygiene

1. Prefer `tempfile` under the OS temp dir with a `hermes-verify-` filename prefix.
2. On macOS, when a gate names `/private/var/folders/.../T`, create the script in that directory (or the equivalent resolved temp path), run it, then delete it.
3. Prefer `execute_code` or `terminal` for temp scripts when `write_file` refuses system temp paths.
4. Leave no `hermes-verify-*`, one-shot review cron, or stray helper under `~/.hermes/scripts/` after closeout.

## Closeout checklist

- [ ] Backups exist and match recorded hashes
- [ ] Support inventory in baseline matches live linked files
- [ ] Ledger live targets pass when a ledger was required
- [ ] Schema/scripts parse or compile
- [ ] Pass and negative fixtures match expected exit codes
- [ ] Fail-open holes each have RED then GREEN fixture proof
- [ ] Review packet integrity matches the latest live files
- [ ] Independent review PASS is for the current packet SHA and counts, with empty required fixes, security concerns, and logic errors when review ran
- [ ] Delayed reviews of older packets were discarded without mutation
- [ ] After review PASS, packet and review_scope hashes were re-checked, `independent-review.json` was written, the full fixture matrix was re-run, then `final-validation.json` separated subtask and whole-change PASS
- [ ] Bundled-skill override tasks assert installed source unchanged
- [ ] Temp verifiers and review helpers removed
- [ ] `skill_view` reloads the skill and linked files successfully
