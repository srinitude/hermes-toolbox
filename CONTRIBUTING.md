# Contributing

Contributions must be reusable, public-safe, identity-neutral, and complete.
`inventory/public-manifest.json` is the source of truth for what is
published; documentation counts and package names are tested against it.

Before opening a pull request, run the full validation packet:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 scripts/validate-public-safety.py
python3 scripts/validate-identity-neutrality.py
python3 scripts/validate-package-completeness.py
python3 scripts/validate-tutorial-suite.py
python3 scripts/verify-python-structure.py scripts tests plugins
bash -n scripts/install-toolbox.sh scripts/publish-public-candidates.sh
```

Requirements:

- Do not include credentials, tokens, auth stores, memory, session data, logs,
  caches, state databases, or runtime artifacts.
- Do not include private profile names, private plugin names, private account
  identifiers, private paths, or personal examples.
- Keep every Python file at or under 200 lines, every named construct at or
  under 30 lines, and nesting at or under three levels
  (`scripts/verify-python-structure.py` enforces this).
- Do not add mocks, stubs, fakes, spies, TODO markers, placeholder bodies,
  skipped tests, or xfail tests; tests exercise real directories, real
  subprocesses, and the real Hermes runtime.
- Packages are published fail-closed: a candidate ships only while its
  current source passes every gate, and a failing candidate leaves the
  existing public package unchanged.
- Use conventional commit subjects such as `docs:`, `feat:`, `fix:`, or
  `chore:`.
- Do not add generated authorship trailers or assistant co-author trailers to
  commits or tracked files.
