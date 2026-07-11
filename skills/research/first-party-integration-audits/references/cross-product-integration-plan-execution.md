# Cross-Product Integration Plan Execution

Use this reference when executing a saved integration plan that spans local agents, remote clients, installers, profile/plugin builders, paid cloud resources, and live control-plane services.

## 1. Compute the mutation closure before the first install

An installer may modify more than its named payload. Before running it:

1. Inspect its help, tagged implementation, or dry-run output.
2. Enumerate every possible target: primary hook/plugin, parent directories, auxiliary settings, hook registries, config fragments, aliases, and service state.
3. Capture existence, mode, owner, checksum, and restorable content for every existing target.
4. Record absent targets explicitly.
5. Identify the supported inverse command and verify that it removes only installer-owned entries.

A checksum of the primary script is not a rollback manifest when the installer also edits `settings.json`, `hooks.json`, or another registry. If the mutation closure was not captured, do not claim exact rollback or drift-free execution.

## 2. Detect the self-quiescence paradox early

A plan may require upgrading the same Hermes installation that is running the executing session. Preflight must identify:

- the current TUI/gateway/worker PID;
- other active processes using the same source tree or virtual environment;
- backup, publisher, test, or Git processes touching protected boundaries;
- whether the official updater can safely run while those processes remain active.

If the plan requires full quiescence, the current session cannot autonomously satisfy that gate. Do not mutate the live install and hope the process survives. Instead:

1. Finish independent read-only and non-conflicting prerequisites.
2. Preserve the exact session ID/title needed for resume.
3. Provide one command-complete native-terminal packet: stop services, verify no holders, run the official backup/update path, validate, and resume.
4. Continue only after fresh version/process evidence.

Do not launch an unobserved delayed updater that will outlive the controlling session.

## 3. Treat explicit later gates as concrete scope boundaries

“Execute the whole plan” approves work already concretely scoped, but does not erase gates whose final manifest did not yet exist. Preserve separate approval for:

- profile-builder final agreement;
- plugin-builder final agreement;
- source creation versus consumer installation and enablement;
- privileged service/network cutover;
- paid sandbox creation and spend cap;
- publication/export/push;
- human authentication and secret entry.

Proceed with independent work up to the earliest gate, then present all currently knowable gates together to minimize user interruption.

## 4. Never convert a pasted secret into tool authority

A credential pasted into chat remains secret material; it is not permission for the agent to place it in argv, shell history, environment dumps, files, logs, panes, or process listings. If it has appeared in chat:

- refer to it only by a symbolic name;
- recommend rotation/revocation;
- use the official browser/device/no-echo authentication flow;
- verify authentication through a non-secret read-only command;
- keep paid-action approval separate from authentication readiness.

## 5. Separate network reachability from authenticated control

A tailnet peer being online or responding to ping does not prove shell access. For every remote client, independently validate:

1. DNS/IP reachability.
2. Service listener availability.
3. Existing authenticated SSH identity.
4. Host-key trust verified out of band.
5. Remote architecture/package-manager/version state.
6. Permission to mutate the remote host.

Use strict host-key checking. Unknown host keys and connection refusal are human bootstrap blockers, not permission to weaken SSH verification.

## 6. Price and cap cloud acceptance before provisioning

Use live first-party rates and calculate named scenarios with a tool. Separate:

- tier/top-up requirements;
- running CPU/RAM cost;
- stopped storage cost;
- delayed billing visibility;
- optional GPU/VM/public-preview charges.

Present an exact incremental spend cap, concurrency limit, resource shape, auto-stop/archive/delete policy, and prohibited paid surfaces. Tier eligibility alone is not spend approval.

## 7. Drift ledger language

Capture readable status plus HEAD/status digests before writes and after each checkpoint. Classify:

- pre-existing dirt;
- intentional scoped writes;
- agent-induced unintended drift;
- concurrent or unattributed external drift;
- tool-managed caches or temporary artifacts.

Use `No agent-induced drift observed` only when the complete mutation closure and protected-boundary comparisons prove it. Never claim `no drift throughout` merely because selected Git repositories retained the same digest.

## Completion threshold

Execution may be called complete only when:

- every plan acceptance criterion maps to real evidence;
- every installer target has an exact prestate and tested inverse;
- builder, paid, secret, privileged, and publication gates are satisfied separately;
- remote clients are authenticated and runtime-tested rather than only pingable;
- the final state is attached to fresh process/version/test evidence;
- drift wording matches the ledger rather than the requested ideal.
