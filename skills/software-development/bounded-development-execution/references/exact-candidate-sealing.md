# Exact Candidate Sealing: Durable Techniques

Use this reference when sealing a large staged Python candidate with subprocess, filesystem, or pinned-compatibility behavior.

## 1. Pin every verdict to a tree

1. Finish cheap format, structure, type, staged-diff, and privacy gates.
2. Stage the candidate and record `git write-tree` plus `git diff --quiet`.
3. Give that tree hash to every reviewer.
4. Any later byte change supersedes full-suite, wheel, and audit verdicts. Stop or discard stale runs, restage, record the new tree, rebuild, and redispatch.
5. A background suite is authoritative only if it exits zero on the unchanged tree. If an edit is required, terminate it rather than citing partial progress.

## 2. Installed-wheel proof must pin Python

Do not rely on an environment manager's default interpreter. A clean tool can select a newer installed Python even when development used another version.

```bash
uv build --wheel --out-dir "$proof/dist"
uv venv --python /absolute/path/to/validated/python "$proof/venv"
uv pip install --python "$proof/venv/bin/python" "$proof/dist/package.whl[dev]"
```

From outside the repository, assert:

- `sys.version_info` matches the validated runtime;
- package `__file__` is below the proof venv's `site-packages`, not repository `src/`;
- required package data exists via `importlib.resources`;
- the installed console script starts;
- critical subprocess/integration tests pass using the proof interpreter.

A compatibility hold under an accidentally different Python is useful fail-closed evidence, but it is not a valid wheel regression verdict for the pinned deployment.

## 3. Atomic `mkdirat` → `openat` ownership

The helper that creates a child directory must own rollback until it returns the opened and validated child dirfd:

```python
os.mkdir(name, mode=0o700, dir_fd=parent)
try:
    child = os.open(name, DIRECTORY_FLAGS, dir_fd=parent)
except BaseException:
    os.rmdir(name, dir_fd=parent)
    raise
```

The coordinator cannot safely clean this window if its `created` flag is set only after the helper returns.

### Real EMFILE regression without mocks

Fork a child process. Enumerate `/proc/self/fd`, set soft `RLIMIT_NOFILE` to `max(observed_fds) + 1`, then call the public renderer. The retained parent open reuses the enumeration fd; the child-directory open exceeds the limit after `mkdirat`. Assert the public call fails and the destination does not exist. Descriptor *count* is insufficient because pytest may hold sparse high-numbered fds.

## 4. Review linter auto-fixes as code changes

After any broad auto-fix:

- inspect its diff;
- rerun the candidate type checker;
- rerun structural limits and focused behavior tests.

In particular, B009/B010 rewrites around a foreign `ModuleType` may replace deliberate dynamic access with attributes unknown to static analysis. Keep `getattr`/`setattr` with narrow line-level justification when runtime patching is the actual pinned integration contract.

## 5. Verification tracker attachment

A long background suite may not satisfy an external tracker even when it eventually becomes human evidence. After the final edit, run one conventional foreground `pytest` packet covering the changed-path closure and preserve its direct zero exit. Do not run stateful integration packets concurrently when they share HOME, sockets, databases, or daemon fixtures.
