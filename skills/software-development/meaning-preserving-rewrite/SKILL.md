---
name: meaning-preserving-rewrite
description: "Use when simplifying policy Markdown without meaning loss."
version: 1.5.2
author: Kiren Srinivasan
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [plain-language, policy, plans, soul, agents, rewrite, voice]
    related_skills: [plan, global-coding-policy, obsidian, humanizer, hermes-skill-lifecycle]
    created_by: agent
    created_with_hermes_commit: unknown
    compatibility_reviewed_with_hermes_commit: 5988fe6cd5547d3620df1de889ac6007f5463b4d
---

# Meaning-Preserving Plain-Language Rewrite
## Overview
Rewrite plans, SOUL, AGENTS, standards notes, and reports so they are dead-simple and sound human, without removing, weakening, broadening, or hiding any rule or decision. Prove preservation with a meaning ledger and independent review.

## When to Use
- User asks for dead-simple, plain, simpler, or easier wording on plans or policy artifacts
- User supplies a VOICE / human-writing brief for the plan or its planned artifacts
- A plan must rewrite SOUL, AGENTS, vault standards, or similar without changing intent
- You need to prove shorter prose still carries full meaning
- A complete-coverage plan needs a live official-docs inventory and primitive catalog before SOUL/AGENTS rewrite
- A user-local skill or policy skill rewrite must preserve prior rules under a meaning ledger (pair package closeout with `hermes-skill-lifecycle`)

**Out of scope:** pure new feature plans with no existing policy text; code refactors (use simplify-code / TDD); environment setup failures; one-off blog copy with no policy ledger (use `humanizer` alone).
## User preference

Prefer dead-simple writing on plans and policy artifacts. Zero loss of content, context, intent, or meaning. Shorter must not weaken, broaden, or blur rules.

Also prefer a real-person voice on those same files. Clarity wins if style and clarity collide. A plain rewrite that still reads like stiff assistant prose is incomplete.

Every sentence must be clear and grammatically natural. Unclear or awkward wording is a fail, even when the meaning ledger still says same meaning. If a reader has to parse what a phrase means, rewrite it.
## Plain-language + voice standard

Apply to the plan and every artifact it creates or rewrites (SOUL, AGENTS, notes, reports, templates). Load `humanizer` when the user asks for voice, or when a rewrite still reads machine-made.

1. Start with the result or rule.
2. Use common words and active voice.
3. One rule per bullet; short sentences.
4. Define a technical term on first use.
5. Keep paths, commands, setting names, hashes, and source quotations exact.
6. Use `must` / `must not` / `may` when strength matters.
7. Reason after the rule only when it helps a decision.
8. Move detail to linked notes; do not densify runtime files.
9. No old chat context required to understand the artifact.
10. Do not replace a precise rule with a vague summary.
11. Use contractions whenever they sound natural (`don't`, `it's`, `we'll`).
12. Vary sentence rhythm. Put a short sentence next to a longer one.
13. Be concrete. Name the file, command, count, or check. No motivational filler.
14. No neat antithesis pairs for effect. No forced three-item prose lists (technical checklists that need every check are fine).
15. No em dash or en dash characters. Use a period, comma, or short link word.
16. No sycophancy, hedges, or polished assistant closers.
17. English only.
18. Prefer direct statements over compressed imperatives that hide the subject or the strength (`X is mandatory` beats `Keep X above mandatory`).
19. Every pronoun and pointer (`above`, `this`, `those`) must have an obvious referent in the same section.

Blocked words, phrases, and closers live in `references/voice-check.md`. Put the live lists in a fenced `text` block labeled as test data so scanners can skip them. Never use those strings in real prose.

Backups and raw command output stay verbatim.

## Procedure

### 1. Baseline (Task 1; no rewrites yet)

