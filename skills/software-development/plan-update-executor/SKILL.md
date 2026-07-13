---
name: plan-update-executor
description: Reconcile and execute plan update requests.
version: 0.2.2
author: Kiren Srinivasan
license: Apache-2.0
metadata:
  hermes:
    tags: [Plans, Execution, Reconciliation, Validation, Safety]
---

# Plan Update Executor

Use this skill to turn any plan-update request into a grounded reconciliation pass, then execute it in the same session. It does not stop at drafting a stronger prompt unless the user explicitly asks for prompt text only. It is domain-agnostic: Hermes plans, project plans, product specs, rollout plans, cost plans, research plans, and pasted planning documents all follow the same source-first workflow.

## When to Use
- User asks to update, revise, reconcile, refresh, harden, expand, or tighten a plan.
- User provides a plan path, URL, pasted plan, directory, prior-session reference, or "what we just did" as the plan source.
- User mixes sources and requirements in any order.
- User wants new criteria folded into the existing plan without losing content/context/intent/meaning.
- User asks for the plan file to be changed, or for the full reconciled plan to be returned.
- User invokes `/prompt-enhancer` around a plan-update prompt and expects the resulting task to be carried out.

## Prerequisites
- A target plan source: local file path, URL, pasted artifact, named directory, session reference, or explicit placeholder if the user intentionally wants a reusable prompt pattern.
- The full user request, including prose after paths or links; treat that prose as requirements, not incidental context.
- Access to `read_file`, `search_files`, `web_extract`, `web_search`, `session_search`, `patch`, `write_file`, and `execute_code` as needed.
- No credentials are required. Do not read secrets, token stores, raw OAuth files, payment data, or unrelated profile/runtime data.
- For Hermes Agent claims, validate against `https://hermes-agent.nousresearch.com/docs/`, `https://github.com/NousResearch/hermes-agent`, and live Hermes CLI/tool output when checking the local install.
- For non-Hermes domains, prefer first-party docs, official pricing pages, source repositories, vendor docs, project files, or primary sources named by the user.

## How to Run
First use the `prompt-enhancer` discipline internally: make the objective, allowed writes, prohibited writes, sources, and validation threshold explicit. If the user explicitly invokes `/prompt-enhancer`, or the revised plan can later create or modify source/tests, load the current `prompt-enhancer` skill rather than relying on memory and propagate its active coding contract into the plan's implementation and validation sections. Then execute that brief immediately unless the user asked for prompt text only or a safety ambiguity blocks execution. Use `read_file` for local plan files, `search_files` to recover missing paths or inspect named directories, `web_extract` for URLs and official docs, `web_search` for current external facts when no URL is supplied, `session_search` only for referenced prior conversation context, and `patch` or `write_file` to change only the target plan when file mutation is in scope.

## Quick Reference
- `read_file path="<plan_path>"`
- `search_files pattern="<filename-or-plan-glob>" target="files" path="."`
- `web_extract urls=["<named_url_or_first_party_doc>"]`
- `web_search query="<current fact or UX/pricing/tooling claim>"`
- `session_search query="<prior conversation topic>"`
- `patch path="<plan_path>" old_string="..." new_string="..."`
- `write_file path="<plan_path>" content="<full_reconciled_plan>"`
- `execute_code` for banned-term scans, source coverage checks, or final artifact validation.

## Procedure
1. **Extract the operative brief.** Identify the user outcome, target plan source, sources to gather, requirements to enforce, write scope, prohibited surfaces, and validation threshold. Continue prior session work unless the user explicitly resets it. Done when every field is known, explicitly assumed, or identified as a blocker.

2. **Partition sources from requirements.** Build two lists, but treat every sentence as load-bearing. Text after a file path, directory, URL, or pasted artifact is a requirement about how to use that source. Done when every path, URL, pasted note, conversation reference, constraint, banned term, output format, and validation demand is accounted for.

3. **Resolve the target plan.** Use `read_file` for a concrete local path. If it fails, use `search_files` in the workspace and relevant plan directories before treating the path as unavailable. Use `web_extract` for a plan URL, the pasted text for a pasted plan, and `session_search` only when the user points to prior conversation rather than a direct source. Done when you can honestly state whether the plan was read, recovered, extracted, pasted, or unavailable.

