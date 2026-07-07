# Honcho Profile Isolation Setup Reference

Session-derived reference for configuring Honcho as Hermes Agent's external memory provider while preserving profile isolation. Do not store real API keys here.

## Successful Flow

1. Verify first-party docs and live CLI:
   - Honcho docs describe multi-agent profiles as one shared workspace/user peer plus one AI peer per Hermes profile.
   - Profiles docs state profiles are isolated by `HERMES_HOME`.
   - `hermes memory status` shows whether Honcho is active.
2. Run the official setup path:
   ```bash
   hermes memory setup honcho
   ```
3. For cloud API-key setup, provide:
   - deployment: `cloud`
   - auth method: `apikey`
   - user peer: stable human name
   - AI peer: default profile peer, usually `hermes`
   - workspace: stable workspace ID
4. Recommended balanced defaults:
   ```json
   {
     "recallMode": "hybrid",
     "writeFrequency": "async",
     "sessionStrategy": "per-session",
     "contextTokens": 1200,
     "contextCadence": 1,
     "dialecticCadence": 2,
     "dialecticDepth": 1,
     "dialecticReasoningLevel": "low",
     "reasoningHeuristic": true,
     "reasoningLevelCap": "high",
     "observationMode": "directional",
     "saveMessages": true,
     "timeout": 15
   }
   ```
5. Run profile sync for existing profiles:
   ```bash
   hermes honcho sync
   ```
6. Validate:
   ```bash
   hermes memory status
   hermes honcho status
   hermes honcho status --all
   hermes honcho peers
   ```

## What Good Output Looks Like

`hermes memory status` should show:

- Built-in: always active
- Provider: honcho
- Plugin: installed
- Status: available

`hermes honcho status` should show:

- Enabled: True
- Auth: API key or OAuth, masked
- Config: profile-local `honcho.json`
- Workspace: expected workspace
- User peer: expected user peer
- AI peer: expected profile-specific AI peer
- Session strategy, recall mode, context budget, dialectic cadence, observation, write frequency
- Connection: OK

Permissions should be restrictive:

```text
$HERMES_HOME/config.yaml 0600
$HERMES_HOME/honcho.json 0600
$HERMES_HOME/.env       0600
```

## Profile Boundary Nuance

- `hermes honcho sync` backfills existing named profiles.
- `hermes profile create NAME --clone` or `--clone-all` causes the new profile to inherit Honcho config and get a dedicated AI peer.
- Plain `hermes profile create NAME` creates a blank profile and does not automatically inherit the default profile's Honcho setup. If the user wants hard enforcement for every future blank profile, clarify the desired mechanism:
  - managed scope (`/etc/hermes/config.yaml`) for non-secret config only,
  - upstream/source change to profile creation behavior,
  - or a user-local wrapper/procedure.

## Security Notes

- Never save real Honcho API keys in skills, references, memory, or final answers.
- Do not use managed-scope `.env` for secrets because it is commonly world-readable.
- Final replies should report masked status and validation evidence only.
