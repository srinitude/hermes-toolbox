# Tailscale policy candidate audits

Use this checklist for read-only, exact-hash audits of Tailscale HuJSON/JSON policy candidates against an exported prestate and an authoritative plan.

## Evidence boundary

1. Hash candidate, prestate, and plan before analysis and again at the end.
2. Record mode, size, and mtime. Do not save, apply, or open a live policy editor unless explicitly requested.
3. Separate four verdicts:
   - static policy semantics;
   - test-source completeness;
   - observed Tailscale editor/compiler result;
   - live/runtime behavior.
   A valid JSON/HuJSON parse is not a passing policy-editor test, and source assertions are not observed RED/GREEN evidence.

## Semantic comparison

Normalize only for analysis; preserve byte hashes as the authority. Compare top-level keys and prove that every pre-existing non-access section is semantically unchanged. For a default wildcard migration, verify the old `* -> * -> *` grant is removed, not supplemented: Tailscale grants are additive.

When the preservation selector is `autogroup:member`, require inventory evidence that every preserved device is direct-member-owned and untagged. Tagged devices lose user identity and are not covered by the direct-member grant. State this inventory dependency explicitly rather than treating the selector as unconditional equivalence to wildcard access.

For a tagged sandbox pattern, verify the exact grant set rather than relying on absence searches:

- direct member -> direct member -> `*`;
- approved clients -> sandbox tag -> `tcp:443`;
- sandbox tag -> exact private host -> `tcp:22`;
- sandbox tag -> `autogroup:internet` -> `tcp:80`, `tcp:443`.

Confirm no grant involving the sandbox tag contains `*`, `tcp:5900`, `tcp:5901`, or `tcp:6080`. Distinguish this static no-grant result from runtime claims that noVNC is loopback-only, Serve is private, Funnel is absent, or no public listener exists.

## Test-matrix audit

Parse tests into a `(src, proto)` index and check for duplicate cases, duplicate assertions, and accept/deny overlap. Derive expected matrices from the plan rather than counting test objects.

For member preservation, verify every source/destination pair has representative:

- TCP low, service, HTTPS, and high ports;
- UDP low, DNS, HTTPS/QUIC, and high ports;
- ICMP with destination port `0`.

Count endpoint assertions, not just test objects. Additional accepted endpoints (for example, approved-client sandbox HTTPS) must be separated from preservation assertions.

For sandbox inbound isolation:

- approved clients accept only sandbox `443`;
- every other member explicitly denies sandbox `443`;
- if the plan requires all members to deny raw or unrelated ports, ensure those negatives appear for every member—not merely the approved clients.

For sandbox outbound isolation:

- positively assert only the private SSH target and public TCP 80/443;
- deny representative non-22 ports on the private SSH host;
- deny representative ports on every other tailnet host;
- deny public UDP and ICMP;
- add representative public TCP negatives when the acceptance wording claims TCP 80/443 *only*, even if the grant itself is narrow.

## IPv4 versus IPv6

`"proto": "icmp"` with port `0` is the correct Tailscale test form, but an IPv4-only host alias proves only an IPv4 destination. If the plan explicitly requires ICMPv4 and ICMPv6, require IPv6 literals or IPv6-resolving selectors in the test evidence. Do not infer IPv6 coverage merely from the protocol name.

## Reporting

Lead with a split verdict such as `BLOCKED — static semantics pass; editor and test-completeness gates do not`. Provide exact hashes and line evidence. List missing assertions by source and destination, and classify each finding as:

- semantic policy defect;
- regression-test coverage defect;
- unobserved editor/compiler gate;
- unobserved runtime behavior;
- approval/application gate.

End by stating whether any policy save, tailnet/device probe, or file mutation occurred.
