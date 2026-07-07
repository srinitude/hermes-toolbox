---
name: first-setup
description: "Plain-language Hermes tutorial content for First Setup."
version: 0.1.0
author: Kiren Srinivasan
license: Apache-2.0
---

# First Setup

This bundled tutorial skill belongs to `hermes-setup-coach`.

## Purpose

Get one plain Hermes chat working first, then add tools, profiles, gateways, and automations gradually.

## How to use it

1. Read the concept in plain language.
2. Verify current behavior against official Hermes docs or live `hermes --help` / `hermes <command> --help` output.
3. Try the smallest safe exercise first.
4. Stop and ask for help before pasting secrets, editing credential stores, or touching runtime state.

## Safety checklist

- Profiles are not operating-system sandboxes.
- Secrets belong in setup/auth flows, not chat or tutorial files.
- Prefer official `hermes config`, `hermes tools`, `hermes auth`, `hermes mcp`, `hermes gateway`, and `hermes cron` commands over direct edits.
- Validate completion with real command output.

## When to Use

Use this bundled tutorial skill when a learner is practicing the related Hermes concept and needs a short, safe procedure. Load it before making changes so the learner sees the vocabulary, write boundaries, and validation habit for this topic. Prefer it for explanation, rehearsal, review, or assessment prompts.


## Practice Exercise

1. State the task objective in one sentence.
2. Identify whether the next step is read-only, plan-only, or a write/execute action.
3. Name the exact allowed write surface if a write is required.
4. Name at least one source-of-truth check, such as official Hermes docs or live CLI output.
5. Define the smallest validation threshold that proves the step worked.


## Validation

- Check official Hermes documentation when the lesson makes a product claim.
- Check `hermes --help` or `hermes <command> --help` when the lesson mentions a command.
- Treat tutorial examples as starting points, not authority over the live install.
- Stop when the validation threshold is met; do not add adjacent work.


## Safety Boundaries

- Do not paste secrets, API keys, OAuth tokens, passwords, or private endpoint URLs into tutorial answers.
- Do not edit credential stores, runtime databases, sessions, logs, caches, pairing state, or generated backups.
- Prefer official Hermes setup, auth, config, tools, MCP, gateway, and cron commands over raw file edits.
- Use placeholders such as `$HERMES_HOME`, `$HOME`, `<profile>`, `<plugin>`, and `example.com` in reusable examples.


## Review Questions

- What problem does this Hermes concept solve?
- Which lighter primitive should be tried before escalating to a plugin or automation?
- What proof would convince a skeptical reviewer that the lesson was completed safely?
