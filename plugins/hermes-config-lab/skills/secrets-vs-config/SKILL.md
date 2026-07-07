---
name: secrets-vs-config
description: "Plain-language Hermes tutorial content for Secrets Vs Config."
version: 0.1.0
author: Kiren Srinivasan
license: Apache-2.0
---

# Secrets Vs Config

This bundled tutorial skill belongs to `hermes-config-lab`.

## Purpose

Teach learners to separate normal Hermes configuration from sensitive credential material. Use `hermes config` for non-secret settings and setup/auth flows for secrets.

## How to use it

1. Read the concept in plain language.
2. Classify the setting as public config, private config, or secret credential material.
3. Verify current behavior against official Hermes docs or live `hermes --help` / `hermes <command> --help` output.
4. Try the smallest safe read-only exercise first.
5. Stop and ask for help before pasting secrets, editing credential stores, or touching runtime state.

## Safety checklist

- Profiles are not operating-system sandboxes.
- Secrets belong in setup/auth flows, not chat or tutorial files.
- Prefer official `hermes config`, `hermes tools`, `hermes auth`, `hermes mcp`, `hermes gateway`, and `hermes cron` commands over direct edits.
- Validate completion with real command output.

## When to Use

Use this bundled tutorial skill when a learner is deciding whether a value belongs in Hermes configuration, an environment file, an auth flow, or a placeholder in public documentation. Load it before any configuration change that might involve provider keys, OAuth state, webhook URLs, tokens, endpoint credentials, private paths, or user-specific identifiers.

## Practice Exercise

1. Name the value or setting the learner wants to configure.
2. Decide whether it is safe public configuration, private-but-not-secret configuration, or secret material.
3. Choose the safest surface: `hermes config` for non-secret settings, setup/auth flows for credentials, and placeholders for public examples.
4. State what must never be pasted into chat or committed to a repo.
5. Define the validation command that proves the setting is present without exposing the secret itself.

## Validation

- Check official Hermes documentation when the lesson makes a product claim.
- Check `hermes --help` or `hermes <command> --help` when the lesson mentions a command.
- For public repo examples, use placeholders such as `$HERMES_HOME`, `$HOME`, `<profile>`, `<provider>`, and `example.com`.
- For private setup, verify through the owning command's status output rather than reading raw credential files.
- Stop when the validation threshold is met; do not add adjacent work.

## Safety Boundaries

- Do not paste API keys, OAuth tokens, passwords, cookies, private webhook URLs, or credential files into tutorial answers.
- Do not edit credential stores, runtime databases, sessions, logs, caches, pairing state, or generated backups.
- Do not turn a private local path into a public example; use placeholders instead.
- Prefer official Hermes setup, auth, config, tools, MCP, gateway, and cron commands over raw file edits.

## Review Questions

- What is the difference between a non-secret config value and a credential?
- Which Hermes command or setup flow owns the value?
- What proof would convince a skeptical reviewer that the value was configured without exposing it?
