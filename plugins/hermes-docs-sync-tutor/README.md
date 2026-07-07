# Hermes Docs Sync Tutor

Keeps tutorial content aligned with official Hermes documentation.

## Tutorial level

Builder/master

## What it teaches

Tutorial content is helpful guidance, but official Hermes docs and live CLI output win when they differ.

## Slash commands

- `/docs-check`

## Tools

- `tutorial_check_docs_link`
- `tutorial_compare_lesson_to_docs`
- `tutorial_flag_stale_lesson`

## Bundled skills

- `hermes-docs-sync-tutor:docs-freshness-audit`

## Safety

This plugin is designed for tutorial use. It does not require secrets. Runtime learner progress, when present, stays in the active profile's local data path and is not part of public packages.

Official Hermes docs and live CLI output are the source of truth if tutorial content differs.
