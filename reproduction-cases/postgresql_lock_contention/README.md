# PostgreSQL Lock Contention RCA Lab

## Scope and evidence boundary

An independent, public, **synthetic demonstration** of PostgreSQL incident reproduction,
diagnosis, recovery, and prevention. It extends this portfolio's reproduction cases;
it does not use the legacy Tibero/Java failure framework or require TimescaleDB.
No customer data, schema, configuration, logs, or workload is included.

As of **2026-10-12**, participation in an OpenSQL customer PoC is **authorized;
handover is pending**. No PostgreSQL customer project execution or production
PostgreSQL support accomplishment is claimed here. This lab's execution evidence
is reported separately in [VALIDATION.md](VALIDATION.md).

## Problem and simulated impact

An application updates a hot account and then leaves its transaction open while
waiting for another action. A second application tries to update the same account.
The second UPDATE appears slow even though its SQL and primary-key access are simple.
In a real service, this pattern could cause request latency and connection-pool
pressure. This demo measures lock behavior; it does not simulate customer traffic,
an SLA breach, throughput, or a production outage.

## Environment

- Docker Engine/Desktop **with Linux containers** and Docker Compose v2 supporting
  `up --wait` (Compose 2.20+ recommended).
- Python 3.10+ for orchestration; only the standard library is used.
- Official PostgreSQL 17 Debian Bookworm image; two synthetic integer-balance rows.
- All connections run through `docker compose exec`; no host database port is published.
- `log_lock_waits=on`, `deadlock_timeout=500ms`, UTC logs, PID/application log prefix.
  The short diagnostic threshold is a lab setting, not a production recommendation.
- The default image is pinned to the immutable digest captured from the successful
  PostgreSQL 17.11 / Bookworm CI run. The runner records the actual version, image
  ID, and repository digest. Set `PG_IMAGE` to another reviewed `postgres@sha256:...`
  digest to evaluate an update; overrides such as `postgres:17-bookworm` follow a
  moving tag and should be resolved back to a digest for repeatable evidence.
  Major-version overrides other than 17 deliberately fail the version check.
- Credentials are disposable demo values and the `lab` role is a superuser for
  observability. Production access should follow least privilege; cross-role
  activity visibility can require `pg_read_all_stats`, and signaling is separate.

## Automated reproduction and minimum integration tests

From this directory, on Windows, Linux, or macOS:

```text
python scripts/run_lab.py
```

The runner creates a unique `pg-lock-rca-<id>` Compose project and a fresh
`artifacts/<project>/` directory. It starts and resets only that disposable
database, polls for actual session/lock conditions, captures evidence, recovers,
and removes its own containers and volumes. It never connects to an external DB.
Exit code 0 requires all checks **and** cleanup to pass; failure records the error,
available diagnostics, and cleanup status in `result.json`.

Verified conditions required by the runner:

1. PostgreSQL major version is 17.
2. `lab_blocker` is `idle in transaction`; active `lab_waiter` waits on
   `Lock / transactionid` and `pg_blocking_pids` identifies that blocker.
3. The captured blocking graph contains exactly the scenario pair.
4. `pg_locks` shows the waiter's ungranted transaction `ShareLock` and the
   blocker's granted `ExclusiveLock` for the **same transaction ID**.
5. The server emits a lock-wait log after the diagnostic threshold.
6. An ordinary SELECT sees the committed balance 1000; an UPDATE of account 2
   completes independently, changing it to 1001.
7. A third same-row UPDATE with `lock_timeout=1s` fails with SQLSTATE `55P03`;
   the original blocker and waiter remain in the blocking relationship.
8. Owner ROLLBACK releases the first transaction; the waiter commits successfully.
   Account 1 becomes 990, proving the blocker's attempted -100 was discarded.
9. The recovered graph is empty. A subsequent short transaction with local
   timeouts completes, changing account 1 to 980. No scenario connections remain.

The workflow [PostgreSQL Lock Contention RCA](../../.github/workflows/postgresql-lock-rca.yml)
runs the same real integration checks on GitHub's Linux Docker runner and uploads
evidence on success or failure (30-day retention). It also validates Compose and
Python syntax. Docker must be available for integration checks; syntax alone
does not establish PostgreSQL behavior.