- Load `global-coding-policy` before any Markdown write.
- Hash only files that exist now; record not-yet-created paths as `absent` (do not invent hashes).
- Record per present source: absolute path, sha256, bytes, line count, headings, file mode.
- Backup live SOUL/AGENTS (and other rewrite targets) to fixed owner-only paths (`0600` when local policy asks). Prove backups are byte-identical to sources after copy.
- Capture git inventory for the Hermes source root and any workspace worktrees: head, branch, clean/dirty, AGENTS/mise hits. Exclude credential-bearing remote URLs.
- Record current source commit and `future_note` absence/presence explicitly.
- Stop on hash drift without user disposition.
- Write `baseline.json` under the task report dir. Do not mutate SOUL, AGENTS, vault notes, plans, source trees, config, memory, or plugins in this step.
- Delete any temporary ledger/baseline builder scripts under the report dir before you call Task 1 done.

Concrete field shapes and a validation recipe: `references/baseline-task.md`.

### 1b. Official docs inventory (when the plan claims every docs page / primitive)

- Re-fetch live `/docs`, `/docs/llms.txt`, and `/docs/llms-full.txt` (do not trust the planning snapshot alone).
- Build `docs-inventory.json` (root + every source marker) and `primitive-catalog.json` with reverse coverage.
- Parse `llms.txt` via markdown links `](...)`; bare path regexes undercount absolute URLs.
- Document nav aliases when `public_path(source)` does not equal the live nav URL; never invent markers.
- Run builders from `/tmp` and delete them; leave only intended report JSON.

Full field shapes, URL transform, known aliases, and checks objects: `references/hermes-docs-inventory.md`.

### 2. Meaning ledger (before rewrite)

Enumerate clauses from live sources, not from memory:

1. Split multi-rule paragraphs into separate IDs before acceptance.
2. Walk every bullet line in SOUL and AGENTS (programmatic line pass preferred).
3. Add every new voice rule from the plan/user brief as its own entry.
4. Also add the plan-level rule that the same voice applies to the plan and all planned artifacts (SOUL, AGENTS, notes, reports, future templates). Individual style bullets do not cover that meta rule.
5. Document `coverage_method` in the ledger wrapper.

For each clause, record:

| Field | Purpose |
|---|---|
| `id` | Stable ID (e.g. `SRC-014`) |
| `source_file` | Absolute path of the original file |
| `original` | Exact source clause |
| `meaning` / `strength` | What it requires; must/must_not/may/prefer |
| `new_file` / `new_section` | Destination |
| `new_text` | Plain-language replacement |
| `action` | `keep` \| `split` \| `move` \| `clarify` only |
| `review` | `same_meaning` \| `failed` |

Ledger field shapes: `references/ledger-template.md`. Acceptance: 100% coverage; unique IDs; no `drop`; shorter ≠ weaker/broader/less precise; every entry `review: same_meaning` before rewrite.

When building entries from maps/tuples, keep pack and unpack arity identical. A length mismatch aborts the whole ledger.

### 3. Rewrite

- Rewrite in plain language and this voice; keep governed files ≤ 200 lines (compress blanks first, then progressive disclosure).
- If the plan rewrites SOUL, add a short voice section that carries the rules and checker data into future replies and artifacts.
- The plan itself must state that the same voice applies to SOUL, AGENTS, notes, reports, and future templates, not only the plan body.
- Moves must name the new owner (SOUL vs AGENTS vs skill vs Obsidian). Keep one canonical owner for runbooks and standards; sibling notes may link and summarize, not host a second executable checklist.
- Prefer short live bullets over packed compounds. When one source clause becomes several bullets, set `action` to `split` and use a `targets` array (see `references/ledger-template.md`).
- Update ledger entries as text lands. After each material rewrite pass, re-read the live section and remap every entry whose `new_text` no longer appears verbatim.
- Diff against backups; explain each block via ledger IDs.

### 4. Validate and review

