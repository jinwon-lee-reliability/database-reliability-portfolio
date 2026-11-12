# Validation record

## Scope: 2026-10-12

Existing repository inspected at base commit `0286b18` on `main`. Existing Java /
Bash reproduction cases and the Tiger Cloud / TimescaleDB learning lab were
preserved. This change adds a standalone reproduction case and an additive root
README entry; it removes no existing content.

Customer PoC status is **authorized / handover pending**. All execution below is
the independent synthetic lab on a GitHub-hosted runner, not customer work.

## Actual checks

| Check | Result | Evidence / limitation |
| --- | --- | --- |
| Python syntax on local Windows host | PASS | Bundled Python `py_compile` of `scripts/run_lab.py` |
| Git whitespace/error check | PASS | `git diff --cached --check` |
| Local Docker/PostgreSQL integration | NOT RUN | Docker executable and usable WSL Linux environment unavailable |
| Compose configuration and Python syntax on Linux CI | PASS | [Push run 38203138252](https://github.com/jinwon-lee-reliability/database-reliability-portfolio/actions/runs/38203138252) |
| Real Docker / PostgreSQL integration | PASS: all 15 assertions | Same run; source commit `60567322063f788a253a171e662d5b44a8a40c67` |
| Containers/volumes cleanup and evidence upload | PASS | `cleanup_passed=true`; 24 captured files uploaded |
| Pull-request-triggered repeat | PASS | [PR run 38203234117](https://github.com/jinwon-lee-reliability/database-reliability-portfolio/actions/runs/38203234117) for the same source commit |
| Downloaded evidence integrity | PASS | ZIP SHA-256 matches Actions digest; all 23 per-file hashes in `result.json` verified |

The first integration scenario ran **13:16:56–13:17:18 KST** on 2026-10-12
(04:16:56–04:17:18 UTC), using PostgreSQL **17.11** on Linux amd64. The default
Compose image is now pinned to the exact repository digest from that run:

```text
postgres@sha256:3645570cccdfa447589da9f57dd740faa29b30938e861289a5574b6ca6b03826
```

The immutable [evidence snapshot](evidence/2026-10-12-ci/README.md) records its
original source commit. It was produced before the subsequent documentation /
image-pin commit. The PR's current checks report validation of its latest head.
No hand-edited diagnostic output is used.

## Observed outcome

- Blocker PID **116**: `idle in transaction`, `Client / ClientRead`.
- Waiter PID **130**: active, `Lock / transactionid`, blocking PID array `{116}`.
- Transaction ID **744**: waiter ungranted `ShareLock`, blocker granted `ExclusiveLock`.
- Server emitted the wait log; the ordinary SELECT saw committed balance 1000,
  and the independent row UPDATE completed at 1001.
- The third conflicting UPDATE failed with **SQLSTATE 55P03** / lock timeout;
  the original blocking relationship persisted.
- Owner ROLLBACK discarded the attempted -100. Waiter committed -10; balance
  became 990. The short-transaction prevention example then committed -10.
- Final balances: **account 1 = 980, account 2 = 1001**. No scenario sessions
  remained, the recovered graph was empty, and disposable resources were removed.

PIDs, transaction IDs, timings, and file hashes are run-specific. A fresh run
should validate relationships and data outcomes rather than these literal IDs.

## Limits

The automated test covers owner ROLLBACK and transaction-local lock timeout.
Admin termination, idle-timeout disconnection, application retry/pool behavior,
production workloads, deadlock cycles, and HA failover are not tested here.
Manual instructions were inspected; an interactive Windows Docker walkthrough
was not executed. Patroni / etcd remains a [separate planned stage](FOLLOW_UP_HA.md).
