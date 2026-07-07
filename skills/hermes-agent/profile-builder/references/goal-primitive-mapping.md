# Goal-to-Primitive Mapping Notes

Use this reference when a profile-building conversation includes user goals, desired outcomes, or a rationale for creating a dedicated profile instead of using `default`.

## Compact Mapping Pattern

For each user goal, keep a compact coverage row instead of long prose:

```yaml
- goal: "Automate research briefings for my trading workflow"
  desired_outcome: "A dedicated profile can collect, summarize, and deliver recurring market context without relying on the default profile."
  primitive_coverage:
    profile: ["name/description identify this as a research-briefing profile", "surface includes cron/gateway if delivery is needed"]
    identity: ["SOUL describes concise analyst behavior and source skepticism"]
    model: ["quality/cost tradeoff chosen for summarization and extraction"]
    configuration: ["compression/tools/security keys set or left default intentionally"]
    terminal: ["backend/cwd chosen for any scripts or project files"]
    capabilities: ["web/search, file, cron, and relevant research skills enabled"]
    memory: ["only stable preferences saved; no market diary"]
    automation: ["cron job prompt/delivery defined if recurring"]
    security: ["approvals/secret policy specified"]
    performance: ["speed/cost/quality priority recorded"]
    validation: ["doctor/status/tools list/smoke chat/cron list as applicable"]
    portability: ["env requirements and export needs recorded"]
  not_applicable: []
  unmapped_primitives: []
  status: mapped
```

## Rules of Thumb

- Preserve the user's words as compact `goals.stated[]` entries before normalizing them into implementation choices.
- Do not dump every goal into SOUL. SOUL captures identity and communication style; most goals also imply tools, model, config, memory, automation, security, performance, and validation decisions.
- Do not let the `default` profile implicitly satisfy a goal. If the new profile needs something from `default`, record an approved clone/import path and name what is inherited.
- The final approval preview should have no silent blanks: every primitive is mapped, marked not applicable/skipped, or blocked with a reason.
- Validation should prove the new profile carries the behavior: use profile show, config check/show, tools list, prompt-size, smoke chat, cron/gateway/MCP checks, or a clearly stated user-action blocker.
