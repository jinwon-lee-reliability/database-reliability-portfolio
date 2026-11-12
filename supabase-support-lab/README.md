# Supabase Database Support Hands-on Evidence

I used a personal Supabase Cloud lab with synthetic users and tickets to investigate Auth and the Data API, compare Supavisor connection modes, and trace PostgreSQL session and lock behavior. **Verified** refers to an observation I made during the lab. The procedures below show how to repeat the diagnostic checks. They are separate from the recorded results.

## Additional Lab Evidence

- [MVCC, VACUUM, and WAL on Supabase Cloud](mvcc-vacuum-wal/README.md)
- [Table restore failure and recovery on local OpenSQL](../opensql-lab/migration-failure-recovery/README.md)
- [OpenSQL recovery after reboot](../opensql-lab/restart-recovery/README.md)

## Observations

| Area | Status | Recorded result |
| --- | --- | --- |
| Auth, grants, and RLS | Verified | Signed in with JWTs, checked table privileges and RLS, and confirmed that test users A and B could each read only their own ticket. |
| Data API row visibility | Verified | `USING (false)` returned HTTP 200 with `[]`. Restoring the per-user policy recovered the expected A/B visibility. |
| Supavisor connectivity | Verified | Connected through the shared Session pooler on port `5432` and the shared Transaction pooler on port `6543`. |
| Supavisor backend reuse | Verified | Observed a PostgreSQL backend PID reused in transaction mode. |
| Temporary table visibility | Verified observation | In transaction mode, client B read synthetic data from a temporary table created by client A when both were served by the same PostgreSQL backend. |
| Database connection settings | Verified | `max_connections = 60` and `superuser_reserved_connections = 3` in this project. |
| Service activity | Verified | Observed Supavisor, PostgREST, and Storage connections in `pg_stat_activity`. |
| Idle transaction and lock wait | Verified | Reproduced `idle in transaction`. Used `pg_blocking_pids()` to identify PID `838063` blocking waiting PID `841717`. |
| SQL Editor data check | Verified | Queried two synthetic `support_tickets` rows in the SQL Editor. |
| Connection exhaustion | Not reproduced | This lab recorded connection settings and activity. It did not reach a connection limit. |

## Root Cause Analysis and Findings

**An empty REST response can be a row visibility issue.** A role can have `SELECT` and still see no rows when its RLS predicate evaluates to false. The working policy restored access only to the matching user's row. The [Auth and RLS RCA](auth-rls-rca-01/README.md) contains the original Auth, privilege, and recovery sequence, including safe REST examples.

**Logical client connections and PostgreSQL sessions have different lifetimes in transaction mode.** Supavisor can lend the same backend to separate clients. PostgreSQL temporary tables belong to a backend session and ordinarily survive a commit unless an `ON COMMIT` option changes that behavior. The observed visibility is consistent with temporary state remaining on a reused backend. The original table definition, effective database roles, pool configuration, and reset sequence were not captured. The lab establishes the observed behavior within this project. Cross-role and cross-project isolation were outside its scope.

**An idle transaction can hold locks even when it is between statements.** `pg_blocking_pids()` identified the blocking relationship in this lab. The exact lock mode, statements, and state of the recorded blocking PID were not retained. For session-dependent work, use a Session pooler or direct connection and explicitly scope temporary state to the operation. For lock waits, inspect the waiting and blocking sessions and coordinate rollback or commit with the transaction owner.

**Server slots and pooler client connections are separate measurements.** The two recorded settings describe PostgreSQL backend capacity and the superuser reserve. Service connections, any additional reserves, and pool settings affect available capacity. Use the lab's settings as a snapshot of that project.

## Reproduction and Diagnostics

Use a disposable project and synthetic data. Keep connection strings, keys, tokens, user IDs, and raw diagnostic output private. Use the pooler options from the project's Connect dialog so the host and mode match.

### Auth and row visibility

