---
name: openrouter-mcp-server
description: "Use when routing Hermes subagent work through OpenRouter models selected by OpenRouter MCP. Enforces live MCP-backed model selection from the max output price $5 and max age 270 day model universe, and uses independent Hermes child processes when per-subagent model choice is required."
version: 0.1.1
author: Kiren Srinivasan
license: Apache-2.0
metadata:
  hermes:
    tags: [openrouter, mcp, subagents, model-routing, delegation]
    related_skills: [hermes-agent, prompt-enhancer]
---

# OpenRouter MCP Server

## Overview

Use this skill to let the currently selected Hermes main model act as an orchestrator while OpenRouter's MCP server provides live model catalog data for subagent model selection.

The allowed model universe is exactly the OpenRouter model catalog slice represented by:

```text
https://openrouter.ai/models?max_output_price=5&max_age_days=270
```

The orchestrator must not choose a subagent model outside that universe. A model is eligible only when OpenRouter MCP data verifies that it satisfies both constraints:

- output price is `<= $5 / 1M output tokens` or the MCP-equivalent pricing unit;
- model age is `<= 270 days`, or the MCP-equivalent release/created date proves it is within that window.

Hard Hermes limitation: the built-in `delegate_task` tool does **not** select a different model per child. Child tasks inherit the parent model unless delegation is globally pinned in config. When per-subagent model routing matters, spawn independent Hermes child processes with `hermes chat --provider openrouter --model <verified-model-slug> ...` and treat those processes as model-routed subagents.

## When to Use

Use this skill when:

- The user asks Hermes to route subagents to the "right" OpenRouter model for each job.
- The main Hermes model should remain currently selected, but children should use different OpenRouter models.
- The task requires current model prices, ages, context windows, capabilities, benchmarks, endpoint latency, or provider availability.
- The user imposes the allowed model universe `max_output_price=5&max_age_days=270`.

Do not use this skill when:

- The user wants a normal `delegate_task` child that inherits the current model.
- The user has not configured OpenRouter MCP and does not want to configure it.
- A model can be chosen from a fixed user-supplied slug without routing or comparison.
- The task requires a model outside the allowed universe; report that no eligible model may be selected instead of expanding the filter.

## Prerequisites

### OpenRouter provider key

Hermes child processes need OpenRouter provider access:

```bash
# Configure OPENROUTER_API_KEY through the official setup/auth/env flow, not as a non-secret config key
hermes config check
```

Completion criterion: `hermes config check` shows `✓ OPENROUTER_API_KEY`.

### OpenRouter MCP server

Configure the remote OpenRouter MCP server through Hermes' native MCP client:

```bash
hermes mcp add openrouter --url https://mcp.openrouter.ai/mcp --auth oauth
hermes mcp login openrouter
```

If `hermes mcp add` runs in a non-interactive environment and reports that no cached OAuth token exists, save the config anyway if prompted, then ensure the non-secret config is enabled through the official config CLI:

```bash
hermes config set mcp_servers.openrouter.auth oauth
hermes config set mcp_servers.openrouter.enabled true
hermes mcp login openrouter
```

### Remote VPS / local browser OAuth

If Hermes runs on a VPS and the browser is on a local computer, a callback URL like `http://127.0.0.1:<port>/callback?...` points to the local computer, not the VPS. Use one of these official remote-host patterns:

1. **Paste-back flow:** keep `hermes mcp login openrouter` running in the interactive VPS terminal, open the authorize URL locally, let the local browser fail on `127.0.0.1`, copy the full final redirect URL, and paste it back into the waiting VPS terminal prompt. Do not paste it into chat; the PKCE verifier lives in the waiting login process.
2. **SSH port-forward flow:** before starting login, forward the callback port from local to VPS, e.g. `ssh -N -L 52591:127.0.0.1:52591 user@vps`, then run `hermes mcp login openrouter` on the VPS and complete the browser flow locally.

Then restart Hermes or start a fresh session so MCP tools are discovered.

### Disable billable chat-send tool

The OpenRouter MCP server advertises `chat-send`, which performs a real model inference and can spend credits. For routing workflows, keep it filtered out at the MCP client layer so it is not exposed to Hermes agents by default.

