# Large Multi-Slice Run Worksheet

Use this before beginning a long implementation request.

## 1. Inventory

```text
Repository instructions read: [ ]
Plan/tasks read in full: [ ]
Current Git status recorded: [ ]
Required external/live source inspected read-only: [ ]
Requested commit granularity: per behavior / per task / final only
Final verification commands reserved: [ ]
```

## 2. Slice Table

| Slice | Focused RED/GREEN command | Regression command | Structural check | Commit required | State |
|---|---|---|---|---|---|
| 1 |  |  |  |  | pending |
| 2 |  |  |  |  | pending |

States should be only `pending`, `red-confirmed`, `green`, or `committed`. Do not mark `green` until the focused behavior and relevant regressions pass.

## 3. Conservative Call Budget

Reserve approximately six action rounds per behavior:

1. Write one behavior test.
2. Run focused RED.
3. Implement minimum production code.
4. Run focused GREEN.
5. Run regressions/structural checks.
6. Commit and capture SHA.

Batch only independent reads or independent final checks. Do not batch a RED run with implementation because implementation depends on observing the intended failure.

Reserve additional final rounds for:

- Full test suite
- Compatibility/integration suites
- Compile or static analysis
- Repository-specific structure verifier
- Banned-term/private-path/tracked-file scans
- Git diff/status and commit metadata verification

## 4. Compact Boundary-Test Pattern

Avoid putting a megabyte payload directly in a pytest parameter because pytest includes parameter values in node IDs and failure output.

Prefer:

```python
@pytest.mark.parametrize("case", ["oversized", "bad_utf8"], ids=["size", "utf8"])
def test_bad_frame(case: str) -> None:
    frame = b"x" * 1_048_577 if case == "oversized" else b"\xff\n"
    ...
```

This preserves the real boundary behavior while keeping test output usable.

## 5. Contract-Contradiction Pattern

When a request says an installed contract has one surface but exact source inspection shows another:

```text
observed_contract: <source-derived values>
declared_contract: <requested/audited values>
status: compatibility_hold
reason: declared_contract_mismatch
```

The corresponding compatibility test should pass when the system correctly enters hold. Do not rewrite the observed values to match the request.

## 6. Stop Boundary

Before starting the next slice, answer:

- Can this slice reach focused GREEN?
- Can regressions run afterward?
- Can the requested commit be created?
- Is enough budget still reserved for final verification?

If any answer is no, stop at the current committed GREEN boundary and report exact remaining work. If uncommitted work already exists, identify it explicitly and do not describe the repository as clean or fully verified.