Follow the [existing Auth and RLS walkthrough](auth-rls-rca-01/README.md#reproduce-in-a-disposable-project) for the JWT, GRANT, and per-user RLS baseline. Apply the lab-only false predicate, check the empty response, restore the policy, and repeat the two user reads. The observed recovery was verified through both signed-in clients.

To repeat the separate SQL Editor data check, query only the synthetic row IDs.

```sql
select id from public.support_tickets order by id;
```

The SQL Editor confirms that the fixture rows exist under the editor's database role. The A/B Data API reads establish each user's row visibility.

### Pooler connection and backend PID

Connect a lab client to each shared pooler endpoint and run this read-only probe. Record the mode, client label, and returned PID. Repeat a few short requests and compare the samples. A backend can be reused in transaction mode, and repeated requests can also be served by different backends.

```sql
select pg_backend_pid() as backend_pid;
```

Use this probe to check backend assignment without creating or querying any temporary data. For workloads that require session state across transactions, choose session mode and validate the application with synthetic fixtures.

### PostgreSQL settings and activity

Use an authorized observer session. Collect settings and activity at roughly the same time. Group activity by service label, backend type, and state. PostgreSQL limits some details for other roles. The snapshot reflects connections visible to the observer at the time of the query.

```sql
select name, setting
from pg_settings
where name in ('max_connections', 'superuser_reserved_connections', 'reserved_connections')
order by name;

select application_name, backend_type, state, count(*) as connections
from pg_stat_activity
group by application_name, backend_type, state
order by application_name, backend_type, state;
```

### Controlled lock wait

Use a new schema and one synthetic row in the disposable project. Open Session pooler connections for two clients using the lab role that owns the fixture. Use a separate observer that can see both sessions. The example uses fresh PIDs and a bounded wait.

```sql
begin;
create schema support_pooler_lab;
revoke all on schema support_pooler_lab from public;
create table support_pooler_lab.lock_probe (id integer primary key, value integer not null);
insert into support_pooler_lab.lock_probe values (1, 0);
commit;
```

In client A, update the synthetic row and leave the transaction open briefly.

```sql
set application_name = 'support_lab_blocker';
begin;
set local idle_in_transaction_session_timeout = '90s';
update support_pooler_lab.lock_probe set value = 1 where id = 1;
```

In client B, request an update to that row. The local timeout bounds the wait. In a separate observer, inspect activity while B is waiting.

```sql
set application_name = 'support_lab_waiter';
begin;
set local lock_timeout = '15s';
update support_pooler_lab.lock_probe set value = 2 where id = 1;
```

```sql
select pid, application_name, state, wait_event_type, wait_event,
       case when wait_event_type = 'Lock' then pg_blocking_pids(pid) end as blocking_pids
from pg_stat_activity
where datname = current_database()
  and application_name in ('support_lab_blocker', 'support_lab_waiter');
```

For this procedure, the expected observation is A between statements in an open transaction and B waiting on a lock with A listed as a blocker. If the wait times out before inspection, roll back B before another attempt. Finish by issuing `ROLLBACK` in both lab clients, then confirm there are no remaining lab transactions or blockers. Run the following check in a fresh transaction. The expected result is one row with its original value and no lock wait.

```sql
begin;
set local lock_timeout = '5s';
select id, value from support_pooler_lab.lock_probe where id = 1 for update;
rollback;
```

Drop the disposable `support_pooler_lab.lock_probe` table and empty `support_pooler_lab` schema after both clients release their locks.

## Recovery, Cleanup, and Limits

| Check | Evidence status |
| --- | --- |
| Auth and RLS recovery | Verified. The working policy was restored and both test users again saw only their own ticket. |
| SQL Editor reads | Verified. Two synthetic rows were returned. This check confirms fixture visibility under the SQL Editor role. |
| Temporary state cleanup and post-cleanup validation | Unverified. The record ends with the visibility observation. |
| Lock release, waiter completion, and object cleanup | Unverified in the recorded lab. The replay instructions include separate cleanup and verification steps. |
| Connection exhaustion, queueing, and recovery under saturation | Not reproduced. The record contains a settings snapshot and observed activity. |

For a support handoff, retain the time window, connection mode, sanitized client and role labels, and the sampled backend PIDs. Include the exact wait and blocker relationship when available. Record whether recovery and cleanup were tested. This lab has no customer workload or production incident data.

## References

- [Supabase Cloud connection modes](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [Supavisor connection terminology](https://supabase.com/kb/troubleshooting/supavisor-and-connection-terminology-explained-9pr_ZO)
- [PostgreSQL temporary tables and ON COMMIT](https://www.postgresql.org/docs/current/sql-createtable.html)
- [PostgreSQL connection settings](https://www.postgresql.org/docs/current/runtime-config-connection.html)
- [PostgreSQL session monitoring](https://www.postgresql.org/docs/current/monitoring-stats.html)
- [PostgreSQL backend and lock information functions](https://www.postgresql.org/docs/current/functions-info.html)