- Focused checks: line limits, sections, hashes, ledger coverage, links, secrets, context loading when relevant.
- Target presence: every ledger target string must be a substring of its live file. Recompute entry `strength` as `mixed` when sibling targets disagree on force.
- Voice scan on prose only: blocked terms, banned closers, em/en dashes, stiff forms (`Do not` / `is not` / `cannot` when a contraction fits), contractions present, even-rhythm warnings. Skip fenced test-data blocks, exact quotes, backups, and raw command output. See `references/voice-check.md`.
- Clarity pass: read each rule aloud. Fail unclear or awkward grammar even when term lists are clean. Prefer subject + owner + action (`Define a different role for each named profile in that profile's SOUL.md`) over compressed slogans that hide who does what.
- Confirm ledger `new_section` and target text match the live headings and wording after every fix.
- Ad-hoc verifiers must copy literal live wording after a `read_file` of the real lines. Never invent backticks, phase labels, or paraphrases for order checks. On exact-string FAIL, re-read the live line first; do not retry the same guessed needle.
- Temporary verifier scripts run from a temp path and delete before the task is done. Leave no `hermes-verify-*.py` residue.
- Independent read-only review is required before final PASS. Procedure: `references/final-validation.md`.
- Require every entry `same_meaning` and voice compliance. Fix and revalidate on any fail.
- Label ad-hoc validation honestly; do not claim full-suite green.
- Do not run mutating doctor/fix commands (`hermes doctor --fix`) during a no-side-effects reconciliation unless the plan explicitly allows them. Unrelated advisories may stay noted without a fix.

## Common pitfalls

1. **Leaving SOUL dense because an earlier plan said “byte-identical.”** If the user asks for plain wording with full meaning, allow rewrite under a complete ledger.
2. **Hashing files not created yet.** Baseline marks future paths absent.
3. **Vague summaries.** “Keep skill rules” is not enough; enumerate the rule classes or map each clause.
4. **Dropping exceptions.** Narrow exceptions (e.g. scratch work without GitHub CI) must survive as explicitly narrow.
5. **Chat-context dependence.** Artifacts must stand alone.
6. **Plain language without voice.** Dead-simple alone is not enough when the user asked for human voice. Contractions, rhythm, and banned terms are required too.
7. **Voice only on the plan.** If the plan rewrites SOUL/AGENTS/notes/reports, those targets must get the same voice, and validation must scan them.
8. **Scanner false positives.** Put blocked-term lists in fenced test-data blocks. Do not leave them bare in prose.
9. **Line-limit creep after voice pass.** Compress blank layout first; do not drop rules to hit 200 lines.
10. **Partial bullet coverage.** Hand-picking “important” SOUL/AGENTS bullets fails Task 1. Enumerate every bullet and split multi-rule paragraphs.
11. **Missing meta voice entry.** Listing style rules without a separate entry for “same voice on plan + all planned artifacts” is incomplete coverage.
12. **Map/tuple arity bugs.** When a builder map packs five fields and the loop unpacks six, the ledger dies mid-run. Keep pack and unpack shapes identical, then re-parse JSON.
13. **Calling Task 1 done with source drift or leftover builders.** Re-hash sources after writing reports. Remove temporary builder scripts. Backups must stay mode `0600` and byte-identical.
14. **Remote secrets in baseline.** Record remotes by name only; never paste credential-bearing remote URLs into baseline or reports.
15. **Overclaiming verification.** Label ad-hoc JSON/schema/hash checks as ad-hoc. Do not claim full-suite green when none exists.
16. **Awkward but ledger-passable phrasing.** `Keep every review gate above mandatory` keeps the idea and still fails clarity. Prefer `Every review gate in the skill rules above is mandatory`. After any wording fix, update matching ledger `new_text` and target texts in the same edit.
17. **Grammar as an afterthought.** Voice scans for banned words are not enough. Read each rule aloud. If the sentence is stiff, inverted, or hard to parse, rewrite it before review.
18. **Stale ledger locations.** After section renames or ownership rewrites, update every entry's `new_section` and target text to the live headings. A correct bullet under a wrong section name fails review.
19. **Narrow term for a broad exception.** If the source exception covers commit, push, publish, deploy, and CI, say `scratch work` for those gates. Keep `scratch code` only where mise, tests, TDD, or code durability is the real topic.
20. **Combined targets after live splits.** Packing several rules into one ledger `new_text` fails as soon as the live file is split into short bullets. Remap to one target per live bullet, set `action: split`, and re-check substring presence for every target.
21. **Guessed verifier needles.** Building checks from memory (`Follow \`BOOTSTRAP\`` vs live `Follow BOOTSTRAP`) creates false FAILs and tool loops. Copy the exact live string after reading the file.
22. **Duplicate executable standards.** If AGENTS and two vault notes describe the same runbook, pick one owner for the checklist and make the others link. Dual full checklists drift.
23. **Order-sensitive workflows without order proof.** Sequences such as BOOTSTRAP, then RED, then GREEN, then REFACTOR, then focused tests need both presence and relative position checks against live text.
24. **Final PASS while independent review is still BLOCKED.** Human `VALIDATION.md`, machine `final-validation.json`, and `independent-review.json` must agree. Do not claim overall PASS until the independent review is PASS with empty `failed` and `required_fixes`.
25. **Stale evidence counts after adding review artifacts.** When the final voice scan gains `independent-review.json` or another governed report, update the human report counts in the same closeout. `covered 10` is wrong if the scan scope is 11.
26. **Post-scan prose edits without a recheck.** Any wording fix in a scanned report after the final voice scan needs a voice recheck of that file, then a consistency check that human report, machine report, hashes, and review status still match.
27. **Mutation tools on the independent reviewer.** The independent reviewer must have no file write, patch, terminal mutation, or skill_manage tools. Prefer a read-only `search` toolset and a prebuilt source packet. Save the toolset claim in `independent-review.json`.
28. **Silent doctor auto-fix during no-side-effects work.** `hermes doctor --fix` can change session/DB state. Record exit 0 and advisories; do not auto-fix unless the plan allows it.
29. **Docs inventory nav parse too weak.** Relative path scrapes of `llms.txt` miss absolute `https://hermes-agent.nousresearch.com/docs/...` links. Use markdown destinations, then alias residual `/index` and guide redirects against real markers (see `references/hermes-docs-inventory.md`).
30. **Clearing unmatched nav without a real source.** Aliases must point at an existing `<!-- source: ... -->` path. Prefer documenting the alias over changing the global URL transform for one redirect.
31. **Stale review packet after a fix.** After any post-review edit to live targets or evidence, rebuild the source packet and recompute its integrity hash before the next review cycle or final PASS. Correct live files with stale packet metadata are still BLOCKED.
32. **Component PASS sold as whole-rewrite PASS.** Focused ledger or voice checks never prove the full rewrite. Keep subtask and whole-change status separate in the final report.