Preferred interactive path:

```bash
hermes mcp configure openrouter
# uncheck chat-send, keep the read-only catalog/status tools enabled
```

Expected user config shape:

```yaml
mcp_servers:
  openrouter:
    url: https://mcp.openrouter.ai/mcp
    enabled: true
    auth: oauth
    tools:
      exclude:
        - chat-send
```

Do not use `hermes config set mcp_servers.openrouter.tools.include '[...]'` for this list: `hermes config set` treats that JSON-looking value as a string on current Hermes versions, and the MCP filter will not behave as intended. Use the supported interactive command instead:

```bash
hermes mcp configure openrouter
```

If an interactive configuration session is unavailable, stop and ask the operator to run that command rather than editing Hermes config or credential files directly.

Completion criterion: OpenRouter MCP tools appear with the `mcp_openrouter_` prefix, but `mcp_openrouter_chat_send` does **not** appear. Expected read-only tools include:

- `mcp_openrouter_models_list`
- `mcp_openrouter_model_get`
- `mcp_openrouter_model_endpoints`
- `mcp_openrouter_benchmarks`
- `mcp_openrouter_docs_search`
- `mcp_openrouter_ping`

Validate the configured server and authentication with supported Hermes commands:

```bash
hermes mcp list
hermes mcp test openrouter
```

Then start a fresh Hermes session and confirm that the expected read-only OpenRouter tools are present while `chat-send` remains excluded.

If tools are not visible, do not pretend model routing is MCP-backed. Tell the user to restart Hermes or complete `hermes mcp login openrouter`.

## OpenRouter MCP Tool Policy

Prefer read-only tools for routing:

| MCP tool | Hermes tool name pattern | Use |
| --- | --- | --- |
| `models-list` | `mcp_openrouter_models_list` | Find eligible candidates with filters. |
| `model-get` | `mcp_openrouter_model_get` | Verify one model's pricing, age, context, and capabilities. |
| `model-endpoints` | `mcp_openrouter_model_endpoints` | Check provider pricing, latency, throughput, and data policy. |
| `benchmarks` | `mcp_openrouter_benchmarks` | Compare task-relevant quality scores. |
| `rankings-daily` | `mcp_openrouter_rankings_daily` | Use popularity/trend only as weak supporting evidence. |
| `docs-search` | `mcp_openrouter_docs_search` | Resolve exact OpenRouter API/MCP parameter questions. |
| `credits-get` | `mcp_openrouter_credits_get` | Check available credit when the user asks or before billable tests. |
| `providers-list` | `mcp_openrouter_providers_list` | Understand provider routing choices. |

Billable tool rule:

- `chat-send` sends a real inference request and can spend the MCP key's balance.
- Keep `chat-send` excluded from `mcp_servers.openrouter.tools` for normal routing workflows.
- If a user explicitly approves a billable MCP model test, temporarily re-enable `chat-send` only for that test, then disable it again before finishing.
- If `chat-send` is used, retrieve cost evidence with `generation-get` and include it in the final report.

## Model Eligibility Gate

Before launching any subagent with a model slug, pass this gate:

1. Query OpenRouter MCP for candidates with filters equivalent to:
   - `max_output_price <= 5`
   - `max_age_days <= 270`
2. If the `models-list` schema is unknown, call `mcp_openrouter_docs_search` for the exact `models-list` filter names.
3. Verify the selected slug with `model-get`.
4. When endpoint choice matters, verify endpoint data with `model-endpoints`.
5. Record an evidence row:

```markdown
| Job | Selected model | Output price | Age/release evidence | Key capabilities | MCP evidence |
| --- | --- | ---: | --- | --- | --- |
| job-id | provider/model-slug | <= $5/M | <=270 days | coding/tool-calling/etc. | models-list + model-get |
```

6. If a candidate cannot be proven inside the allowed universe, reject it.
7. If no eligible candidate fits a job, report the blocker. Do not widen the filter without user permission.

Never select a model from memory, training data, blog posts, leaderboards, or the unfiltered OpenRouter catalog.

## Routing Procedure

### 1. Decompose the work

