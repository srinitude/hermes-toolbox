# complete-plugin

Minimal complete plugin fixture for the public export pipeline tests. It
registers one tool (`fixture_echo`) and one command (`fixture-status`)
through the real Hermes plugin context, so tests can prove discovery,
registration parity, and handler behavior without any test doubles.

## Install

Copy this directory into `$HERMES_HOME/plugins/complete-plugin` (or a
profile's `plugins/` directory) and enable it:

```bash
hermes plugins enable complete-plugin --no-allow-tool-override
```

## Usage

- Tool `fixture_echo`: returns `{"success": true, "plugin": "complete-plugin", "echo": "..."}`.
- Command `fixture-status`: returns a one-line status string.

## Tests

`tests/test_contract.py` exercises the handlers directly with real inputs.
