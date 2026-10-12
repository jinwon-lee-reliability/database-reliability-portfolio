SELECT clock_timestamp() AS captured_at_utc,
       a.pid, a.application_name, a.state,
       l.locktype, l.mode, l.granted,
       l.relation::regclass AS relation,
       l.transactionid, l.virtualxid, l.page, l.tuple,
       l.waitstart
FROM pg_locks AS l
JOIN pg_stat_activity AS a ON a.pid = l.pid
WHERE a.datname = current_database()
  AND a.application_name IN ('lab_blocker', 'lab_waiter')
ORDER BY l.granted, a.pid, l.locktype, l.mode;
-- Row locks live on disk; a row-update waiter usually waits on transactionid.
-- A granted relation RowExclusiveLock alone does NOT identify the blocker.
