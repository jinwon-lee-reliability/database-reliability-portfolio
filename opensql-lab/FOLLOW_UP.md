# v0.2 follow-up ? planned work and acceptance criteria

**Current status:** not executed by this documentation PR. The post-migration
Patroni DCS RCA remains **IN PROGRESS**.

The operator continues the lab manually. Completion requires actual commands,
observed results, and reviewed evidence; this checklist does not imply those
actions have already happened.

| Work item | Evidence needed before marking complete |
|---|---|
| Patroni DCS recovery | Confirm effective DCS endpoint/API settings and capture a successful connection to the intended etcd instance |
| Current Leader validation | Capture post-address-change Patroni cluster/role state and a small PostgreSQL query; distinguish this from the old initial Leader result |
| OpenProxy address change | Review the effective proxy target/listen configuration and capture a successful proxy connection/query |
| Full VM reboot validation | After a complete VM reboot, capture static addressing, service states, etcd health/membership, Patroni role, and direct/proxy SQL checks |
| Dependency-resolution record | Record the exact package list, source/provenance, installed SFCGAL version, action taken, and any optional-component limitations |
| Version inventory | Capture actual PostgreSQL engine, Patroni, etcd/etcdctl, and other relevant installed versions |
| Snapshot verification | Capture real snapshot metadata/integrity results; any restore test must use a separate disposable environment and be described separately from identity-preserving migration |
| Public evidence bundle | Review and redact actual logs, retain capture dates and redaction notes, and compute hashes for the resulting files; do not invent or reconstruct absent output |
| Upstream-only reproduction | Reproduce the stale-endpoint scenario using upstream PostgreSQL/Patroni/etcd and synthetic data, record chosen versions and actual runs, and clearly separate it from this product-based lab |

No standalone upstream reproduction, restore, HA quorum/failover, or reboot
recovery result is claimed by v0.1.

## Relationship to the existing Lock Contention Lab

[PR #1](https://github.com/jinwon-lee-reliability/database-reliability-portfolio/pull/1)
already contains the synthetic PostgreSQL Lock Contention RCA implementation.
Inspect its current README, validation evidence, and PR status before extending
or reusing it; do not duplicate the implementation in this directory.

The multi-node Patroni/etcd HA and failover proposal is a separate later stage.
First close the current endpoint-migration checks and preserve their evidence.
A future HA exercise must establish its own quorum, failure, recovery, and
data-integrity results.

## Merge and claim gates

- Keep the v0.1 PR as a draft until public-content and claim review is complete.
- Check that recorded observations, operator reports, and reference explanations
  remain distinguishable.
- Preserve the explicit SFCGAL remediation gap until real supporting detail is
  available.
- Keep Patroni DCS recovery, OpenProxy, and post-reboot validation IN PROGRESS
  until their actual results exist.
- Review all new artifacts for licenses, secrets, customer data, proprietary
  files, real addresses, and private identifiers before publishing.
