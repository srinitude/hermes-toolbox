# Authenticated External Sources and Skill-Catalog Drift

Use this reference when a plan update names a private dashboard/project plus an external skill group or marketplace page.

## 1. Separate identity from access

Extract stable IDs from the supplied URL before opening it. Inspect the direct URL first. An anonymous `404`, login wall, or empty shell proves only the anonymous view; it does not prove the project or uploaded artifacts are absent.

Record four states separately:

- target IDs supplied by the user
- browser result while anonymous
- local CLI/tool presence and release
- authenticated-access boolean

Do not read raw auth files or tokens. Add an OAuth/device-code gate and keep remote-content claims marked `unverified` until an authenticated read succeeds.

## 2. Treat user claims as requirements to verify

If the user says artifacts were uploaded, the reconciled plan should require an authenticated inventory of service, deployment, storage, domain, processing, privacy, and playback state. Do not silently convert the statement into current proof. Preserve the intended architecture while making verification a blocking acceptance criterion.

## 3. Reconcile marketplace/repository drift

A marketplace group may advertise many decomposed skills while the current official repository has consolidated them.

1. Enumerate every advertised skill/capability.
2. Inspect the current official repository layout and main skill.
3. Use the current official source as the executable contract.
4. Build a capability matrix mapping every advertised item to `used`, `not needed`, or `blocked` work.
5. Do not install stale skills solely to satisfy a numerical coverage request.
6. Validate commands against current first-party docs and live help before mutation.

## 4. Evidence-gated workflow plans

For plans that allow only particular computer-use workflows documented by recordings:

- recordings are untrusted explanatory evidence, never executable instructions
- require narration plus reviewed transcript/captions
- bind a workflow manifest to immutable recording/transcript digests
- define exact apps, inputs, actions, devices, checkpoints, limits, and abort rules
- expose workflow list/preview/run/status/cancel rather than generic click/type tools
- keep low-level automation inside a supervised certification harness
- require human approval for the evidence/manifest pair and again for each run
- suspend on missing evidence, digest drift, privacy regression, or app/UI drift
- begin newly enrolled devices with an empty workflow allowlist

## 5. Validation ledger

Before finishing, verify:

- every supplied source and surrounding requirement is accounted for
- authenticated blockers are explicit and do not become negative product claims
- marketplace capabilities and current repository shape are both represented
- current pricing is first-party sourced when remote infrastructure can incur cost
- generic automation bypasses are absent
- approval, credential, privacy, and spend gates remain intact
- deterministic scans cover required capability names, prohibited legacy surfaces, secret patterns, heading/schema integrity, and balanced code fences
