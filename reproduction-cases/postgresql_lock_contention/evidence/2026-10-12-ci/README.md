# Reviewed synthetic CI evidence: 2026-10-12

These are original, unedited files downloaded from the successful
[GitHub Actions run 38203138252](https://github.com/jinwon-lee-reliability/database-reliability-portfolio/actions/runs/38203138252).
Source commit: `60567322063f788a253a171e662d5b44a8a40c67`.
Scenario: `pg-lock-rca-507926fdb5c6`; PostgreSQL 17.11, Linux amd64.
They contain only this independent synthetic lab and public CI environment metadata.
The password shown in Compose is the disposable `synthetic-demo-only` value.

The [downloaded artifact](https://github.com/jinwon-lee-reliability/database-reliability-portfolio/actions/runs/38203138252/artifacts/11726054533)
has SHA-256 `224bb67a5f3b3f5dd7d7793f416b840532464b8f31a745b5f3b968683d4735a4`.
It expires after 30 days; these 24 captured files remain versioned here.
`result.json` hashes the other 23 captured files; this README is added context.
`evidence/.gitattributes` disables newline conversion to preserve captured bytes.

Start with [activity](before-recovery-activity.txt), [locks](before-recovery-locks.txt),
[blocking graph](before-recovery-graph.json), [server logs](server.log),
[timeout SQLSTATE](lock-timeout.txt), [final data/session check](final-verification.txt),
and [assertions / hashes](result.json). Compare [after-recovery graph](after-recovery-graph.json)
and [cleanup](cleanup.txt).

All 15 integration assertions passed and cleanup succeeded. This snapshot is
execution evidence for an independent lab, not customer PoC or production support.
PID / transaction ID values and timestamps are specific to this run.