## Support files

- `references/ledger-template.md` — ledger field shapes and reviewer rules
- `references/voice-check.md` — blocked terms, scan scope, and acceptance checks
- `references/baseline-task.md` — Task 1 baseline/backup/ledger acceptance recipe
- `references/hermes-docs-inventory.md` — live docs inventory + primitive catalog for complete-coverage plans
- `references/final-validation.md` — independent review, final reports, hash closeout

## Verification checklist

- [ ] Baselines and owner-only backups recorded before edits; sources re-hashed unchanged
- [ ] Ledger covers 100% of original clauses, every bullet, and new voice rules (including the meta same-voice rule); no `drop`
- [ ] Every entry `same_meaning` after independent review
- [ ] Plain-language + voice standard applied to plan and planned artifacts
- [ ] Every sentence is clear and grammatically natural on a plain reading
- [ ] Voice scan clean on prose (see `references/voice-check.md`), including final report strings and independent-review prose fields when present
- [ ] Governed Markdown ≤ 200 lines each
- [ ] Paths/commands/hashes exact; secrets and credential URLs absent
- [ ] Temporary builder scripts removed
- [ ] Every ledger target string still present in its live file after the last rewrite pass
- [ ] Independent review PASS with read-only toolset only; `independent-review.json` saved
- [ ] Frozen packet integrity matches the latest live packet when a review packet was used
- [ ] Human and machine final reports agree on PASS/BLOCKED and evidence counts; subtask and whole-change status stay separate
- [ ] Focused validation written as PASS/BLOCKED with evidence (ad-hoc labeled honestly)
