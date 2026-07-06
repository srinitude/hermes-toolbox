# Contributing

Contributions should be reusable, public-safe, and identity-neutral.

Before opening a pull request, run:

```bash
python3 scripts/validate-public-safety.py
python3 scripts/validate-identity-neutrality.py
```

Requirements:

- Do not include credentials, tokens, auth stores, memory, session data, logs,
  caches, state databases, or runtime artifacts.
- Do not include private profile names, private plugin names, private account
  identifiers, private paths, or personal examples.
- Use conventional commit subjects such as `docs:`, `feat:`, `fix:`, or `chore:`.
- Do not add generated authorship trailers or assistant co-author trailers to
  commits or tracked files.
