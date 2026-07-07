# Hermes Learning Progress

Tracks learner progress through lessons, quizzes, labs, and capstones.

## Tutorial level

All levels

## What it teaches

Progress state is local runtime data and must never be exported as public tutorial content.

## Slash commands

- `/progress`
- `/review`
- `/resume-tutorial`

## Tools

- `tutorial_record_progress`
- `tutorial_get_progress`
- `tutorial_mark_lesson_complete`
- `tutorial_recommend_review`

## Bundled skills

- `hermes-learning-progress:progress-tracking-basics`

## Safety

This plugin is designed for tutorial use. It does not require secrets. Runtime learner progress, when present, stays in the active profile's local data path and is not part of public packages.

Official Hermes docs and live CLI output are the source of truth if tutorial content differs.
