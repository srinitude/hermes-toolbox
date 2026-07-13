# Paid Resource Lifecycle Recovery

Use this pattern for cloud sandboxes, VMs, GPU jobs, databases, tunnels, and other metered resources whose create/delete APIs may be eventually consistent.

## Core invariant

A failed client call or an empty immediate list is **not** proof that create failed. Once a create request may have reached the provider, treat ownership as unresolved until the provider's authoritative list is reconciled.

## Before create

1. Write durable private intent evidence before submitting the request:
   - Unique deterministic name.
   - Exact ownership labels/tags.
   - Resource shape and public/private setting.
   - Auto-stop/archive/delete backstops.
   - Spend formula and approved cap.
2. Verify the authoritative pre-create resource count and refuse a second resource when the expected prestate is not satisfied.
3. Use labels that distinguish this run without containing secrets, credentials, user data, or raw prompts.
4. Record units exactly as returned and as documented. Do not relabel GiB as MiB or infer units from a bare number.

## Reconcile ambiguous create results

If create returns an error, times out, or is not immediately visible:

1. Do **not** issue another create.
2. Query the provider directly with bounded retries and backoff.
3. Match by the full ownership tuple—not a partial name substring:
   - Name.
   - All run labels/tags.
   - Resource class/shape.
   - Creation window when available.
4. Continue only when exactly one owned resource is proven.
5. If zero or multiple candidates remain after the retry window, stop normal work and enter cleanup/reconciliation mode.

## Cleanup protocol

1. Persist the provider resource ID as soon as uniquely identified.
2. Stop active workloads and metered auxiliary services first.
3. Invoke delete by exact recorded ID.
4. Retry authoritative list/info reads until the resource is absent or a bounded deadline expires.
5. Treat these as distinct states:
   - `stopped`: compute halted; resource may still incur storage or retention cost.
   - `delete requested`: not yet proof of deletion.
   - `absent from authoritative inventory`: cleanup proof.
6. If delete returns nonzero, retain the ID and evidence. Never erase the manifest or claim cleanup because auto-delete is configured.
7. Auto-stop/auto-delete is a backstop, not acceptance evidence.
8. Report residual resources before unrelated progress. Cleanup takes priority over implementation, review, or provisioning another resource.

## Evidence schema

Keep a private structured record with:

```json
{
  "create_requested_at": "ISO-8601",
  "name": "run-owned-name",
  "labels": {"owner": "bounded-run"},
  "resource_id": "opaque provider ID",
  "resources": {"cpu_vcpu": 1, "memory_gib": 1, "disk_gib": 3},
  "public": false,
  "created": true,
  "execution_proof": false,
  "stopped": true,
  "delete_requested": true,
  "deleted": false,
  "residual_count": 1,
  "billing_delay_warning": "provider-specific"
}
```

Store credentials nowhere in this record. Opaque resource IDs are operational identifiers, not authentication secrets, but keep them private when the plan requires it.

## Verification checklist

- [ ] Intent and ownership tuple persisted before create.
- [ ] No second create after an ambiguous response.
- [ ] Exact owned singleton reconciled from the provider.
- [ ] Resource ID persisted before execution or cleanup.
- [ ] Stop and delete outcomes recorded separately.
- [ ] Authoritative inventory confirms absence.
- [ ] Auto-delete is treated only as a fallback.
- [ ] Units and projected cost formulas are correct.
- [ ] Delayed billing is disclosed rather than guessed.
