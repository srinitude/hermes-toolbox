# Parser-Based Structural Contract Verification

Use this reference when a repository imposes hard limits such as files ≤200 physical lines, named constructs ≤30 physical lines, or semantic control nesting ≤3.

## Verify the real contract

Do not rely on `wc`, visual inspection, or indentation regexes alone. Build a parser-based verifier and run it across both production and test code at each requested commit boundary.

For Python:

- Parse every `src/**/*.py` and `tests/**/*.py` file with `ast.parse`.
- Count physical file lines with `splitlines()`.
- For functions, async functions, and classes, measure from the earliest decorator line through `end_lineno`; signatures, comments, blanks, and bodies all count.
- Measure control nesting relative to each named construct. Count `if`, `for`, `async for`, `while`, `try`, `with`, `async with`, and `match`; do not charge an outer construct for control flow inside a nested function/class, because that nested construct is checked separately.
- Report every violation with file, start line, construct name, measured span/nesting, and the limit. Exit nonzero on any violation.

When the repository has no checked-in checker, create a focused verifier under `/tmp`, run it, and remove it in the same command after capturing the result. Do not leave ad-hoc verification artifacts in the project.

## Refactoring patterns

- A class-span failure usually means behavior belongs in module-level helpers or small capability mixins; merely shortening methods does not reduce the class declaration-to-end span.
- A nesting failure from `elif` chains may be real in AST terms because each `elif` is another nested `If`. Prefer same-depth guard clauses or dispatch tables.
- Split graph validation, serialization, or platform isolation into bounded modules before the source file reaches the cap.
- Keep test helpers bounded too. Move long setup into small fixture/build helpers rather than exempting tests.

## Verification sequence

1. Focused GREEN for the refactored behavior.
2. Full regression and compile/static checks.
3. Parser structural verifier.
4. Banned-content/private-path scans and `git diff --check`.
5. Commit only after all checks cover the final tree.

If the verifier exposes a pre-existing violation in a touched task boundary, refactor it under existing GREEN tests rather than weakening the checker.
