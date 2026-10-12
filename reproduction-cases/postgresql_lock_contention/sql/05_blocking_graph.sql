SELECT clock_timestamp() AS captured_at_utc,
       w.pid AS waiter_pid, w.application_name AS waiter_application,
       w.wait_event_type, w.wait_event,
       b.pid AS blocker_pid, b.application_name AS blocker_application,
       b.state AS blocker_state,
       clock_timestamp() - b.xact_start AS blocker_transaction_age,
       left(w.query, 400) AS waiting_query,
       left(b.query, 400) AS blocker_last_query
FROM pg_stat_activity AS w
CROSS JOIN LATERAL unnest(pg_blocking_pids(w.pid)) AS p(blocker_pid)
LEFT JOIN pg_stat_activity AS b ON b.pid = p.blocker_pid
WHERE w.datname = current_database()
  AND w.application_name = 'lab_waiter';
-- pg_blocking_pids includes hard blockers and wait-queue blockers.
-- In general, PID 0 can represent a prepared transaction (no live backend).
