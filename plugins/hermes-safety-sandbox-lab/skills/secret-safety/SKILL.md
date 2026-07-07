---
name: secret-safety
description: "Plain-language Hermes tutorial content for Secret Safety."
version: 0.1.0
author: Kiren Srinivasan
license: Apache-2.0
---

# Secret Safety

This bundled tutorial skill belongs to `hermes-safety-sandbox-lab`.

## Purpose

Teach learners how Hermes should handle secrets safely: never paste credentials into chat, never commit them to public repos, and prefer the setup/auth/config flow that owns the credential.

## How to use it

1. Read the concept in plain language.
2. Identify the sensitive value, credential store, or runtime surface involved.
3. Choose a read-only verification step before attempting any write.
4. Use placeholders in examples and public docs.
5. Stop and ask for help before pasting secrets, editing credential stores, or touching runtime state.

## Safety checklist

- Profiles are not operating-system sandboxes.
- Secrets belong in setup/auth flows, not chat or tutorial files.
- Prefer official `hermes config`, `hermes tools`, `hermes auth`, `hermes mcp`, `hermes gateway`, and `hermes cron` commands over direct edits.
- Validate completion with real command output that does not reveal the secret value.

## When to Use

Use this bundled tutorial skill when a learner's task involves API keys, OAuth tokens, passwords, cookies, webhook secrets, private endpoint URLs, `.env` files, auth stores, MCP token stores, gateway pairing state, or any value that would be harmful if exposed. Load it before troubleshooting setup flows, creating public examples, or deciding whether a file can be read, edited, copied, committed, or shared.

## Practice Exercise

1. Name the action the learner wants Hermes to take.
2. Identify every secret-bearing surface that might be touched.
3. Replace any concrete credential or private URL in the explanation with a placeholder.
4. Choose the official setup/auth/status command that can verify the state without printing the secret.
5. State the stop condition: what would make the learner pause and ask for explicit approval?

## Validation

- Check official Hermes documentation when the lesson makes a product claim.
- Check `hermes --help` or `hermes <command> --help` when the lesson mentions a command.
- For public repo examples, scan for concrete keys, tokens, private URLs, private emails, and machine-specific absolute paths.
- For private setup, validate through status output or a successful non-secret operation, not by reading raw credential files.
- Stop when the validation threshold is met; do not add adjacent work.

## Safety Boundaries

- Do not paste API keys, OAuth tokens, passwords, cookies, private webhook URLs, or credential files into tutorial answers.
- Do not directly read or rewrite credential stores such as auth JSON files, token directories, project `.env*` files, or pairing state unless the user explicitly provides a safe redacted excerpt and the task requires it.
- Do not edit runtime databases, sessions, logs, caches, generated backups, or state files for normal troubleshooting.
- Prefer official Hermes setup, auth, config, tools, MCP, gateway, and cron commands over raw file edits.

## Review Questions

- What makes a value a secret rather than normal configuration?
- Which tool or command should own setup and validation for that secret?
- What proof would convince a skeptical reviewer that the task was completed without exposing the secret?
