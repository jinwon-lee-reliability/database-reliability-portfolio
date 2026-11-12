# MVCC, VACUUM, and WAL on Supabase Cloud

Personal synthetic lab on Supabase Cloud with PostgreSQL 17.11 and a dedicated table of 10,000 rows.

## Symptom

After an `UPDATE`, the measured WAL and total table size increased. A manual `VACUUM` left 10,000 dead row versions in place while a long `REPEATABLE READ` transaction remained open.

## Evidence

| Check | Recorded result |
| --- | --- |
| Test fixture | 10,000 synthetic rows |
| WAL generated after the `UPDATE` | 4,120 kB |
| Total table size before and after the `UPDATE` | 2,712 kB → 5,352 kB |
| `VACUUM` while the long transaction was open | `0 removed, 10000 dead but not yet removable` |
| `VACUUM` after the long transaction ended | `10000 removed, 0 dead but not yet removable` |

## Root Cause

PostgreSQL `UPDATE` creates a new version of a row. The earlier version can remain visible to an older MVCC snapshot. In `REPEATABLE READ`, a transaction retains the snapshot acquired by its first non-transaction-control statement. The change in `VACUUM` results after the long transaction ended supports snapshot retention as the reason the old versions could not be removed during the first run.

## Action

Ended the long transaction and ran `VACUUM` again. Checked the logical row count and `SUM`, then removed the disposable lab schema.

## Validation

The second `VACUUM` removed 10,000 obsolete row versions and reported zero dead versions that were still ineligible for removal. The logical row count and `SUM` matched in the lab checks. The lab schema was deleted.

## Limitations

- The WAL and table sizes are measurements from this lab run. The evidence does not isolate other WAL activity during the measurement window.
- The reported size change is from before to after the `UPDATE`. No post-`VACUUM` size measurement is recorded. Standard `VACUUM` generally makes space available for reuse inside the relation.
- The exercise reproduced snapshot retention during manual `VACUUM`. Autovacuum failure and WAL exhaustion were not reproduced.

## References

- [PostgreSQL 17 transaction isolation](https://www.postgresql.org/docs/17/transaction-iso.html#XACT-REPEATABLE-READ)
- [PostgreSQL 17 routine vacuuming](https://www.postgresql.org/docs/17/routine-vacuuming.html)