Split the user request into subagent jobs. For each job, write a one-sentence job brief and classify requirements:

- task type: coding, review, planning, research, data extraction, creative, vision, long-context, etc.;
- input modality: text, image, file, audio, video;
- output constraints: JSON/schema, code patch, prose, citations, tests;
- context length needed;
- tool needs;
- latency vs quality vs cost preference;
- privacy/data-retention needs;
- whether a billable test prompt is worth asking about.

Completion criterion: every subagent job has explicit model-selection criteria.

### 2. Query OpenRouter MCP

For each job, call `models-list` with the hard eligibility filters and task-relevant filters when available.

Example intent, not a guaranteed schema:

```json
{
  "max_output_price": 5,
  "max_age_days": 270,
  "supports_parameters": ["tools", "structured_outputs"],
  "modality": "text",
  "query": "coding agent unit test generation"
}
```

If the actual schema differs, inspect it through the MCP tool description or `docs-search`; do not guess field names repeatedly.

Completion criterion: candidates come from OpenRouter MCP, not model memory.

### 3. Score and choose

Pick the lowest-risk eligible model for each job:

1. Hard constraints first: eligibility, modality, context, required parameters.
2. Quality signals second: benchmarks relevant to the job.
3. Endpoint health third: latency, throughput, provider availability, data policy.
4. Cost last among models that satisfy the job; prefer cheaper/faster models when quality is likely sufficient.

Completion criterion: each chosen model has a short rationale tied to MCP evidence.

### 4. Launch model-routed subagents

Use independent Hermes child processes when per-subagent model selection is required. The child process does **not** need OpenRouter MCP tools after the orchestrator has selected and verified the model, so prefer an isolated child invocation that disables unnecessary customizations and reduces shutdown/crash risk.

Before launching a batch, run this minimal billable child-process preflight once in the same environment only when the user has approved that inference within the routing spend scope:

```bash
set +e
hermes chat -Q --ignore-rules --source tool -q 'Reply exactly HERMES_CHILD_PREFLIGHT_OK.'
printf 'child_preflight_exit=%s\n' "$?"
```

Completion criterion: output contains `HERMES_CHILD_PREFLIGHT_OK` and `child_preflight_exit=0`. If the child exits non-zero, especially `134` / `Aborted (core dumped)`, do **not** launch model-routed subagents yet. Report the blocker, restart/reload Hermes if appropriate, or fall back to inherited-model `delegate_task` only if the user accepts losing per-child model routing. Without billable-preflight approval, skip the synthetic inference and use the first actual approved child job as the health gate before launching the rest of the batch.

Bounded one-shot pattern from a Hermes tool call:

```python
terminal(
    command=(
        "hermes chat -Q --safe-mode --source tool "
        "--provider openrouter "
        "--model '<verified-model-slug>' "
        "--toolsets '<comma-separated-toolsets>' "
        "-q '<self-contained task brief>'"
    ),
    workdir="<project-root>",
    background=True,
    notify_on_complete=True,
)
```

Use `--safe-mode` by default for model-routed children because the prompt is self-contained and the child does not need MCP, memory, plugins, or project rules to select its model. If the job explicitly needs project context files or skills, use `--ignore-rules` only after a preflight with that exact flag exits `0`.

Shell safety requirements:

- Quote dynamic model slugs, paths, and prompts with `shell_quote` or equivalent.
- Do not put API keys or secrets in the prompt.
- Include the write scope and validation threshold in each child prompt.
- Tell the child not to switch models; the orchestrator owns model routing.
- Use `notify_on_complete=True` for bounded work.
- Treat any non-zero child exit code as a failed subagent even if it printed plausible output.

Interactive or long-running pattern:

- Prefer Hermes `terminal(background=True, notify_on_complete=True)` for bounded long-running child jobs so lifecycle and output remain tracked.
- For a genuinely interactive child, use `terminal(pty=True)` in the foreground and keep the session attached.
- Do not require `tmux`; if the user explicitly requests it, first verify `command -v tmux` and treat it as an optional operator dependency.

Completion criterion: each child process command uses `--provider openrouter --model <verified-slug>`, exits `0` for bounded jobs, and the slug appears in the evidence table.

