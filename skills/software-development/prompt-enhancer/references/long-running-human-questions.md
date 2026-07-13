# Long-Running Human Questions and Work Packets

Use this reference when the user must run commands, inspect a GUI, complete OAuth, collect evidence, or perform several acceptance checks before answering.

## Distinguish a decision from a work packet

A quick choice can use a clarification field. A work packet needs enough time to complete the work, not merely enough time to read the question.

For this user's multi-step workflows, use a one-hour clarification window unless the user requests another duration.

## Hermes timeout configuration pattern

Validate the current first-party Hermes contract before changing configuration. When the installed surfaces require both compatibility paths:

1. Create a rollback record containing only the existing timeout keys.
2. Use `hermes config set clarify.timeout 3600` for CLI/TUI compatibility.
3. Use `hermes config set agent.clarify_timeout 3600` for messaging/gateway compatibility.
4. Read back only those keys and run `hermes config check`.
5. State whether the current process must restart before the new value is guaranteed.

Do not edit Hermes source to change a user preference.

## Current-session fallback

A running CLI/TUI may have loaded its timeout at process start. When the new value is not guaranteed in the current process:

- ask the work-intensive question in ordinary chat so the user can reply later;
- do not repeatedly issue expiring clarification fields;
- do not treat an empty or timed-out response as refusal, approval, or consent;
- preserve the pending gate and continue only independent read-only work.

## Work-packet format

Bundle related checks into one bounded packet containing:

- why the evidence is needed;
- exact commands or GUI actions;
- explicit redaction/no-secret rules;
- expected fields or pass/fail checks;
- the reply format;
- which later mutation or approval gate remains blocked.

Keep separate privileged decisions separate. A long timeout never weakens an approval gate.