## Manual reproduction: three terminals

Use this sequence independently of the automated runner. Keep all terminals in
this directory. The default manual project is `pg-lock-rca`.

**Initialize** (no blocker/waiter sessions should be open):

```text
docker compose up -d --wait
docker compose exec -T postgres psql -X -U lab -d lock_lab -v ON_ERROR_STOP=1 -f /lab/sql/00_setup.sql
```

**Terminal A — blocker:** open an interactive psql connection:

```text
docker compose exec postgres psql -X -U lab -d lock_lab -v ON_ERROR_STOP=1
```

Then enter:

```sql
\i /lab/sql/01_blocker.sql
```

Leave the connection open at its prompt. Do not run this blocker with `psql -f`
in a one-shot command: process exit would roll back the transaction immediately.
Its idle transaction timeout is 120 seconds, so capture and recover promptly.

**Terminal B — waiter:**

```text
docker compose exec -T postgres psql -X -U lab -d lock_lab -v ON_ERROR_STOP=1 -f /lab/sql/02_blocked.sql
```

This waits at UPDATE until A releases its transaction, or until the 45-second
statement timeout. If the timeout fires, rerun B while A is still holding the lock.

**Terminal C — observe and capture** (PowerShell or a POSIX shell):

```text
python -c "from pathlib import Path; Path('artifacts/manual').mkdir(parents=True, exist_ok=False)"
docker compose exec -T postgres psql -X -U lab -d lock_lab -v ON_ERROR_STOP=1 -P pager=off -f /lab/sql/03_activity.sql > artifacts/manual/activity.txt
docker compose exec -T postgres psql -X -U lab -d lock_lab -v ON_ERROR_STOP=1 -P pager=off -f /lab/sql/04_locks.sql > artifacts/manual/locks.txt
docker compose exec -T postgres psql -X -U lab -d lock_lab -v ON_ERROR_STOP=1 -P pager=off -f /lab/sql/05_blocking_graph.sql > artifacts/manual/blocking.txt
docker compose logs --no-color --timestamps postgres > artifacts/manual/server.log
```

Choose a new capture directory on each manual run to preserve earlier evidence.
Use autocommit for observation; a long-running observer transaction can retain
an old activity snapshot. The automated runner uses fresh observers each time.

## Investigation and RCA

| Hypothesis | Diagnostic evidence | Interpretation |
| --- | --- | --- |
| Expensive SQL or broad resource exhaustion | Simple primary-key UPDATE; ordinary read and different-row UPDATE still complete | Supports a contention diagnosis for this controlled scenario; not a general CPU/I/O exclusion method |
| Lock contention | `wait_event_type=Lock`, `wait_event=transactionid`, nonempty blocking PID array | The UPDATE is waiting for a transaction to finish |
| Open transaction retains ownership | Blocker is `idle in transaction`, has a transaction start time, and owns the matching transaction lock | Its UPDATE finished, but its transaction did not |
| Deadlock | One directional waiter -> idle blocker edge, no reverse wait | This scenario is a blocking wait, not a deadlock cycle |

**Root cause in this synthetic scenario:** A's uncommitted UPDATE owns the row;
B's conflicting UPDATE must wait for A's transaction outcome. Application code
retained the transaction after the SQL completed. The blocker can wait for its
client (`ClientRead`) while the waiter waits for a lock: an idle backend is not
necessarily harmless.

`pg_stat_activity.query` is the **last** statement for an idle backend. Here it
may show `SELECT pg_backend_pid()`, not the UPDATE that acquired the row lock.
Correlate transaction age, backend identity, the reproduced workload, blocking
PIDs, locks, and logs; do not infer lock ownership from last-query text alone.

Row locks are not generally listed individually in `pg_locks`. In this two-session
UPDATE case the wait appears on `transactionid`; both sessions can also hold
compatible relation `RowExclusiveLock`s. A relation lock's presence or mode alone
does not prove who blocks whom. `pg_blocking_pids` supplies the relationship;
the lock rows corroborate its mechanism. More complex queues, parallel workers,
or prepared transactions require additional interpretation.

## Recovery and data validation

After capturing evidence, in **Terminal A**, issue:

```sql
ROLLBACK;
\q
```

