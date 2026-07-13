# Installer profile and installed-wheel completeness

Use this during read-only audits of inert systemd deployment bundles that provision a named Hermes worker profile and an overriding plugin.

## Closure checklist

1. **Named-profile shape**
   - Validate the rendered profile path lexically as `<service-home>/.hermes/profiles/<profile>`.
   - Require the final component to equal the configured profile name.
   - Trace post-exec environment construction: in profile mode `HERMES_HOME` is the profile directory itself, while `HOME` is the service home and `HERMES_PROFILE` names the profile.
   - Check the installer and runtime enforce the same equation; a correct test fixture alone is insufficient.

2. **Authenticated profile inventory**
   - Include the exact profile `config.yaml` payload and every plugin byte in the authenticated manifest, with mode, size, and digest.
   - Require exact inventory equality so omitted and extra files both fail verification.
   - Ensure config explicitly enables the plugin and grants any required native-tool override.
   - Distinguish authenticated bundle presence from destination mapping and publication; an inert bundle may still be incomplete if no later contract identifies final paths, owners, and modes.
   - Authenticate the installed-tree mapping too: source artifact, final pathname, owner, group, mode, and archive extraction root. A manifest of bundle-relative names cannot prove an installed consumer when, for example, the bundle emits `broker.yaml` but the unit references `config.yaml`.

3. **Interpreter/package closure**
   - Inspect every import made by the copied directory plugin. If it imports its parent distribution, the worker's Hermes interpreter must have that exact wheel installed.
   - A broker executable in one venv does not prove package availability to a Hermes executable in another venv.
   - A `PYTHONPATH` containing only the pinned upstream Hermes source does not satisfy absolute imports from the broker/plugin distribution. Require the exact installed wheel or an authenticated immutable path containing that distribution and its package data.
   - Source `copytree`, repository `PYTHONPATH`, or test-script `sys.path` injection are development proofs, not installed-wheel proofs. In particular, an E2E helper that inserts both upstream and project source roots can hide a production environment that inserts only upstream.
   - Prefer one temporary-venv test that builds or consumes the exact wheel, installs it into the worker interpreter, installs the profile/plugin payload, and crosses real plugin discovery without source-path injection.
   - If plugin resources are read from the distribution, prefer `importlib.resources` and explicitly verify non-Python files such as `plugin.yaml` and compatibility contracts are wheel members.

4. **Identity and directory closure**
   - Cross-check `User=`, `Group=`, `SupplementaryGroups=`, sysusers users/groups/memberships, runtime authorization tuples, and tmpfiles ownership.
   - For every Unix socket, prove the complete GID equation: tmpfiles parent GID = server listener/configuration GID = socket inode GID = an admission group actually held by each intended client. A distinct client group in sysusers is useless if runtime assembly passes the operator GID; strict descriptor-bound socket setup may fail before bind rather than merely denying clients later.
   - A dedicated public-socket group must be distinct from operator, registrar, broker, launcher, and worker primary groups.
   - Provision the broker database parent explicitly, not merely the socket/runtime roots.
   - Inventory every `ReadWritePaths=` entry. Each path must already exist through tmpfiles, `RuntimeDirectory=`, another ordered provisioning unit, or use an intentional `-` prefix; otherwise a clean-host service can fail during mount-namespace setup before `ExecStart`.

5. **Cold-start ordering**
   - If launcher readiness requires an authenticated broker probe, the launcher unit must require and order after the broker.
   - The aggregate target should wait for both notify services.
   - Keep explicit migration separate from restart: an `ExecStartPre=migrate` weakens fail-closed startup. A check-only preflight plus an operator migration step is acceptable, but clean-host provisioning must be documented as a prerequisite.

6. **Immutable named-profile control code**
   - Do not install the overriding directory plugin or its `config.yaml` worker-owned beneath a profile-wide `ReadWritePaths=` grant. A worker from task A can persist modified registration/readiness code that executes with task B's fresh activation credential.
   - Keep plugin code and override-bearing config root-owned and read-only. Provision only the exact Hermes runtime-state subdirectories that need worker writes; authenticate each destination owner, group, and final mode.
   - Treat `HERMES_HOME=<named-profile>` plus post-exec plugin discovery as a future-code execution path. Include that installed plugin/config path in protected-path and cross-task persistence checks.
   - For native-name overrides, register under a distinct plugin toolset even when `override=True` and `allow_tool_override: true` are present. Same-toolset replacement can skip the host registry's collision, ownership, and audit branch. Pin the final registry sink in addition to the `PluginContext` facade.

7. **Exact wheel and venv-action closure**
   - A `.whl` suffix, regular-file check, and size bound do not establish package identity. Validate the expected distribution name/version, required package members and package data, archive safety, and an externally pinned digest before authenticating the bundle.
   - Never use a toy wheel containing only `__init__.py` and `METADATA` as the positive installer fixture when the directory plugin imports sibling modules. The acceptance fixture must be the exact built artifact or a byte-equivalent complete wheel.
   - Inventory every interpreter that executes or imports the distribution. If broker, launcher/worker-slot service, and Hermes worker use separate venvs, the authenticated operation map must provision each one; installing the wheel only into the Hermes worker venv does not create the service CLI executable.
   - Validate command-derived targets before signing them. A one-token absolute executable is insufficient when `parent.parent` derives a privileged venv target: require the exact `<approved-root>/venv/bin/<fixed-entrypoint>` grammar and reject system roots.
   - A venv plan naming a Hermes tag/version/peeled commit is only an instruction until it also binds the source/artifact and exact creation/install operation. Keep latest-release freshness separate from installed-interpreter proof.
   - Cross the real installed boundary in a disposable venv without project-source `PYTHONPATH` or `sys.path` injection; source injection can make an incomplete bundled wheel appear operable.

8. **Installed-tree semantics, not bundle-file semantics**
   - Distinguish the mode of a bundle payload from the final installed mode. A source archive or wheel stored as `0600` says nothing about extracted plugin files, console scripts, venv directories, or config destinations.
   - For `copy`, `extract-zip`, and `venv-install`, authenticate destination path, owner, group, final mode policy, extraction root, exact member inventory, and required executable bits. Verify the installed post-state against that mapping.
   - One artifact may need multiple authenticated operations. Do not force a one-file/one-target manifest shape when the same exact wheel must populate more than one interpreter.

## Read-only syntax probes

- Render artifacts in memory with `PYTHONDONTWRITEBYTECODE=1`.
- `systemd-sysusers --dry-run <config>` validates sysusers syntax without account writes.
- For systemd 255 builds where `systemd-tmpfiles` lacks `--dry-run`, feed the config on stdin with a guaranteed nonmatching `--prefix`; this parses the file while selecting no entries for creation.
- Parse polkit JavaScript with a JavaScript syntax checker, while clearly labeling that as syntax-only—not semantic polkit authorization proof.
- `systemd-analyze verify` requires acceptable named unit paths on some versions and may reject `/proc/self/fd/*`. In strict no-write audits, report unit syntax as static-only rather than creating temporary unit files contrary to scope.

## Concurrent dirty-candidate repairs

Installer candidates often change during review. Re-hash the focused installer files before finalizing. Report only the final observed candidate as current, and note earlier missing artifacts as concurrent remediation rather than current defects. A test added before production wiring is useful RED evidence but does not itself close the candidate.