4. **Gather source-of-truth evidence.** Match validation sources to the request's domain. Use official Hermes docs/repo only for Hermes claims; project files for project claims; first-party product docs for vendor/tooling claims; official pricing pages for costs; current web research for UX, market, or tool availability claims. Inspect a user-supplied live dashboard/project URL before relying on conversation history. If it requires authentication, record the observable anonymous result and safe CLI/auth state, add an explicit OAuth/access gate, and treat claimed remote contents as requirements to verify rather than current proof. When a supplied artifact labels host state, versions, settings, or availability as **current**, **live**, or **canonical**, recheck those claims through safe live reads when possible. Live read-only evidence governs current-state sections; preserve a conflicting supplied value only as historical input and record the discrepancy in the plan's audit record. “Canonical” does not freeze stale operational facts. When a skills catalog/group and its official source repository disagree, enumerate the advertised capability set, inspect the current repository layout, use the current official contract as authoritative, and preserve requested coverage through a capability matrix instead of installing stale decomposed skills. Done when each factual change has a supporting source or a clearly labeled assumption/blocker.

5. **Reconcile, do not drift.** Read the full current plan before changing it. Preserve existing content, context, intent, dependencies, assumptions, approval gates, and meaning unless a user criterion explicitly supersedes them. Remove contradictions introduced by the new criteria. When a new source describes a broader capability than the existing plan permits, keep the stricter non-contradictory safety boundary unless the user explicitly replaces it. Reconcile the broader primitive as maintenance-, certification-, or acceptance-only when that preserves both requirements; never convert a generic capability description into operational authority by implication. Do not silently delete safety gates, cost caps, privacy constraints, or validation requirements. Done when the plan reads as one coherent canonical artifact.

6. **Apply request-specific rules only.** Add domain rules only when the user asked for them. Examples include Kanban lifecycle, profile-builder assumptions, one-default-path UX, no raw IDs/JSON, model/cost validation, hardware removal, privacy gates, or banned wording. Do not import constraints from old examples or prior tasks unless they apply to the current plan. Done when every added rule traces to the current request, project context, or a required safety boundary.

7. **Write or return the artifact.** If the user asked to mutate a file and the path is an allowed write surface, update only that target plan with `patch` for scoped changes or `write_file` for a full reconciled replacement. If the user asked for output only, do not write; return the full requested artifact. If the user asked for both, do both. Done when the requested artifact exists in the requested place or is printed in the requested format.

8. **Validate the result.** Use a focused check appropriate to the request: re-read the changed plan, scan for banned terms, confirm all criteria appear, confirm no unrelated example-specific constraints leaked in, verify links or first-party claims, and check that write boundaries were respected. Use `execute_code` for deterministic scans when useful. For large plans, read the complete artifact in explicit chunks and run the final scanner against the canonical raw file text/bytes rather than a rendered preview or truncated tool wrapper. If a validator suddenly reports widespread unrelated failures, inspect the validator's actual input before treating the artifact as broken; rerun against the canonical path and include raw size, line count, fence balance, secret scan, and digest in the evidence. Done when objective evidence proves the plan satisfies the brief.

9. **Report concise evidence.** Final output should match the user's requested format. If they asked for the full plan verbatim, return that and no changelog. Otherwise include the target path, what was executed, and validation evidence. Done when the final answer is grounded in actual tool output and does not promise later work.