B should complete with balance **990** and COMMIT. Rolling back A discards its
uncommitted change; it does not undo B's later committed UPDATE. Run:

```text
docker compose exec -T postgres psql -X -U lab -d lock_lab -v ON_ERROR_STOP=1 -f /lab/sql/08_verify.sql
```

For the manual rollback scenario alone, expect account 1 = 990 and account 2 =
1000, with no blocker/waiter connection. The automated scenario additionally
updates account 2 and executes prevention SQL, so its final balances differ.

In an operational incident, coordinate with the transaction owner first. COMMIT
is appropriate only if that transaction's work is valid and intended. If the
owner cannot release it, an authorized administrator may terminate a verified
backend; termination disconnects it and rolls back its uncommitted transaction.
Recheck PID, `backend_start`, user, database, application, transaction state,
and impact immediately before signaling to avoid a stale/reused PID. This
alternative is documented here; the automated test uses owner ROLLBACK only.
`pg_cancel_backend` cancels a running statement; it is not a dependable release
mechanism for an idle open transaction. Do not restart the whole database for
this demonstrated single blocking transaction.

## Prevention and verification

- End transactions promptly and move user interaction or remote calls outside them.
  Verify the application commits/rolls back on success, exceptions, and cancellation.
- Set transaction-local `lock_timeout` below `statement_timeout` where the business
  operation can tolerate a bounded wait. A timeout limits waiting, not lock ownership
  in another session. Roll back after an error; retry only appropriate/idempotent
  operations with a bounded retry policy and jitter.
- Consider a role/session-specific `idle_in_transaction_session_timeout` and
  validate pool handling of disconnections. The blocker already has a 120-second
  lab safeguard; idle-timeout disconnection is not part of the automated test.
- Monitor aged open transactions, lock wait duration, waiter/blocker fan-out, and
  pool saturation. Choose alert thresholds from actual workload/SLO evidence.

`06_lock_timeout.sql` verifies bounded lock waiting while the blocker still exists.
After recovery, `07_short_transaction.sql` demonstrates prompt commit with local
timeouts. These checks do not prove an application's retry or pool behavior.

To repeat manually, close all scenario connections before rerunning setup. When
finished, remove only this disposable lab:

```text
docker compose down --volumes
```

## Evidence inventory

The runner saves human-readable activity/locks/graph snapshots before and after
recovery, timestamped JSON graph edges, blocker/waiter transcripts, lock-timeout
SQLSTATE, independent-row and read checks, final balances, server logs, Docker/
Compose versions, resolved Compose config, PostgreSQL settings, image metadata,
and cleanup output. `result.json` records assertions, UTC times, source commit
in CI, exit status, cleanup status, and SHA-256 hashes for captured files.
`artifacts/` is ignored to prevent automatic publication of future captures.
This lab's generated evidence is synthetic; review any external evidence before
publishing it. There is no dependency on customer access or PoC execution.

The reviewed [2026-10-12 CI evidence snapshot](evidence/2026-10-12-ci/README.md)
preserves the actual successful run in Git, independently of CI artifact expiry.

## Separate follow-up

[Patroni / etcd HA and Failover plan](FOLLOW_UP_HA.md) is an unimplemented next
stage with its own topology, failure hypotheses, and validation gates.

## PostgreSQL primary references

- [Activity visibility, states, wait events, and snapshot behavior](https://www.postgresql.org/docs/17/monitoring-stats.html#MONITORING-PG-STAT-ACTIVITY-VIEW)
- [pg_locks and row-lock interpretation](https://www.postgresql.org/docs/17/view-pg-locks.html)
- [pg_blocking_pids semantics](https://www.postgresql.org/docs/17/functions-info.html#FUNCTIONS-INFO-SESSION)
- [Timeout settings](https://www.postgresql.org/docs/17/runtime-config-client.html)
- [Cancel and terminate functions](https://www.postgresql.org/docs/17/functions-admin.html#FUNCTIONS-ADMIN-SIGNAL)
- [Lock-wait logging](https://www.postgresql.org/docs/17/runtime-config-logging.html#GUC-LOG-LOCK-WAITS)
- [Official PostgreSQL container image](https://hub.docker.com/_/postgres)