### 5. Use `delegate_task` only for inherited-model work

`delegate_task` is acceptable only when:

- all children may use the current parent model; or
- the user globally configured delegation to one model and per-child routing is not required.

Do not say `delegate_task` selected a child-specific OpenRouter model. It does not.

Completion criterion: per-child model claims always map to independent Hermes child processes, not `delegate_task`.

## Subagent Prompt Template

Use this structure for each model-routed child:

```markdown
You are a Hermes model-routed subagent.

## Assigned Model
Provider: OpenRouter
Model: <verified-model-slug>
Eligibility evidence: returned by OpenRouter MCP under max_output_price<=5 and max_age_days<=270.

## Objective
<one concrete job>

## Context
<only the context needed for this job>

## Scope
Allowed actions:
- <tool/file/actions>

Not in scope:
- Choosing or switching models
- Editing outside <paths>
- Reading raw secrets

## Validation Threshold
The job is complete only when:
1. <objective proof>
2. <test/tool output proof>
3. <safety proof>

## Required Output
Return a concise result with commands run, files changed, and blockers.
```

## Final Report Format

After all children finish, report:

```markdown
## Model Routing Evidence
| Job | Model | Why this model | Price/age proof | MCP tools used |
| --- | --- | --- | --- | --- |

## Subagent Results
- <job>: <result, validation, blockers>

## Safety Notes
- Confirmed no model outside `max_output_price=5&max_age_days=270` was used.
- Confirmed whether `chat-send` was avoided or explicitly approved.
```

## Common Pitfalls

1. **Using `delegate_task` for per-child model choice.** It cannot do that. Use independent Hermes child processes for model-specific children.
2. **Picking models from memory.** Always call OpenRouter MCP and verify the hard filters.
3. **Forgetting the model age constraint.** Price alone is insufficient; the model must also be within `max_age_days=270`.
4. **Treating `chat-send` as read-only.** It is a billable inference call. Keep it filtered out of MCP tools by default; temporarily re-enable only with explicit user approval and disable it again before finishing.
5. **Ignoring child-process exit codes.** A spawned `hermes chat` can print useful-looking output and still fail on shutdown. Always capture/inspect the exit code; treat `134` / `Aborted (core dumped)` as a blocker, not a success.
6. **Configuring MCP and expecting current-session tools instantly.** Restart Hermes or start a fresh session after adding or filtering the MCP server.
7. **Pasting a loopback callback URL into chat instead of the OAuth terminal.** A URL like `http://127.0.0.1:<port>/callback?...` must reach the `hermes mcp login openrouter` process that generated it. If the browser cannot connect, paste the full redirect URL back into that interactive terminal prompt; the agent usually cannot redeem it after the listener closes or when it runs on a different host.
8. **Reading raw token files.** Use `hermes mcp login`, `hermes mcp configure`, and status/list commands; do not inspect secret stores.
9. **Expanding the allowed model universe silently.** If no model fits, report the blocker and ask whether to change constraints.

## Verification Checklist

- [ ] OpenRouter provider key is configured via `hermes config set OPENROUTER_API_KEY ...`.
- [ ] OpenRouter MCP is configured with `hermes mcp add openrouter --url https://mcp.openrouter.ai/mcp --auth oauth`.
- [ ] OpenRouter MCP OAuth is completed with `hermes mcp login openrouter`.
- [ ] `mcp_servers.openrouter.tools.exclude` contains `chat-send`, or an equivalent MCP tool filter removes it.
- [ ] A fresh Hermes process can see read-only `mcp_openrouter_*` tools and cannot see `mcp_openrouter_chat_send`.
- [ ] A child-process preflight with the intended flags exits `0`; do not ignore `Aborted (core dumped)` / exit `134`.
- [ ] Every selected subagent model is returned by MCP under `max_output_price<=5` and `max_age_days<=270`.
- [ ] Every selected model is verified with `model-get` before launch.
- [ ] Every model-routed subagent command uses `--provider openrouter --model <verified-slug>`.
- [ ] `delegate_task` is not used to claim per-child model selection.
- [ ] `chat-send` is not used without explicit approval.
- [ ] Final report includes model routing evidence and validation results.
