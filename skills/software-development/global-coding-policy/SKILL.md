---
name: global-coding-policy
description: "Use when writing code or Markdown anywhere."
version: 1.1.1
author: Kiren Srinivasan
metadata:
  hermes:
    tags: [coding, markdown, mise, ci, tdd]
    related_skills: [hermes-agent, test-driven-development, meaning-preserving-rewrite]
    created_with_hermes_commit: 3f2a389c7e1f1729cad91ae63c26fb08c7753c74
    compatibility_reviewed_with_hermes_commit: 5988fe6cd5547d3620df1de889ac6007f5463b4d
---

# Global Coding Policy

## Scope and Triggers

Load this policy before writing or modifying code or Markdown anywhere, including outside repositories and projects. This includes files, temporary scripts, generated code, response snippets, tests, delegated work, and every terminal backend.

Apply its coding, structure, toolchain, and TDD rules to artifacts in directories Hermes recommends users customize or modify. Hermes-managed or core directories that Hermes prohibits or discourages users from altering are outside those user-area shape rules: do not modify those directories, and never treat this scope boundary as permission to write there. When work requires a Hermes core change, use a separate user-owned source checkout and follow the repository's contribution rules without rewriting existing core files solely to satisfy user-area size limits.

Apply only the sections triggered by the artifact:

- Any code work: apply all relevant coding, toolchain, TDD, and Hermes alignment rules below.
- Markdown-only work: enforce the 200-line limit and progressive disclosure; do not bootstrap code CI or TDD unless code is also written. When the user wants dead-simple wording without meaning loss on plans or policy Markdown, also load `meaning-preserving-rewrite`.
- Configuration/data-only work: preserve the schema and validate the format; the 200-line limit does not apply.
- `SKILL.md`: also enforce the description limit.
- Any test creation: create Mise tasks first.
- Code-test creation: also establish and exercise minimal local and GitHub CI/CD through Mise first.
- Delegated, scheduled, or background code/Markdown work: pass this policy onward and verify the result against it.

Use progressive disclosure after loading this baseline: load other task-specific skills and their linked files only when their triggers apply. Project rules may strengthen this policy but may not weaken the rules that apply in user-modifiable areas.

## Scope and Structure

- Limit every code and Markdown file governed by the user-area rules to 200 lines. When more Markdown context is needed, use progressive disclosure and reference another file.
- Configuration and data files are exempt from the 200-line limit. YAML, JSON, TOML, INI, XML, CSV, and comparable declarative formats may exceed 200 lines when their schema or data requires it.
- Keep the `description` frontmatter field in every `SKILL.md` under 60 characters.
- Limit each coding-language construct, including functions, classes, interfaces, and protocols, to 30 lines.
- Limit nesting depth to 3; in tests, measure depth relative to the test declaration.

## CI and Toolchains

- Write Mise tasks before writing any tests.
- Before writing code tests, establish minimal local and GitHub CI/CD powered by [Mise](https://mise.jdx.dev/) and test both CI paths.
- Use specialized Mise toolchains whose dependency graphs each have exactly one default path.

## TDD and Implementation

- Follow a BOOTSTRAP/RED/GREEN/REFACTOR, TDD-first workflow.
- Write tests before production code.
- Test only user-facing situations, contracts, APIs, integration boundaries, and interfaces—not implementation details or tests for their own sake.
- Use real tests, behavior, services, and functionality; never add TODOs, mocks, stubs, or placeholders.
- Add or change only the smallest necessary tests and production-code diffs, minimizing blast radius.
- Write only production code that passes the tests and is directly required to make them pass.
- Parallelize independent TDD workstreams when doing so conforms to the current Hermes Agent codebase.
- Prefer removing tests and their related code when removal solves the problem completely and correctly while preserving codebase conformity.

## Hermes Agent Alignment

- At the start of code work, identify the current Hermes Agent commit with `git -C ~/.hermes/hermes-agent rev-parse HEAD`.
- Comb through the relevant code at that commit and every relevant page of the [official Hermes documentation](https://hermes-agent.nousresearch.com/docs).
- Ensure all tests and code conform to the current codebase's shape while minimizing execution time and memory usage.
- Do not modify directories that would break Hermes Agent's installed shape or functionality; use a separate user-owned checkout for core source work.

## Ad-hoc verification (no suite)

When the workspace marks edits unverified and no canonical test/lint/build command exists:

1. Create a focused temporary verifier under an OS-safe tempfile dir with a `hermes-verify-` filename prefix (for example `tempfile.NamedTemporaryFile(..., prefix="hermes-verify-", delete=False)`).
2. Assert only the changed behavior: paths, sizes, hashes, boundaries, and report claims.
3. Run it, require exit 0, delete it, and confirm cleanup.
4. Label the result **focused ad-hoc verification, not suite green**. Never claim full CI green from this path.

If `write_file` refuses the system temp path (macOS `/private/var/folders/...` and similar sensitive paths), write the script with `execute_code` or `terminal` instead. Do not move the verifier into a project tree just to bypass the guard.

## Verification Checklist

- [ ] The policy was loaded before any code or Markdown was written.
- [ ] Every triggered section was applied in user-modifiable areas, including outside projects.
- [ ] No Hermes-managed or prohibited directory was modified.
- [ ] Every changed code or Markdown file governed by the user-area rules is at most 200 lines.
- [ ] Configuration/data files were schema-validated rather than line-limited.
- [ ] Every governed coding construct is at most 30 lines and nesting is at most 3.
- [ ] Mise, CI, and TDD gates ran in the required order when tests or production code were written.
- [ ] Hermes commit, source, and official docs were checked for code work.
- [ ] Delegated outputs were checked against this same policy.
- [ ] When no suite ran: hermes-verify temp script exited 0, was cleaned up, and the result was labeled ad-hoc not suite green.
