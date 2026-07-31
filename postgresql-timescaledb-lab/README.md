# PostgreSQL / Tiger Data (TimescaleDB) Hands-on Lab

## Overview

This repository documents my hands-on learning with PostgreSQL and Tiger Data (TimescaleDB) while preparing for Database Support Engineer roles.

The objective is not to claim production PostgreSQL experience, but to build practical understanding of PostgreSQL internals, execution plans, time-series storage, and database troubleshooting through reproducible lab exercises.

All experiments were performed using Tiger Cloud.

---

## Environment

- PostgreSQL
- Tiger Data (TimescaleDB)
- Tiger Cloud
- SQL
- EXPLAIN / EXPLAIN ANALYZE

---

## Topics Covered

### PostgreSQL

- SQL query analysis
- Execution plans
- `EXPLAIN`
- `EXPLAIN ANALYZE`
- Query optimization fundamentals

### TimescaleDB

- Hypertables
- Time partitioning
- Hash dimensions
- Chunk creation
- Chunk inspection
- Chunk pruning
- Index behavior across chunks

### Hypercore

- Rowstore
- Columnstore
- Mixed rowstore/columnstore storage
- Columnar scans
- Vectorized aggregation

### Compression

- Manual compression
- Compression statistics
- Compression policies
- Storage reduction analysis

### Time-Series Analytics

- `time_bucket`
- Continuous Aggregates
- Continuous Aggregate metadata
- Materialization hypertables

---

## Hands-on Exercises

### 1. Hypertables

Created a hypertable and verified automatic chunk creation based on time partitions.

**Verified**

- Hypertable metadata
- Chunk creation
- Time partition boundaries

---

### 2. Hash Dimension

Added an additional hash dimension to understand multi-dimensional partitioning.

Verified:

- Hash partitions
- Chunk allocation
- Metadata inspection

---

### 3. Query Plans

Compared execution plans using:

```sql
EXPLAIN
EXPLAIN ANALYZE
```

Observed:

- Sequential Scan
- Index Scan
- Append
- Chunk pruning

---

### 4. Hypercore

Converted historical chunks into Hypercore columnstore.

Verified:

- Rowstore
- Columnstore
- Mixed storage behavior
- ColumnarScan execution

---

### 5. Compression

Measured storage before and after compression.

Observed:

- Approximately 86% storage reduction
- Significant reduction of table and index storage
- Increased TOAST usage for compressed columnar data

---

### 6. Continuous Aggregates

Created a Continuous Aggregate using `time_bucket()`.

Verified:

- Materialized hypertable creation
- Metadata inspection
- Querying precomputed time-series summaries

---

## Key Findings

During the lab I confirmed:

- Chunk pruning reduces unnecessary scans.
- Execution plans change depending on storage layout.
- Hypercore supports mixed rowstore and compressed columnstore data.
- Compression significantly reduces storage usage.
- Continuous Aggregates improve analytical query efficiency.
- Tiger Cloud provides an accessible environment for learning PostgreSQL time-series concepts.

---

## Why This Lab

My professional experience is centered on enterprise database support, customer escalations, production incident response, SQL performance analysis, and root cause investigation.

This lab demonstrates how I apply those same investigation skills while learning PostgreSQL and Tiger Data technologies through evidence-based testing and execution-plan analysis.

---

## Next Topics

Planned areas for continued learning include:

- PostgreSQL system catalogs
- pg_stat_activity
- pg_stat_statements
- VACUUM and autovacuum
- Lock monitoring
- WAL and replication fundamentals
- Backup and recovery workflows
