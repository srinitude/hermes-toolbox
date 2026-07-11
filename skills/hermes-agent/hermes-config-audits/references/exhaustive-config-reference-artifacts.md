# Exhaustive config-reference artifact pattern — 2026-07

Use this when a user asks for every `config.yaml` parameter/value, where an inline answer would be too large to verify reliably.

## Artifact set

1. `default-config.yaml` — `yaml.safe_dump(DEFAULT_CONFIG, sort_keys=False)`.
2. `flattened-config-inventory.csv` — one source-ordered row per leaf: dotted path, runtime type, serialized default, accepted values/domain, explanation, and `file:line`.
3. `flattened-config-inventory.md` — the same rows grouped by top-level section.
4. `dynamic-and-compatibility-schemas.md` — model object aliases, providers/custom providers, fallback/routing, MCP, toolsets/platforms, and every open-ended map that cannot be represented by `DEFAULT_CONFIG`.
5. `validation-manifest.json` — installed version/commit, config schema version, counts, source hash, and artifact hashes.
6. `README.md` plus a compressed archive for user-visible delivery.

## Extraction technique

- Import the installed `DEFAULT_CONFIG` for runtime truth.
- Parse `hermes_cli/config.py` with `ast` and recursively map dict keys to source lines.
- Harvest adjacent source comments for explanations. Supply explicit path-specific prose only where comments are absent.
- Derive finite enums from the actual runtime normalizer/consumer, not merely setup/dashboard option metadata.
- Treat provider/model/plugin/MCP identifiers as open-ended when registries can extend them.

## Adversarial threshold

Before delivery, independently prove:

- flattened leaf count equals recursive runtime leaf count;
- all paths are unique and in exact recursive source order;
- YAML values and recursive key order round-trip exactly;
- every row has a non-placeholder explanation, accepted domain, and source line;
- dynamic/compatibility schemas are clearly separated from static defaults;
- no credential-shaped literals appear in any artifact;
- manifest hashes recompute exactly;
- archive member list contains every promised artifact and nothing unintended.

Delete temporary generator/verifier scripts after validation. Preserve only the requested export artifacts.

## Important pitfall

UI/dashboard `CONFIG_SCHEMA` option lists can lag runtime behavior. For example, an older dashboard schema may advertise historical approval names while `tools/approval.py::_normalize_approval_mode` accepts only `manual`, `smart`, and `off`. Resolve conflicts against the installed runtime normalizer/consumer and current first-party docs, and record the installed-version scope.
