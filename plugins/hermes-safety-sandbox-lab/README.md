# Hermes Safety Sandbox Lab

Teaches safety, approvals, secrets, filesystem boundaries, and sandboxing.

## Tutorial level

Confident beginner

## What it teaches

Profiles isolate Hermes state, not the operating-system user or filesystem; sandboxing is a separate terminal/backend choice.

## Slash commands

- `/safety-lab`
- `/is-this-safe`

## Tools

- `classify_hermes_action_risk`
- `explain_write_surface`
- `suggest_safer_hermes_action`

## Bundled skills

- `hermes-safety-sandbox-lab:write-safety`
- `hermes-safety-sandbox-lab:secret-safety`
- `hermes-safety-sandbox-lab:sandboxing`

## Safety

This plugin is designed for tutorial use. It does not require secrets. Runtime learner progress, when present, stays in the active profile's local data path and is not part of public packages.

Official Hermes docs and live CLI output are the source of truth if tutorial content differs.
