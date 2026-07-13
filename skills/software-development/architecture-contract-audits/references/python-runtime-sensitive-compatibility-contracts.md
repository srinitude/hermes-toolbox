# Python runtime-sensitive compatibility contracts

Use when a wheel pins a live Python API shape—especially `argparse`, `inspect.signature`, AST unparsing, enum/repr text, dataclass fields, or exception strings—and claims support across a Python version range.

## Failure pattern

A compatibility snapshot can match the exact dependency commit yet fail under a different Python patch release. One observed example normalized `argparse.Action.required` for positional arguments. The same pinned parser produced `required=true` under Python 3.11.15 and 3.12.3 but `required=false` under Python 3.12.13 for four positional actions. CLI behavior remained broadly recognizable, but the package correctly entered a fail-closed compatibility hold because the serialized contract differed. A suite run only under the repository's Python 3.11 venv missed the dispatched Python 3.12.13 failure.

## Audit recipe

1. Record all three independently: wheel `Requires-Python`, the interpreter that ran supplied tests, and the exact target/dispatched interpreter including patch version.
2. Install the exact wheel into a fresh temporary environment using the target interpreter. Do not use the source checkout or its venv as package evidence.
3. Run the packaged contract loader against the exact pinned consumer commit.
4. If the result is a hold, produce a structural recursive diff between packaged expected data and live normalized data. Report exact parser path, action destination/options, and old/new field values.
5. Re-run only the normalizer under the suite interpreter and, when available, another supported interpreter. This distinguishes dependency drift from interpreter-sensitive normalization.
6. Cross the real consumer boundary. For plugins, use a fresh real manager with native tools pre-registered and test both absent and explicit override grants. A schema preflight that raises before registration can mask the expected trust-gate error; report the observed ordering rather than claiming both gates were independently proven.
7. Treat any target-runtime hold as a release blocker even when import and `--help` succeed. Importability is weaker than operability.

## Design guidance

- Prefer semantic fields derived from parser declarations or stable source structure over incidental runtime object attributes.
- If runtime introspection is required, normalize known patch-sensitive details into a version-independent semantic representation.
- Add a compatibility matrix covering every supported Python minor and the actual deployment patch line.
- Do not solve a patch-sensitive snapshot merely by regenerating expected bytes under one newer interpreter; first decide whether the changed field represents user-visible semantics.
- If only one interpreter is intended, encode that honestly in packaging and deployment metadata rather than declaring a broad `Requires-Python` range.

## Reporting

Lead with the target-runtime verdict. Keep these facts separate:

- exact dependency commit matched;
- wheel installed/imported;
- CLI help rendered;
- compatibility contract passed or held;
- plugin/consumer registration succeeded or remained native;
- supplied suite interpreter and result.
