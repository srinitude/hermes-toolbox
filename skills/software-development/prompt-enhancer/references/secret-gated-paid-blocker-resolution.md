# Secret-gated paid blocker resolution

Use this pattern when a user approves spending or asks to fix all blockers, but some blockers require API keys, OAuth tokens, or other secret values.

## Core posture

- Treat spend approval and credential availability as separate gates.
- Apply the approved spend cap to config/manifests/tooling, but do not infer permission to print, type, store, or replay secrets in chat/tool calls.
- Fix all non-secret blockers immediately: CLI installation, dry-run wiring, config caps, manifests, local validators, plugin gates, syntax checks, and status commands.
- Isolate credential-only blockers as user-side setup items when resolving them would require the agent to type or print secret values.
- Report whether any money was actually spent. If only dry-runs/status checks happened, say no paid actions were performed.

## Recommended artifacts

1. A no-echo secret setup helper that the user runs from a trusted shell, e.g. `scripts/secure_configure_secrets.py`.
   - Use `getpass.getpass()` or provider auth CLI flows.
   - Write only to the intended profile `.env` or official credential store.
   - Print key names and status only; never print values.
   - Set restrictive file permissions when writing `.env`.
2. A live readiness validator, e.g. `scripts/check_live_readiness.py`.
   - Checks CLI presence, login/token presence, and required API-key presence.
   - Returns structured JSON.
   - Includes a boolean attesting that protected values were not printed.
3. A blocker-resolution report.
   - Lists fixed blockers.
   - Lists remaining credential-only blockers.
   - Includes exact validation output.
   - States spend status.

## OAuth callback and paste-back handling

Treat OAuth authorization codes, full localhost redirect URLs, PKCE callback queries, device codes, and state-bearing callback URLs as credential material even when the user pastes them voluntarily.

- Never replay, type, store, quote, or pass a callback URL/code through an agent tool call.
- The user must paste it into the **same waiting first-party CLI process** that created the OAuth state/verifier. A callback cannot safely be completed by a new unrelated process.
- If that process no longer exists, the callback is stale or unusable: start a fresh official login and have the user complete the new flow locally.
- Verify authentication independently with a non-secret first-party read command. Do not infer success from the user reaching a localhost URL.
- Distinguish auth modes. API-key mode may permit resource calls while rejecting organization, billing, or account commands that require browser/JWT auth.
- If a pasted callback entered chat, avoid repeating it and recommend rotation/revocation only when the provider treats the code as reusable or the surrounding credential may have been exposed.

## Paid-action gate shape

For each live paid action, require all of:

```yaml
paid_actions_enabled: true
approved_spend_cap_usd: 10.0  # example only; replace with the user's approved cap
require_per_action_cap: true
execute: true
cap_usd: 1.0
protected_inputs_ready: true
```

Dry-runs should succeed without credentials when they only validate shape/cost/gates and do not contact paid APIs.

## Validation checklist

- Runtime/model locks still pass after edits.
- CLI/tool dependency now exists where applicable.
- Plugin/tool registration still works.
- Dry-run gates pass for paid operations.
- Live readiness clearly fails only on absent user-side credentials, if credentials remain absent.
- Generated artifacts contain no raw secret-like values.
- Final response separates fixed blockers from isolated credential-only blockers and gives the exact manual secure setup command.