## Pitfalls
- Do not stop after writing an improved prompt; execute the plan-update task unless the user explicitly asked for prompt text only.
- Do not overfit to the sample request that originally taught the workflow. Kanban, multiple boards, profile-builder, one-default-path UX, and hidden IDs belong only in plans that ask for those ideas.
- Do not treat a file path as the whole request; text around it often defines the real criteria.
- Do not fetch the first source and ignore the rest.
- Do not treat a private dashboard's anonymous `404` or login wall as proof that the named remote project/resource is absent. Preserve the supplied IDs, record the access blocker, and add a safe OAuth/read-only verification gate.
- Do not assume a skills marketplace/group page and its official repository expose the same installable shape. Reconcile catalog drift explicitly: current official source wins for execution, while every user-requested legacy capability remains accounted for in a coverage ledger.
- Do not paraphrase `prompt-enhancer` from memory when it was explicitly invoked or the plan includes code implementation. Load it and carry forward its current structural/TDD contract.
- Do not claim a missing plan was read. Search for it, then label it unavailable, recovered, or placeholder-based.
- Do not use `session_search` as primary proof when the user supplied a direct file path, URL, app, repo, or live source.
- Do not return a changelog when the user asked for a full reconciled artifact.
- Do not let "validate with web tooling" become generic filler. Name which claims need web validation and which first-party sources count.
- Do not loosen approval, payment, credential, privacy, publishing, or external side-effect gates while reconciling a plan.
- For long-running public-repository plans, do not treat per-package atomicity as whole-batch atomicity, fingerprint an unrestricted filesystem walk, or trust a candidate report without validating its path contract and manifest agreement.
- Do not claim completion at local-green state when the plan requires PR checks, merge, remote-state verification, original-checkout reconciliation, or an explicit publisher-state decision.
- When a focused execution request exposes a source defect and the user chooses “update the saved plan only,” that choice supersedes earlier blanket execution/publication language for the current turn. Preserve the existing plan path, pin the live/public versions and blocker, encode the smallest future remediation as a separate approval gate with rollback and validation, and perform no source edit, branch, export, commit, PR, or upload.
- For destructive requests such as “remove outdated packages,” do not collapse digest-stale, semantically invalid, dependency-broken, and merely superseded into one label. Build the exact package matrix first, present materially different deletion/update outcomes with final manifest counts, and obtain a concrete scope choice before deleting or publishing.
- Recompute dependency closure after every withdrawal decision using the exact retained package bytes. A retained skill that imperatively says to load a withdrawn peer is not standalone merely because it restates part of that peer's procedure or lists the peer only as `related_skills`; witness a focused semantic RED before broad validation, then withdraw or separately remediate the dependent package.
- Keep NUL change lists, logs, and other binary verification artifacts outside the repository root. Otherwise whole-repository public-safety validators can correctly reject the verification artifact itself and obscure the package result.
- A package withdrawal must also clean tracked default/fallback selectors and public config examples. A clean clone lacks local `.git/info` overrides, and an example can remain invalid after the package name is removed if it still uses an obsolete config key. Add focused RED→GREEN contracts for both surfaces.
- After withdrawing a package, replace any test that uses it as an “unselected other package” sentinel; otherwise the assertion can pass vacuously because the fixture no longer contains that package. Use a distinct retained manifest package and assert the sentinel itself is real.
- Separate hard dependency closure from advisory ecosystem references. Mandatory load/install/`skill_view`/marker contracts must resolve in the final manifest or bundled runtime. Treat `related_skills` as public discovery metadata: remove withdrawn package names and cover that rule with a regression test. Neutral external-workflow prose may remain only when it is neither discovery metadata nor a mandatory install/load/runtime instruction.
- Make the reintroduction boundary explicit: current-repository removal is not a permanent tombstone. If permanent withdrawal is required, add a tracked deny policy and tests for every selection surface; otherwise preserve explicit manual selection semantics and keep automation paused.
- Bind independent review to a fully staged snapshot: no unstaged/untracked paths, exact staged path count, and a recorded `git diff --cached --binary` digest. Any remediation invalidates the verdict and requires fresh review; classify late async results by the digest/scope they actually reviewed.
- If canonical verification is not recognized, run a focused OS-tempfile verifier with a `hermes-verify-` prefix, label it ad-hoc rather than suite-green, clean it afterward, and prove it left no workspace residue.
- If a live candidate drifts after classification, re-hash and reclassify that exact candidate before commit even when it is currently selected for withdrawal. If the fresh isolated staged-public audit preserves the same disposition, update the evidence boundary and continue; if it changes the final dependency closure or publishability, return to the user's exact scope gate.
- Do not write outside the target plan, workspace `.hermes/plans/`, or explicitly approved output path.

## References
- `references/withdrawal-cleanup-review.md` — freeze staged withdrawal candidates by digest, audit repository-wide operational/discovery/test closure, and re-review after every remediation.
- `references/drift-safe-public-repository-execution.md` — execute mutable-source public-repository plans with candidate drift ledgers, whole-batch rollback, strict fingerprint scope, privacy review, dependency-closed withdrawals, tracked fallback/example cleanup, digest-bound staged reviews, ad-hoc verifier hygiene, idempotence, disposable installation, and remote reconciliation gates.
- `references/authenticated-sources-and-skill-catalog-drift.md` — reconcile private dashboard access, catalog/repository drift, capability coverage, and recording-backed workflow allowlists without inventing remote state.
- `references/large-plan-live-state-reconciliation.md` — reconcile canonical artifacts with newer live state, preserve stricter operational gates, and validate large plans against canonical raw bytes.
- `references/read-only-plan-gate-audits.md` — audit numbered implementation tasks and cutover gates without writes; separate committed, concurrent-worktree, and live-runtime evidence; produce exact artifact/test and approval matrices.

## Verification
A plan-update run is complete only when the target plan source was gathered or honestly marked unavailable; every user source and requirement was accounted for; appropriate first-party or primary-source validation was used; the plan was reconciled without unrelated example constraints; writes were limited to the approved target; the resulting artifact was re-read or otherwise checked; and the final response matches the user's requested output format.
