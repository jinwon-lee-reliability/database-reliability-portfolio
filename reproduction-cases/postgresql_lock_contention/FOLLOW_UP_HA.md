# Planned next stage: Patroni / etcd HA and Failover Lab

**Status: planned, not implemented or executed.** This is a separate independent
synthetic lab. It is not customer PoC execution or production-support evidence.
The customer PoC remains authorized / handover pending as of 2026-10-12.

## Entry gate

First complete and review the lock RCA lab's Docker execution evidence. Use actual
handover details to choose any additional targeted learning, without copying
customer configurations, topology, data, or logs into this public portfolio.

## Proposed scope

- Three PostgreSQL/Patroni nodes and a three-member etcd quorum in an isolated
  Docker network. Pin reviewed versions and record image digests.
- Synthetic writes with unique IDs and timestamps; a separate client/router path
  so client reconnection can be measured independently from leader election.
- Document asynchronous versus synchronous replication tradeoffs before injection.
- Planned switchover, abrupt primary-container loss, one replica loss, and etcd
  member/quorum failure as distinct cases. Partition/split-brain testing requires
  an explicit fencing hypothesis and a reviewed isolated topology.
- Capture Patroni/etcd state, timeline, WAL/LSN and replication lag, election and
  PostgreSQL logs, and client-visible errors/reconnection.
- Verify there is only one writable leader, quantify observed recovery time and
  acknowledged-write survival for the selected replication mode, and test old
  leader rejoin. Do not claim zero data loss without the relevant evidence.

## Deliverables and completion gate

A separate reproduction-case directory with Compose, configuration, injection
and restoration scripts, fresh-run checks, evidence capture, and per-case RCA.
Distinguish expected outcomes from measured outcomes. Report observed RTO and
RPO with workload/mode constraints rather than implying production guarantees.
No HA implementation or execution result is included in the lock-contention PR.
