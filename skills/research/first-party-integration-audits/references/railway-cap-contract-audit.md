# Railway + Cap contract-audit snapshot (2026-07-09)

Use this as a dated reconnaissance map, not as current truth. Re-open every first-party URL and re-run only read-only `--help`/version probes before relying on it.

## Railway CLI contract lessons

- Installed CLI was `5.13.0`; first-party latest stable was `5.26.0`. Compare the live binary with GitHub's latest immutable release before interpreting help output.
- Read-only preflight that does not authenticate or inspect credentials: `railway --version`, `railway --help`, nested `--help`, and `railway check_updates`.
- Agent setup is mutating: `railway setup agent`, `railway mcp install`, and `railway skills install` write tool configuration. Under read-only constraints, inspect help only.
- Login is browser OAuth with headless device-code fallback. Remote MCP uses OAuth, rejects project tokens, and exposes a narrower documented tool set than local MCP/CLI.

First-party sources:
- https://docs.railway.com/cli/login
- https://docs.railway.com/agents
- https://docs.railway.com/ai/mcp-server
- https://docs.railway.com/ai/agent-skills
- https://github.com/railwayapp/cli/releases

## Explicit-ID inspection is command-specific

Never infer that one `--project` flag makes the whole CLI no-link capable. Inventory selectors at every nested command and inspect tagged source when help is ambiguous.

At Railway CLI `5.13.0`:
- Explicit project/environment/service selectors existed for service list/status, deployment list, logs, metrics, volumes, and `up`.
- `railway status` was linked-context only.
- Environment list/config loaded the linked project; config's environment selector did not replace project context.
- Bucket commands accepted environment/bucket selectors but still loaded the linked project.
- Therefore a complete no-`railway link`, explicit-ID audit required a mixed strategy: selector-capable CLI commands plus OAuth-scoped MCP or GraphQL for uncovered project/environment/bucket reads.

First-party sources:
- https://docs.railway.com/cli/status
- https://raw.githubusercontent.com/railwayapp/cli/v5.13.0/src/commands/service.rs
- https://raw.githubusercontent.com/railwayapp/cli/v5.13.0/src/commands/deployment.rs
- https://raw.githubusercontent.com/railwayapp/cli/v5.13.0/src/commands/environment/list.rs
- https://raw.githubusercontent.com/railwayapp/cli/v5.13.0/src/commands/environment/config.rs
- https://raw.githubusercontent.com/railwayapp/cli/v5.13.0/src/commands/bucket.rs

## Deployment-success semantics

- `SUCCESS` is the authoritative successful deployment state; `FAILED` and `CRASHED` are failures.
- `--detach`/`--no-wait` exit 0 means queued, not healthy.
- Do not generalize “non-detached exit 0” to captured non-TTY execution. Tagged `up` source had a non-TTY, non-CI path that returned after upload without awaiting terminal state.
- Strong acceptance rule: require an explicit final `status: success`/`SUCCESS`, or poll `railway deployment list --json`; do not infer success from log-stream completion.
- `--json` and CI paths should still be checked against the exact installed tag because terminal-state handling is implementation-sensitive.

First-party sources:
- https://docs.railway.com/cli/up
- https://docs.railway.com/cli/deployment
- https://raw.githubusercontent.com/railwayapp/cli/v5.13.0/src/commands/up.rs

## Railway storage/pricing snapshot

At the audit date, first-party docs stated:
- Bucket storage: $0.015/GB-month; S3 operations and bucket egress free.
- Service-to-bucket uploads still incur service egress because buckets use the public network.
- Buckets are private; use authorized backends or temporary presigned URLs.
- Volume storage: $0.15/GB-month; service egress: $0.05/GB; RAM: $10/GB-month; CPU: $20/vCPU-month.
- Hobby/Pro minimum commitments: $5/$20 with matching included usage.

Sources:
- https://docs.railway.com/pricing
- https://docs.railway.com/pricing/understanding-your-bill
- https://docs.railway.com/storage-buckets/billing
- https://docs.railway.com/storage-buckets/uploading-serving
- https://docs.railway.com/volumes/reference

## Cap v0.5.3 self-host lessons

Pinned release: `cap-v0.5.3`, commit `f4eb1fb39c254ba9488734e6b8b1756c26e0b5c0`.

- Instant Mode uploads/processes after stop; Studio Mode records locally, supports review/editing, then uploads.
- Tagged `docker-compose.yml` still referenced `ghcr.io/capsoftware/cap-web:latest`; cloning a release tag did not pin the complete runtime. Audit deployed image digests separately.
- Self-host requires Cap Web, MySQL, S3/MinIO, and media processing. Raw object presence is not proof of processed playback.
- Privacy default was public: tagged env/schema defaulted videos public, and docs said anyone with the link can view unless access controls/password are applied.
- Self-host logs may contain login links when email is not configured; default compose secrets are placeholders; optional transcription/AI can send content to Deepgram/Groq/OpenAI.
- Historical embed issue #906 was stale for v0.5.3: merged PR #1951 and tagged `proxy.ts` allowed `/embed/` and the workflow route; current docs supported custom-domain embeds. Keep a live iframe/CSP/password test, but do not call the defect unfixed at that tag.
- Older self-host workflow/ArrayBuffer reports remained useful risk evidence, but tagged source contained fixes for the known route-block and transcription-dispatch race. Classify residual risk separately from fixed release behavior.

Sources:
- https://github.com/CapSoftware/Cap/releases/tag/cap-v0.5.3
- https://cap.so/docs/self-hosting
- https://cap.so/docs/recording/instant-mode
- https://cap.so/docs/recording/studio-mode
- https://cap.so/docs/sharing/share-a-cap
- https://cap.so/docs/sharing/embeds
- https://raw.githubusercontent.com/CapSoftware/Cap/cap-v0.5.3/docker-compose.yml
- https://raw.githubusercontent.com/CapSoftware/Cap/cap-v0.5.3/packages/env/server.ts
- https://raw.githubusercontent.com/CapSoftware/Cap/cap-v0.5.3/apps/web/proxy.ts
- https://raw.githubusercontent.com/CapSoftware/Cap/cap-v0.5.3/apps/web/lib/transcribe.ts
- https://raw.githubusercontent.com/CapSoftware/Cap/cap-v0.5.3/apps/web/workflows/process-video.ts
- https://github.com/CapSoftware/Cap/pull/1951
- https://github.com/CapSoftware/Cap/issues/1550
- https://github.com/CapSoftware/Cap/issues/1651

## Gate reporting pattern

When OAuth is prohibited, separate public-contract verification from tenant-state verification. Explicitly defer project existence/access, service topology, deployed version/image digest, recordings, privacy/password state, playback/embed/CSP, metrics, and actual cost to the OAuth gate. Never expose supplied private IDs in the report.
