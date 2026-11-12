# Table Restore Failure and Recovery on OpenSQL

Personal synthetic lab on Rocky Linux with local OpenSQL and PostgreSQL 17.11. The source and restore databases were separate.

## Symptom

A table-only custom-format archive was created successfully. Restoring it into a separate database failed with `schema "migration_lab" does not exist`.

## Evidence

- `pg_dump -Fc -t migration_lab.test_data` succeeded for the synthetic table.
- The restore target lacked the `migration_lab` schema and the restore returned the missing-schema error.
- After the schema was created, `pg_restore --single-transaction --exit-on-error` succeeded.

## Root Cause

The archive selected a schema-qualified table with `-t`. A table-only dump does not automatically include all dependent objects, including a schema needed in an empty target. The target therefore could not create `migration_lab.test_data` until its schema existed.

## Action

Created `migration_lab` in the separate restore database and retried the archive restore with `--single-transaction --exit-on-error`. The successful retry applied the restore as a single transaction. The explicit `--exit-on-error` flag matches the recorded invocation.

## Validation

| Database | Row count | `SUM(value)` |
| --- | ---: | ---: |
| Source | 1,000 | 5,005,000 |
| Restored | 1,000 | 5,005,000 |

## Limitations

- Row count and aggregate checks cover this synthetic fixture. Row-by-row equality, index and constraint parity, privileges, and application behavior were outside the recorded validation.
- This exercise covered a table-only PostgreSQL archive restore on local OpenSQL. Oracle migration, production cutover and cleanup of the restore database were not validated in this record.

## References

- [PostgreSQL 17 pg_dump table selection](https://www.postgresql.org/docs/17/app-pgdump.html)
- [PostgreSQL 17 pg_restore transaction options](https://www.postgresql.org/docs/17/app-pgrestore.html)
