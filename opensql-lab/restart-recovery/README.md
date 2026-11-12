# OpenSQL Recovery After Reboot

Personal local OpenSQL lab. This case records the service state after a reboot and the observed result of a manual Patroni start.

## Symptom

After rebooting the lab host, Patroni and PostgreSQL were not running. OpenProxy was also down.

## Evidence

| Check | Recorded observation |
| --- | --- |
| etcd after reboot | Process running |
| Patroni and PostgreSQL after reboot | Not running before manual recovery |
| Patroni after manual start | `Leader` / `running`, timeline `4` |
| PostgreSQL after manual start | Listening on port `5432` |
| OpenProxy | Port `6432` not listening |

## Root Cause

**Working hypothesis.** Patroni was not configured to start automatically at boot. The post-reboot state and successful manual start support investigating that hypothesis. The systemd unit configuration and boot logs have not been verified, so the startup cause remains open.

## Action

Confirmed the etcd process was running, started Patroni manually and checked Patroni state and the PostgreSQL listener.

## Validation

Patroni reported `Leader` and `running` on timeline `4`, and PostgreSQL listened on `5432`. These checks confirm the observed Patroni state and direct database listener after the manual start. OpenProxy remained down on `6432`.

## Limitations

- An etcd process was observed. Cluster health and quorum were not verified in this restart check.
- PostgreSQL listening on `5432` confirms the socket state. An end-to-end SQL check and client access through OpenProxy were not recorded.
- OpenProxy recovery and automatic startup through systemd remain unverified. A further reboot with service-status, listener and connection checks is pending.

## References

- [Patroni cluster status and timeline fields](https://patroni.readthedocs.io/en/latest/patronictl.html#patronictl-list)
