SELECT clock_timestamp() AS captured_at_utc,
       pid, backend_start, application_name, usename, state,
       clock_timestamp() - xact_start AS transaction_age,
       clock_timestamp() - query_start AS query_age,
       wait_event_type, wait_event,
       pg_blocking_pids(pid) AS blocking_pids,
       left(query, 400) AS query
FROM pg_stat_activity
WHERE datname = current_database()
  AND application_name IN ('lab_blocker', 'lab_waiter')
ORDER BY pid;
