# Deterministic Workflow Primitives

This repository packages reusable primitives that make Hermes workflows
repeatable and auditable.

- Validator personality primitive: install
  `primitives/personalities/validator/config.public.yaml`, then start with
  `/personality validator`.
- Prompt-enhancement primitive: run `/prompt-enhancer [prompt]` before action.
- Profile-compartmentalization primitive: use `/profile-builder [goal]` for
  isolated responsibilities.
- Plugin-extension primitive: use `/plugin-builder [goal]` for reusable tools
  and integrations.
- Public profile package primitive: export only generic declarative profile
  metadata after removing private/runtime state.
- Public plugin package primitive: export only sanitized plugin packages from a
  configured public-plugin-source profile.
- Public-safety validator primitive.
- Identity-neutrality validator primitive.
- Public exporter primitive.
- Public candidate scanner primitive.
- Public publisher primitive with silent no-op behavior.
- Private backup validator primitive.
- Selective backup/restore primitive.
- No-agent every-5-minute cron primitive.
- Manifest/fingerprint primitive for meaningful update detection.
