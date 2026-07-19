# Reviewed-only Honcho host template

Read the target profile's `honcho.json` and run `hermes honcho status` before applying this template. Replace every angle-bracket placeholder with a reviewed local value.

## Use this pattern when

- SOUL, live sources, and local sessions must outrank hosted inference.
- The agent should call Honcho tools explicitly instead of receiving automatic prompt injection.
- One shared working directory would otherwise mix unrelated tasks.

## Host block shape

```json
{
  "hosts": {
    "<host-name>": {
      "enabled": true,
      "environment": "production",
      "workspace": "<workspace-name>",
      "peerName": "<user-peer-name>",
      "aiPeer": "<ai-peer-name>",
      "pinUserPeer": false,
      "userPeerAliases": {},
      "runtimePeerPrefix": "",
      "recallMode": "tools",
      "initOnSessionStart": false,
      "saveMessages": false,
      "writeFrequency": "async",
      "observation": {
        "user": {"observeMe": true, "observeOthers": false},
        "ai": {"observeMe": false, "observeOthers": true}
      },
      "sessionStrategy": "per-session",
      "sessionPeerPrefix": false,
      "contextTokens": 800,
      "injectionFrequency": "every-turn",
      "contextCadence": 2,
      "dialecticCadence": 5,
      "queryRewrite": false,
      "firstTurnBaseWait": 3.0,
      "firstTurnDialecticWait": 2.0,
      "dialecticDepth": 2,
      "dialecticReasoningLevel": "low",
      "dialecticDynamic": true,
      "reasoningHeuristic": true,
      "reasoningLevelCap": "medium",
      "dialecticMaxChars": 600,
      "messageMaxChars": 25000,
      "dialecticMaxInputChars": 10000
    }
  }
}
```

The cadence and character limits remain bounded fallbacks if automatic injection is enabled later. They do not restore message capture while `saveMessages` is false.

## Verification

1. Run `hermes honcho mode`, `hermes honcho strategy`, `hermes honcho tokens`, and `hermes honcho status`.
2. Confirm the resolved host, peer names, workspace, mode, and observation flags match the target profile.
3. Confirm no credential fields were written to `honcho.json`.
4. Start a fresh Hermes process before testing prompt-time behavior. An existing TUI may retain the previous provider object.
