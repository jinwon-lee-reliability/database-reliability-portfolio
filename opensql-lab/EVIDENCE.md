# Evidence ledger ? v0.1

**Cutoff:** 2026-10-14 KST. **Overall DCS RCA:** IN PROGRESS.

This is a transcription of operator-executed terminal/work records and the
operator's completion report. Original terminal files, full transcripts, and
their checksums are not attached. Some historical observations were available
only as summaries; these are not raw log artifacts or an independent replay.
No missing output, exit code, checksum, performance result, or runtime version
has been fabricated.

The public reader can inspect claim scope, chronology, references, and the
listed values. Exact reproduction and cryptographic verification of the
original private sessions are not possible from v0.1 alone.

## Claim register

| ID | Source and date | Recorded fact or operator report | Verification limit |
|---|---|---|---|
| H01 | RECORDED, Oct 12 | Hyper-V features Enabled; console file missing; module import failed; PowerShell 64-bit; management-tool cycling ineffective; DISM found repairable component-store damage. Later record: RestoreHealth completed, SFC found no integrity violations, console opened after reboot. | Specific damaged files/packages and full repair logs absent; no claim of a verified PowerShell-module recovery check |
| I01 | RECORDED, Oct 13 | Rocky Linux 9.8; local OpenSQL 3.17.11.7 single-node installation complete; pre-address-change Patroni Leader/running. | Embedded PostgreSQL and Patroni versions not captured; initial Leader is a pre-migration observation |
| I02 | RECORDED + REPORTED, Oct 13/14 | Installed/available EPEL SFCGAL 1.5.0 did not meet recorded >=2.0.0 installation requirement. Operator reports prerequisite conflicts resolved and installation complete. | Exact missing-package list and resolution method absent; no evidence of a >=2.0 upgrade or GIS tests |
| N01 | RECORDED + REPORTED, Oct 14 | Hyper-V Internal Switch and static private guest address configured; old address remained in service configuration after the change. | Original host/guest network configuration not attached; NAT, gateway, external routing, and reboot persistence not verified |
| P01 | RECORDED, Oct 14 | Patroni attempted the old etcd client address and timed out; local PostgreSQL port 5432 accepted connections; old-address references found in the three component configurations. | Stale endpoint is an observed contributor; corrected Patroni connection and current Leader pending |
| E01 | RECORDED, Oct 14 approximately 13:15 KST | Snapshot save succeeded; approximately 41 kB recorded; etcd server 3.6.0 reported during the save; configuration backups also recorded. | Snapshot bytes, hash/revision/key-count output, and restore test not published |
| E02 | RECORDED, Oct 14 approximately 13:26 KST | Existing member peer URL updated; etcd configuration applied; service restarted; later member listing used new peer and client addresses. | Full membership output, environment file, and data-directory configuration withheld; exact configuration-line diff not available |
| E03 | RECORDED, Oct 14 approximately 13:37 KST | Service active; local health true; member started; same member ID before and after; peer/client URLs use new static address. | Raw identity and addresses redacted; no full original output bundle, keyspace-integrity test, or post-VM-reboot validation |

Dates identify recorded sessions, not CI execution. Approximate times are
chronological anchors, not performance or outage-duration measurements.

## Recorded post-migration values

These are values transcribed from the operator record, not a fabricated
complete `member list` or terminal log.

| Check | Recorded value |
|---|---|
| etcd service activity | `active` |
| Local HTTP health response | `{"health":"true","reason":""}` |
| Member status | `started` |
| Peer URL | New static address, port 2380; literal address withheld |
| Client URL | New static address, port 2379; literal address withheld |
| Before/after member identity | Equal in the operator record; literal ID withheld |

No `etcdctl endpoint health` output, SQL query results, or Leader result after
the address migration is substituted for these checks.

## Redacted shapes of recorded commands

These are historical command shapes with private identifiers replaced by
variables. The variables have no supplied values here; this is not a runnable
installation or migration script.

Snapshot save (E01):

```sh
env -u ETCDCTL_ENDPOINTS -u ETCDCTL_API \
  etcdctl --endpoints=http://127.0.0.1:2379 \
  snapshot save "$SNAPSHOT_PATH"
```

The recorded command explicitly selected the local endpoint and cleared the
two listed environment variables for that invocation. The snapshot path is
withheld.

Existing-member peer update (E02):

```sh
etcdctl member update "$MEMBER_ID" --peer-urls="$NEW_PEER_URL"
```

A local service restart and subsequent checks were recorded. The service
configuration and proprietary service wrapper are not reproduced. No snapshot
restore or new-member creation is claimed.

## Outstanding evidence

- Exact dependency remediation, package provenance, and any optional GIS test.
- Reviewed original diagnostic/validation extracts with timestamps and redaction
  notes; hashes only after those artifacts actually exist.
- Actual embedded PostgreSQL and installed Patroni/client versions.
- Post-change Patroni DCS connection, current Leader, and a small SQL check.
- OpenProxy effective address and successful connection/query.
- Service/network/member checks after a full VM reboot.
- Independently executed upstream-only reproduction with synthetic data.

## Publication review performed for this revision

The added documents use symbolic addresses/member IDs and contain no license
contents, credentials, customer identifiers, proprietary payload, copied
installer/configuration, snapshot bytes, or full private logs. No lab commands
were executed while preparing this documentation.

Review before merge must confirm source accuracy, the dependency-remediation
gap, the outstanding DCS state, and that every claim remains within the
documented evidence level. New evidence must be reviewed before being added;
local ignore rules do not protect files that are already tracked.
