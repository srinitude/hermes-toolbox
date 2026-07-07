# Hermes Assessment Certifier

Tests whether a learner has actually mastered each tutorial stage.

## Tutorial level

Builder/master

## What it teaches

Assessment should test recall, practical execution, safety judgment, troubleshooting judgment, and design competence.

## Slash commands

- `/quiz`
- `/certify`

## Tools

- `tutorial_generate_quiz`
- `tutorial_grade_answer`
- `tutorial_assign_capstone`
- `tutorial_evaluate_capstone`

## Bundled skills

- `hermes-assessment-certifier:beginner-assessment`
- `hermes-assessment-certifier:intermediate-assessment`
- `hermes-assessment-certifier:advanced-assessment`
- `hermes-assessment-certifier:mastery-assessment`

## Safety

This plugin is designed for tutorial use. It does not require secrets. Runtime learner progress, when present, stays in the active profile's local data path and is not part of public packages.

Official Hermes docs and live CLI output are the source of truth if tutorial content differs.
