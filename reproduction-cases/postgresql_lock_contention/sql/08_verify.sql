SELECT id, balance, note FROM lock_demo.accounts ORDER BY id;
SELECT pid, application_name, state, pg_blocking_pids(pid) AS blocking_pids
FROM pg_stat_activity
WHERE datname = current_database()
  AND application_name IN ('lab_blocker', 'lab_waiter', 'lab_timeout');
-- After automated recovery + prevention: account 1 = 980, account 2 = 1001;
-- no remaining scenario sessions and no blocked PID.
